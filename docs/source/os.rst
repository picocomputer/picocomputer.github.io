============================
RP6502-OS
============================

RP6502 - Operating System


Introduction
============

The :doc:`ria` runs a 32-bit operating system that the 6502 can call
into. It lives entirely on the RIA's own processor — protected from the
6502 and using none of its system RAM — so it never gets in the way of
developing a native 6502 OS of your own.

The OS is POSIX-like, with an Application Binary Interface (ABI) modeled
on `cc65's fastcall <https://cc65.github.io/doc/cc65-intern.html>`__. It
offers ``stdio.h`` and ``unistd.h`` services to both the `cc65
<https://cc65.github.io>`__ and `llvm-mos <https://llvm-mos.org/>`_
compilers, plus calls to reach RP6502 features and manage FAT
filesystems.

.. note::

   ExFAT is ready to go and will be enabled when the patents expire.


Memory Map
==========

There is no ROM, and nothing in zero page is used or reserved — the
Picocomputer starts every project as a clean slate. VGA, audio, storage,
keyboards, mice, gamepads, the RTC, and networking are all reached
through just the 32 registers of the RIA.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Address
     - Description
   * - $0000-$FEFF
     - RAM, 63.75 KB
   * - $FF00-$FFCF
     - Unassigned
   * - $FFD0-$FFDF
     - VIA, see the `WDC datasheet
       <https://www.westerndesigncenter.com/wdc/w65c22-chip.php>`_
   * - $FFE0-$FFFF
     - RIA, see the :doc:`RP6502-RIA datasheet <ria>`
   * - $10000-$1FFFF
     - XRAM, 64 KB for :doc:`ria` and :doc:`vga`

The unassigned space is open for hardware experimenters. Design your own
chip-select logic to use it: add more VIAs downward and other hardware
upward — for example, VIA0 at $FFD0, VIA1 at $FFC0, SID0 at $FF00, and
SID1 at $FF20.


Application Binary Interface
============================

.. seealso::

   :doc:`ria` — the hardware register map referenced throughout this section.

The ABI for calling the operating system is based on fastcall from the
`cc65 internals <https://cc65.github.io/doc/cc65-intern.html>`__. The OS
itself uses nothing from cc65 and is just as easy to call from assembly.
At its core, the ABI is four simple rules:

* Stack arguments are pushed left to right.
* Last argument passed by register A, AX, or AXSREG.
* Return value in register AX or AXSREG.
* May return data on the stack.

A and X are the 6502 registers. The pseudo-register AX combines them
into 16 bits, and AXSREG extends that to 32 bits with the 16 SREG bits.
Here's how to make an OS call through the RIA registers. Every OS call is
specified as a C declaration, like so:

.. c:function:: int doit(int arg0, int arg1);

The RIA has registers called ``RIA_A``, ``RIA_X``, and ``RIA_SREG``. An
int is 16 bits, so we load arg1 into the ``RIA_A`` and ``RIA_X``
registers. Throughout this explanation, "A" means the 6502 register and
"RIA_A" means the RIA register.

arg0 goes on the XSTACK. Reading ``RIA_XSTACK`` pops bytes; writing
pushes them. It's a top-down stack, so push each argument left to right,
keeping little-endian byte order.

To execute the call, store the operation ID in ``RIA_OP``; the operation
begins immediately. You can keep the 6502 busy with other work — a
loading animation, say — by polling ``RIA_BUSY``, or just JSR to
``RIA_SPIN`` to block until it's done.

``JSR RIA_SPIN`` can unblock within 3 clock cycles and loads A and X for
you. Sequential operations run fastest this way. Under the hood, you're
jumping into a self-modifying program that runs out of the RIA registers.

.. code-block:: asm

   FFF1: BRA #$??   ; RIA_BUSY {-2 or 0}
   FFF3: LDA #$??   ; RIA_A
   FFF5: LDX #$??   ; RIA_X
   FFF7: RTS

Polling is just snooping on that same program. The ``RIA_BUSY`` register
is the -2 or 0 in the BRA above. Per the RIA datasheet, bit 7 signals
busy, which the 6502 can test quickly with the BIT operator to set flag
N. Once it clears, read ``RIA_A`` and ``RIA_X`` with absolute instructions.

