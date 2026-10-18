============================
API
============================

Application Programming Interface


Introduction
============

The API is how a 6502 program uses the host. The host is the modern side
of the machine behind the registers of the :doc:`ria`, such as the Pico
2 of an :doc:`pico` or the computer that runs the :doc:`emu`. A program
calls a function such as ``open()`` or ``time()``, and the C library
passes the call through the RIA registers to the host. The host does the
work and passes the result back, much like a remote procedure call. The
host runs outside the 6502 and uses none of its RAM, so all of RAM
remains available to the program.

The API comes with the compilers. It is part of the C libraries of cc65
and llvm-mos, so a program needs nothing else to use it. This is the
"Hello, world!" program of the :doc:`sdk` template:

.. code-block:: C

  #include <rp6502.h>
  #include <stdio.h>
  #include "xram.h"

  int main(void)
  {
      puts("Hello, world!");
  }

``puts()`` is the standard C function. In both compilers it ends in
`WRITE_XSTACK`_, an API call. The C library pushes the bytes to the
extended stack (XSTACK), a 512-byte stack in the RIA, and the host
writes them to the console. Most of the API is standard C in this way:
``fcntl.h``, ``unistd.h``, and ``stdio.h`` for the console and files,
and ``time.h`` for the clock. ``rp6502.h`` adds what standard C has no
call for: XRAM, the `RIA attributes <RIA Attributes_>`_, the FAT
attributes and dates of files, directories, drives, the line editor, and
the start of another ROM.

The API has no calls for the video, the sound, or the state of the
keyboard, mouse, and gamepads. A program maps each of those devices to
an XRAM address with ``xreg()``, as :ref:`XRAM Memory Map
<sdk-xram-memory-map>` in the :doc:`sdk` shows. Then the program reads
and writes the XRAM of the device with the XRAM functions of
``rp6502.h``. The :doc:`ria` and :doc:`vga` datasheets describe each
device.

Under the C functions is the Application Binary Interface (ABI), the
register-level form of each call. The C library implements the ABI, so
a C program does not use it directly. `Application Binary Interface`_,
at the end of this page, describes it for assembly programs and for a
port of another compiler.


Application Programming Interface
=================================

Most calls behave as their POSIX equivalents do. The calls for files and
directories follow FAT, the standard filesystem of USB drives and memory
cards, so ``f_stat()`` replaces ``stat()`` and returns the attributes and
dates of FAT.

Each section below has one or more C declarations, a description, and a
list of fields. Most declarations are both a C function and the ABI form
of an API call. A few API calls take their arguments in a different
order in the ABI than in C, so their sections have one declaration of
each form. A flag before the return type marks a declaration that has
only one of the two forms:

.. c:function:: ABI int an_api_call (int arg0, int arg1)
                lib int a_library_call (int arg1, int arg0)
   :no-index-entry:
   :no-contents-entry:

``ABI`` marks a declaration of the ABI form only. ``lib`` marks a
function of the C library only.

The fields are:

- ``Operation`` is the operation ID that a program writes to the RIA
  register ``RIA_OP`` to make the API call. A section with no
  ``Operation`` field describes functions that make no API call of their
  own.
- ``C proto`` is the header that declares the C function.
- ``a regs`` lists the arguments that a program may pass in ``RIA_A``
  alone, with ``RIA_X`` unset, and ``return`` when the return value fits
  in ``RIA_A``.
- ``errno`` lists every errno that the section can set, from the API call
  or from the C library. `Errno Translations`_ gives the number of each.

A C program does not use the ``Operation`` and ``a regs`` fields. They
are for the ABI.


.. _api-extended-memory:

Extended Memory
---------------

Extended RAM (XRAM) is 64 KB of memory outside the address space of the
6502. A program reads and writes it through the two :ref:`XRAM portals
<ria-xram-portals>` of the RIA. Each portal has its own address and step
registers, so the two portals can point at different places in XRAM. The
functions whose names start with ``xram0_`` use portal 0, and the
functions whose names start with ``xram1_`` use portal 1. Each function
changes the registers of its portal.

XRAM_READ
~~~~~~~~~

.. c:function:: lib void xram0_read (void* dest, unsigned src, unsigned count)
                lib void xram1_read (void* dest, unsigned src, unsigned count)

   ``xram0_read()`` and ``xram1_read()`` copy ``count`` bytes from XRAM
   to 6502 RAM, as ``memcpy()`` does.

   :C proto: rp6502.h
   :param dest: Destination in 6502 RAM.
   :param src: Source address in XRAM.
   :param count: Number of bytes to copy.


XRAM_WRITE
~~~~~~~~~~

