============================
RP6502-OS
============================

RP6502 - Operating System


Introduction
============

The :doc:`ria` runs a 32-bit protected operating system that you can call
from the 6502. The OS does not use any 6502 system RAM and will not
interfere with developing a native 6502 OS.

The OS loosely follows POSIX with an Application Binary
Interface (ABI) similar to `cc65's fastcall
<https://cc65.github.io/doc/cc65-intern.html>`__. It provides ``stdio.h`` and
``unistd.h`` services to both `cc65 <https://cc65.github.io>`__ and `llvm-mos
<https://llvm-mos.org/>`_ compilers. There are also calls to access RP6502
features and manage FAT32 filesystems.

.. note::

   ExFAT is ready to go and will be enabled when the patents expire.


Memory Map
==========

There is no ROM. Nothing in zero page is used or reserved. The Picocomputer
starts as a clean slate for every project. VGA, audio, storage, keyboards,
mice, gamepads, RTC, and networking are all accessed using only the 32
registers of the RIA.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Address
     - Description
   * - $0000-$FEFF
     - RAM, 63.75K
   * - $FF00-$FFCF
     - Unassigned
   * - $FFD0-$FFDF
     - VIA, see the `WDC datasheet
       <https://www.westerndesigncenter.com/wdc/w65c22-chip.php>`_
   * - $FFE0-$FFFF
     - RIA, see the :doc:`RP6502-RIA datasheet <ria>`
   * - $10000-$1FFFF
     - XRAM, 64K for :doc:`ria` and :doc:`vga`

The unassigned space is available for hardware experimenters. Design
your own chip select hardware to use this address space. Add additional
VIAs downward and other hardware upward. For example: VIA0 at $FFD0,
VIA1 at $FFC0, SID0 at $FF00, and SID1 at $FF20.


Application Binary Interface
============================

.. seealso::

   :doc:`ria` — the hardware register map referenced throughout this section.

The ABI for calling the operating system is based on fastcall from the
`cc65 internals <https://cc65.github.io/doc/cc65-intern.html>`__. The
OS does not use or require anything from cc65 and is easy for
assembly programmers to use. At its core, the OS ABI is four simple rules.

* Stack arguments are pushed left to right.
* Last argument passed by register A, AX, or AXSREG.
* Return value in register AX or AXSREG.
* May return data on the stack.

A and X are the 6502 registers. The pseudo register AX combines them for 16
bits. AXSREG allows 32 bits with the 16 additional SREG bits. Let's look at
how to make an OS call through the RIA registers. All OS calls are specified
as a C declaration like so:

.. c:function:: int doit(int arg0, int arg1);

The RIA has registers called ``RIA_A``, ``RIA_X``, and ``RIA_SREG``. An int is 16 bits,
so we set the ``RIA_A`` and ``RIA_X`` registers with arg1. I'll use "A" for the 6502
register and "RIA_A" for the RIA register in this explanation.

We use the XSTACK for arg0. Reading ``RIA_XSTACK`` pops bytes; writing
pushes bytes. It's a top-down stack, so push each argument left to
right and maintain little-endian byte order.

To execute the call, store the operation ID in ``RIA_OP``. The operation begins
immediately. You can keep doing 6502 things, like running a loading animation, by
polling ``RIA_BUSY``. Alternatively, JSR to ``RIA_SPIN`` to block.

``JSR RIA_SPIN`` can unblock within 3 clock cycles and immediately loads A
and X. Sequential operations run fastest with this technique. Under the hood,
you're jumping into a self-modifying program that runs on the RIA registers.

.. code-block:: asm

   BRA #$??      ; RIA_BUSY {-2 or 0}
   LDA #$??      ; RIA_A
   LDX #$??      ; RIA_X
   RTS

Polling is simply snooping on the above program. The ``RIA_BUSY`` register is
the -2 or 0 in the BRA above. The RIA datasheet specifies bit 7 indicates
busy, which the 6502 can check quickly by using the BIT operator to set
flag N. Once clear, we read ``RIA_A`` and ``RIA_X`` with absolute instructions.

.. code-block:: asm

   wait:
   BIT RIA_BUSY
   BMI wait
   LDA RIA_A
   LDX RIA_X

All operations returning ``RIA_A`` will also return ``RIA_X`` to assist with C
integer promotion. ``RIA_SREG`` is only updated for 32-bit returns. ``RIA_ERRNO``
is only updated if there is an error.

Some operations return strings or structures on the stack. You must pull the
entire stack before the next call. However, tail call optimizations are
possible. For example, you can chain `read_xstack() <READ_XSTACK_>`_ and `write_xstack() <WRITE_XSTACK_>`_ to
copy a file without using any RAM or XRAM.