.. code-block:: asm

   wait: BIT RIA_BUSY
         BMI wait
         LDA RIA_A
         LDX RIA_X

Any operation that returns ``RIA_A`` also returns ``RIA_X`` to help with
C integer promotion. Loading X last allows fast testing for negative
return values. ``RIA_SREG`` is updated only for 32-bit returns, and
``RIA_ERRNO`` only when there's an error.

Some operations return strings or structures on the stack. Pull the
entire stack before the next call or use
``zxstack()`` to abandon the stack in O(1) time without a loop.
Tail-call optimizations are still possible, though — you can chain
`read_xstack() <READ_XSTACK>`_ and `write_xstack() <WRITE_XSTACK>`_ to
copy a file without touching any RAM or XRAM.

The time operations chain the same way, without cycling the XSTACK:
`TIME_GET`_ returns seconds positioned as the input to `GMTIME`_,
`LOCALTIME`_, or `TIME_SET`_; their struct tm feeds `MKTIME`_ directly,
or `STRFTIME`_ after pushing only the zero-terminated format on top;
and `MKTIME`_ returns seconds ready for another conversion.

Short Stacking
---------------

In the pursuit of saving every cycle, you can trim a few off the stack
push when you don't need the full range. This applies only to the first
stack argument pushed. Take `LSEEK`_:

.. code-block:: C

   long f_lseek(long offset, int whence, int fildes)

Here you push a 32-bit value, and — not by coincidence — it sits in the
right position for short stacking. If the offset always fits in 16 bits,
push two bytes instead of four.

Trimmed bytes are zero-filled, so short pushes read as unsigned. The
time operations accept seconds as 4 or 8 bytes; negative values need
all 8.

Shorter AX
----------

Many operations can save a few cycles by ignoring REG_X. Returned
integers are always at least 16 bits, to help with C integer promotion,
but many operations ignore REG_X on the way in and keep their return
value within REG_A. Those are flagged below as "A regs".

Bulk Data
---------

Functions that move bulk data come in two flavors, depending on where
the data lives. A RAM pointer means nothing to the RIA, since it can't
touch 6502 RAM — so bulk data moves through the XSTACK or XRAM instead.

Bulk XSTACK Operations
~~~~~~~~~~~~~~~~~~~~~~

These work only for sizes of 512 bytes or less — the size of the XSTACK
they pass data on. A pointer in the C prototype marks the type and
direction (to or from the OS) of the data. A few examples:

.. code-block:: C

   int open(const char *path, int oflag);

Send ``oflag`` in ``RIA_A``; per the `OPEN`_ docs, ``RIA_X`` doesn't need
to be set. Send the path on the XSTACK by pushing the string from its
last character backward. You can skip the terminating zero, but strings
are capped at 255 bytes. From the C SDK this just works — the
implementation pushes the string for you.

.. code-block:: C

   int read_xstack(void *buf, unsigned count, int fildes)

Send ``count`` as a short stack and ``fildes`` in ``RIA_A``; per the
`READ_XSTACK`_ docs, ``RIA_X`` doesn't need to be set. The value returned
in AX tells you how many values to pull from the stack. From the C SDK,
it copies the XSTACK into buf[] for you.

.. code-block:: C

   int write_xstack(const void *buf, unsigned count, int fildes)

Send ``fildes`` in ``RIA_A``; per the `WRITE_XSTACK`_ docs, ``RIA_X``
doesn't need to be set. Push the buf data onto the XSTACK. Don't send
``count`` — the OS knows it from its internal stack pointer. From the C
SDK, it copies count bytes of buf[] onto the XSTACK for you.

Note that read() and write() are part of the C SDK, not OS operations. C
requires them to handle counts larger than the XSTACK can return, so the
implementation makes as many OS calls as it takes.

Bulk XRAM Operations
~~~~~~~~~~~~~~~~~~~~

These load and save XRAM directly through `READ_XRAM`_ and `WRITE_XRAM`_,
so you can pull assets straight in without routing them through 6502 RAM.

.. code-block:: C

   int read_xram(unsigned buf, unsigned count, int fildes)
   int write_xram(unsigned buf, unsigned count, int fildes)

