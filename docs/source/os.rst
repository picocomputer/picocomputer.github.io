============================
RP6502-OS
============================

RP6502 - Operating System

Introduction
============

The :doc:`ria` runs a 32-bit protected operating system that
you can call from the 6502. The :doc:`os` does not use any 6502 RAM
and will not interfere with developing a native 6502 OS.

The :doc:`os` is loosely based on POSIX with an ABI similar to
CC65's fastcall. It provides stdio.h and unistd.h services to both
CC65 and LLVM-MOS compilers. There are also calls access RP6502
features and manage FAT32 filesystems. ExFAT is ready to go and will
be enabled when the patents expire.


Memory Map
==========

There is no ROM. Nothing in zero page is used or reserved. There isn't
a book-sized list to study. The Picocomputer design lets you start with
a clean slate for every project. VGA, audio, storage, keyboards, mice,
gamepads, RTC, and networking are all accessed using only the 32
registers of the RIA.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Address
     - Description
   * - 0000-FEFF
     - RAM, 63.75K
   * - FF00-FFCF
     - Unassigned
   * - FFD0-FFDF
     - VIA, see the `WDC datasheet
       <https://www.westerndesigncenter.com/wdc/w65c22-chip.php>`_
   * - FFE0-FFFF
     - RIA, see the :doc:`RP6502-RIA datasheet <ria>`
   * - 10000-1FFFF
     - XRAM, 64K for :doc:`ria` and :doc:`vga`

The unassigned space is available for hardware experimenters. You will
need to design your own address decoder logic hardware to use this
address space. It is recommended that additional VIAs be added "down"
and other hardware added "up". For example: VIA0 at $FFD0, VIA1 at
$FFC0, SID0 at $FF00, and SID1 at $FF20.


Application Binary Interface (ABI)
==================================

The binary interface for calling the operating system is based on
fastcall from the `CC65 Internals
<https://cc65.github.io/doc/cc65-intern.html>`_. The RP6502-OS
fastcall does not use or require anything from CC65 and is easy for
assembly programmers to use. At its core, the OS API ABI is based on
a C ABI with four simple rules.

* Stack arguments are pushed left to right.
* Last argument passed by register A, AX, or AXSREG.
* Return value in register AX or AXSREG.
* May return data on the stack.

A and X are the 6502 registers. The pseudo register AX combines them
for 16 bits. AXSREG is 32 bits with 16 SREG bits.  Let's look at how
to make an OS call through the RIA registers. All OS calls are
specified as a C declaration like so:

.. c:function:: int doit(int arg0, int arg1);

The RIA has registers called RIA_A, RIA_X, and RIA_SREG. An int is 16
bits, so we set the RIA_A and RIA_X registers with arg1. I'll use "A"
for the 6502 register and "RIA_A" for the RIA register in this
explanation.

We use the XSTACK for arg0. Reading or writing data to the
RIA_XSTACK register removes or adds bytes to the XSTACK. It's a
top-down stack, so push each argument from left to right and maintain
little endian-ness in memory.

To execute the call, store the operation ID in RIA_OP. The operation
begins immediately. You can keep doing 6502 things, like running a
loading animation, by polling RIA_BUSY. Or, JSR RIA_SPIN to block.

The JSR RIA_SPIN method can unblock in less than 3 clock cycles and
does an immediate load of A and X. Sequential operations will run
fastest with this technique. Under the hood, you're jumping into a
self-modifying program that runs on the RIA registers.

.. code-block:: asm

   BRA #$??      ; RIA_BUSY {-2 or 0}
   LDA #$??      ; RIA_A
   LDX #$??      ; RIA_X
   RTS

Polling is simply snooping on the above program. The RIA_BUSY register
is the -2 or 0 in the BRA above. The RIA datasheet specifies bit 7
indicates busy, which the 6502 can check quickly by using the BIT
operator to set flag N. Once clear, we read RIA_A and RIA_X with
absolute instructions.