Short Stacking
---------------

In the pursuit of saving every cycle, you can save a few on the stack
push when you don't need the full range. This only applies to the first
stack argument pushed. For example, in `LSEEK`_:

.. code-block:: C

   long f_lseek(long offset, char whence, int fildes)

Here we need to push a 32 bit value. Not coincidentally, it's in the right
position for short stacking. If, for example, the offset always fits in 16
bits, push only two bytes instead of four.

Shorter AX
----------

Many operations can save a few cycles by ignoring REG_X. All returned
integers are always available as at least 16 bits to assist with C integer
promotion. However, many operations will ignore REG_X in the register
parameter and limit their return to fit in REG_A. These will be documented
below as "A regs".

Bulk Data
---------

Functions that move bulk data come in two flavors, depending on
where the data lives. A RAM pointer is meaningless to the RIA because it cannot change 6502
RAM. Instead, use the XSTACK or XRAM to move data.

Bulk XSTACK Operations
~~~~~~~~~~~~~~~~~~~~~~

These only work if the size is 512 bytes or less. Bulk data is passed on the
XSTACK, which is 512 bytes. A pointer appears in the C prototype to indicate
the type and direction (to or from the OS) of this data. Let's look at some examples.

.. code-block:: C

   int open(const char *path, int oflag);

Send ``oflag`` in ``RIA_A``. ``RIA_X`` doesn't need to be set according to the
`OPEN`_ docs. Send the path on XSTACK by pushing the string starting with the last
character. You may omit pushing the terminating zero, but strings are
limited to a length of 255. Calling this from the C SDK will "just work"
because there's an implementation that pushes the string for you.

.. code-block:: C

   int read_xstack(void *buf, unsigned count, int fildes)

Send ``count`` as a short stack and ``fildes`` in ``RIA_A``. ``RIA_X`` doesn't
need to be set according to the `READ_XSTACK`_ docs. The returned value in AX indicates how
many values must be pulled from the stack. If you call this from the C SDK
then it will copy XSTACK to buf[] for you.

.. code-block:: C

   int write_xstack(const void *buf, unsigned count, int fildes)

Send ``fildes`` in ``RIA_A``. ``RIA_X`` doesn't need to be set according to the
`WRITE_XSTACK`_ docs. Push the buf data to XSTACK. Do not send ``count``, the OS knows this
from its internal stack pointer. If you call this from the C SDK then it
will copy count bytes of buf[] to XSTACK for you.

Note that read() and write() are part of the C SDK, not an OS operation. C
requires these to support a count larger than the XSTACK can return so the
implementation makes multiple OS calls as necessary.

Bulk XRAM Operations
~~~~~~~~~~~~~~~~~~~~

These load and save XRAM directly via `READ_XRAM`_ and `WRITE_XRAM`_. You can load game assets without
going through 6502 RAM or capture a screenshot with ease.

.. code-block:: C

   int read_xram(xram_addr buf, unsigned count, int fildes)
   int write_xram(xram_addr buf, unsigned count, int fildes)

The OS expects ``buf`` and ``count`` on the XSTACK as integers with ``fildes`` in
``RIA_A``. The OS has direct access to XRAM so internally it will use
something like ``&XRAM[buf]``. You will need to use ``RIA_RW0`` or ``RIA_RW1`` to access
this memory from the 6502.

These operations stand out for their high performance and ability to
run in the background while the 6502 does other work. Expect close to
64 KB/sec, meaning a game level's worth of assets loads in under a
second.

Bulk XRAM operations are why the Picocomputer 6502 was designed without
paged memory.


Application Programmer Interface
================================

.. seealso::

   `FatFs documentation <https://elm-chan.org/fsw/ff/>`__ —
   many of the filesystem functions below are thin wrappers around FatFs.

Much of this API is based on POSIX and FatFs. In particular, filesystem and
console access should feel extremely familiar. However, some operations will
have a different argument order or data structures than what you're used to.
The reason for this becomes apparent when you start to work in assembly and
fine tune short stacking and integer demotions. You might not notice the
differences if you only work in C because the standard library has wrapper
functions and familiar prototypes. For example, the ``f_lseek()`` described
below has reordered arguments that are optimized for short stacking the long
argument. But you don't have to call ``f_lseek()`` from C, you can call the
usual ``lseek()`` which has the traditional argument order.

The OS is built around FAT filesystems, the de facto standard for
unsecured USB storage devices. POSIX filesystems are not fully
compatible with FAT but there is a solid intersection of basic IO that is
100% compatible. You will see some familiar POSIX functions like ``open()`` and
others like ``f_stat()`` which are similar to the POSIX function but tailored to
FAT. Should it ever become necessary to have a POSIX ``stat()``, it can be
implemented in the C standard library or in an application by translating
``f_stat()`` data.