The OS expects ``buf`` and ``count`` on the XSTACK as integers, with
``fildes`` in ``RIA_A``. From the 6502, reach
XRAM memory through ``RIA_RW0`` or ``RIA_RW1``.

These operations stand out for their speed and for running in the
background while the 6502 does other work. Depending on the request size,
expect up to 800 KB/sec — a full 64 KB of XRAM loads or saves multiple times
per second with no wait states or 6502 work.

Bulk XRAM operations are why the Picocomputer 6502 has no paged memory.
You don't need it when "disk" access has zero seek time and DMA to XRAM.


Application Programmer Interface
================================

.. seealso::

   `FatFs documentation <https://elm-chan.org/fsw/ff/>`__ —
   many of the filesystem functions below are thin wrappers around FatFs.

Much of this API is based on POSIX and FatFs, so filesystem and console
access should feel very familiar. A few operations reorder their
arguments or change their data structures, though. The reason becomes
clear once you're in assembly, fine-tuning short stacking and integer
demotion — shrinking a return value to fit in fewer registers. In C you
may never notice, because the standard library wraps these calls in
familiar prototypes. The ``f_lseek()`` below, for instance, reorders its
arguments to put the long one in position for short stacking — but you
don't have to call ``f_lseek()`` from C. You can call the usual
``lseek()``, which keeps the traditional argument order.

The OS is built around FAT filesystems, the de facto standard for
unsecured USB storage. POSIX filesystems aren't fully compatible with
FAT, but there's a solid core of basic I/O where the two agree
completely. So you'll find familiar POSIX functions like ``open()``
alongside others like ``f_stat()`` — close to their POSIX cousins, but
tailored to FAT. If a true POSIX ``stat()`` is ever needed, it can be
built in the C standard library or in an application by translating
``f_stat()`` data.


ZXSTACK
-------
.. c:function:: void zxstack (void);

   Abandon the XSTACK by resetting the XSTACK pointer. This is the only
   operation you don't have to wait on, and you never need it after a
   failed operation. It's handy when you want to quickly ignore part of a
   returned structure.

   :Op code: RIA_OP_ZXSTACK 0x00
   :C proto: rp6502.h


XREG
----

.. c:function:: int xreg (char device, char channel, unsigned char address, ...);
.. c:function:: int xregn (char device, char channel, unsigned char address, unsigned count, ...);

   Prefer xreg() from C to avoid a counting mistake. The count isn't sent
   over the ABI, so both prototypes are equally valid.

   The variadic argument is a list of ints to store in the extended
   registers, starting at address on the given device and channel. See the
   :doc:`ria` and :doc:`vga` docs for what each register does. Setting an
   extended register can fail, which doubles as feature detection: EINVAL
   means the device sent a negative acknowledgement, and EIO means a
   timeout waiting for ack/nak.

   This is how you add virtual hardware to extended RAM. Both the :doc:`ria`
   and :doc:`vga` ship with virtual devices you can install, and you can
   build your own hardware for the PIX bus and configure it with this same
   call.

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

   The virtual _argv is called during C initialization to supply argc and
   argv to main(). It returns an array of zero-terminated string indexes
   followed by the strings themselves.
   e.g. ["ABC", "DEF"] is 06 00 0A 00 00 00 41 42 43 00 44 45 46 00
   The returned data is guaranteed valid.

   Because this can use up to 512 bytes of RAM, you opt in by providing
   storage for the argv data. Use static memory, or dynamically allocated
   memory you can free afterward. You can also reject an oversized argv by
   returning NULL.

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

   The virtual _exec is called by ria_execl() and ria_execv(). Note one
   difference from the execl() and execv() you may know: because RAM is
   precious, the path is supplied once, not again in argv[0]. The launched
   ROM sees argv[0] as the filename.

   The data sent by _exec() is checked for pointer safety and sanity, but
   the path is assumed to point at a loadable ROM file. On EINVAL, the argv
   buffer is cleared, so later calls to _argv() return an empty set. If the
   ROM turns out to be invalid, the user is dropped back to the console
   with an error message.

   The ria_execl() and ria_execv() wrappers accept at most 16 strings (the
   path plus up to 15 arguments) totaling no more than 512 bytes including
   the offset table; exceeding either limit returns -1 with EINVAL.

   :Op code: RIA_OP_EXEC 0x09
   :C proto: rp6502.h
   :returns: Does not return on success — the new ROM begins
      executing. -1 on error.
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