.. c:function:: lib void xram0_write (unsigned dest, const void* src, unsigned count)
                lib void xram1_write (unsigned dest, const void* src, unsigned count)

   ``xram0_write()`` and ``xram1_write()`` copy ``count`` bytes from 6502
   RAM to XRAM, as ``memcpy()`` does.

   :C proto: rp6502.h
   :param dest: Destination address in XRAM.
   :param src: Source in 6502 RAM.
   :param count: Number of bytes to copy.


XRAM_SET
~~~~~~~~

.. c:function:: lib void xram0_set (unsigned dest, unsigned char val, unsigned count)
                lib void xram1_set (unsigned dest, unsigned char val, unsigned count)

   ``xram0_set()`` and ``xram1_set()`` fill ``count`` bytes of XRAM with
   ``val``, as ``memset()`` does.

   :C proto: rp6502.h
   :param dest: Address in XRAM to fill.
   :param val: Byte to write to every address.
   :param count: Number of bytes to fill.


XRAM_MOVE
~~~~~~~~~

.. c:function:: lib void xram_move (unsigned dest, unsigned src, unsigned count)

   ``xram_move()`` copies ``count`` bytes from one XRAM address to
   another, as ``memmove()`` does, so the result is correct when the two
   ranges overlap. It uses both portals, so the copy is fast and the data
   does not pass through 6502 RAM.

   :C proto: rp6502.h
   :param dest: Destination address in XRAM.
   :param src: Source address in XRAM.
   :param count: Number of bytes to copy.


XRAM_PEEK
~~~~~~~~~

.. c:function:: lib unsigned char xram0_peek8 (unsigned addr)
                lib unsigned char xram1_peek8 (unsigned addr)
                lib unsigned xram0_peek16 (unsigned addr)
                lib unsigned xram1_peek16 (unsigned addr)

   ``xram0_peek8()`` and ``xram1_peek8()`` read one byte from XRAM.
   ``xram0_peek16()`` and ``xram1_peek16()`` read a 16-bit value.

   :C proto: rp6502.h
   :param addr: Address in XRAM to read.
   :returns: The value read.


XRAM_POKE
~~~~~~~~~

.. c:function:: lib void xram0_poke8 (unsigned addr, unsigned char val)
                lib void xram1_poke8 (unsigned addr, unsigned char val)
                lib void xram0_poke16 (unsigned addr, unsigned val)
                lib void xram1_poke16 (unsigned addr, unsigned val)

   ``xram0_poke8()`` and ``xram1_poke8()`` write one byte to XRAM.
   ``xram0_poke16()`` and ``xram1_poke16()`` write a 16-bit value.

   :C proto: rp6502.h
   :param addr: Address in XRAM to write.
   :param val: Value to write.


.. _api-xreg:

XREG
~~~~

.. c:function:: int xreg (char device, char channel, unsigned char index, ...);

   ``xreg()`` configures the peripherals of the :ref:`Peripheral
   Information Exchange (PIX) <ria-pix>`. A program uses it to map
   devices, such as the keyboard and the video modes, to XRAM. Then the
   program uses each device through its XRAM, with the XRAM functions.
   The section of each device in the :doc:`ria` and :doc:`vga`
   datasheets gives its registers and its ``xreg()`` call.

   The manual writes the address of an extended register (XREG) as
   $device:channel:index. These are the first three arguments of
   ``xreg()``: ``device``, ``channel``, and ``index``. Each value after
   them goes to the next register in sequence, from ``index`` up. This
   call sets $1:0:01 to 3, $1:0:02 to 2, and $1:0:03 to $FF00:

   .. code-block:: C

      xreg(0x1, 0x0, 0x01, 3, 2, 0xFF00);

   When a program maps a device, the device can refuse a value, and the
   call fails. A refusal usually means that the value is not valid, but
   it can also mean that the machine does not have the feature.
   :ref:`Extended Registers <ria-xreg>` in the :doc:`ria` datasheet
   describes the errors.

   :Operation: RIA_OP_XREG 0x01
   :C proto: rp6502.h
   :param device: PIX device ID. 0:RIA, 1:VGA, 2-6:unassigned
   :param channel: PIX channel. 0-15
   :param index: Index of the register in the channel. 0-255
   :param ...: 16-bit values to set, from ``index`` up.
   :a regs: return
   :errno: EACCES, EINVAL, EIO


Process
-------

.. _api-argv:

ARGV
~~~~

