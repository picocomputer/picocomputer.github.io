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
compilers, plus calls that control RP6502 features and manage FAT
filesystems.

.. note::

   ExFAT is ready to go and will be enabled when the patents expire.


.. _os-memory-map:

Memory Map
==========

Everything below $FF00 is RAM, and nothing in zero page is used or
reserved. The Picocomputer starts every project as a clean slate. VGA,
audio, storage, keyboards, mice, gamepads, the RTC, and networking are
all reached through just the 32 registers of the RIA.

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
chip-select logic to use it. Add more VIAs downward and other hardware
upward, for example VIA0 at $FFD0, VIA1 at $FFC0, SID0 at $FF00, and
SID1 at $FF20.

Your program's own layout of RAM and XRAM is set up in the SDK's
:ref:`RAM Memory Map <sdk-ram-memory-map>` and
:ref:`XRAM Memory Map <sdk-xram-memory-map>`.


Application Binary Interface
============================

.. seealso::

   :doc:`ria` — the hardware register map referenced throughout this section.

A C program does none of this, because the compiler's library is the
implementation. What follows is for assembly programs and for anyone
bringing another compiler to the Picocomputer.

The ABI for calling the operating system is based on fastcall from the
`cc65 internals <https://cc65.github.io/doc/cc65-intern.html>`__. The OS
itself uses nothing from cc65, so assembly calls it the same way C
does. The compiler is a convenience here, not a dependency.

At its core, the ABI is four rules:

* Stack arguments are pushed left to right.
* Last argument passed by register A, AX, or AXSREG.
* Return value in register AX or AXSREG.
* May return data on the stack.

A and X are the 6502 registers. The pseudo-register AX combines them
into 16 bits, and AXSREG extends that to 32 bits with the 16 SREG bits.
Every OS call is specified as a C declaration, like so:

.. c:function:: int doit(int arg0, int arg1);
   :no-index-entry:
   :no-contents-entry:

The RIA has registers called ``RIA_A``, ``RIA_X``, and ``RIA_SREG``. An
int is 16 bits, so arg1 goes into the ``RIA_A`` and ``RIA_X``
registers. Throughout this explanation, "A" means the 6502 register and
"RIA_A" means the RIA register.

arg0 goes on the XSTACK. Reading ``RIA_XSTACK`` pops bytes; writing
pushes them. It's a top-down stack, so push the arguments left to right,
and push each value high byte first so that it lies in memory low byte
first.

To execute the call, store the operation ID in ``RIA_OP``; the operation
begins immediately. You can keep the 6502 busy with other work, such as a
loading animation, by polling ``RIA_BUSY``, or just JSR to ``RIA_SPIN``
to block until it's done.

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
entire stack before the next call, or use `ria_drop() <DROP_XSTACK_>`_
to abandon the stack in O(1) time without a loop. One operation's output
can also be the next one's input. `read_xstack() <READ_XSTACK_>`_ leaves
its data on the XSTACK where `write_xstack() <WRITE_XSTACK_>`_ takes it,
so the two copy a file without touching any RAM or XRAM.

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

   ABI long f_lseek(long offset, unsigned char whence, int fildes)

Here you push a 32-bit value, and — not by coincidence — it sits in the
right position for short stacking. If the offset always fits in 16 bits,
push two bytes instead of four.

Signed arguments are sign-extended, so two bytes carry -32768 to 32767.
Unsigned arguments are zero-filled.

.. warning::

   Size a short push by the signed range. An offset of 200 pushed as the
   single byte 0xC8 arrives as -56, because the top bit of 0xC8 is the
   sign. Push 0x00 and then 0xC8 to send 200.

Shorter AX
----------

A program can save a few cycles by leaving ``RIA_X`` alone. Returned
integers are always at least 16 bits, to help with C integer promotion,
but many operations ignore ``RIA_X`` on the way in and keep their return
value within ``RIA_A``. Those are listed below under ``a regs``.

Bulk Data
---------

Functions that move bulk data come in two flavors, depending on where
the data lives. A RAM pointer means nothing to the RIA, since it can't
touch 6502 RAM, so bulk data moves through the XSTACK or XRAM instead.

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
are capped at 255 bytes. From the C SDK, the implementation pushes the
string for you.

.. code-block:: C

   int read_xstack(void *buf, unsigned count, int fildes)

Send ``count`` as a short stack and ``fildes`` in ``RIA_A``; per the
`READ_XSTACK`_ docs, ``RIA_X`` doesn't need to be set. The value returned
in AX is the number of bytes to pull from the stack. From the C SDK, it
copies the XSTACK into buf[] for you.

.. code-block:: C

   int write_xstack(const void *buf, unsigned count, int fildes)

Send ``fildes`` in ``RIA_A``; per the `WRITE_XSTACK`_ docs, ``RIA_X``
doesn't need to be set. Push the buf data onto the XSTACK. Don't send
``count``; the OS takes it from the XSTACK pointer. From the C SDK, it
copies count bytes of buf[] onto the XSTACK for you.

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

The OS takes ``buf`` and ``count`` on the XSTACK as integers, with
``fildes`` in ``RIA_A``. The 6502 reads and writes XRAM through
``RIA_RW0`` or ``RIA_RW1``.