TIME_GET
--------

.. c:function:: time_t time (time_t *timep)

   Obtains the current time as seconds since the Unix epoch,
   1970-01-01T00:00:00Z. The seconds are pushed to the XSTACK as a
   64-bit signed integer.

   :Op code: RIA_OP_TIME_GET 0x3F
   :C proto: time.h
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EIO


TIME_SET
--------

.. c:function:: int time_set (long long time)

   Sets the clock to seconds since the Unix epoch. Push the seconds to
   the XSTACK as a signed integer of up to 64 bits; short pushes are
   unsigned.

   :Op code: RIA_OP_TIME_SET 0x3E
   :C proto: rp6502.h
   :param time: Seconds since 1970-01-01T00:00:00Z.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EINVAL, ERANGE


GMTIME
------

.. c:function:: struct tm *gmtime (const time_t *timep)

   .. code-block:: c

      struct tm {
         int16_t tm_sec;   /* 0-61 */
         int16_t tm_min;   /* 0-59 */
         int16_t tm_hour;  /* 0-23 */
         int16_t tm_mday;  /* 1-31 */
         int16_t tm_mon;   /* 0-11 */
         int16_t tm_year;  /* years since 1900 */
         int16_t tm_wday;  /* 0-6, Sunday = 0 */
         int16_t tm_yday;  /* 0-365 */
         int16_t tm_isdst; /* >0 DST, 0 no DST, <0 unknown */
      };

   Converts seconds since the Unix epoch to UTC broken-down time.
   Push the seconds as a signed integer of up to 64 bits; short pushes
   are unsigned. The struct tm above is pushed back to the XSTACK.

   :Op code: RIA_OP_GMTIME 0x3A
   :C proto: time.h
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EINVAL, ERANGE


LOCALTIME
---------

.. c:function:: struct tm *localtime (const time_t *timep)

   Converts seconds since the Unix epoch to local broken-down time
   using the configured time zone. Run ``help set tz`` on the monitor
   to learn how to configure your time zone. Push the seconds as a
   signed integer of up to 64 bits; short pushes are unsigned. A
   struct tm (see `GMTIME`_) is pushed back to the XSTACK.

   :Op code: RIA_OP_LOCALTIME 0x3B
   :C proto: time.h
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EINVAL, ERANGE


MKTIME
------

.. c:function:: time_t mktime (struct tm *timep)

   Converts local broken-down time to seconds since the Unix epoch.
   Push a struct tm (see `GMTIME`_) to the XSTACK; fields outside
   their ranges are normalized. The seconds are pushed back as a
   64-bit signed integer. The C library mktime() then calls
   `LOCALTIME`_ to write the normalized struct, with tm_wday and
   tm_yday set, back to the caller.

   :Op code: RIA_OP_MKTIME 0x3C
   :C proto: time.h
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EINVAL, ERANGE


STRFTIME
--------

.. c:function:: size_t strftime (char *buf, size_t bufsize, const char *format, const struct tm *tm)

   Formats a broken-down time as a string. Push a struct tm (see
   `GMTIME`_), then a zero-terminated format string, to the XSTACK.
   All struct tm fields must be in range, e.g. as returned by
   `GMTIME`_, `LOCALTIME`_, or `MKTIME`_. The formatted string is
   pushed back without a terminator and its length returned; the
   format and result share the XSTACK, which limits the result. The
   C library strftime() compares the length to its buffer size and
   abandons an oversized result with `ZXSTACK`_.

   ``%a %A %b %B %c %p %r %x %X`` follow the locale set with
   ``SET LOC``. ``%z %Z`` follow the time zone set with ``SET TZ``.
   The format and result are code page text. ``%E`` and ``%O``
   modifiers are ignored.

   :Op code: RIA_OP_STRFTIME 0x3D
   :C proto: time.h
   :returns: Length of the formatted string. 0 if empty or it does
      not fit. -1 on error.
   :a regs: return
   :errno: EINVAL


OPEN
----

