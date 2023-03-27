RP6502-API
##########

Rumbledethumps Picocomputer 6502 Application Programming Interface.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The :doc:`ria` runs a protected 32-bit kernel that you can call from the 6502. The kernel runs on a processor that is significnatly faster than a 6502. This is the only practical way to run modern networking and USB host stacks.

The RP6502 presents an opportunity to create a new type of operating system. A 6502 OS based on the C programming language with familiar POSIX-like operations.

2. Calling with fastcall
========================

If you only plan on writing C code, you can skip this section. The binary interface is based on fastcall from the `CC65 Internals <https://cc65.github.io/doc/cc65-intern.html>`_. However, the RP6502 fastcall does not use or require anything from CC65.

The CC65 fastcall is simply a pattern which I think works well for both C and assembly programmers. In short:

* Kernel calls have C declarations.
* Last argument is passed by register.
* Stack arguments are pushed left to right.
* Return value in register.

The register is known as AX for 16 bits and AXSREG for 32-bits. CC65 keeps SREG in zero page. A and X are the 6502 registers. Let's look at an example function. All kernel calls are specified as a C declaration like so:

.. c:function:: int doit(int arg0, int arg1);

The RIA has registers called RIA_A, RIA_X, and RIA_SREG. An int is 16 bits, so we set the RIA_A and RIA_X registers with arg1. I'll use "A" for the 6502 register and "RIA_A" for the RIA register in this explanation.

Next we push arg0 on the VSTACK. Writing data to the RIA_STACK register does this. It's a top-down stack, so push each value from left to right and maintain little endian-ness in memory.

To call, store the operation ID in RIA_OP. The operation begins immediately. You can keep doing 6502 things, like running a loading animation, by polling RIA_BUSY. Or, JSR RIA_RETURN to block.

The JSR RIA_RETURN method can unblock in less than 2 clock cycles and does an immediate mode load of A and X. Sequential operations will run fastest with this technique. Under the hood, you're jumping into a self-modifying program that runs on the RIA registers.

.. code-block:: asm

   BRA -2 or 0  ; RIA_BUSY
   LDA #00      ; RIA_A
   LDX #00      ; RIA_X
   RTS

Polling is simply snooping on the above program. The RIA_BUSY register is the -2 or 0 in the BRA above. The RIA datasheet said to use bit 7, which the 6502 can check quickly. Once clear, we read RIA_A and RIA_X with absolute instructions.

.. code-block:: asm

   wait:
   BIT RIA_BUSY
   BMI wait
   LDA #RIA_A
   LDX #RIA_X

RIA_A and RIA_X will both always be updated to assist with CC65's integer promotion requirements. RIA_SREG is only updated for 32-bit returns. RIA_ERRNO is only updated if there is an error.

Some operations return data on the stack. You must pull the entire stack before the next call. Or, the next function you call must understand the stack. For example, it is possible to chain read() and write() to copy a file without using any RAM or VRAM.

2.1. Short Stacking
-------------------

In the never ending pursuit of saving all the clocks, it is possible to save a few on the stack push if you don't need all the range. This only works on the stack argument that gets pushed first. For example:

.. code-block:: C

   long lseek64(unsigned long long offset, int fildes)

Here we are asked for a 64 bit value. Not coincidentally, it's in the right position for short stacking. If you only need 24 bits, push three bytes. The significant bytes will be implicit.

2.2. Shorter Integers
---------------------

Many operations can save a few clocks by ignoring REG_X. All integers are always available as 16 bits to assist with CC65 and integer promotion. However, many operations will ignore REG_X on the register parameter and limit their return to fit in REG_A. This will be documented below as "A regs".

2.3. Bulk Data
--------------

Functions that move bulk data will come in three flavors. These are any function with a "char \*" or "void \*" parameter. This pointer is passed by special means because the kernel can only change registers, not 6502 RAM.


2.2.1. Bulk VSTACK Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These only work if the count is 256 or less. Bulk data is passed on the VSTACK, which is 256 bytes. Let's look at some examples.

.. code-block:: C

   int open(const char *path, int oflag);

Send `oflag` in AX. Send the path on VSTACK by pushing the string starting with the last character. You may omit pushing the terminating zero but strings are limited to a length of 255.

.. code-block:: C

   int read_(char *buf, int count, int fildes)

Send `count` as a short stack and `fildes` in AX. The returned value in AX indicates how many values must be pulled from the stack.

The trailing underbar on read_() and write_() is there to leave room for <unistd.h> functions. Much of this API works like POSIX, but argument ordering is optimized for the RP6502 binary interface.

.. code-block:: C

   int write_(const void *buf, int count, int fildes)

Send `fildes` in AX. Push the data to VSTACK. Do not send `buf` or `count`. Pulling from VSTACK will begin with the first character.


2.2.2. Bulk VRAM Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These functions get their pointer from RIA_ADDR0 or RIA_ADDR1. Setting an ADDR register sets the pointer. It does not matter if the value later changes with STEP and RW, the pointer is what you set initially. This way you can set the ADDR, write some data, *not* re-set the ADDR, and call the OP.

.. code-block:: C

   int read0(vram_ptr addr0, int count, int fildes)

The kernel expects `addr0` to come from RIA_ADDR0, so that leaves `count` for the stack and `fildes` for AX. Using a short stack and knowing fildes fits in REG_A, we can do something like:

.. code-block:: C

   RIA_ADDR0 = addr0; // This is a 16-bit move in the C API
   RIA_STACK = count; // Short stacked. Just 8 bits.
   RIA_A = fildes;    // OK because read() ignores X.