These operations stand out for their speed and for running in the
background while the 6502 does other work. Depending on the request size,
expect up to 800 KB/sec. A full 64 KB of XRAM loads or saves multiple times
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
familiar prototypes, and the flags below mark the two forms apart wherever
they differ.

The OS is built around FAT filesystems, the de facto standard for
unsecured removable storage such as USB drives and memory cards. POSIX
filesystems aren't fully compatible with FAT, but there's a solid core of
basic I/O where the two agree completely. So you'll find familiar POSIX
functions like ``open()`` alongside others like ``f_stat()`` — close to
their POSIX cousins, but tailored to FAT. If a true POSIX ``stat()`` is
ever needed, it can be built in the C standard library or in an
application by translating ``f_stat()`` data.

Each operation below is one or more C declarations followed by a short
list of details. Some declarations carry a flag:

.. c:function:: ABI int an_operation (int arg0, int arg1)
                lib int a_library_call (int arg1, int arg0)
   :no-index-entry:
   :no-contents-entry:

``ABI`` marks a prototype that is only the ABI form. ``LIB`` marks a
prototype that exists only in the library. A prototype with neither flag
is both.

``Op code`` is the value a program writes to ``RIA_OP`` to start the
operation, and ``None`` marks one the C library builds out of other
operations. ``C proto`` names the header the declaration comes from.
``a regs`` names the arguments and the return value that fit in ``RIA_A``
alone, so a program can leave ``RIA_X`` unset. ``errno`` lists what can
go wrong, and `ERRNO_OPT Compiler Constants`_ gives the number of each.


.. _os-extended-memory:

Extended Memory
---------------

DROP_XSTACK
~~~~~~~~~~~

.. c:function:: void ria_drop (void);

   Empty the XSTACK by resetting its pointer. This is the only operation
   that finishes immediately, so there is no need to wait for it. It is
   never needed after a failed operation, because a failure already
   empties the XSTACK. Use it to discard the rest of a returned structure,
   or arguments already pushed for a call you decide not to make.

   :Op code: RIA_OP_DROP_XSTACK 0x00
   :C proto: rp6502.h


.. _os-xreg:

XREG
~~~~

.. c:function:: int xreg (char device, char channel, unsigned char address, ...);
                lib int xregn (char device, char channel, unsigned char address, unsigned count, ...);

   Prefer xreg() from C to avoid a counting mistake. The count isn't sent
   over the ABI, so both prototypes are equally valid.

   The variadic argument is a list of ints to store in the extended
   registers, starting at address on the given device and channel. See the
   :doc:`ria` and :doc:`vga` docs for what each register does. Setting an
   extended register can fail, which doubles as feature detection: EINVAL
   means the device sent a negative acknowledgement, EIO means a timeout
   waiting for ack/nak, and EACCES means a write to the VGA control
   channel, which the RIA manages.

   This is how you add virtual hardware to extended RAM. Both the :doc:`ria`
   and :doc:`vga` ship with virtual devices you can install, and you can
   build your own hardware for the PIX bus and configure it with this same
   call.

   Assembly programs use the ``xreg`` macro in rp6502.inc, which takes the
   same arguments: ``xreg 1, 0, 1, 3, 2, $FF00``.

   :Op code: RIA_OP_XREG 0x01
   :C proto: rp6502.h
   :param device: PIX device ID. 0:RIA, 1:VGA, 2-6:unassigned
   :param channel: PIX channel. 0-15
   :param address: PIX address. 0-255
   :param ...: 16 bit integers to set starting at address.
   :a regs: return
   :errno: EACCES, EINVAL, EIO


XRAM_STRUCT_SET
~~~~~~~~~~~~~~~

.. c:macro:: xram0_struct_set (addr, type, member, val)
             xram1_struct_set (addr, type, member, val)

   Set one member of a structure in XRAM, given the structure's address, its
   type and the member's name. These are convenient but not efficient,
   because every call sets the step and address.

   :Op code: None
   :C proto: rp6502.h


XRAM_READ
~~~~~~~~~

.. c:function:: lib void xram0_read (void* dest, unsigned src, unsigned count)
                lib void xram1_read (void* dest, unsigned src, unsigned count)

   Copy ``count`` bytes from XRAM to 6502 RAM, like ``memcpy``.
   ``xram0_read()`` copies through portal 0 and ``xram1_read()`` through
   portal 1. The other portal is not touched. A count of 0 copies nothing.

   The call changes the portal's address register and sets its step
   register to 1. An interrupt handler that uses the same portal must save
   and restore both.

   This copies within the machine. To load XRAM from a file, use
   `READ_XRAM`_.

   :Op code: None
   :C proto: rp6502.h
   :param dest: Destination in 6502 RAM.
   :param src: Source address in XRAM.
   :param count: Quantity of bytes to copy.


XRAM_WRITE
~~~~~~~~~~