.. c:function:: int open (const char *path, int oflag)

   Create a connection between a file and a file descriptor.

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

   Read ``count`` bytes from a file into a buffer. This is implemented in
   the compiler library as a series of calls to `READ_XSTACK`_.

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

   Read ``count`` bytes from a file to the XSTACK.

   :Op code: RIA_OP_READ_XSTACK 0x16
   :C proto: rp6502.h
   :param buf: Destination for the returned data.
   :param count: Quantity of bytes to read. 0x200 max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes read is returned. On error, -1 is
      returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT,
      FR_TIMEOUT

READ_XRAM
---------

.. c:function:: int read_xram (unsigned buf, unsigned count, int fildes)

   Read ``count`` bytes from a file to XRAM.

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

   Write ``count`` bytes from a buffer to a file. This is implemented in
   the compiler library as a series of calls to `WRITE_XSTACK`_.

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

   Write ``count`` bytes from the XSTACK to a file.

   :Op code: RIA_OP_WRITE_XSTACK 0x18
   :C proto: rp6502.h
   :param buf: Location of the data.
   :param count: Quantity of bytes to write. 0x200 max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes written is returned. On error, -1
      is returned.
   :a regs: fildes
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT,
      FR_TIMEOUT


WRITE_XRAM
----------

.. c:function:: int write_xram (unsigned buf, unsigned count, int fildes)

   Write ``count`` bytes from XRAM to a file.

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

.. c:function:: long f_lseek (long offset, int whence, int fildes)
.. c:function:: off_t lseek (int fildes, off_t offset, int whence)

   Move the read/write pointer. The OS uses the ABI format of f_lseek(). An
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
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE,
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

   Returns file or directory info for requested path. See the
   `FatFs documentation <https://elm-chan.org/fsw/ff/doc/sfileinfo.html>`__
   for details about the data structure.

   :Op code: RIA_OP_STAT 0x1F
   :C proto: rp6502.h
   :param path: Pathname to a directory entry.
   :param dirent: Returned f_stat_t data.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE,
      FR_NO_PATH, FR_INVALID_NAME, FR_INVALID_DRIVE, FR_NOT_ENABLED,
      FR_NO_FILESYSTEM, FR_TIMEOUT, FR_NOT_ENOUGH_CORE


OPENDIR
-------

.. c:function:: int f_opendir (const char* name)

   Create a connection between a directory and a directory descriptor.

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

   Returns directory entry info for the current read position of a
   directory descriptor, then advances the read position.

   :Op code: RIA_OP_READDIR 0x21
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :param dirent: Returned f_stat_t data.
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
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
   :param offs: New read position, as returned by f_telldir().
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
   :a regs: return, crtime
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
   :errno: EINVAL, FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_PATH,
      FR_INVALID_NAME, FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM,
      FR_TIMEOUT, FR_NOT_ENOUGH_CORE


CHDRIVE
-------

.. c:function:: int f_chdrive (const char* name)

   Change the current drive.
   Valid names are ``MSC0:``–``MSC9:`` with shortcuts ``0:``–``9:``.

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

   Get the volume label. Label must have room for (11+1) bytes.

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


RLN_LASTKEY
-----------

.. c:function:: int ria_rln_lastkey (char* key, unsigned char* action)

   Returns the raw bytes of the most recently completed input sequence
   typed by the user during a non-blocking cooked read from ``CON:``.
   This includes single characters and multi-byte escape sequences such
   as arrow, function, and editing keys. The ``action`` out-parameter
   reports whether the line editor handled the key as an editing
   action (non-zero) or passed it through (zero).
   Reading consumes the captured sequence; the next call returns 0
   until another key is typed. Sequences longer than 32 bytes, or any
   call made while no line read is in progress, return 0.

   :Op code: RIA_OP_RLN_LASTKEY 0x30
   :C proto: rp6502.h
   :param key: Storage for the returned byte sequence.
   :param action: Out-parameter set non-zero if the key triggered an
      editing action.
   :returns: Length of key sequence. 0 if no key is available.
   :a regs: return
   :errno: EINVAL


RLN_PEEK
--------

