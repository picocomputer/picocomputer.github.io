RP6502-API
##########

Rumbledethumps Picocomputer 6502 Application Programming Interface.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The :doc:`ria` runs a protected 32-bit kernel that you can call from the 6502. The kernel runs on a processor that is significantly faster than a 6502. This is the only practical way to run modern networking and USB host stacks.

The RP6502 presents an opportunity to create a new type of operating system. A 6502 OS based on the C programming language with familiar POSIX-like operations.

2. Calling with fastcall
========================

The binary interface is based on fastcall from the `CC65 Internals <https://cc65.github.io/doc/cc65-intern.html>`_. However, the RP6502 fastcall does not use or require anything from CC65. I think this works well for both C and assembly programmers. Here's the call flow this section will expand on.

* Kernel calls have C declarations.
* Stack arguments are pushed left to right.
* Last argument is passed by register.
* Return value in register.

The register is known as AX for 16 bits and AXSREG for 32 bits. CC65 keeps SREG in zero page. A and X are the 6502 registers. Let's look at an example function. All kernel calls are specified as a C declaration like so:

.. c:function:: int doit(int arg0, int arg1);

The RIA has registers called RIA_A, RIA_X, and RIA_SREG. An int is 16 bits, so we set the RIA_A and RIA_X registers with arg1. I'll use "A" for the 6502 register and "RIA_A" for the RIA register in this explanation.

Next we push arg0 on the XSTACK. Writing data to the RIA_STACK register does this. It's a top-down stack, so push each argument from left to right and maintain little endian-ness in memory.

To call, store the operation ID in RIA_OP. The operation begins immediately. You can keep doing 6502 things, like running a loading animation, by polling RIA_BUSY. Or, JSR RIA_RETURN to block.

The JSR RIA_RETURN method can unblock in less than 3 clock cycles and does an immediate load of A and X. Sequential operations will run fastest with this technique. Under the hood, you're jumping into a self-modifying program that runs on the RIA registers.

.. code-block:: asm

   BRA {-2 or 0} ; RIA_BUSY
   LDX #$00      ; RIA_X
   LDA #$00      ; RIA_A
   RTS

Polling is simply snooping on the above program. The RIA_BUSY register is the -2 or 0 in the BRA above. The RIA datasheet specifies bit 7, which the 6502 can check quickly. Once clear, we read RIA_A and RIA_X with absolute instructions.

.. code-block:: asm

   wait:
   BIT RIA_BUSY
   BMI wait
   LDX RIA_X
   LDA RIA_A

RIA_A and RIA_X will both always be updated to assist with CC65's integer promotion requirements. RIA_SREG is only updated for 32-bit returns. RIA_ERRNO is only updated if there is an error.

Some operations return data on the stack. You must pull the entire stack before the next call. Or, the next function you call must understand the stack. For example, it is possible to chain read_() and write_() to copy a file without using any RAM or XRAM.

2.1. Short Stacking
-------------------

In the never ending pursuit of saving all the clocks, it is possible to save a few on the stack push if you don't need all the range. This only works on the stack argument that gets pushed first. For example:

.. code-block:: C

   long lseek64(long long offset, char whence, int fildes)

Here we are asked for a 64 bit value. Not coincidentally, it's in the right position for short stacking. If, for example, you only need 24 bits, push only three bytes. The significant bytes will be implicit.

2.2. Shorter Integers
---------------------

Many operations can save a few clocks by ignoring REG_X. All integers are always available as 16 bits to assist with CC65 and integer promotion. However, many operations will ignore REG_X on the register parameter and limit their return to fit in REG_A. This will be documented below as "A regs".

2.3. Bulk Data
--------------

Functions that move bulk data may come in two flavors. These are any function with a pointer parameter. This pointer is meaningless to the kernel because it can not change 6502 RAM. Instead, we use the XSTACK or XRAM for data buffers.

2.3.1. Bulk XSTACK Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These only work if the count is 256 or less. Bulk data is passed on the XSTACK, which is 256 bytes. A pointer appears in the C prototype to indicate the type and direction of this data. Let's look at some examples.

.. code-block:: C

   int open(const char *path, int oflag);

Send `oflag` in AX. Send the path on XSTACK by pushing the string starting with the last character. You may omit pushing the terminating zero, but strings are limited to a length of 255. Calling this from the C SDK will "just work" because there's an implementation that pushes the string for you.

.. code-block:: C

   int read_(void *buf, int count, int fildes)

Send `count` as a short stack and `fildes` in AX. The returned value in AX indicates how many values must be pulled from the stack. If you call this from the C SDK then it will copy XSTACK to buf[] for you.

.. code-block:: C

   int write_(const void *buf, int count, int fildes)

Send `fildes` in AX. Push the data to XSTACK. Do not send `count`, the kernel knows this from its internal stack pointer. If you call this from the C SDK then it will copy buf[] to XSTACK for you.

Note that read() and write() are part of the C SDK, not a kernel operation. CC65 requires them to have POSIX-ordered arguments. They simply call the underbar version after reordering the arguments.