.. code-block:: asm

   wait:
   BIT RIA_BUSY
   BMI wait
   LDA #RIA_A
   LDX #RIA_X

All operations returning RIA_A will also return RIA_X to assist with
C integer promotion. RIA_SREG is only updated for
32-bit returns. RIA_ERRNO is only updated if there is an error.

Some operations return strings or structures on the stack. You must
pull the entire stack before the next call. However, tail call
optimizations are possible. For example, you can chain read_xstack()
and write_xstack() to copy a file without using any RAM or XRAM.

Short Stacking
---------------

In the never ending pursuit of saving all the cycles, it is possible to
save a few on the stack push if you don't need all the range. This only
works on the stack argument that gets pushed first. For example:

.. code-block:: C

   long f_lseek(long offset, char whence, int fildes)

Here we are asked for a 64 bit value. Not coincidentally, it's in the
right position for short stacking. If, for example, you only need 24
bits, push only three bytes. The significant bytes will be implicit.

Shorter Integers
-----------------

Many operations can save a few cycles by ignoring REG_X. All integers
are always available as 16 bits to assist with C integer promotion.
However, many operations will ignore REG_X on the register parameter
and limit their return to fit in REG_A. This will be documented below
as "A regs".

Bulk Data
---------

Functions that move bulk data may come in two flavors. These are any
function with a pointer parameter. A RAM pointer is meaningless to the
RIA because it can not change 6502 RAM. Instead, we use the XSTACK
or XRAM for data buffers.

Bulk XSTACK Operations
~~~~~~~~~~~~~~~~~~~~~~

These only work if the count is 512 or less. Bulk data is passed on the
XSTACK, which is 512 bytes. A pointer appears in the C prototype to
indicate the type and direction of this data. Let's look at some
examples.

.. code-block:: C

   int open(const char *path, int oflag);

Send `oflag` in RIA_A and RIA_X. Send the path on XSTACK by pushing the
string starting with the last character. You may omit pushing the
terminating zero, but strings are limited to a length of 255. Calling
this from the C SDK will "just work" because there's an implementation
that pushes the string for you.

.. code-block:: C

   int read_xstack(void *buf, unsigned count, int fildes)

Send `count` as a short stack and `fildes` in RIA_A. RIA_X doesn't need
to be set according the to docs below. The returned value in AX
indicates how many values must be pulled from the stack. If you call
this from the C SDK then it will copy XSTACK to buf[] for you.

.. code-block:: C

   int write_xstack(const void *buf, unsigned count, int fildes)

Send `fildes` in RIA_A. Push the buf data to XSTACK. Do not send
`count`, the OS knows this from its internal stack pointer. If you call
this from the C SDK then it will copy count bytes of buf[] to XSTACK
for you.

Note that read() and write() are part of the C SDK, not an OS
operation. C requires these to support a count larger than the XSTACK
can return so the implementation makes multiple OS calls as necessary.

Bulk XRAM Operations
~~~~~~~~~~~~~~~~~~~~

These load and save XRAM directly. You can load game assets without
going through 6502 RAM or capture a screenshot with ease.

.. code-block:: C

   int read_xram(xram_addr buf, unsigned count, int fildes)
   int write_xram(xram_addr buf, unsigned count, int fildes)

The OS expects `buf` and `count` on the XSTACK as integers with
`filedes` in RIA_A. The buffer is effectively &XRAM[buf] here.

These operations are interesting because of their high performance and
ability to work in the background while the 6502 is doing something
else. You can expect close to 64KB/sec, which means loading a game
level's worth of assets will take less than a second.

Bulk XRAM operations are why the Picocomputer 6502 was designed
without paged memory.

Function Reference
===================

Much of this API is based on POSIX and FatFs. In particular, filesystem
and console access should feel extremely familiar. However, some
operations will have different argument orders or bitfield values than
what you're used to. The reason for this becomes apparent when you start
to work in assembly and fine tune short stacking and integer demotions.
You might not notice the differences if you only work in C because the
standard library has wrapper functions and familiar prototypes. For
example, the f_lseek() described below has reordered arguments that are
optimized for short stacking the long argument. But you don't have to
call f_lseek() from C, you can call the usual lseek() which has the
traditional argument order.