.. c:function:: int ria_rln_peek (char* peek, unsigned char* pos)

   Returns the current contents of the line editor buffer and the
   cursor position within it. The buffer bytes are pushed to the XSTACK.
   Returns 0 with an empty buffer when no line read is in progress.

   :Op code: RIA_OP_RLN_PEEK 0x31
   :C proto: rp6502.h
   :param peek: Storage for the returned buffer contents. The C wrapper
      null-terminates the result, so it must hold up to
      ``RIA_ATTR_RLN_LENGTH`` + 1 bytes (256 max).
   :param pos: Out-parameter set to the cursor position within the
      buffer.
   :returns: Length of the buffer contents.
   :a regs: return
   :errno: EINVAL


RLN_POKE
--------

.. c:function:: int ria_rln_poke (const char* poke)

   Feeds a string to the line editor as if the user had typed it. The
   bytes pass through the same input pipeline as live keystrokes:
   printable characters are written at the cursor (in overwrite mode
   while the editor is in its line-edit phase), and recognized editing
   escape sequences are honored. Any C0 control byte (0x00–0x1F) finishes
   the input, with two exceptions — ESC (``\33``) begins a CSI sequence,
   and CAN (``\30``) aborts an in-flight one. Control bytes other than
   CR (``\r``) echo in caret notation (``^@``..``^_``)
   when the input length is at least 2. LF submits the field like CR but
   adds no linefeed, which is useful for form input on the last terminal
   row.

   :Op code: RIA_OP_RLN_POKE 0x32
   :C proto: rp6502.h
   :param poke: Null-terminated string to feed into the editor.
   :returns: 0.
   :a regs: return
   :errno: EINVAL


EXIT
----

.. c:function:: void exit (int status)

   Halt the 6502 and hand the console back to the RP6502 monitor. This is
   the only operation that never returns; the OS pulls RESB low before the
   next instruction can execute. The status value is kept for the next ROM
   and is readable via ``RIA_ATTR_EXIT_CODE``.

   Dropping the user back to the monitor is generally discouraged, but
   calling exit() — or falling off the end of main() — beats locking up.

   :Op code: RIA_OP_EXIT 0xFF
   :C proto: stdlib.h
   :a regs: status
   :param status: 0 is success, 1-255 for error.


Launcher
========

The launcher is a feature of the RP6502 process manager that lets one ROM
act as a persistent host for all the others. A ROM registers as the launcher
by setting ``RIA_ATTR_LAUNCHER`` to 1 via :c:func:`ria_attr_set`. From then
on, the process manager automatically re-executes the launcher ROM whenever
any ROM it launched stops. When the launcher ROM itself stops, the chain
ends, the registration clears, and control returns to the monitor.

The launcher ROM decides what to run next by calling `EXEC`_, optionally
passing arguments to the new ROM through argv. The launched ROM reads those
arguments back with `ARGV`_.

Two keystrokes stop a running ROM. Ctrl-Alt-Del stops it and clears the
launcher registration at any time, always returning you to the monitor —
handy for system maintenance. Alt-F4 stops the running ROM and returns to
the launcher, or to the monitor if the ROM was run from there. Pressing
Alt-F4 while the registered launcher ROM is itself running does nothing; it
won't stop it. That makes Alt-F4 the keystroke for ending a ROM while
staying inside your preferred launcher framework, and Ctrl-Alt-Del the one
for breaking all the way back to the monitor.

ROM Cartridge Menu
------------------

The most natural use of the launcher is a menu-driven ROM selector — much
like slotting a physical cartridge into a retro console. The launcher ROM
scans the storage device for ``.rp6502`` files, presents the list, and calls
`EXEC`_ with the chosen filename. When that ROM stops, whether normally or
with an error, the process manager re-executes the launcher and the user
lands back on the menu.

No manual reset is needed between runs. Each ROM is a self-contained binary
that knows nothing about the menu. The launcher can supply context through
argv — a save-file path or difficulty setting, say — and the ROM just calls
`EXIT`_ when it's done.


RIA Attributes
==============