ZXSTACK
-------
.. c:function:: void zxstack (void);


   Abandon the xstack by resetting the xstack pointer. This is the only
   operation that doesn't require waiting for completion. You do not need to
   call this for failed operations. It can be useful if you want to quickly
   ignore part of a returned structure.

   :Op code: RIA_OP_ZXSTACK 0x00
   :C proto: rp6502.h

XREG
----

.. c:function:: int xreg (char device, char channel, unsigned char address, ...);
.. c:function:: int xregn (char device, char channel, unsigned char address, unsigned count, ...);


   Using xreg() from C is preferred to avoid making a counting error. Count
   doesn't need to be sent in the ABI so both prototypes are correct.

   The variadic argument is a list of ints to be stored in extended
   registers starting at address on the specified device and channel. See
   the :doc:`ria` and :doc:`vga` documentation for what each register does.
   Setting extended registers can fail, which you can use for feature
   detection. EINVAL means the device responded with a negative
   acknowledgement. EIO means there was a timeout waiting for ack/nak.

   This is how you add virtual hardware to extended RAM. Both the :doc:`ria`
   and :doc:`vga` have a selection of virtual devices you can install. You
   can also make your own hardware for the PIX bus and configure it with
   this call.

   :Op code: RIA_OP_XREG 0x01
   :C proto: rp6502.h
   :param device: PIX device ID. 0:RIA, 1:VGA, 2-6:unassigned
   :param channel: PIX channel. 0-15
   :param address: PIX address. 0-255
   :param ...: 16 bit integers to set starting at address.
   :a regs: return
   :errno: EINVAL, EIO


ARGV
----

.. c:function:: int _argv (char *argv, int size)


   The virtual _argv is called by C initialization to provide argc and argv for main().
   It returns an array of zero terminated string indexes followed by the strings.
   e.g. ["ABC", "DEF"] is 06 00 0A 00 00 00 41 42 43 00 44 45 46 00
   The returned data is guaranteed to be valid.

   Because this can use up to 512 bytes of RAM you must opt-in by providing storage
   for the argv data. You may use static memory, or dynamically allocated memory which
   can be freed after use. You may also reject an oversized argv by returning NULL.

   .. code-block:: c

      void *argv_mem(size_t size) { return malloc(size); }

   :Op code: RIA_OP_ARGV 0x08
   :C proto: (none)
   :returns: Size of argv data
   :errno: will not fail

EXEC
----

.. c:function:: int ria_execl (const char *path, ...)
.. c:function:: int ria_execv (const char *path, char * const argv[])
.. c:function:: int _exec (const char *argv, int size)


   The virtual _exec is called by ria_execl() and ria_execv(). Be aware of the
   one difference from the execl() and execv() you may be used to. Because RAM
   is precious, the path is only supplied once, not again in argv[0]. The
   launched ROM will see argv[0] as the filename.

   The data sent by _exec() will be checked for pointer safety and sanity, but
   will assume the path points to a loadable ROM file. If EINVAL is returned,
   the argv buffer is cleared so further attempts to _argv() will return an empty set.
   If the ROM is invalid, the user will be left on the console with an error message.

   :Op code: RIA_OP_EXEC 0x09
   :C proto: rp6502.h
   :returns: Does not return on success — the new ROM begins executing. -1 on error.
   :errno: EINVAL


ATTR_GET
--------

.. c:function:: long ria_attr_get (unsigned char id)


   Returns the current value of a RIA attribute. See `RIA Attributes`_
   for attribute IDs and descriptions.

   :Op code: RIA_OP_ATTR_GET 0x0A
   :C proto: rp6502.h
   :param id: Attribute ID. One of the ``RIA_ATTR_*`` constants.
   :a regs: id
   :returns: The attribute value as a 31-bit integer. -1 on error.
   :errno: EINVAL


ATTR_SET
--------

.. c:function:: int ria_attr_set (long val, unsigned char id)


   Sets the value of a RIA attribute. See `RIA Attributes`_ for
   attribute IDs and descriptions.

   :Op code: RIA_OP_ATTR_SET 0x0B
   :C proto: rp6502.h
   :param id: Attribute ID. One of the ``RIA_ATTR_*`` constants.
   :param val: New value.
   :a regs: id
   :returns: 0 on success
   :errno: EINVAL


CLOCK
-----