.. c:function:: ABI int _argv (char *argv, int size)

   The C runtime runs this operation before ``main()`` to get ``argc`` and
   ``argv``. The argv data can use up to 512 bytes of RAM, so ``argc`` and
   ``argv`` are opt-in. To get them in ``main()``, define ``__argv_mem()`` in
   any source file of the program, such as ``main.c``:

   .. code-block:: c

      void *__argv_mem(size_t size) { return malloc(size); }

   The C runtime calls ``__argv_mem()`` with the size of the argv data.
   ``__argv_mem()`` returns storage of that size, in static memory or from
   ``malloc()``. A program can free the memory from ``malloc()`` after it
   reads the arguments. ``__argv_mem()`` can return NULL to reject an argv
   that is too large. With no ``__argv_mem()``, or when it returns NULL,
   ``main()`` gets an ``argc`` of 0.

   The operation returns the argv data on the XSTACK: a table of 16-bit offsets
   that ends with 0, then the zero-terminated strings. Each offset is the
   position of a string from the start of the data. The data is always valid.
   For example, ["ABC", "DEF"] is:

   .. code-block:: text

      06 00 0A 00 00 00 41 42 43 00 44 45 46 00

   :Operation: RIA_OP_ARGV 0x08
   :returns: Size of the argv data.


EXEC
~~~~

.. c:function:: ABI int _exec (const char *argv, int size)
                lib int ria_execl (const char *path, ...)
                lib int ria_execv (const char *path, char * const argv[])

   ``ria_execl()`` and ``ria_execv()`` start another ROM. ``path`` is the path
   of the ROM. The arguments of the new ROM are the strings after ``path`` in
   ``ria_execl()``, or the array ``argv`` in ``ria_execv()``, and each list
   ends with NULL. Unlike the POSIX ``execl()`` and ``execv()``, the arguments
   do not repeat the path, which saves RAM. In the new ROM, ``argv[0]`` is the
   absolute path of the ROM, with its drive, or ``:NAME`` for a ROM on the null
   drive, as :ref:`Installed ROMs <port-installed-roms>` describes. The
   arguments follow it, so the first argument of the call, ``argv[0]`` of
   ``ria_execv()``, becomes ``argv[1]`` in the new ROM.

   After a successful call, the RIA stops the 6502, loads the new ROM, and
   starts it. When the ROM does not load, the 6502 stays stopped, and the
   display shows the console, with its text and the error. An :doc:`pico`
   returns to its monitor. The :doc:`emu` exits, unless it runs with
   ``--debug``. The other machines stay stopped. The ROM does not load when the
   file is missing or is not a valid ROM, when its absolute path is longer than
   255 bytes, or when the argv data with that path does not fit in 512 bytes.

   ``ria_execl()`` and ``ria_execv()`` take at most 16 strings, the path and up
   to 15 arguments, in at most 512 bytes with the offset table. A call over
   either limit returns -1 with EINVAL.

   The EXEC data has the same layout as the ARGV data, with at least one
   string. Each string starts after the zero of the string before it, in the
   order of the offset table. The path in ``argv[0]`` has at most 255 bytes.
   The RIA checks the layout and the length of the path, but does not check
   that the path is a ROM that loads. When a check fails, the call fails with
   EINVAL.

   :Operation: RIA_OP_EXEC 0x09
   :C proto: rp6502.h
   :returns: Does not return on success. -1 on error.
   :errno: EINVAL


EXIT
~~~~

.. c:function:: void exit (int status)

   ``exit()`` ends the program and does not return. A return from
   ``main()`` also ends the program, with the return value as the exit
   code. The RIA stops the 6502 before it runs another instruction, and
   keeps the exit code for the next ROM, which reads it from
   ``RIA_ATTR_EXIT_CODE``.

   When another ROM is the launcher, that ROM runs again, as `Launcher`_
   describes. Otherwise, an :doc:`pico` returns to its monitor, and the
   :doc:`emu` exits with the same exit code, unless it runs with
   ``--debug``. The other machines stay stopped.

   :Operation: RIA_OP_EXIT 0xFF
   :C proto: stdlib.h
   :param status: The exit code. 0 is success, and any other value is an
      error.


Files
-----

.. _api-open:

OPEN
~~~~