The RP6502 is built around FAT filesystems, which is the defacto standard
for USB storage devices. POSIX filesystems are not fully compatible with
FAT but there is a solid intersection of basic IO that is 100% compatible.
You will see some familiar POSIX functions like open() and others like
f_stat() which are similar to the POSIX function but tailored to FAT.
Should it ever become necessary to have a POSIX stat(), it can be
implemented in the C standard library or in an application by translating
f_stat() data.

zxstack
-------
.. c:function:: void zxstack(void);

Abandon the xstack by resetting the xstack pointer. This is the only
operation that doesn't require waiting for completion. You do not need
to call this for failed operations. It can be useful if you want to
quickly ignore part of a returned structure.

xreg
----

.. c:function:: int xreg(char device, char channel, unsigned char address, ...);
.. c:function:: int xregn(char device, char channel, unsigned char address, unsigned count, ...);

   The only difference is that xregn() requires a count of the variadic
   arguments. Using xreg() avoids making a counting error and is
   slightly smaller in CC65.

   Set extended registers on a PIX device. See the :doc:`ria` and
   :doc:`vga` documentation for what each register does. Setting
   extended registers can fail, which you should use for feature
   detection. EINVAL means the device responded with a negative
   acknowledgement. EIO means there was a timeout waiting for ack/nak.

   This is how you add virtual hardware to extended RAM. The 64K of
   system RAM is mapped by address decode logic ICs. The 64K of extended
   RAM is mapped with this command. Mapping a real sound chip to system
   RAM requires schematics and wires. Mapping a virtual sound chip to
   extended RAM is a single xreg() command.

   :param device: PIX device ID. 0-6
   :param channel: PIX channel. 0-15
   :param address: PIX address. 0-255
   :param ...: 16 bit integers to set starting at address.
   :errno: EINVAL, EIO


phi2
----

.. c:function:: int phi2(void)

   Retrieves the PHI2 setting from the RIA. Applications can use this
   for adjusting to or rejecting different clock speeds.

   :returns: The 6502 clock speed in kHz. Typically 800 <= x <= 8000.
   :errno: will not fail


codepage
--------

.. c:function:: int codepage(int cp)

   Temporarily overrides the code page if non zero. Returns to system
   setting when 6502 stops. This is the encoding the filesystem is using
   and, if VGA is installed, the console and default font. If zero, the
   system CP setting is selected and returned. If the requested code page
   is unavailable, a different code page will be selected and returned.
   For example: ``if (850!=codepage(850)) puts("error");``

   :param cp: code page or 0 for system setting.

   :returns: The code page. One of: 437, 720, 737, 771, 775, 850, 852,
      855, 857, 860, 861, 862, 863, 864, 865, 866, 869, 932, 936, 949,
      950.
   :errno: will not fail


lrand
-----

.. c:function:: long lrand(void)

   Generates a random number starting with entropy on the RIA. This is
   suitable for seeding a RNG or general use. The 16-bit rand() in the
   CC65 library can be seeded with this by calling its non-standard
   _randomize() function.

   :returns: Chaos. 0x0 <= x <= 0x7FFFFFFF
   :errno: will not fail


stdin_opt
---------

.. c:function:: int stdin_opt(unsigned long ctrl_bits, unsigned char str_length)

   *** Experimental *** (likely to be replaced with stty-like something)

   Additional options for the STDIN line editor. Set the str_length to
   your buffer size - 1 to make gets() safe. This can also guarantee no
   split lines when using fgets() on STDIN.

   :param ctrl_bits: Bitmap of ASCII 0-31 defines which CTRL characters
      can abort an input. When CTRL key is pressed, any typed input
      remains on the screen but the applicaion receives a line
      containing only the CTRL character. e.g. CTRL-C + newline.
   :param str_length: 0-255 default 254. The input line editor won't
      allow user input greater than this length.
   :a regs: return, str_length
   :returns: 0 on success
   :errno: will not fail