.. c:function:: unsigned long clock (void)


   Obtain the value of a monotonic clock that updates 100 times per second.
   Wraps approximately every 497 days.

   :Op code: RIA_OP_CLOCK 0x0F
   :C proto: time.h
   :returns: 1/100 second monotonic clock
   :errno: will not fail


CLOCK_GETRES
------------

.. c:function:: int clock_getres (clockid_t clock_id, struct timespec *res)


   .. code-block:: c

      struct timespec {
         uint32_t tv_sec; /* seconds */
         int32_t tv_nsec; /* nanoseconds */
      };

   Obtains the clock resolution.

   :Op code: RIA_OP_CLOCK_GETRES 0x10
   :C proto: time.h
   :param clock_id: 0 for CLOCK_REALTIME.
   :returns: 0 on success. -1 on error.
   :a regs: return, clock_id
   :errno: EINVAL


TZSET
-----

.. c:function:: void tzset(void);
.. c:function:: int _tzset (struct _tzset *tz)

   .. code-block:: c

      struct _tzset
      {
         int8_t daylight;  /* non 0 if daylight savings time active */
         int32_t timezone; /* Number of seconds behind UTC */
         char tzname[5];   /* Name of timezone, e.g. CET */
         char dstname[5];  /* Name when daylight true, e.g. CEST */
      };

   The virtual _tzset() is called internally by tzset(). Use `help set tz` on the
   console monitor to learn about configuring your time zone.

   :Op code: RIA_OP_TZSET 0x0D
   :C proto: time.h
   :returns: 0 on success. -1 on error.
   :errno: EINVAL


TZQUERY
-------

.. c:function:: struct tm *localtime(const time_t *timep);
.. c:function:: int _tzquery (uint32_t time, struct _tzquery *dst)

   .. code-block:: c

      struct _tzquery
      {
         int8_t daylight;  /* non 0 if daylight savings time active */
      };

   The virtual _tzquery() is called internally by localtime().

   :Op code: RIA_OP_TZQUERY 0x0E
   :C proto: time.h
   :returns: Seconds to add to UTC for localtime.
   :errno: will not fail


CLOCK_GETTIME
-------------

.. c:function:: int clock_gettime (clockid_t clock_id, struct timespec *tp)


   Obtains the current time.

   :Op code: RIA_OP_CLOCK_GETTIME 0x11
   :C proto: time.h
   :param clock_id: 0 for CLOCK_REALTIME.
   :returns: 0 on success. -1 on error.
   :a regs: return, clock_id
   :errno: EINVAL, EUNKNOWN


CLOCK_SETTIME
-------------

.. c:function:: int clock_settime (clockid_t clock_id, const struct timespec *tp)


   Sets the current time.

   :Op code: RIA_OP_CLOCK_SETTIME 0x12
   :C proto: time.h
   :param clock_id: 0 for CLOCK_REALTIME.
   :returns: 0 on success. -1 on error.
   :a regs: return, clock_id
   :errno: EINVAL, EUNKNOWN

OPEN
----

.. c:function:: int open (const char *path, int oflag)


   Create a connection between a file and a file descriptor. Up to 8 files
   may be open at once.

   :Op code: RIA_OP_OPEN 0x14
   :C proto: fcntl.h
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


CLOSE
-----

.. c:function:: int close (int fildes)


   Finish pending writes and release the file descriptor. File descriptor
   will rejoin the pool available for use by open().

   :Op code: RIA_OP_CLOSE 0x15
   :C proto: fcntl.h
   :param fildes: File descriptor from open().
   :returns: 0 on success. -1 on error.
   :a regs: return, fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT,
      FR_TIMEOUT


READ
----

.. c:function:: int read (int fildes, void *buf, unsigned count)


   Read `count` bytes from a file to a buffer. This is implemented in the
   compiler library as a series of calls to `READ_XSTACK`_.

   :Op code: None
   :C proto: unistd.h
   :param buf: Destination for the returned data.
   :param count: Quantity of bytes to read. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes read is returned. On error, -1 is
      returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT,
      FR_TIMEOUT


READ_XSTACK
-----------

.. c:function:: int read_xstack (void *buf, unsigned count, int fildes)


   Read `count` bytes from a file to xstack.

   :Op code: RIA_OP_READ_XSTACK 0x16
   :C proto: rp6502.h
   :param buf: Destination for the returned data.
   :param count: Quantity of bytes to read. 0x100 max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes read is returned. On error, -1 is
      returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT,
      FR_TIMEOUT

READ_XRAM
---------

.. c:function:: int read_xram (unsigned buf, unsigned count, int fildes)


   Read `count` bytes from a file to xram.

   :Op code: RIA_OP_READ_XRAM 0x17
   :C proto: rp6502.h
   :param buf: Destination for the returned data.
   :param count: Quantity of bytes to read. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes read is returned. On error, -1 is
      returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT,
      FR_TIMEOUT