RIA attributes are 31-bit values identified by an 8-bit ID, accessed with
:c:func:`ria_attr_get` and :c:func:`ria_attr_set`. Both succeed for any
valid attribute ID. Getting or setting an unknown ID returns -1 with
``errno`` set to ``EINVAL``, as does trying to set a get-only attribute.

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
       immediately and revert to the system setting when the ROM stops.
   * - | 0x02
       | ``RIA_ATTR_CODE_PAGE``
     - Active OEM code page used by the filesystem, console, and default
       :doc:`VGA <vga>` font. Reverts to the system setting when the ROM
       stops. If the requested page is unavailable, the system setting is
       selected; follow a set with a get to confirm the result.
       One of: 437, 720, 737, 771, 775, 850, 852, 855, 857, 860, 861, 862,
       863, 864, 865, 866, 869.
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
     - BEL (``\a``) output enable on the console.
       0 silences the alert; 1 (default) enables it.
   * - | 0x06
       | ``RIA_ATTR_LAUNCHER``
     - Launcher flag. Set to 1 to register the current ROM as the launcher;
       set to 0 to deregister. See the `Launcher`_ section for full
       details and usage patterns.
   * - | 0x07
       | ``RIA_ATTR_EXIT_CODE``
     - The exit code of the last ROM to exit.
   * - | 0x08
       | ``RIA_ATTR_SIGINT``
     - Read-only Ctrl-C latch. Returns 1 if a Ctrl-C has been seen on
       any console input — UART, USB, or telnet (including the telnet
       Interrupt Process command) — since the previous get; returns 0
       otherwise. Reading clears the latch. Same as RIA IRQ SIGINT.
   * - | 0x09
       | ``RIA_ATTR_RLN_CAPS``
     - Caps mode applied to keystrokes by the console line editor.
       0 (default) passes characters through unchanged; 1 forces all
       letters to upper case; 2 inverts the case of letters. Reverts
       to the system setting when the ROM stops.
   * - | 0x0A
       | ``RIA_ATTR_RLN_WIDTH``
     - Terminal width in columns used by the stdin line editor.
       Setting a non-zero value pins the width and bypasses
       auto-detect; 0 returns the channel to auto-detect (default).
       Reverts to 0 when the ROM stops. See :doc:`term` for how the
       console manifold probes terminal size.
   * - | 0x0B
       | ``RIA_ATTR_RLN_HEIGHT``
     - Terminal height in rows used by the stdin line editor. Setting
       and revert semantics match ``RIA_ATTR_RLN_WIDTH``. With both
       width and height pinned, the size-probe handshake is skipped
       entirely.
   * - | 0x0C
       | ``RIA_ATTR_RLN_SUPPRESS_NL``
     - Prevents read line from sending a CRLF at the end of input.
       Useful for using the last terminal line for field input.
   * - | 0x10
       | ``RIA_ATTR_CLK_RUN_MS``
     - Read-only milliseconds the 6502 has been running, counted from
       the release of reset. Wraps approximately every 24.8 days. This
       is the C ``clock()``, which has a ``CLOCKS_PER_SEC`` of 1000.
   * - | 0x11
       | ``RIA_ATTR_CLK_RUN_CS``
     - Read-only 6502 run time in 1/100 second ticks. Wraps
       approximately every 248 days.
   * - | 0x12
       | ``RIA_ATTR_CLK_RUN_DS``
     - Read-only 6502 run time in 1/10 second ticks. Wraps
       approximately every 6.8 years.
   * - | 0x13
       | ``RIA_ATTR_CLK_RUN_S``
     - Read-only 6502 run time in whole seconds. Wraps approximately
       every 68 years.


ERRNO_OPT Compiler Constants
============================

OS calls set ``RIA_ERRNO`` when an error occurs. Because cc65 and llvm-mos
each define their own errno constants, the errno option selects which set
of numeric values to use. Both compilers set it automatically in their C
runtime, and ``errno`` in C maps directly to ``RIA_ERRNO``. Assembly
programs must set ``RIA_ATTR_ERRNO_OPT`` themselves before any OS call that
can fail.

The OS maps FatFs errors onto errno, and RP6502 emulators and simulators
are expected to map their native errors too. The table below lists the
FatFs mappings. Because FatFs is so central to the OS, each call is
documented with its native FatFs errors to help when cross-referencing the
`FatFs documentation <https://elm-chan.org/fsw/ff/>`__.

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * -
     - cc65
     - llvm-mos
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
     - 13
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

.. note::

   cc65 does not define ``EDOM`` or ``EILSEQ``; under option 1 the OS reports
   both as ``EUNKNOWN`` (18).