.. c:function:: int open (const char *path, int oflag)

   ``open()`` opens a file or a device stream, and returns a file descriptor.

   ``oflag`` is the options below, ORed together. It must include O_RDONLY,
   O_WRONLY, or O_RDWR, or the call fails with EINVAL. O_RDONLY is 0x01, not 0
   as on most POSIX systems, so ``open(path, 0)`` fails.

   .. list-table::
      :widths: 10 18 72

      * - 0x01
        - O_RDONLY
        - Open for reading only.
      * - 0x02
        - O_WRONLY
        - Open for writing only.
      * - 0x03
        - O_RDWR
        - Open for reading and writing.
      * - 0x10
        - O_CREAT
        - Create the file when it does not exist.
      * - 0x20
        - O_TRUNC
        - With O_WRONLY or O_RDWR, set the length of the file to 0.
      * - 0x40
        - O_APPEND
        - Set the read/write position to the end of the file once, at the
          open, not before each write.
      * - 0x80
        - O_EXCL
        - With O_CREAT, fail when the file exists.

   :Operation: RIA_OP_OPEN 0x14
   :C proto: fcntl.h
   :param path: Path of the file or the device stream.
   :param oflag: Options, ORed together.
   :returns: File descriptor. -1 on error.
   :a regs: return, oflag
   :errno: EACCES, EBUSY, EEXIST, EINVAL, EIO, EMFILE, ENODEV, ENOENT, ENOMEM,
      ENOSPC


CLOSE
~~~~~

.. c:function:: int close (int fildes)

   ``close()`` closes a file descriptor.

   :Operation: RIA_OP_CLOSE 0x15
   :C proto: fcntl.h
   :param fildes: File descriptor from open().
   :returns: 0 on success. -1 on error.
   :a regs: return, fildes
   :errno: EBADF, EIO, ENOSPC


READ
~~~~

.. c:function:: lib int read (int fildes, void *buf, unsigned count)

   ``read()`` reads up to ``count`` bytes from a file into ``buf``. It is a C
   library function that calls `READ_XSTACK`_ as many times as it needs to.

   :C proto: unistd.h
   :param fildes: File descriptor from open().
   :param buf: Destination of the data.
   :param count: Number of bytes to read. 0x7FFF max.
   :returns: The number of bytes read. -1 on error.
   :a regs: fildes
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSYS


READ_XSTACK
~~~~~~~~~~~

.. c:function:: int read_xstack (void *buf, unsigned count, int fildes)

   ``read_xstack()`` reads up to ``count`` bytes from a file into ``buf``,
   through the XSTACK.

   :Operation: RIA_OP_READ_XSTACK 0x16
   :C proto: rp6502.h
   :param buf: Destination of the data.
   :param count: Number of bytes to read. 0x200 max.
   :param fildes: File descriptor from open().
   :returns: The number of bytes read. -1 on error.
   :a regs: fildes
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSYS


.. _api-read-xram:

READ_XRAM
~~~~~~~~~

.. c:function:: int read_xram (unsigned xaddr, unsigned count, int fildes)

   ``read_xram()`` reads up to ``count`` bytes from a file into XRAM at
   ``xaddr``.

   :Operation: RIA_OP_READ_XRAM 0x17
   :C proto: rp6502.h
   :param xaddr: Destination address in XRAM.
   :param count: Number of bytes to read. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: The number of bytes read. -1 on error.
   :a regs: fildes
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSYS


WRITE
~~~~~

.. c:function:: lib int write (int fildes, const void *buf, unsigned count)

   ``write()`` writes ``count`` bytes from ``buf`` to a file. It is a C library
   function that calls `WRITE_XSTACK`_ as many times as it needs to.

   :C proto: unistd.h
   :param fildes: File descriptor from open().
   :param buf: Source of the data.
   :param count: Number of bytes to write. 0x7FFF max.
   :returns: The number of bytes written. -1 on error.
   :a regs: fildes
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSPC, ENOSYS


WRITE_XSTACK
~~~~~~~~~~~~

.. c:function:: int write_xstack (const void *buf, unsigned count, int fildes)

   ``write_xstack()`` writes ``count`` bytes from ``buf`` to a file, through
   the XSTACK.

   :Operation: RIA_OP_WRITE_XSTACK 0x18
   :C proto: rp6502.h
   :param buf: Source of the data.
   :param count: Number of bytes to write. 0x200 max.
   :param fildes: File descriptor from open().
   :returns: The number of bytes written. -1 on error.
   :a regs: fildes
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSPC, ENOSYS


WRITE_XRAM
~~~~~~~~~~

.. c:function:: int write_xram (unsigned xaddr, unsigned count, int fildes)

   ``write_xram()`` writes ``count`` bytes from XRAM at ``xaddr`` to a file.

   :Operation: RIA_OP_WRITE_XRAM 0x19
   :C proto: rp6502.h
   :param xaddr: Source address in XRAM.
   :param count: Number of bytes to write. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: The number of bytes written. -1 on error.
   :a regs: fildes
   :errno: EACCES, EAGAIN, EBADF, EBUSY, EINTR, EINVAL, EIO, ENOSPC, ENOSYS