WRITE
-----

.. c:function:: int write (int fildes, const void *buf, unsigned count)


   Write `count` bytes from buffer to a file. This is implemented in the
   compiler library as a series of calls to `WRITE_XSTACK`_.

   :Op code: None
   :C proto: unistd.h
   :param buf: Location of the data.
   :param count: Quantity of bytes to write. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes written is returned. On error, -1
      is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT,
      FR_TIMEOUT


WRITE_XSTACK
------------

.. c:function:: int write_xstack (const void *buf, unsigned count, int fildes)


   Write `count` bytes from xstack to a file.

   :Op code: RIA_OP_WRITE_XSTACK 0x18
   :C proto: rp6502.h
   :param buf: Location of the data.
   :param count: Quantity of bytes to write. 0x100 max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes written is returned. On error, -1
      is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT,
      FR_TIMEOUT


WRITE_XRAM
----------

.. c:function:: int write_xram (unsigned buf, unsigned count, int fildes)


   Write `count` bytes from xram to a file.

   :Op code: RIA_OP_WRITE_XRAM 0x19
   :C proto: rp6502.h
   :param buf: Location of the data.
   :param count: Quantity of bytes to write. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes written is returned. On error, -1
      is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT,
      FR_TIMEOUT


LSEEK
-----

.. c:function:: static long f_lseek (long offset, char whence, int fildes)
.. c:function:: off_t lseek (int fildes, off_t offset, int whence)


   Move the read/write pointer. The OS uses the ABI format of f_seek(). An
   lseek() compatible wrapper is provided with the compiler library.

   This can also be used to obtain the current read/write position with
   ``f_lseek(0, SEEK_CUR, fd)``.

   :Op code: See table below.
   :C proto: f_lseek: rp6502.h, lseek: unistd.h
   :param offset: How far you wish to seek.
   :param whence: From whence you wish to seek. See table below.
   :param fildes: File descriptor from open().
   :returns: Read/write position. -1 on error. If this value would be too
      large for a long, the returned value will be 0x7FFFFFFF.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT, FR_TIMEOUT

   .. list-table::
      :header-rows: 1
      :widths: 25 25 25

      * -
        - RIA_OP_LSEEK_LLVM
        - RIA_OP_LSEEK_CC65
      * - RIA_OP_LSEEK
        - 0x1D
        - 0x1A
      * - SEEK_SET
        - 0
        - 2
      * - SEEK_CUR
        - 1
        - 0
      * - SEEK_END
        - 2
        - 1


UNLINK
------

.. c:function:: int unlink (const char* name)


   Removes a file or directory from the volume.

   :Op code: RIA_OP_UNLINK 0x1B
   :C proto: unistd.h
   :param name: File or directory name to unlink (remove).
   :returns: 0 on success. -1 on error.
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE,
      FR_NO_PATH, FR_INVALID_NAME, FR_DENIED, FR_WRITE_PROTECTED,
      FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT,
      FR_LOCKED, FR_NOT_ENOUGH_CORE


RENAME
------

.. c:function:: int rename (const char* oldname, const char* newname)


   Renames and/or moves a file or directory.

   :Op code: RIA_OP_RENAME 0x1C
   :C proto: stdio.h
   :param oldname: Existing file or directory name to rename.
   :param newname: New object name.
   :returns: 0 on success. -1 on error.
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE,
      FR_NO_PATH, FR_INVALID_NAME, FR_EXIST, FR_WRITE_PROTECTED,
      FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT,
      FR_LOCKED, FR_NOT_ENOUGH_CORE


SYNCFS
------

.. c:function:: int syncfs (int fildes)


   Finish pending writes for the file descriptor.

   :Op code: RIA_OP_SYNCFS 0x1E
   :C proto: unistd.h
   :param fildes: File descriptor from open().
   :returns: 0 on success. -1 on error.
   :a regs: return, fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT,
      FR_TIMEOUT


STAT
----

.. c:function:: int f_stat (const char* path, f_stat_t* dirent)

   .. code-block:: c

      typedef struct {
         unsigned long fsize;
         unsigned fdate;
         unsigned ftime;
         unsigned crdate;
         unsigned crtime;
         unsigned char fattrib;
         char altname[12 + 1];
         char fname[255 + 1];
      } f_stat_t;

   Returns file or directory info for requested path.
   See the `FatFs documentation <https://elm-chan.org/fsw/ff/doc/sfileinfo.html>`__
   for details about the data structure.

   :Op code: RIA_OP_STAT 0x1F
   :C proto: rp6502.h
   :param path: Pathname to a directory entry.
   :param dirent: Returned f_stat_t data.
   :returns: 0 on success. -1 on error.
   :a regs: return, dirent
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE,
      FR_NO_PATH, FR_INVALID_NAME, FR_INVALID_DRIVE, FR_NOT_ENABLED,
      FR_NO_FILESYSTEM, FR_TIMEOUT, FR_NOT_ENOUGH_CORE