.. c:function:: lib void xram0_write (unsigned dest, const void* src, unsigned count)
                lib void xram1_write (unsigned dest, const void* src, unsigned count)

   Copy ``count`` bytes from 6502 RAM into XRAM. This is the other direction
   of `XRAM_READ`_ and follows the same rules.

   :Op code: None
   :C proto: rp6502.h
   :param dest: Destination address in XRAM.
   :param src: Source in 6502 RAM.
   :param count: Quantity of bytes to copy.


XRAM_SET
~~~~~~~~

.. c:function:: lib void xram0_set (unsigned dest, unsigned char val, unsigned count)
                lib void xram1_set (unsigned dest, unsigned char val, unsigned count)

   Fill ``count`` bytes of XRAM with ``val``, like ``memset``.
   ``xram0_set()`` uses portal 0 and ``xram1_set()`` uses portal 1, with the
   same effect on the portal's registers as `XRAM_READ`_.

   :Op code: None
   :C proto: rp6502.h
   :param dest: Address in XRAM to fill.
   :param val: Byte written to every position.
   :param count: Quantity of bytes to fill.


XRAM_MOVE
~~~~~~~~~

.. c:function:: lib void xram_move (unsigned dest, unsigned src, unsigned count)

   Copy ``count`` bytes from one XRAM address to another, like ``memmove``,
   so the result is correct even when the two ranges overlap. Portal 0 reads
   and portal 1 writes, and both address registers are changed. Both step
   registers are left at 1, or at -1 if the destination overlaps the end of
   the source and the copy runs backward.

   :Op code: None
   :C proto: rp6502.h
   :param dest: Destination address in XRAM.
   :param src: Source address in XRAM.
   :param count: Quantity of bytes to copy.


Process
-------

.. _os-argv:

ARGV
~~~~

.. c:function:: ABI int _argv (char *argv, int size)

   The virtual _argv is called during C initialization to supply argc and
   argv to main(). It returns an array of zero-terminated string indexes
   followed by the strings themselves. The returned data is guaranteed
   valid. For example, ["ABC", "DEF"] is:

   .. code-block:: text

      06 00 0A 00 00 00 41 42 43 00 44 45 46 00

   Because this can use up to 512 bytes of RAM, you opt in by defining
   ``__argv_mem()`` to provide storage for the argv data. Use static
   memory, or dynamically allocated memory you can free afterward. You can
   also reject an oversized argv by returning NULL. The argv data is on
   the XSTACK while ``__argv_mem()`` runs, so ``__argv_mem()`` must not
   make an OS call, not even through printf().

   .. code-block:: c

      void *__argv_mem(size_t size) { return malloc(size); }

   :Op code: RIA_OP_ARGV 0x08
   :C proto: (none)
   :returns: Size of argv data
   :errno: will not fail


EXEC
~~~~

.. c:function:: ABI int _exec (const char *argv, int size)
                lib int ria_execl (const char *path, ...)
                lib int ria_execv (const char *path, char * const argv[])

   The virtual _exec is called by ria_execl() and ria_execv(). Note one
   difference from the execl() and execv() you may know: because RAM is
   precious, the path is supplied once, not again in argv[0]. In the
   launched ROM, argv[0] is the absolute form of the path given, with its
   drive, or ``:NAME`` for a ROM on the null drive, as described in
   :ref:`Installed ROMs <port-installed-roms>`.

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


EXIT
~~~~

.. c:function:: void exit (int status)

   Halt the 6502 and hand the console back to the machine. This is
   the only operation that never returns; the OS pulls RESB low before the
   next instruction can execute. The status value is kept for the next ROM
   and is readable via ``RIA_ATTR_EXIT_CODE``.

   Dropping the user out of your program is generally discouraged, but
   calling exit() beats locking up, as does falling off the end of main().

   :Op code: RIA_OP_EXIT 0xFF
   :C proto: stdlib.h
   :a regs: status
   :param status: 0 is success, 1-255 for error.


Attributes
----------

ATTR_GET
~~~~~~~~

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
~~~~~~~~

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


Time
----

TIME_GET
~~~~~~~~

.. c:function:: ABI int _time (time_t *timep)
                lib time_t time (time_t *timep)

   Obtains the current time as seconds since the Unix epoch,
   1970-01-01T00:00:00Z. The operation pushes the seconds to the XSTACK
   as a 64-bit signed integer and returns 0, or -1 on error. The cc65
   time_t has 32 bits, so the cc65 time() fails with ERANGE when the
   seconds do not fit.

   :Op code: RIA_OP_TIME_GET 0x3F
   :C proto: time.h
   :returns: The current time, also stored at ``timep`` if it is not
      NULL. -1 on error.
   :a regs: return
   :errno: EINVAL, EIO, ERANGE


TIME_SET
~~~~~~~~

.. c:function:: int time_set (long long time)

   Sets the clock to seconds since the Unix epoch. Supported only on
   :doc:`pico`.

   :Op code: RIA_OP_TIME_SET 0x3E
   :C proto: rp6502.h
   :param time: Seconds since 1970-01-01T00:00:00Z.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL


GMTIME
~~~~~~