clock
-----

.. c:function:: unsigned long clock(void)

   Obtain the value of a monotonic clock that updates 100 times per
   second. Wraps approximately every 497 days.

   :returns: 1/100 second monotonic clock
   :errno: will not fail


clock_getres
------------

.. c:function:: int clock_getres(clockid_t clock_id, struct timespec *res)

   .. code-block:: c

      struct timespec {
         uint32_t tv_sec; /* seconds */
         int32_t tv_nsec; /* nanoseconds */
      };

   Copies the clock resolution to `res`.

   :param clock_id: 0 for CLOCK_REALTIME.
   :returns: 0 on success. -1 on error.
   :a regs: return, clock_id
   :errno: EINVAL


clock_gettime
-------------

.. c:function:: int clock_gettime(clockid_t clock_id, struct timespec *tp)

   Copies the current time to `tp`.

   :param clock_id: 0 for CLOCK_REALTIME.
   :returns: 0 on success. -1 on error.
   :a regs: return, clock_id
   :errno: EINVAL, EUNKNOWN


clock_settime
-------------

.. c:function:: int clock_settime(clockid_t clock_id, const struct timespec *tp)

   Sets the current time to `tp`.

   :param clock_id: 0 for CLOCK_REALTIME.
   :returns: 0 on success. -1 on error.
   :a regs: return, clock_id
   :errno: EINVAL, EUNKNOWN


clock_gettimezone
-----------------

.. c:function:: int clock_gettimezone(uint32_t time, clockid_t clock_id, struct _timezone *tz)

   .. code-block:: c

      struct _timezone
      {
         int8_t daylight;  /* >0 if daylight savings time active */
         int32_t timezone; /* Number of seconds behind UTC */
         char tzname[5];   /* Name of timezone, e.g. CET */
         char dstname[5];  /* Name when daylight true, e.g. CEST */
      };

   Populates a CC65 _timezone structure for the requested time. Use
   `help set tz` on the monitor to learn about configuring your time
   zone.

   :param time: time_t compatible integer.
   :param clock_id: 0 for CLOCK_REALTIME.
   :returns: 0 on success. -1 on error.
   :a regs: return, clock_id
   :errno: EINVAL


open
----

.. c:function:: int open(const char *path, int oflag)

   Create a connection between a file and a file descriptor.

   :param path: Pathname to a file.
   :param oflag: Bitfield of options.
   :returns: File descriptor. -1 on error.
   :a regs: return, oflag
   :errno: EINVAL, EMFILE, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY,
      FR_NO_FILE, FR_NO_PATH, FR_INVALID_NAME, FR_DENIED, FR_EXIST,
      FR_INVALID_OBJECT, FR_WRITE_PROTECTED, FR_INVALID_DRIVE,
      FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT, FR_LOCKED,
      FR_NOT_ENOUGH_CORE, FR_TOO_MANY_OPEN_FILES
   :Options:

      | O_RDONLY 0x01
      |    Open for reading only.
      | O_WRONLY 0x02
      |    Open for writing only.
      | O_RDWR 0x03
      |    Open for reading and writing.
      | O_CREAT 0x10
      |    Create the file if it does not exist.
      | O_TRUNC 0x20
      |    Truncate the file length to 0 after opening.
      | O_APPEND 0x40
      |    Read/write pointer is set end of the file.
      | O_EXCL 0x80
      |    If O_CREAT and O_EXCL are set, fail if the file exists.


close
-----

.. c:function:: int close(int fildes)

   Release the file descriptor. File descriptor will rejoin the pool
   available for use by open().

   :param fildes: File descriptor from open().
   :returns: 0 on success. -1 on error.
   :a regs: return, fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT,
      FR_TIMEOUT


read
----