OPENDIR
-------

.. c:function:: int f_opendir (const char* name)


   Create a connection between a directory and a directory descriptor. Up to
   8 directories may be open at once.

   :Op code: RIA_OP_OPENDIR 0x20
   :C proto: rp6502.h
   :param name: Pathname to a directory.
   :returns: Directory descriptor. -1 on error.
   :a regs: return
   :errno: EINVAL, EMFILE, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY,
      FR_NO_PATH, FR_INVALID_NAME, FR_INVALID_OBJECT, FR_INVALID_DRIVE,
      FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT, FR_NOT_ENOUGH_CORE,
      FR_TOO_MANY_OPEN_FILES


READDIR
-------

.. c:function:: int f_readdir (f_stat_t* dirent, int dirdes)


   Returns directory entry info for the current read position of a directory descriptor,
   then advances the read position.

   :Op code: RIA_OP_READDIR 0x21
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :param dirent: Returned f_stat_t data.
   :returns: 0 on success. -1 on error.
   :a regs: return, dirent
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT, FR_TIMEOUT,
      FR_NOT_ENOUGH_CORE


CLOSEDIR
--------

.. c:function:: int f_closedir (int dirdes)


   Release the directory descriptor. Directory descriptor will rejoin the
   pool available for use by f_opendir().

   :Op code: RIA_OP_CLOSEDIR 0x22
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
   :errno: EINVAL, FR_INT_ERR, FR_INVALID_OBJECT, FR_TIMEOUT


TELLDIR
-------

.. c:function:: long f_telldir (int dirdes)


   Returns the read position of the directory descriptor.

   :Op code: RIA_OP_TELLDIR 0x23
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: Read position. -1 on error.
   :a regs: dirdes
   :errno: EINVAL, EBADF


SEEKDIR
-------

.. c:function:: int f_seekdir (long offs, int dirdes)


   Set the read position for the directory descriptor. Internally, the FatFs
   directory read position can only move forward by one, so use this for
   convenience, not performance.

   :Op code: RIA_OP_SEEKDIR 0x24
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: Read position. -1 on error.
   :a regs: return, dirdes
   :errno: EINVAL, EBADF, FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT,
      FR_TIMEOUT, FR_NOT_ENOUGH_CORE


REWINDDIR
---------

.. c:function:: int f_rewinddir (int dirdes)


   Rewind the read position of the directory descriptor.

   :Op code: RIA_OP_REWINDDIR 0x25
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: 0 on success. -1 on error.
   :a regs: dirdes
   :errno: EINVAL, EBADF, FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT,
      FR_TIMEOUT, FR_NOT_ENOUGH_CORE


CHMOD
-----

.. c:function:: int f_chmod (const char* path, unsigned char attr, unsigned char mask)


   Change the attributes of a file or directory.

   :Op code: RIA_OP_CHMOD 0x26
   :C proto: rp6502.h
   :param path: Pathname to a file or directory.
   :param attr: New bitfield of attributes. See table.
   :param mask: Only attributes with bits set here will be changed.
   :returns: 0 on success. -1 on error.
   :a regs: return, mask
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE,
      FR_NO_PATH, FR_INVALID_NAME, FR_WRITE_PROTECTED, FR_INVALID_DRIVE,
      FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT, FR_NOT_ENOUGH_CORE

   .. list-table::
      :header-rows: 1
      :widths: 25 25

      * - Attribute
        - Bit
      * - Read Only
        - 0x01
      * - Hidden
        - 0x02
      * - System
        - 0x04
      * - Directory
        - 0x10
      * - Archive
        - 0x20


UTIME
-----