.. c:function:: lib struct tm *gmtime (const time_t *timep)

   Converts seconds since the Unix epoch to UTC broken-down time.
   Push the seconds as a signed integer of up to 64 bits. The operation
   pushes this struct tm back to the XSTACK
   and returns 0, or -1 on error.

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

   :Op code: RIA_OP_GMTIME 0x3A
   :C proto: time.h
   :returns: Pointer to a static struct tm. NULL on error.
   :a regs: return
   :errno: EINVAL, ERANGE


LOCALTIME
~~~~~~~~~

.. c:function:: lib struct tm *localtime (const time_t *timep)

   Converts seconds since the Unix epoch to local broken-down time
   using the configured time zone. Run ``help set tz`` on an :doc:`pico`
   monitor to learn how to configure your time zone. Push the seconds as a
   signed integer of up to 64 bits. The
   operation pushes a struct tm (see `GMTIME`_) back to the XSTACK and
   returns 0, or -1 on error.

   :Op code: RIA_OP_LOCALTIME 0x3B
   :C proto: time.h
   :returns: Pointer to a static struct tm. NULL on error.
   :a regs: return
   :errno: EINVAL, ERANGE


MKTIME
~~~~~~

.. c:function:: lib time_t mktime (struct tm *timep)

   Converts local broken-down time to seconds since the Unix epoch.
   Push a struct tm (see `GMTIME`_) to the XSTACK; fields outside
   their ranges are normalized. The operation pushes the seconds back as
   a 64-bit signed integer and returns 0, or -1 on error. The C library
   mktime() then calls `LOCALTIME`_ to write the normalized struct, with
   tm_wday and tm_yday set, back to the caller.

   :Op code: RIA_OP_MKTIME 0x3C
   :C proto: time.h
   :returns: Seconds since the Unix epoch. -1 on error.
   :a regs: return
   :errno: EINVAL, ERANGE


STRFTIME
~~~~~~~~

.. c:function:: lib size_t strftime (char *buf, size_t bufsize, const char *format, const struct tm *tm)

   Formats a broken-down time as a string. Push a struct tm (see
   `GMTIME`_), then a zero-terminated format string, to the XSTACK.
   All struct tm fields must be in range, e.g. as returned by
   `GMTIME`_, `LOCALTIME`_, or `MKTIME`_. The operation pushes the
   formatted string back without a terminator and returns its length: 0
   if the result is empty or does not fit, or -1 on error. The format and
   the result share the XSTACK, which limits the result. The C library
   strftime() compares the length to its buffer size and abandons an
   oversized result with `DROP_XSTACK`_.

   ``%a %A %b %B %c %p %r %x %X`` follow the configured locale and
   ``%z %Z`` the configured time zone. Set both with ``SET LOC`` and
   ``SET TZ`` on an :doc:`pico`. The format and result are code page
   text. ``%E`` and ``%O`` modifiers are ignored.

   :Op code: RIA_OP_STRFTIME 0x3D
   :C proto: time.h
   :returns: Length of the string in ``buf``, not counting the
      terminator. 0 on error, or if the result is empty or does not fit.
   :a regs: return
   :errno: EINVAL


Files
-----

.. _os-open:

OPEN
~~~~

.. c:function:: int open (const char *path, int oflag)

   Create a connection between a file and a file descriptor.

   The options must include O_RDONLY, O_WRONLY or O_RDWR, or the call
   fails with EINVAL. An open of a directory fails with EACCES. A file can
   be open on several descriptors at once. Close a descriptor that writes
   a file before opening that file again, as described in
   :ref:`Files and Folders <port-files>`.

   A path can also name a device: ``CON:`` and ``TTY:`` in :doc:`term`,
   ``ROM:`` followed by an asset name in :doc:`sdk`, ``SAVE:`` followed by
   a save name in :ref:`RP6502-PORT <port-save>`, ``VCP0:``, ``MIDI0:``
   and ``NFC:`` in :doc:`ria`, and ``AT:`` in :doc:`ria_w`.

   :Op code: RIA_OP_OPEN 0x14
   :C proto: fcntl.h
   :param path: Pathname to a file.
   :param oflag: Bitfield of options.
   :returns: File descriptor. -1 on error.
   :a regs: return, oflag
   :errno: EACCES, EBUSY, EEXIST, EINVAL, EIO, EMFILE, ENODEV, ENOENT, ENOMEM,
      ENOSPC
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
      |    Read/write pointer is set to the end of the file at open.
      | O_EXCL 0x80
      |    If O_CREAT and O_EXCL are set, fail if the file exists.


CLOSE
~~~~~

.. c:function:: int close (int fildes)

   Finish pending writes and release the file descriptor. The descriptor
   goes back to the pool that open() draws from. What survives a failure
   after close differs by machine, as listed in
   :ref:`Durability <port-durability>`.

   :Op code: RIA_OP_CLOSE 0x15
   :C proto: fcntl.h
   :param fildes: File descriptor from open().
   :returns: 0 on success. -1 on error.
   :a regs: return, fildes
   :errno: EBADF, EIO, ENOSPC


READ
~~~~

.. c:function:: lib int read (int fildes, void *buf, unsigned count)

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
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSYS


READ_XSTACK
~~~~~~~~~~~

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
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSYS


.. _os-read-xram:

READ_XRAM
~~~~~~~~~

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
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSYS


WRITE
~~~~~

.. c:function:: lib int write (int fildes, const void *buf, unsigned count)

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
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSPC, ENOSYS


WRITE_XSTACK
~~~~~~~~~~~~

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
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSPC, ENOSYS


WRITE_XRAM
~~~~~~~~~~

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
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSPC, ENOSYS


LSEEK
~~~~~

.. c:function:: ABI long f_lseek (long offset, unsigned char whence, int fildes)
                lib off_t lseek (int fildes, off_t offset, int whence)

   Move the read/write pointer.

   This can also be used to obtain the current read/write position with
   ``f_lseek(0, SEEK_CUR, fd)``.

   A seek past the end of a file opened for writing extends the file with
   zeros. On a full drive, that seek fails with ENOSPC and leaves the file
   and the position unchanged. A seek past the end of a file opened only
   for reading stops at the end.

   :Op code: See table below.
   :C proto: f_lseek: rp6502.h, lseek: unistd.h
   :param offset: Distance to move the pointer.
   :param whence: Where the offset is measured from. See table below.
   :param fildes: File descriptor from open().
   :returns: Read/write position. -1 on error. A resulting position past
      0x7FFFFFFF cannot be represented in the returned long; the seek then
      fails with errno ERANGE and the file position is left unchanged.
   :a regs: fildes
   :errno: EBADF, EINVAL, EIO, ENOSPC, ENOSYS, ERANGE, ESPIPE

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


SYNCFS
~~~~~~

.. c:function:: int syncfs (int fildes)

   Finish pending writes for the file descriptor. The call returns once
   the data is stored, within the limits of each machine listed in
   :ref:`Durability <port-durability>`.

   :Op code: RIA_OP_SYNCFS 0x1E
   :C proto: unistd.h
   :param fildes: File descriptor from open().
   :returns: 0 on success. -1 on error.
   :a regs: return, fildes
   :errno: EACCES, EBADF, EINVAL, EIO, ENOSPC, ENOSYS


Paths
-----

STAT
~~~~

.. c:function:: int f_stat (const char* path, f_stat_t* dirent)

   Returns file or directory info for requested path. See the
   `FatFs documentation <https://elm-chan.org/fsw/ff/doc/sfileinfo.html>`__
   for details about the data structure.

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

   A drive root, such as ``/`` or ``MSC0:/``, returns one fixed entry: a
   directory named ``/``, with size 0 and zero dates. An empty path or a
   bare drive name, such as ``MSC0:``, fails with EINVAL.

   :Op code: RIA_OP_STAT 0x1F
   :C proto: rp6502.h
   :param path: Pathname to a directory entry.
   :param dirent: Returned f_stat_t data.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


UNLINK
~~~~~~

.. c:function:: int unlink (const char* name)

   Removes a file or directory from the volume. A read-only file fails
   with EACCES. Close a file before removing it.

   :Op code: RIA_OP_UNLINK 0x1B
   :C proto: unistd.h
   :param name: File or directory name to unlink (remove).
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EBUSY, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


RENAME
~~~~~~

.. c:function:: int rename (const char* oldname, const char* newname)

   Renames or moves a file or directory within its drive. A new name on
   another drive fails with ENODEV. A file already at the new name is
   replaced when the old name is also a file, and any other entry at the
   new name fails with EEXIST. Close a file before renaming it, and
   before a rename replaces it.

   :Op code: RIA_OP_RENAME 0x1C
   :C proto: stdio.h
   :param oldname: Existing file or directory name to rename.
   :param newname: New object name.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EBUSY, EEXIST, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSPC,
      ENOSYS


CHMOD
~~~~~

.. c:function:: int f_chmod (const char* path, unsigned char attr, unsigned char mask)

   Change the attributes of a file or directory.

   :Op code: RIA_OP_CHMOD 0x26
   :C proto: rp6502.h
   :param path: Pathname to a file or directory.
   :param attr: New bitfield of attributes. See table.
   :param mask: Only attributes with bits set here will be changed.
   :returns: 0 on success. -1 on error.
   :a regs: return, mask
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS

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
~~~~~

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
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS

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
~~~~~

.. c:function:: int f_mkdir (const char* name)

   Make a new directory entry.

   :Op code: RIA_OP_MKDIR 0x28
   :C proto: rp6502.h
   :param name: Pathname of the directory to create.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EEXIST, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSPC, ENOSYS


Directories
-----------

OPENDIR
~~~~~~~

.. c:function:: int f_opendir (const char* name)

   Create a connection between a directory and a directory descriptor.

   :Op code: RIA_OP_OPENDIR 0x20
   :C proto: rp6502.h
   :param name: Pathname to a directory.
   :returns: Directory descriptor. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, EMFILE, ENODEV, ENOENT, ENOMEM, ENOSYS


READDIR
~~~~~~~