.. c:function:: int read(int fildes, void *buf, unsigned count)

   Read `count` bytes from a file to a buffer.

   :param buf: Destination for the returned data.
   :param count: Quantity of bytes to read. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes read is returned. On error, -1
      is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED,
      FR_INVALID_OBJECT, FR_TIMEOUT


read_xstack
-----------

.. c:function:: int read_xstack(void *buf, unsigned count, int fildes)

   Read `count` bytes from a file to xstack.

   :param buf: Destination for the returned data.
   :param count: Quantity of bytes to read. 0x100 max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes read is returned. On error, -1
      is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED,
      FR_INVALID_OBJECT, FR_TIMEOUT

read_xram
---------

.. c:function:: int read_xram(unsigned buf, unsigned count, int fildes)

   Read `count` bytes from a file to xram.

   :param buf: Destination for the returned data.
   :param count: Quantity of bytes to read. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes read is returned. On error, -1
      is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED,
      FR_INVALID_OBJECT, FR_TIMEOUT


write
-----

.. c:function:: int write(int fildes, const void *buf, unsigned count)

   Write `count` bytes from buffer to a file.

   :param buf: Location of the data.
   :param count: Quantity of bytes to write. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes written is returned. On error,
      -1 is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED,
      FR_INVALID_OBJECT, FR_TIMEOUT


write_xstack
------------

.. c:function:: int write_xstack(const void *buf, unsigned count, int fildes)

   Write `count` bytes from xstack to a file.

   :param buf: Location of the data.
   :param count: Quantity of bytes to write. 0x100 max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes written is returned. On error,
      -1 is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED,
      FR_INVALID_OBJECT, FR_TIMEOUT


write_xram
----------

.. c:function:: int write_xram(unsigned buf, unsigned count, int fildes)

   Write `count` bytes from xram to a file.

   :param buf: Location of the data.
   :param count: Quantity of bytes to write. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes written is returned. On error,
      -1 is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED,
      FR_INVALID_OBJECT, FR_TIMEOUT


lseek
-----

.. c:function:: off_t lseek(int fildes, off_t offset, int whence)
.. c:function:: static long lseek_impl(long offset, char whence, int fildes)

   Move the read/write pointer. This is implemented internally with an
   argument order to take advantage of short stacking the offset.

   :param offset: How far you wish to seek.
   :param whence: From whence you wish to seek.
   :param fildes: File descriptor from open().
   :returns: Read/write position. -1 on error. If this value would be
      too large for a long, the returned value will be 0x7FFFFFFF.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT,
      FR_TIMEOUT
   :whence:

      | SEEK_SET = 2
      |    The start of the file plus offset bytes.
      | SEEK_CUR = 0
      |    The current location plus offset bytes.
      | SEEK_END = 1
      |    The size of the file plus offset bytes.


unlink
------

.. c:function:: int unlink (const char* name)

   Removes a file or directory from the volume.

   :param name: File or directory name to unlink (remove).
   :returns: 0 on success. -1 on error.
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE,
      FR_NO_PATH, FR_INVALID_NAME, FR_DENIED, FR_WRITE_PROTECTED,
      FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT,
      FR_LOCKED, FR_NOT_ENOUGH_CORE


rename
------

.. c:function:: int rename (const char* oldname, const char* newname)

   Renames and/or moves a file or directory.

   :param oldname: Existing file or directory name to rename.
   :param newname: New object name.
   :returns: 0 on success. -1 on error.
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE,
      FR_NO_PATH, FR_INVALID_NAME, FR_EXIST, FR_WRITE_PROTECTED,
      FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT,
      FR_LOCKED, FR_NOT_ENOUGH_CORE


exit
----

.. c:function:: void exit(int status)

   Halt the 6502 and return the console to RP6502 monitor control. This
   is the only operation that does not return. RESB will be pulled down
   before the next instruction can execute. Status is currently ignored
   but will be used in the future.

   :param status: 0 is good, !0 for error.