.. c:function:: int f_utime (const char* path, unsigned fdate, unsigned ftime, unsigned crdate, unsigned crtime)


   Update the date and time stamps of a file or directory. A date of 0
   (invalid) leaves the date and time unchanged.

   :Op code: RIA_OP_UTIME 0x27
   :C proto: rp6502.h
   :param path: Pathname to a file or directory.
   :param fdate: Modification date.
   :param ftime: Modification time.
   :param crdate: Creation date.
   :param crtime: Creation time.
   :returns: 0 on success. -1 on error.
   :a regs: return, mask
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE,
      FR_NO_PATH, FR_INVALID_NAME, FR_WRITE_PROTECTED, FR_INVALID_DRIVE,
      FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT, FR_NOT_ENOUGH_CORE

   .. list-table:: Date
      :header-rows: 0
      :widths: 10 25

      * - bit15:9
        - Years since 1980 (0..127)
      * - bit8:5
        - Month (1..12)
      * - bit4:0
        - Day (1..31)

   .. list-table:: Time
      :header-rows: 0
      :widths: 10 25

      * - bit15:11
        - Hour (0..23)
      * - bit10:5
        - Minute (0..59)
      * - bit4:0
        - Second / 2 (0..29)


MKDIR
-----

.. c:function:: int f_mkdir (const char* name)


   Make a new directory entry.

   :Op code: RIA_OP_MKDIR 0x28
   :C proto: rp6502.h
   :param name: Pathname of the directory to create.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_PATH,
      FR_INVALID_NAME, FR_DENIED, FR_EXIST, FR_WRITE_PROTECTED,
      FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT,
      FR_NOT_ENOUGH_CORE


CHDIR
-----

.. c:function:: int chdir (const char* name)


   Change to a directory entry.

   :Op code: RIA_OP_CHDIR 0x29
   :C proto: unistd.h
   :param name: Pathname of the directory to make current.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_PATH,
      FR_INVALID_NAME, FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM,
      FR_TIMEOUT, FR_NOT_ENOUGH_CORE


CHDRIVE
-------

.. c:function:: int f_chdrive (const char* name)


   Change the current drive.
   Valid names are ``USB0:``–``USB9:`` with shortcuts ``0:``–``9:``.

   :Op code: RIA_OP_CHDRIVE 0x2A
   :C proto: rp6502.h
   :param name: Drive name to change to.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: FR_INVALID_DRIVE


GETCWD
-------

.. c:function:: int f_getcwd (char* name, int size)


   Get the current working directory. Size is ignored by the OS but the C
   wrapper will use it.

   :Op code: RIA_OP_GETCWD 0x2B
   :C proto: rp6502.h
   :param name: The returned directory.
   :returns: Size of returned name. -1 on error.
   :errno: ENOMEM, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NOT_ENABLED,
      FR_NO_FILESYSTEM, FR_TIMEOUT, FR_NOT_ENOUGH_CORE


SETLABEL
--------

.. c:function:: int f_setlabel (const char* name)


   Change the volume label. Max 11 characters.

   :Op code: RIA_OP_SETLABEL 0x2C
   :C proto: rp6502.h
   :param name: Label with optional volume name.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_INVALID_NAME,
      FR_WRITE_PROTECTED, FR_INVALID_DRIVE, FR_NOT_ENABLED,
      FR_NO_FILESYSTEM, FR_TIMEOUT


GETLABEL
--------

.. c:function:: int f_getlabel (const char* path, char* label)


   Get the volume label. Label must have room for (22+1) bytes.

   :Op code: RIA_OP_GETLABEL 0x2D
   :C proto: rp6502.h
   :param name: Volume name.
   :param label: Storage for returned label.
   :returns: Size of returned label. -1 on error.
   :a regs: return
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_INVALID_DRIVE,
      FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT


GETFREE
-------

.. c:function:: int f_getfree (const char* name, unsigned long* free, unsigned long* total)

   .. code-block:: c

      struct {
         unsigned long free;
         unsigned long total;
      };

   Get the volume free and total space in number of 512 bytes blocks.

   :Op code: RIA_OP_GETFREE 0x2E
   :C proto: rp6502.h
   :param name: Volume name.
   :param free: Storage for returned value.
   :param total: Storage for returned value.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_INVALID_DRIVE,
      FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT


EXIT
----

.. c:function:: void exit (int status)


   Halt the 6502 and return the console to RP6502 monitor control. This is
   the only operation that does not return. The OS pulls RESB low before
   the next instruction can execute. The status argument is currently
   unused but reserved for future use.

   In general, dropping the user back to the monitor is discouraged. But
   calling exit() or falling off main() is preferred to locking up.

   :Op code: RIA_OP_EXIT 0xFF
   :C proto: stdlib.h
   :a regs: status
   :param status: 0 is success, 1-255 for error.


RIA Attributes
==============