LSEEK
~~~~~

.. c:function:: long f_lseek (long offset, char whence, int fildes)
                lib off_t lseek (int fildes, off_t offset, int whence)

   ``lseek()`` and ``f_lseek()`` move the read/write position of a file.
   ``f_lseek(0, SEEK_CUR, fd)`` returns the current position.

   A seek past the end of a file that is open for writing extends the
   file with zeros. On a full drive, that seek fails with ENOSPC and does
   not change the file or the position. A seek past the end of a file
   that is open only for reading stops at the end.

   cc65 and llvm-mos give SEEK_SET, SEEK_CUR, and SEEK_END different
   values, so each compiler has its own operation ID:

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

   :Operation: See the table above.
   :C proto: f_lseek: rp6502.h, lseek: unistd.h
   :param offset: Distance in bytes from the position that ``whence``
      selects.
   :param whence: SEEK_SET, SEEK_CUR, or SEEK_END.
   :param fildes: File descriptor from open().
   :returns: The new read/write position. -1 on error. A position past
      0x7FFFFFFF does not fit in the returned long, so that seek fails
      with ERANGE and does not change the position.
   :a regs: fildes
   :errno: EBADF, EINVAL, EIO, ENOSPC, ENOSYS, ERANGE, ESPIPE


SYNCFS
~~~~~~

.. c:function:: int syncfs (int fildes)

   ``syncfs()`` flushes the pending writes of a file descriptor to storage.

   :Operation: RIA_OP_SYNCFS 0x1E
   :C proto: unistd.h
   :param fildes: File descriptor from open().
   :returns: 0 on success. -1 on error.
   :a regs: return, fildes
   :errno: EACCES, EBADF, EINVAL, EIO, ENOSPC, ENOSYS


ISATTY
~~~~~~

.. c:function:: lib int isatty (int fildes)

   ``isatty()`` returns 1 when a file descriptor is the console: stdin,
   stdout, stderr, ``CON:``, or ``TTY:``.

   :C proto: unistd.h
   :param fildes: File descriptor.
   :returns: 1 for the console. 0 for any other file descriptor.


Paths
-----

STAT
~~~~

.. c:function:: int f_stat (const char* path, f_stat_t* dirent)

   ``f_stat()`` returns the :ref:`directory entry <api-directory-entries>`
   of a file or a directory. For the root of a drive, such as ``/`` or
   ``MSC0:/``, it returns a directory named ``/``, with size 0 and zero
   dates.

   :Operation: RIA_OP_STAT 0x1F
   :C proto: rp6502.h
   :param path: Path of a file or a directory.
   :param dirent: The returned f_stat_t data.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


REMOVE
~~~~~~

.. c:function:: int remove (const char* name)

   ``remove()`` removes a file or an empty directory. It is the lightest
   of the three calls that remove an entry, because it does not test the
   type of the entry first. The removal fails with EACCES on a read-only
   file, and on a directory that is not empty.

   :Operation: RIA_OP_REMOVE 0x1B
   :C proto: stdio.h
   :param name: Path of the file or the directory to remove.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EBUSY, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


UNLINK
~~~~~~

.. c:function:: lib int unlink (const char* name)

   ``unlink()`` removes a file. It makes two API calls: `STAT`_ tests that
   the entry is not a directory, and `REMOVE`_ removes it. ``unlink()``
   fails with EACCES on a directory, and on a read-only file.

   :C proto: unistd.h
   :param name: Path of the file to remove.
   :returns: 0 on success. -1 on error.
   :errno: EACCES, EBUSY, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


RMDIR
~~~~~

.. c:function:: lib int rmdir (const char* name)

   ``rmdir()`` removes an empty directory. It makes two API calls: `STAT`_
   tests that the entry is a directory, and `REMOVE`_ removes it.
   ``rmdir()`` fails with EACCES on a file, and on a directory that is not
   empty.

   :C proto: unistd.h
   :param name: Path of the directory to remove.
   :returns: 0 on success. -1 on error.
   :errno: EACCES, EBUSY, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


RENAME
~~~~~~

.. c:function:: int rename (const char* oldname, const char* newname)

   ``rename()`` renames or moves a file or a directory on its drive. It
   does not replace a read-only file. A refused replacement fails with
   EACCES, and a move to another drive fails with ENODEV.

   :Operation: RIA_OP_RENAME 0x1C
   :C proto: stdio.h
   :param oldname: Path of the file or directory to rename.
   :param newname: New path.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EBUSY, EEXIST, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSPC,
      ENOSYS


CHMOD
~~~~~