2.3.2. Bulk XRAM Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^

These load and save XRAM directly. You can load game assets without going through 6502 RAM or capture a screenshot with ease.

.. code-block:: C

   int readv(xram_ptr buf, int count, int fildes)

The kernel expects `buf` and `count` on the XSTACK as integers with `filedes` in AX. The buffer is effectively &XRAM[buf] here. There's nothing special about these calls in regards to how the binary interface rules are applied.

3. Function Reference
=====================

Much of this API is based on CC65 and POSIX. In particular, filesystem access should feel extremely modern. However, many functions will have different argument orders or bitfield values than what you're used to. The reason for this becomes apparent when you start to work in assembly and fine tune short stacking and integer demotions. You might not notice if you only work in C because the standard library has wrapper functions and familiar prototypes. For example, fread() and read() are portable and familiar, but the read_() described below is optimized for a RIA fastcall.

Warning
-------
This is new. Expect lots of little changes. In particular, a renumbering of the IDs is planned and error numbers are definitely unstable. Mostly, the thing to watch out for is argument reordering. Operations tend to have an obvious best way to align with the binary interface so the big picture won't change much, just some details which will probably only need a recompile with the new headers.

Typedefs
--------

.. c:type:: int int16_t
.. c:type:: unsigned int uint16_t
.. c:type:: uint16_t xram_ptr


$00 zxstack
-----------
.. c:function:: void zxstack(void);

Abandon the xstack by resetting the pointer. Not needed for normal operation, but some performance tricks can be achieved. This is the only operation that doesn't require waiting for completion.

$01 open
--------

.. c:function:: int open(const char *path, int oflag)

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


$05 read ($05 $06)
------------------

.. c:function:: int read_(void *buf, unsigned count, int fildes)
.. c:function:: int readx(xram_ptr buf, unsigned count, int fildes)

   Read `count` bytes from a file to a buffer. Requests are limited to 0x7FFF bytes. Requesting more will return at most 0x7FFF bytes.

   :param buf: Destination for the returned data.
   :param count: Quantity of bytes to read. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes read is returned. On error, -1 is returned, and errno is set to indicate the error.
   :a regs: fildes
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT, FR_TIMEOUT


$08 write ($08 $09)
-------------------

.. c:function:: int write_(const void *buf, unsigned count, int fildes)
.. c:function:: int writex(xram_ptr buf, unsigned count, int fildes)

   Write `count` bytes from buffer to a file.

   :param buf: Location of the data.
   :param count: Quantity of bytes to write. 0x7FFF max.
   :param fildes: File descriptor from open().
   :returns: On success, number of bytes written is returned. On error, -1 is returned, and errno is set to indicate the error.
   :a regs: fildes
   :errno: FR_DISK_ERR, FR_INT_ERR, FR_DENIED, FR_INVALID_OBJECT, FR_TIMEOUT


$0B lseek
---------

.. c:function:: long lseek64(long long offset, char whence, int fildes)
.. c:function:: long lseek32(long offset, char whence, int fildes)
.. c:function:: long lseek16(int offset, char whence, int fildes)

   Move the read/write pointer. The 64 bit variant is only available on C compilers that support 64 bit. Only the 64 bit variant is actually implemented in the kernel because you can short stack the offset to any size you want. The shorter variants are to keep C from promoting integers.

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


$10 xreg
--------

.. c:function:: void xreg(unsigned value, unsigned reg, int devid)

   Set a register on a PIX device. See the :doc:`ria`:audio and :doc:`vga` documentation for what each register does. PIX is a broadcast protocol so this can not fail and there is nothing to return. However, you still need to wait on RIA_BUSY before the next op.

   :param value: Value to store. 0-65535
   :param reg: Register location. 0-4095
   :param devid: PIX device ID. 0-6
   :a regs: devid


$11 phi2
--------

.. c:function:: unsigned phi2(void)

   Retrieves the PHI2 setting from the RIA. Applications can use this to adapt to different speeds.

   :returns: The 6502 clock speed in kHz.

$12 codepage
------------

.. c:function:: unsigned codepage(void)

   Retrieves the CP setting from the RIA.

   :returns: The code page. One of: 437, 720, 737, 771, 775, 850, 852, 855, 857, 860, 861, 862, 863, 864, 865, 866, 869, 932, 936, 949, 950.

$13 rand
--------

.. c:function:: unsigned long rand32(void)
.. c:function:: unsigned rand16(void)

   Generates a random number utilizing entropy on the RIA. This is suitable for seeding a RNG or general use. The rand16() variant is only in the C SDK to avoid integer promotion (it ignores SREG).

   :returns: Chaos.


$FF exit
-----------
.. c:function:: void exit(int status)

   Halt the 6502 and return to the kernel command interface. This is the only operation that does not return. RESB will be pulled down before the next instruction can execute. Status is currently ignored but will be used in the future.

   :param status: 0 is good, 1-255 for error.
   :a regs: status
