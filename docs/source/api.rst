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

The binary interface is based on fastcall from the `CC65 Internals <https://cc65.github.io/doc/cc65-intern.html>`_. The last parameter is passed by register and everything else is pushed on the stack from left to right. The return value is also passed by register.

The register is known as AX for 16 bits and AXSREG for 32-bits. CC65 keeps SREG in zero page. A and X are the 6502 registers. Let's look at this example function.

.. c:function:: int doit(int arg0, int arg1);

The RIA has registers called RIA_A, RIA_X, and RIA_SREG. An int is 16 bits, so we set the RIA_A and RIA_X registers with arg1. I'll use "A" for the 6502 register and "RIA_A" for the RIA register in this explanation.

Next we push arg0 on the VSTACK. Writing data to the RIA_STACK register does this. It's a top-down stack, so push each value from left to right and maintain little endian-ness in memory.

Get the operation ID from the function reference and store that in RIA_OP. The operation is running now. You can keep doing 6502 things, like running a loading animation, by polling RIA_BUSY. Or, JSR RIA_RETURN to block.

If you poll, the return values will be in RIA_A, RIA_X, and RIA_SREG. If you JSR RIA_RETURN then A and X will be set upon return. If an error occurs, RIA_ERRNO will be updated.

You can now proceed to pull values off the stack. You must pull the entire stack before the next call.

2.1. Short Stacking
-------------------

In the never ending pursuit of saving all the clocks, it is possible to save a few on the stack push if you don't need all the range. This only works on the final int passed. For example:

.. c:function:: int doit2it(unsigned long long int arg0, int arg1);

Here we are required to pass a 64 bit value, perhaps for a file seek. If you're only working with 64K files, you only need 16 bits, so you only need to push the two low bytes.

2.2. Bulk Data
--------------

Many functions come in three flavors. These functions pass blocks of data. For example, reads and writes. They all have a "const char \*" parameter. This pointer is passed by special means. This is because the kernel can only change registers, not 6502 RAM.

2.2.1. $XX+0 Bulk VSTACK Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the bulk data is 256 bytes or less, you can pass it on the VSTACK. If you're passing a string, like a filename, you can omit the trailing zero. Strings are still limited to a length of 255 though. Don't pass a "pointer" on the stack, just push or pull the data.

The CC65 library uses these stack functions. It will break up large reads and writes into multiple calls. This makes C library functions like fread() work exactly as expected with no unwanted side effects. However, the C standard library has no concept of VRAM, so it's worth learning how to use the kernel API if you're doing anything with graphics and sound.

2.2.2. $XX+1 and $XX+2 Bulk VRAM Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These functions get their pointer from RIA_ADDR0 or RIA_ADDR1. Setting an ADDR register sets the pointer. It does not matter if the value later changes with STEP and RW, the pointer is what you set initially. This way you can set the ADDR, write some data, *not* re-set the ADDR, and call the OP.

Calling these functions updates VRAM. If you're loading graphics, you can load exactly what you need right where you need it without the 6502 doing any work.


3. Function Reference
=====================

These C declarations will "just work" in CC65 when using the SDK. The first declaration (without numeric suffix) is the main prototype for the binary interface as described above.

Calling kernel API functions from the C SDK will will do any copying work for you and block until the operation completes. The numbered VRAM variants will use their respective RW portal and do not preserve the VRAM registers.

While calling from C SDK is easy and usually fast enough, you can also use the API from C in the same way an assembly program would.

Typedefs
--------

.. c:type:: int uint16_t
.. c:type:: uint16_t vram_ptr


$00 zvstack
-----------
.. c:function:: void zvstack(void);

    Abandon the vstack by resetting the pointer. Not needed for normal operation, but some performance tricks can be achieved. This is the only operation that doesn't require waiting for completion.

$01 open ($01 $02 $03)
----------------------

.. c:function:: int open(const char *path, int oflag);
.. c:function:: int open0(vram_ptr addr0, int oflag);
.. c:function:: int open1(vram_ptr addr1, int oflag);

   Open a file.

   :param path: Filename
   :param oflag: Flags
   :retval -1: on error.
   :retval >=0: The file handle number.

$FF exit
-----------
.. c:function:: void exit(int status);

   Halt the 6502 and return to the kernel command interface. This is the only operations that does not return. RESB will be pulled down before the next instruction can execute.