RIA attributes are 31-bit values identified by an 8-bit ID. They are
accessed with :c:func:`ria_attr_get` and :c:func:`ria_attr_set`. Both
functions succeed for any valid attribute ID. Attempting to get or set an
unknown ID returns -1 with ``errno`` set to ``EINVAL``. Attempting to set a
get-only attribute also returns -1 with ``EINVAL``.

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - ID / Name
     - Description
   * - | 0x00
       | ``RIA_ATTR_ERRNO_OPT``
     - Errno mapping option. Selects which set of errno constants the OS
       uses. Both cc65 and llvm-mos set this automatically at C runtime
       startup; assembly programs must set it before making OS calls that
       can fail. See `ERRNO_OPT Compiler Constants`_ for option values.
   * - | 0x01
       | ``RIA_ATTR_PHI2_KHZ``
     - CPU clock speed in kHz. Range 100–8000. Changes take effect
       immediately and revert to the system setting when the 6502 stops.
   * - | 0x02
       | ``RIA_ATTR_CODE_PAGE``
     - Active OEM code page used by the filesystem, console, and default
       :doc:`VGA <vga>` font. Reverts to the system setting when the 6502 stops. If the
       requested page is unavailable, the console setting is selected;
       follow a set with a get to confirm the result.
       One of: 437, 720, 737, 771, 775, 850, 852, 855, 857, 860, 861, 862,
       863, 864, 865, 866, 869, 932, 936, 949, 950.
   * - | 0x03
       | ``RIA_ATTR_RLN_LENGTH``
     - Maximum input line length for the stdin line editor. 1–255,
       default 254.
   * - | 0x04
       | ``RIA_ATTR_LRAND``
     - 31-bit hardware random number seeded with entropy from the RIA.
       Returns a value in the range 0x0 to 0x7FFFFFFF. Suitable for
       seeding a PRNG or direct use. The 16-bit ``rand()`` in the cc65
       library can be seeded with this by calling ``_randomize()``.
   * - | 0x05
       | ``RIA_ATTR_BEL``
     - BEL (``\a``) output enable on the console UART.
       0 silences the alert; 1 (default) enables it.
   * - | 0x06
       | ``RIA_ATTR_LAUNCHER``
     - Launcher flag. When set to 1, the process manager records the
       currently running ROM as the launcher. Whenever any other ROM
       finishes, the launcher ROM is automatically re-executed. When the
       launcher ROM itself finishes, the chain ends and the flag is cleared.
       Setting to 0 clears the launcher registration. A console break
       (Ctrl-Alt-Del) also clears it unconditionally.


ERRNO_OPT Compiler Constants
============================

OS calls will set ``RIA_ERRNO`` when an error occurs. The errno option
selects which numeric values to use because cc65 and llvm-mos each define
their own errno constants. Both compilers set this automatically in their C
runtime. Assembly programs must set ``RIA_ATTR_ERRNO_OPT`` before any OS
call that can fail. ``errno`` in C maps directly to ``RIA_ERRNO``.

The OS maps FatFs errors onto errno. RP6502 emulation and simulation
software is expected to map their native errors as well. The table below
shows the FatFs mappings. Because FatFs is so integral to the OS, calls are
documented here with their native FatFs errors to assist when cross
referencing the `FatFs documentation <https://elm-chan.org/fsw/ff/>`__.

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * -
     - cc65
     - llvm_mos
     - FatFs
   * - option
     - 1
     - 2
     -
   * - ENOENT
     - 1
     - 2
     - FR_NO_FILE, FR_NO_PATH
   * - ENOMEM
     - 2
     - 12
     - FR_NOT_ENOUGH_CORE
   * - EACCES
     - 3
     - 23
     - FR_DENIED, FR_WRITE_PROTECTED
   * - ENODEV
     - 4
     - 19
     - FR_NOT_READY, FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM
   * - EMFILE
     - 5
     - 24
     - FR_TOO_MANY_OPEN_FILES
   * - EBUSY
     - 6
     - 16
     - FR_LOCKED
   * - EINVAL
     - 7
     - 22
     - FR_INVALID_NAME, FR_INVALID_PARAMETER
   * - ENOSPC
     - 8
     - 28
     -
   * - EEXIST
     - 9
     - 17
     - FR_EXIST
   * - EAGAIN
     - 10
     - 11
     - FR_TIMEOUT
   * - EIO
     - 11
     - 5
     - FR_DISK_ERR, FR_INT_ERR, FR_MKFS_ABORTED
   * - EINTR
     - 12
     - 4
     -
   * - ENOSYS
     - 13
     - 38
     -
   * - ESPIPE
     - 14
     - 29
     -
   * - ERANGE
     - 15
     - 34
     -
   * - EBADF
     - 16
     - 9
     - FR_INVALID_OBJECT
   * - ENOEXEC
     - 17
     - 8
     -
   * - EDOM
     - 18
     - 33
     -
   * - EILSEQ
     - 18
     - 84
     -
   * - EUNKNOWN
     - 18
     - 85
     -