.. c:function:: int f_readdir (f_stat_t* dirent, int dirdes)

   Returns directory entry info for the current read position of a
   directory descriptor, then advances the read position. At the end of
   the directory, the call succeeds and ``fname`` is empty.

   A name with a character that the code page cannot hold, or that FAT
   refuses, shows character 127 in place of each such character. That
   entry cannot be opened, because character 127 is refused in a path. On
   an :doc:`pico`, a name with a character that the code page cannot hold
   shows as its short 8.3 name instead, and that name opens the file.

   :Op code: RIA_OP_READDIR 0x21
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :param dirent: Returned f_stat_t data.
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
   :errno: EACCES, EBADF, EINVAL, EIO, ENOENT, ENOMEM, ENOSYS


CLOSEDIR
~~~~~~~~

.. c:function:: int f_closedir (int dirdes)

   Release the directory descriptor. The descriptor goes back to the pool
   that f_opendir() draws from.

   :Op code: RIA_OP_CLOSEDIR 0x22
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
   :errno: EBADF, EINVAL, EIO, ENOSYS


TELLDIR
~~~~~~~

.. c:function:: long f_telldir (int dirdes)

   Returns the read position of the directory descriptor.

   :Op code: RIA_OP_TELLDIR 0x23
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: Read position. -1 on error.
   :a regs: dirdes
   :errno: EBADF, EINVAL, ENOSYS


SEEKDIR
~~~~~~~

.. c:function:: int f_seekdir (long offs, int dirdes)

   Set the read position for the directory descriptor. The OS reads
   entries one at a time up to the new position, starting from the
   current position when seeking forward and from the start of the
   directory when seeking backward. Use this for convenience, not
   performance.

   :Op code: RIA_OP_SEEKDIR 0x24
   :C proto: rp6502.h
   :param offs: New read position, as returned by f_telldir().
   :param dirdes: Directory descriptor from f_opendir().
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
   :errno: EACCES, EBADF, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


REWINDDIR
~~~~~~~~~

.. c:function:: int f_rewinddir (int dirdes)

   Rewind the read position of the directory descriptor.

   :Op code: RIA_OP_REWINDDIR 0x25
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
   :errno: EACCES, EBADF, EINVAL, EIO, ENODEV, ENOENT, ENOSYS


Drives and Volumes
------------------

CHDIR
~~~~~

.. c:function:: int chdir (const char* name)

   Change to a directory entry. A directory on another drive also makes
   that drive the current drive.

   :Op code: RIA_OP_CHDIR 0x29
   :C proto: unistd.h
   :param name: Pathname of the directory to make current.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


CHDRIVE
~~~~~~~

.. c:function:: int f_chdrive (const char* name)

   Change the current drive. The name is that of a mounted drive, colon
   included, such as ``MSC1:``, and the name of a drive that is not
   mounted fails with ENODEV. Each drive keeps the last directory used on
   it, and that directory becomes current again. The drive names of each
   machine are listed in :ref:`Filesystems <port-filesystems>`.

   :Op code: RIA_OP_CHDRIVE 0x2A
   :C proto: rp6502.h
   :param name: Drive name to change to.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT


.. _os-getcwd:

GETCWD
~~~~~~~

.. c:function:: int f_getcwd (char* name, int size)

   Get the current working directory.

   The result is absolute and always includes a device name, such as
   ``MSC0:/games``. Each folder name in it shows as it does in
   `READDIR`_. When the directory is longer than 255 bytes, the call
   fails with ENOMEM, because no call accepts a path that long.

   :Op code: RIA_OP_GETCWD 0x2B
   :C proto: rp6502.h
   :param name: The returned directory.
   :param size: Size of the ``name`` buffer. It stays in the C library,
      which fails with ENOMEM when the directory does not fit.
   :returns: Size of returned name. -1 on error.
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM


GETLABEL
~~~~~~~~

.. c:function:: int f_getlabel (const char* path, char* label)

   Get the volume label. Label must have room for (11+1) bytes. Only an
   :doc:`pico` has volume labels, and other machines fail with EACCES, or
   ENOSYS on the Pocket.

   :Op code: RIA_OP_GETLABEL 0x2D
   :C proto: rp6502.h
   :param path: Volume to read the label from.
   :param label: Storage for returned label.
   :returns: Size of returned label. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


SETLABEL
~~~~~~~~

.. c:function:: int f_setlabel (const char* name)

   Change the volume label. Max 11 characters. Only an :doc:`pico` has
   volume labels, and other machines fail with EACCES, or ENOSYS on the
   Pocket.

   :Op code: RIA_OP_SETLABEL 0x2C
   :C proto: rp6502.h
   :param name: Label with optional volume name.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


GETFREE
~~~~~~~

.. c:function:: int f_getfree (const char* name, unsigned long* free, unsigned long* total)

   Get the free and total space of a volume in 512-byte blocks. The
   operation pushes both counts to the XSTACK in this layout:

   .. code-block:: c

      struct {
         unsigned long free;
         unsigned long total;
      };

   :Op code: RIA_OP_GETFREE 0x2E
   :C proto: rp6502.h
   :param name: Volume name.
   :param free: Storage for returned value.
   :param total: Storage for returned value.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


Line Editor
-----------

.. _os-rln-lastkey:

RLN_LASTKEY
~~~~~~~~~~~