.. c:function:: int f_chmod (const char* path, unsigned char attr, unsigned char mask)

   ``f_chmod()`` changes the attributes of a file or a directory, the bits
   of ``fattrib`` in its :ref:`directory entry <api-directory-entries>`. It
   changes only the attributes whose bits are set in ``mask``, and it does
   not change the Directory attribute.

   :Operation: RIA_OP_CHMOD 0x26
   :C proto: rp6502.h
   :param path: Path of a file or a directory.
   :param attr: New attributes.
   :param mask: Attributes to change.
   :returns: 0 on success. -1 on error.
   :a regs: return, mask
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


UTIME
~~~~~

.. c:function:: int f_utime (const char* path, unsigned fdate, unsigned ftime, unsigned crdate, unsigned crtime)

   ``f_utime()`` sets the dates and times of a file or a directory, in the
   format of its :ref:`directory entry <api-directory-entries>`. An
   ``fdate`` of 0 keeps the modification date and time, and a ``crdate`` of
   0 keeps the creation date and time.

   :Operation: RIA_OP_UTIME 0x27
   :C proto: rp6502.h
   :param path: Path of a file or a directory.
   :param fdate: Modification date.
   :param ftime: Modification time.
   :param crdate: Creation date.
   :param crtime: Creation time.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


MKDIR
~~~~~

.. c:function:: int f_mkdir (const char* name)

   ``f_mkdir()`` creates a directory.

   :Operation: RIA_OP_MKDIR 0x28
   :C proto: rp6502.h
   :param name: Path of the directory to make.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EEXIST, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSPC, ENOSYS


Directories
-----------

OPENDIR
~~~~~~~

.. c:function:: int f_opendir (const char* name)

   ``f_opendir()`` opens a directory and returns a directory descriptor for it.

   :Operation: RIA_OP_OPENDIR 0x20
   :C proto: rp6502.h
   :param name: Path of a directory.
   :returns: Directory descriptor. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, EMFILE, ENODEV, ENOENT, ENOMEM, ENOSYS


READDIR
~~~~~~~

.. c:function:: int f_readdir (f_stat_t* dirent, int dirdes)

   ``f_readdir()`` returns the next :ref:`directory entry
   <api-directory-entries>` of a directory. At the end of the
   directory, it succeeds with an empty ``fname``.

   :Operation: RIA_OP_READDIR 0x21
   :C proto: rp6502.h
   :param dirent: The returned f_stat_t data.
   :param dirdes: Directory descriptor from f_opendir().
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
   :errno: EACCES, EBADF, EINVAL, EIO, ENOENT, ENOMEM, ENOSYS


CLOSEDIR
~~~~~~~~

.. c:function:: int f_closedir (int dirdes)

   ``f_closedir()`` closes a directory descriptor.

   :Operation: RIA_OP_CLOSEDIR 0x22
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
   :errno: EBADF, EINVAL, ENOSYS


TELLDIR
~~~~~~~

.. c:function:: long f_telldir (int dirdes)

   ``f_telldir()`` returns the read position of a directory descriptor, as
   a location for ``f_seekdir()``.

   :Operation: RIA_OP_TELLDIR 0x23
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: Location. -1 on error.
   :a regs: dirdes
   :errno: EBADF, EINVAL, ENOSYS


SEEKDIR
~~~~~~~

.. c:function:: int f_seekdir (long loc, int dirdes)

   ``f_seekdir()`` restores the read position of a directory descriptor to
   a location from ``f_telldir()``.

   :Operation: RIA_OP_SEEKDIR 0x24
   :C proto: rp6502.h
   :param loc: Location from f_telldir().
   :param dirdes: Directory descriptor from f_opendir().
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
   :errno: EACCES, EBADF, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


REWINDDIR
~~~~~~~~~

.. c:function:: int f_rewinddir (int dirdes)

   ``f_rewinddir()`` sets the read position of a directory descriptor to
   the start of the directory.

   :Operation: RIA_OP_REWINDDIR 0x25
   :C proto: rp6502.h
   :param dirdes: Directory descriptor from f_opendir().
   :returns: 0 on success. -1 on error.
   :a regs: return, dirdes
   :errno: EACCES, EBADF, EINVAL, EIO, ENODEV, ENOENT, ENOSYS


Drives
------

CHDIR
~~~~~

.. c:function:: int chdir (const char* name)

   Change to a directory entry. A directory on another drive also makes
   that drive the current drive.

   :Operation: RIA_OP_CHDIR 0x29
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

   :Operation: RIA_OP_CHDRIVE 0x2A
   :C proto: rp6502.h
   :param name: Drive name to change to.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT


.. _api-getcwd:

GETCWD
~~~~~~

.. c:function:: int f_getcwd (char* name, int size)

   Get the current working directory.

   The result is absolute and always includes a device name, such as
   ``MSC0:/games``. Each folder name in it shows as it does in
   `READDIR`_. When the directory is longer than 255 bytes, the call
   fails with ENOMEM, because no call accepts a path that long.

   :Operation: RIA_OP_GETCWD 0x2B
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

   :Operation: RIA_OP_GETLABEL 0x2D
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

   :Operation: RIA_OP_SETLABEL 0x2C
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

   :Operation: RIA_OP_GETFREE 0x2E
   :C proto: rp6502.h
   :param name: Volume name.
   :param free: Storage for returned value.
   :param total: Storage for returned value.
   :returns: 0 on success. -1 on error.
   :a regs: return
   :errno: EACCES, EINVAL, EIO, ENODEV, ENOENT, ENOMEM, ENOSYS


Line Editor
-----------

.. _api-rln-lastkey:

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

   :Operation: RIA_OP_RLN_LASTKEY 0x30
   :C proto: rp6502.h
   :param key: Storage for the returned byte sequence.
   :param action: Out-parameter set non-zero if the key triggered an
      editing action.
   :returns: Length of key sequence. 0 if no key is available.
   :a regs: return
   :errno: EINVAL


.. _api-rln-peek:

RLN_PEEK
~~~~~~~~

.. c:function:: int ria_rln_peek (char* peek, unsigned char* pos)

   Returns the current contents of the line editor buffer and the
   cursor position within it. The buffer bytes are pushed to the XSTACK.
   It fails with EINVAL when no line read is in progress.

   :Operation: RIA_OP_RLN_PEEK 0x31
   :C proto: rp6502.h
   :param peek: Storage for the returned buffer contents. The C wrapper
      null-terminates the result, so it must hold up to
      ``RIA_ATTR_RLN_LENGTH`` + 1 bytes (256 max).
   :param pos: Out-parameter set to the cursor position within the
      buffer.
   :returns: Length of the buffer contents. -1 on error.
   :a regs: return
   :errno: EINVAL


.. _api-rln-poke:

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

   :Operation: RIA_OP_RLN_POKE 0x32
   :C proto: rp6502.h
   :param poke: Null-terminated string to feed into the editor.
   :returns: 0.
   :a regs: return
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

   :Operation: RIA_OP_TIME_GET 0x3F
   :C proto: time.h
   :returns: The current time, also stored at ``timep`` if it is not
      NULL. -1 on error.
   :a regs: return
   :errno: EINVAL, EIO, ERANGE


TIME_SET
~~~~~~~~

.. c:function:: int time_set (long long time)

   Sets the clock to seconds since the Unix epoch. Supported only on the
   :doc:`pico`.

   :Operation: RIA_OP_TIME_SET 0x3E
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

   :Operation: RIA_OP_GMTIME 0x3A
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

   :Operation: RIA_OP_LOCALTIME 0x3B
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

   :Operation: RIA_OP_MKTIME 0x3C
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
   oversized result with `DROP`_.

   ``%a %A %b %B %c %p %r %x %X`` follow the configured locale and
   ``%z %Z`` the configured time zone. Set both with ``SET LOC`` and
   ``SET TZ`` on an :doc:`pico`. The format and result are code page
   text. ``%E`` and ``%O`` modifiers are ignored.

   :Operation: RIA_OP_STRFTIME 0x3D
   :C proto: time.h
   :returns: Length of the string in ``buf``, not counting the
      terminator. 0 on error, or if the result is empty or does not fit.
   :a regs: return
   :errno: EINVAL


Attributes
----------

ATTR_GET
~~~~~~~~

.. c:function:: long ria_attr_get (unsigned char id)

   Returns the current value of a RIA attribute. See `RIA Attributes`_
   for attribute IDs and descriptions.

   :Operation: RIA_OP_ATTR_GET 0x0A
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

   :Operation: RIA_OP_ATTR_SET 0x0B
   :C proto: rp6502.h
   :param id: Attribute ID. One of the ``RIA_ATTR_*`` constants.
   :param val: New value.
   :a regs: id
   :returns: 0 on success
   :errno: EINVAL


.. _api-ria-attributes:

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
       making API calls that can fail. See `Errno Translations`_
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


Errno Translations
==================

API calls set ``RIA_ERRNO`` when an error occurs. Because cc65 and llvm-mos
each define their own errno constants, the errno option selects which set
of numeric values to use. In C, ``errno`` maps directly to ``RIA_ERRNO``,
and both C runtimes set the option at startup whenever the program links
``errno``. Assembly programs must set ``RIA_ATTR_ERRNO_OPT`` themselves
before any API call that can fail.

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