Unlike the VSTACK, the kernel doesn't track a length for the VRAM portals. A set of rules around RIA_RW access could be made, but the use case where this is advantageous is too narrow to justify the complexity.

Calling read functions will update VRAM. This means you can load graphics assets right where you need it without the 6502 doing any work. This leaves the 6502 free to entertain the user with an animation while the entire 64K is transferred in less than a second.


3. Function Reference
=====================

Much of this API is based on CC65 and POSIX. In particular, filesystem access should feel extremely modern. However, many functions will have different argument orders or bitfield values than what you're used to. The reason for this becomes apparent when you start to work in assembly and fine tune short stacking and integer demotions. You might not notice if you only work in C because the SDK has wrapper functions with familiar prototypes. For example, fread() and read() are portable and familiar, but the read_() descibed below is optimized for a RIA fastcall.

Warning
-------
This is new. Expect lots of little changes. In particular, a renumbering of the IDs is planned and error numbers are definitely unstable. Mostly, the thing to watch out for is argument reordering. Operations tend to have an obvious best way to align with the binary interface so the big picture won't change much, just some details which will probably only need a recompile with the new headers.

Typedefs
--------

.. c:type:: int int16_t
.. c:type:: unsigned int uint16_t
.. c:type:: uint16_t vram_ptr


$00 zvstack
-----------
.. c:function:: void zvstack(void);

Abandon the vstack by resetting the pointer. Not needed for normal operation, but some performance tricks can be achieved. This is the only operation that doesn't require waiting for completion.

$01 open ($01 $02 $03)
----------------------

.. c:function:: int open(const char *path, int oflag)
.. c:function:: int open0(vram_ptr path, int oflag)
.. c:function:: int open1(vram_ptr path, int oflag)

   Create a connection between a file and a file descriptor.

   :param path: Pathname to a file.
   :param oflag: Bitfield of options.
   :returns: File descriptor. -1 on error.
   :a regs: return, oflag
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_NOT_READY, FR_NO_FILE, FR_NO_PATH, FR_INVALID_NAME, FR_DENIED, FR_EXIST, FR_INVALID_OBJECT, FR_WRITE_PROTECTED, FR_INVALID_DRIVE, FR_NOT_ENABLED, FR_NO_FILESYSTEM, FR_TIMEOUT, FR_LOCKED, FR_NOT_ENOUGH_CORE, FR_TOO_MANY_OPEN_FILES
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


$04 close
---------

.. c:function:: int close(int fildes)

   Release the file descriptor. File descriptor will rejoin the pool available for use by open().

   :param fildes: File descriptor from open().
   :returns: 0 on success. -1 on error.
   :a regs: return, fildes
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT, FR_TIMEOUT


$05 read ($05 $06 $07)
----------------------

.. c:function:: int read_(void *buf, int count, int fildes)
.. c:function:: int read0(vram_ptr buf, int count, int fildes)
.. c:function:: int read1(vram_ptr buf, int count, int fildes)

   Read `count` bytes from a file to a buffer.

   :param buf: Destination for the returned data.
   :param count: Quantity of bytes to read. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: Bytes read on success. -1 on error.
   :a regs: fildes
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT, FR_TIMEOUT

$08 write ($08 $09 $0A)
-----------------------

.. c:function:: int write_(const void *buf, int count, int fildes)
.. c:function:: int write0(vram_ptr buf, int count, int fildes)
.. c:function:: int write1(vram_ptr buf, int count, int fildes)

   Write `count` bytes from buffer to a file.

   :param buf: Location of the data.
   :param count: Quantity of bytes to write. 0x7FFF max.
   :param fildes: File descriptor from open().
   :a regs: fildes
   :errno:


$0B lseek
---------

.. c:function:: long lseek64(long long offset, char whence, int fildes)
.. c:function:: long lseek32(long offset, char whence, int fildes)
.. c:function:: long lseek16(int offset, char whence, int fildes)

   Move the read/write pointer. The 64 bit variant is only available on C compilers that support 64 bit. Only the 64 bit variant is actually implemented in the kernel becuase you can short stack the offset to any size you want. The shorter variants are to keep C from promoting integers.

   :param offset: How far you wish to seek.
   :param whence: From whence you wish to seek.
   :param fildes: File descriptor from open().
   :returns: Read/write position. -1 on error. If this value would be too large for a long, the returned value will be 0x7FFFFFFF.
   :a regs: fildes
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_INVALID_OBJECT, FR_TIMEOUT
   :whence:
      | SEEK_SET
      |    The start of the file (0) plus offset bytes.
      | SEEK_CUR
      |    The current location plus offset bytes.
      | SEEK_END
      |    The size of the file plus offset bytes.


$10 vreg
--------

.. c:function:: void vreg(unsigned int value, unsigned char key, int devid)

   Set a VREG on a PIX device. See the :doc:`vga` and :doc:`opl` documentation for what each register does. PIX is a broadcast protocol so this can not fail and there is nothing to return. However, you still need to wait on RIA_BUSY before the next op.

   :param value: VREGs are 16 bit so they can point to VRAM.
   :param key: PIX devices may have up to 256 registers.
   :param devid: PIX device ID. 0=OPL, 1=VGA, 2-6=Unassigned, 7=Reserved.
   :a regs: fildes


$FF exit
-----------
.. c:function:: void exit(int status);

   Halt the 6502 and return to the kernel command interface. This is the only operation that does not return. RESB will be pulled down before the next instruction can execute. Status is currently ignored but will be used in the future.

   :param status: 0 is good, 1-255 for error.
   :a regs: status