.. c:function:: int ria_rln_lastkey (char* key, unsigned char* action)

   Returns the raw bytes of the most recently completed input sequence
   typed by the user during a non-blocking cooked read from ``CON:``.
   This includes single characters and multi-byte escape sequences such
   as arrow, function, and editing keys. The ``action`` out-parameter
   reports whether the line editor handled the key as an editing
   action (non-zero) or passed it through (zero). Reading consumes the
   captured sequence; the next call returns 0 until another key is
   typed. Sequences longer than 32 bytes, or any call made while no line
   read is in progress, return 0.

   :Op code: RIA_OP_RLN_LASTKEY 0x30
   :C proto: rp6502.h
   :param key: Storage for the returned byte sequence.
   :param action: Out-parameter set non-zero if the key triggered an
      editing action.
   :returns: Length of key sequence. 0 if no key is available.
   :a regs: return
   :errno: EINVAL


.. _os-rln-peek:

RLN_PEEK
~~~~~~~~

.. c:function:: int ria_rln_peek (char* peek, unsigned char* pos)

   Returns the current contents of the line editor buffer and the
   cursor position within it. The buffer bytes are pushed to the XSTACK.
   It fails with EINVAL when no line read is in progress.

   :Op code: RIA_OP_RLN_PEEK 0x31
   :C proto: rp6502.h
   :param peek: Storage for the returned buffer contents. The C wrapper
      null-terminates the result, so it must hold up to
      ``RIA_ATTR_RLN_LENGTH`` + 1 bytes (256 max).
   :param pos: Out-parameter set to the cursor position within the
      buffer.
   :returns: Length of the buffer contents. -1 on error.
   :a regs: return
   :errno: EINVAL


.. _os-rln-poke:

RLN_POKE
~~~~~~~~

.. c:function:: int ria_rln_poke (const char* poke)

   Feeds a string to the line editor as if the user had typed it. The
   bytes pass through the same input pipeline as live keystrokes:
   printable characters are written at the cursor (in overwrite mode
   while the editor is in its line-edit phase), and recognized editing
   escape sequences are honored. Any C0 control byte (0x00–0x1F) finishes
   the input, with two exceptions — ESC (``\33``) begins a CSI sequence,
   and CAN (``\30``) aborts an in-flight one. Control bytes other than
   CR (``\r``) echo in caret notation (``^@``..``^_``) when the input
   length is at least 2. LF submits the field like CR but adds no
   linefeed, which is useful for form input on the last terminal row.

   :Op code: RIA_OP_RLN_POKE 0x32
   :C proto: rp6502.h
   :param poke: Null-terminated string to feed into the editor.
   :returns: 0.
   :a regs: return
   :errno: EINVAL


Launcher
========

The launcher is a feature of the RP6502 process manager that lets one ROM
act as a persistent host for all the others. A ROM registers as the launcher
by setting ``RIA_ATTR_LAUNCHER`` to 1 via :c:func:`ria_attr_set`. From then
on, the process manager automatically re-executes the launcher ROM whenever
any ROM it launched stops. When the launcher ROM itself stops, the chain
ends, the registration clears, and control returns to the machine. Where
the chain ends depends on which machine: an :doc:`pico` returns to its
monitor, the :doc:`emu` exits unless debugging, and the :doc:`fpga` stops
until you load a new ROM with the host menu.

The launcher ROM runs the next one by calling `EXEC`_, optionally
passing arguments to it through argv. The launched ROM reads those
arguments back with `ARGV`_.

Two keystrokes stop a running ROM. Ctrl-Alt-Del stops it and clears the
launcher registration at any time, always returning you to the machine,
which is handy for system maintenance. Alt-F4 stops the running ROM and
returns to the launcher, or to the machine if the ROM was run from there.
Pressing Alt-F4 while the registered launcher ROM is itself running does
nothing; it won't stop it. That makes Alt-F4 the keystroke for ending a
ROM while staying inside your preferred launcher framework, and
Ctrl-Alt-Del the one for breaking all the way back out.

ROM Cartridge Menu
------------------

The most natural use of the launcher is a menu-driven ROM selector — much
like slotting a physical cartridge into a retro console. The launcher ROM
lists the ``.rp6502`` files in a folder, presents the list, and calls
`EXEC`_ with the chosen filename. When that ROM stops, whether normally or
with an error, the process manager re-executes the launcher and the user
lands back on the menu. Listing a folder is not available on every
machine, and the machines without it are listed under
:ref:`Compatibility <port-compatibility>`.

No manual reset is needed between runs. Each ROM is a self-contained binary
with nothing in it about the menu. The launcher can supply context through
argv, such as the ``SAVE:`` name of a save slot or a difficulty setting,
and the ROM just calls `EXIT`_ when it's done.


.. _os-ria-attributes:

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
       uses. The cc65 and llvm-mos C runtimes set it at startup whenever
       the program links ``errno``; assembly programs must set it before
       making OS calls that can fail. See `ERRNO_OPT Compiler Constants`_
       for option values.
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
     - Maximum input line length for the stdin line editor. 0–255,
       default 254. With 0, only a blank line can be entered.
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
     - Read-only Ctrl-C latch. Returns 1 if a Ctrl-C has been seen since
       the previous get on any terminal attached to the console manifold,
       including the telnet Interrupt Process command; returns 0 otherwise.
       Reading clears the latch. Same as RIA IRQ SIGINT.
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