Launcher
========

A ROM is the whole state of the machine as it comes out of reset, like a
cartridge, so running one normally replaces whatever ran before. A ROM
also takes arguments through `ARGV`_ and returns an exit status through
`EXIT`_, like a program. The launcher puts the two together: a ROM that
starts other ROMs with `EXEC`_ gets control back when each one stops.

A ROM registers as the launcher by setting ``RIA_ATTR_LAUNCHER`` to 1
with :c:func:`ria_attr_set`. From then on, when a ROM it started stops,
whether it calls exit(), returns from main() or fails, the launcher ROM
runs again from the start, and ``RIA_ATTR_EXIT_CODE`` holds the exit
status of the ROM that stopped. The launcher starts fresh each time, so
it keeps anything it needs between runs in a file. When the launcher
itself stops, the registration clears.

For example, a shell ROM can run a compiler, a linker and a packager,
each a ROM of its own, as three steps. It starts each one with EXEC and
its arguments, reads the exit code when it runs again, and ends the chain
when a step fails. The same mechanism serves a menu for an anthology of
games, which comes back when a game exits. That works best when every
game in it has a way to exit, such as an Exit item in its menu.


Application Binary Interface
============================

.. seealso::

   :ref:`RIA registers <ria-registers>` — the hardware register map
   referenced throughout this section.

A compiler turns each call of a C function into machine code in a
standard way: where each argument goes, in what order, and where the
result comes back. That byte-level convention is an Application Binary
Interface (ABI). This section describes the ABI of the API calls: how a
6502 program passes the arguments to the RIA, starts the call, and reads
the result back from the host.

The ABI is based on fastcall from the `cc65 internals
<https://cc65.github.io/doc/cc65-intern.html>`__. The compiler's library
follows it for every C program, so a C programmer can skip this section.
An assembly programmer, or anyone bringing another compiler to the
Picocomputer, needs all of it.

At its core, the ABI is four rules:

* Stack arguments are pushed left to right.
* Last argument passed by register A, AX, or AXSREG.
* Return value in register AX or AXSREG.
* May return data on the stack.

A and X are the 6502 registers. The pseudo-register AX combines them
into 16 bits, and AXSREG extends that to 32 bits with the 16 SREG bits.
Every API call is specified as a C declaration, like so:

.. c:function:: int doit(int arg0, int arg1);
   :no-index-entry:
   :no-contents-entry:

The RIA has registers called ``RIA_A``, ``RIA_X``, and ``RIA_SREG``. An
int is 16 bits, so arg1 goes into the ``RIA_A`` and ``RIA_X``
registers. Throughout this explanation, "A" means the 6502 register and
"RIA_A" means the RIA register.

arg0 goes on the extended stack (XSTACK), 512 bytes of memory in the
RIA. Reading ``RIA_XSTACK`` pops bytes; writing pushes them. It's a
top-down stack, so push the arguments left to right, and push each value
high byte first so that it lies in memory low byte first.

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
is the -2 or 0 in the BRA above. Per the :ref:`RIA registers
<ria-registers>`, bit 7 signals busy, which the 6502 can test quickly
with the BIT operator to set flag N. Once it clears, read ``RIA_A`` and
``RIA_X`` with absolute instructions.

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
entire stack before the next call, or use `ria_drop() <DROP_>`_
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
--------------

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
value within ``RIA_A``. Those are listed under ``a regs`` in each
operation of the `Application Programming Interface`_.

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
are capped at 255 bytes. In C, the library pushes the string for you.

.. code-block:: C

   int read_xstack(void *buf, unsigned count, int fildes)

Send ``count`` as a short stack and ``fildes`` in ``RIA_A``; per the
`READ_XSTACK`_ docs, ``RIA_X`` doesn't need to be set. The value returned
in AX is the number of bytes to pull from the stack. In C, the library
copies the XSTACK into buf[] for you.

.. code-block:: C

   int write_xstack(const void *buf, unsigned count, int fildes)

Send ``fildes`` in ``RIA_A``; per the `WRITE_XSTACK`_ docs, ``RIA_X``
doesn't need to be set. Push the buf data onto the XSTACK. Don't send
``count``; the OS takes it from the XSTACK pointer. In C, the library
copies count bytes of buf[] onto the XSTACK for you.

Note that read() and write() are part of the C library, not API calls. C
requires them to handle counts larger than the XSTACK can return, so the
implementation makes as many API calls as it takes.

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