Host Error Codes
================

A program never gets a host's own error codes. Each host maps them onto
the errno values in the left column, and the table shows which become
which, for a developer porting code from POSIX or Windows. ``ENOTDIR``,
for one, has no errno of its own here and arrives as ``ENOENT``. The
littlefs codes are shown without their ``LFS_ERR_`` prefix and the Windows
codes without their ``ERROR_`` prefix. Any other code becomes ``EIO``.

.. list-table::
   :header-rows: 1
   :widths: 14 22 20 20 24

   * -
     - FatFs
     - littlefs
     - POSIX
     - Windows
   * - ENOENT
     - FR_NO_FILE, FR_NO_PATH
     - NOENT
     - ENOENT, ENOTDIR
     - FILE_NOT_FOUND, PATH_NOT_FOUND, NO_MORE_FILES, DIRECTORY
   * - EACCES
     - FR_DENIED, FR_WRITE_PROTECTED
     -
     - EACCES, EPERM, EROFS, EISDIR, ENOTEMPTY
     - ACCESS_DENIED, SHARING_VIOLATION, LOCK_VIOLATION, WRITE_PROTECT, DIR_NOT_EMPTY
   * - EINVAL
     - FR_INVALID_NAME, FR_INVALID_PARAMETER
     - NOTDIR, ISDIR, NOTEMPTY, INVAL, NAMETOOLONG
     - EINVAL, ENAMETOOLONG
     - FILENAME_EXCED_RANGE, INVALID_NAME, INVALID_PARAMETER, NEGATIVE_SEEK
   * - ENODEV
     - FR_NOT_READY, FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM
     -
     - ENODEV, ENXIO, EXDEV
     - NOT_READY, BAD_UNIT, INVALID_DRIVE, NOT_SAME_DEVICE
   * - ENOSPC
     -
     - FBIG, NOSPC
     - ENOSPC, EFBIG
     - DISK_FULL, HANDLE_DISK_FULL
   * - EEXIST
     - FR_EXIST
     - EXIST
     - EEXIST
     - ALREADY_EXISTS, FILE_EXISTS
   * - EMFILE
     - FR_TOO_MANY_OPEN_FILES
     -
     - EMFILE, ENFILE
     - TOO_MANY_OPEN_FILES
   * - ENOMEM
     - FR_NOT_ENOUGH_CORE
     - NOMEM
     - ENOMEM
     - NOT_ENOUGH_MEMORY, OUTOFMEMORY
   * - EBUSY
     - FR_LOCKED
     -
     - EBUSY
     - BUSY, PIPE_BUSY
   * - EBADF
     - FR_INVALID_OBJECT
     - BADF
     - EBADF
     - INVALID_HANDLE
   * - EAGAIN
     - FR_TIMEOUT
     -
     - EAGAIN
     -
   * - EINTR
     -
     -
     -
     - OPERATION_ABORTED
   * - ESPIPE
     -
     -
     - ESPIPE
     -
   * - ERANGE
     -
     -
     - ERANGE
     -
   * - EIO
     - FR_DISK_ERR, FR_INT_ERR, FR_MKFS_ABORTED
     - IO, CORRUPT, NOATTR
     - EIO
     -

On POSIX, a read or write on a descriptor opened the wrong way fails with
``EBADF`` from the host and ``EACCES`` here.

The Pocket sets errno itself rather than mapping a host's codes, so it has
no column. The calls it lacks are listed under
:ref:`Compatibility <port-compatibility>`.


ERRNO_OPT Compiler Constants
============================

OS calls set ``RIA_ERRNO`` when an error occurs. Because cc65 and llvm-mos
each define their own errno constants, the errno option selects which set
of numeric values to use. In C, ``errno`` maps directly to ``RIA_ERRNO``,
and both C runtimes set the option at startup whenever the program links
``errno``. Assembly programs must set ``RIA_ATTR_ERRNO_OPT`` themselves
before any OS call that can fail.

.. list-table::
   :header-rows: 1
   :widths: 34 33 33

   * -
     - cc65
     - llvm-mos
   * - option
     - 1
     - 2
   * - ENOENT
     - 1
     - 2
   * - ENOMEM
     - 2
     - 12
   * - EACCES
     - 3
     - 13
   * - ENODEV
     - 4
     - 19
   * - EMFILE
     - 5
     - 24
   * - EBUSY
     - 6
     - 16
   * - EINVAL
     - 7
     - 22
   * - ENOSPC
     - 8
     - 28
   * - EEXIST
     - 9
     - 17
   * - EAGAIN
     - 10
     - 11
   * - EIO
     - 11
     - 5
   * - EINTR
     - 12
     - 4
   * - ENOSYS
     - 13
     - 38
   * - ESPIPE
     - 14
     - 29
   * - ERANGE
     - 15
     - 34
   * - EBADF
     - 16
     - 9
   * - ENOEXEC
     - 17
     - 8
   * - EDOM
     - 18
     - 33
   * - EILSEQ
     - 18
     - 84
   * - EUNKNOWN
     - 18
     - 85
