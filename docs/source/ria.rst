====================
RIA
====================

RP6502 Interface Adapter


Introduction
============

The RP6502 Interface Adapter (RIA) is the boundary between a WDC W65C02S
microprocessor and the host. The host is the modern computer on the other
side, such as the Pico 2 of an :doc:`pico` or the computer that runs the
:doc:`emu`. Through the RIA, a 6502 program uses the services of the
operating system of the host, such as Windows or Linux. The RP6502-PICO
runs an operating system written for the Pico 2, so that the machine
needs only minimal hardware.

The RIA provides the operating system calls of the :doc:`api`, such as
files, the console, and the real-time clock. It also provides keyboard,
mouse, tablet, and gamepad input, and two sound generators: a
programmable sound generator (:ref:`PSG <ria-psg>`) and a Yamaha FM sound
generator (:ref:`OPL2 <ria-opl2>`). This page describes these devices,
and the registers that a program uses to reach them.


Reset
=====

The RIA controls RESB, the reset line of the 6502 and the 65C22 VIA. Think
of reset as two states rather than a pulse on RESB. While RESB is low, the
6502 and the VIA are stopped. To start a program, the RIA brings RESB
high, and the 6502 begins at its reset vector at $FFFC. When the program
exits or the user stops it, the RIA brings RESB low again.


PHI2
====

PHI2 is the clock signal of the 6502, and the RIA generates it. A program
starts with PHI2 at 8 MHz, unless the user has set the machine to a lower
frequency. The program can change the frequency with
:ref:`RIA_ATTR_PHI2_KHZ <api-ria-attributes>`, to anything from 100 kHz
to 8 MHz, and the change lasts until the program stops. The frequency is
set in steps of 1 kHz, and every machine except the RP6502-PICO generates
it exactly. The RP6502-PICO rounds up to the next frequency that it can
generate, so a program that needs to know the frequency reads the
attribute back.


.. _ria-registers:

Registers
=========

The RIA is 32 registers at $FFE0-$FFFF in the address space of the 6502.
Every :ref:`API call <api-call>` goes through them. The last six bytes
hold the vectors of the 6502 and work as RAM.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $FFE0
     - READY
     - The status of the console `UART`_.

       * bit 7 - TX is ready to transmit a byte.
       * bit 6 - RX holds a received byte.

   * - $FFE1
     - TX
     - Writing a byte transmits it to the console.
   * - $FFE2
     - RX
     - Reading returns a byte received from the console.
   * - $FFE3
     - VSYNC
     - Increments every 1/60 second while the :doc:`vga` is connected.
   * - $FFE4
     - RW0
     - Reading or writing accesses the XRAM byte at ADDR0, as
       `XRAM Portals`_ describes.
   * - $FFE5
     - STEP0
     - Signed byte added to ADDR0 after every access to RW0.
   * - | $FFE6 -
       | $FFE7
     - ADDR0
     - The XRAM address that RW0 accesses.
   * - $FFE8
     - RW1
     - Reading or writing accesses the XRAM byte at ADDR1, as
       `XRAM Portals`_ describes.
   * - $FFE9
     - STEP1
     - Signed byte added to ADDR1 after every access to RW1.
   * - | $FFEA -
       | $FFEB
     - ADDR1
     - The XRAM address that RW1 accesses.
   * - $FFEC
     - XSTACK
     - Writing pushes a byte on the `Extended Stack (XSTACK)`_, and
       reading pulls one.
   * - | $FFED -
       | $FFEE
     - ERRNO
     - The errno of the last failed API call, as :ref:`Errno Translations
       <api-errno>` describes.
   * - $FFEF
     - OP
     - Writing an operation ID starts an :ref:`API call <api-call>`.
   * - $FFF0
     - IRQ
     - Interrupt enable and status, as :ref:`IRQ <api-irq>` describes.

       * bit 7 - VSYNC
       * bit 6 - SIGINT

   * - $FFF1
     - SPIN
     - $80, the BRA opcode. JSR SPIN returns when the :ref:`API call
       <api-call>` finishes, with the return value in A and X.
   * - $FFF2
     - BUSY
     - Bit 7 is 1 while an :ref:`API call <api-call>` runs.
   * - $FFF3
     - LDA
     - $A9, the LDA immediate opcode, part of SPIN.
   * - $FFF4
     - A
     - The A register of an :ref:`API call <api-call>`.
   * - $FFF5
     - LDX
     - $A2, the LDX immediate opcode, part of SPIN.
   * - $FFF6
     - X
     - The X register of an :ref:`API call <api-call>`.
   * - $FFF7
     - RTS
     - $60, the RTS opcode, part of SPIN.
   * - | $FFF8 -
       | $FFF9
     - SREG
     - The SREG register of an :ref:`API call <api-call>`.
   * - | $FFFA -
       | $FFFB
     - NMIB
     - The NMI vector of the 6502.
   * - | $FFFC -
       | $FFFD
     - RESB
     - The reset vector of the 6502.
   * - | $FFFE -
       | $FFFF
     - BRK/IRQB
     - The IRQ and BRK vector of the 6502.

.. _ria-volatile:

cc65 Does Not Support ``volatile``
----------------------------------

``volatile`` has no effect on the cc65 optimizer, so wrap C code that
accesses RIA or VIA registers directly in an optimize pragma:

.. code-block:: C

  #pragma optimize (push, off)
  static void timer_start(void)
  {
      VIA.acr = 0x40;
  }
  #pragma optimize (pop)

.. _ria-uart:

UART
----

READY, TX, and RX connect a program to the console the way a serial port
does. They exist for one narrow use: porting machine code that drives a
serial port, by patching the code in place. A test of READY is one BIT
instruction and uses no registers, so it fits in place of the serial code
of almost any existing program. A new program has no existing machine
code to fit, so it should use the stdio functions of the :doc:`api`,
which do not go through these registers.

BIT copies bit 7 of READY to N and bit 6 to V, so BPL waits for TX and
BVC waits for RX:

.. code-block:: ca65

  tx: BIT RIA_READY
      BPL tx
      STA RIA_TX

  rx: BIT RIA_READY
      BVC rx
      LDA RIA_RX

A program must not use these registers while a stdio function of the
:doc:`api` runs.

.. _ria-xram-portals:

XRAM Portals
------------

`Extended RAM (XRAM)`_ is outside the address space of the 6502, so a
program reaches it through the two portals of the RIA. A portal is three
registers. ADDR holds an XRAM address, and RW is the byte at that
address: a load from RW reads it, and a store to RW writes it. After each
load or store, the RIA adds STEP to ADDR. STEP is signed, so a portal
steps forward or backward through XRAM. Portal 0 is ADDR0, RW0, and
STEP0, and portal 1 is ADDR1, RW1, and STEP1.

This example points portal 0 at $1000 and writes two bytes, $12 to $1000
and $34 to $1001, with the register names from ``rp6502.inc``:

.. tab:: ca65

   .. code-block:: ca65

      lda #<$1000
      sta RIA_ADDR0
      lda #>$1000
      sta RIA_ADDR0+1
      lda #1
      sta RIA_STEP0
      lda #$12
      sta RIA_RW0 ; $1000
      lda #$34
      sta RIA_RW0 ; $1001

.. tab:: llvm-mc

   .. code-block:: ca65
      :force:

      lda #<$1000
      sta RIA_ADDR0
      lda #>$1000
      sta RIA_ADDR0+1
      lda #1
      sta RIA_STEP0
      lda #$12
      sta RIA_RW0 ; $1000
      lda #$34
      sta RIA_RW0 ; $1001

In C, the ``xram0_`` and ``xram1_`` functions of :ref:`Extended Memory
<api-extended-memory>` read and write XRAM through portal 0 and portal 1.
This is the same write in C, with :c:func:`xram0_poke16` storing the
value low byte first:

.. code-block:: C

  xram0_poke16(0x1000, 0x3412);

The portals are safe to use in interrupt handlers. When a handler uses a
portal that the main program also uses, it only has to save the ADDR and
STEP of that portal, and restore them when it is done.

Extended Stack (XSTACK)
-----------------------

The XSTACK is a 512-byte stack in the RIA that carries the arguments and
the returned data of API calls. The C library handles it for a C program.
An assembly program pushes and pulls bytes on it, as :ref:`Making an API
Call <api-call>` shows. Reading the XSTACK when it is empty returns zeros.


.. _ria-pix:

Peripheral Information Exchange (PIX)
=====================================

Keyboards, mice and gamepads are connected over USB and Bluetooth, and
the video and sound are made by modern hardware. A 6502 cannot use any of
these directly, so each one is given a simple interface of bytes in
extended RAM (XRAM). The RIA writes keyboard, mouse and gamepad input into
XRAM for a program to read, and the sound generators and the video system
read settings and data that a program writes into XRAM. This arrangement
is called Peripheral Information Exchange (PIX). A program maps each
device to an XRAM address by setting an extended register (XREG). Until
then, the device is off and has no XRAM address.

Extended RAM (XRAM)
-------------------

XRAM is 64 KB of memory outside the 6502's address space. A program reads
and writes it through the `XRAM Portals`_, and every device uses the same
64 KB.

.. _ria-xreg:

Extended Registers (XREG)
-------------------------

An extended register (XREG) is a 16-bit register of a PIX device.
Device 0 is the RIA, device 1 is the :doc:`vga`, and devices 2-6 are
open for expansion. Each PIX device has 16 channels of 256 registers. A
program sets XREGs to map devices, such as the keyboard, to XRAM. XREGs
are not in the address space of the 6502, so a load or a store cannot
access one. A program sets them with the :ref:`xreg() <api-xreg>` API
call, and cannot read them back.

This call maps the keyboard to XRAM $1000:

.. code-block:: C

  xreg(0x0, 0x0, 0x00, 0x1000);

The first three arguments are the PIX device, the channel, and the index
of the register in the channel. Together they are the address of the
XREG, written $device:channel:index, so the keyboard XREG is $0:0:00.
The last argument is the value. After the call, the RIA keeps the state
of the keyboard in the 32 bytes at $1000-$101F.

An XREG is a key register or an argument register. When a program sets
a key register, the device applies the value, such as the XRAM address
of the keyboard, before ``xreg()`` returns. ``xreg()`` returns 0 when
the device accepts the value, or -1 with ``errno`` set when the device
refuses it. An argument register holds a value for a key register, and
has no effect until the program sets that key register.

Every XREG of the RIA is a key register. The VGA has two key registers,
as :ref:`Key Registers <vga-key-registers>` in the :doc:`vga` datasheet
describes. CANVAS selects the size of the canvas, the grid of pixels
that the VGA draws. MODE programs a video mode from the argument
registers above it. One ``xreg()`` call can set MODE and its arguments
together, because the first value goes to the register at the index, and
each next value to the next register up:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 3, 2, 0xFF00);

This call sets MODE ($1:0:01) to 3, the :ref:`bitmap mode <vga-mode-3>`.
It sets $1:0:02 to 2, which selects 4-bit color, and $1:0:03 to $FF00,
the XRAM address of the configuration structure of the mode. Mode 3
takes 2 and $FF00 as its arguments, and then the VGA clears the argument
registers. A program can also set the arguments with one call and MODE
with a later call. The argument registers keep their values until a
write to CANVAS or MODE clears them, or until the ROM stops.

One ``xreg()`` call logically sets all of its registers at once. The RIA
receives every value of the call before it sets a register. Then it sets
the key registers in order, from the lowest index, and sets the
argument registers of each key register before that key register. So
one call to the VGA can select the canvas and program the first video
mode, which is all the video setup that many programs need:

.. code-block:: C

  xreg(0x1, 0x0, 0x00, 1, 3, 2, 0xFF00);

This call selects the 320x240 canvas, and then programs mode 3 as the
call above does.

When a key register refuses its value, the call ends and fails. The
registers that the RIA set before the failure keep their new values, and
the RIA does not set the others. A device refuses a value that it does
not support, so a program can set a key register to test for a feature.
A failed call sets ``errno`` to one of these:

- EINVAL: a key register refused its value, or the arguments of the call
  are not valid.
- EIO: on an :doc:`pico`, the VGA did not answer a write to CANVAS or
  MODE, as when no VGA is connected.
- EACCES: the call wrote to :ref:`channel $F <vga-control-channel>` of
  the VGA, which the RIA manages.

A device 2-6 cannot refuse a value, so a valid call to one always
succeeds. On an :doc:`pico`, hardware that you build for the
:ref:`PIX bus <pico-pix>` is a device 2-6, and takes its settings
through ``xreg()``.

An assembly program uses the ``xreg`` macro of ``rp6502.inc``, which
takes the same arguments as ``xreg()``:

.. code-block:: ca65

  xreg $1, $0, $01, 3, 2, $FF00

The macro loads each argument as an immediate operand, so an argument
must be a constant or a symbol. The macro pushes the device, the
channel, and the index, one byte each, and then each value, high byte
first. ``RIA_A`` and ``RIA_X`` carry no argument.

The XREGs of the RIA, device 0, are in the table below. Each one maps a
device to XRAM at the address written to it. Writing ``$FFFF`` turns the
device off and always succeeds. Any other address that is invalid for
the device also turns it off, and the call fails with ``EINVAL``. A write
to a register that the table does not list fails with ``EINVAL``.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:0:00
     - KEYBOARD
     - Maps the key bits of the `Keyboard`_.
   * - $0:0:01
     - MOUSE
     - Maps the state of the `Mouse`_.
   * - $0:0:02
     - GAMEPADS
     - Maps the state of the `Gamepads`_.
   * - $0:0:03
     - TABLET
     - Maps the state of the `Tablet`_.
   * - $0:1:00
     - PSG
     - Maps the `Programmable Sound Generator`_.
   * - $0:1:01
     - OPL
     - Maps the `Yamaha OPL2 FM Sound Generator`_.


.. _ria-keyboard:

Keyboard
========

The RIA can provide applications direct access to keyboard data, which is
what you want when you need key-up and key-down events or the modifier
keys. If you don't need that, the UART or stdin works just as well.

Enable and disable direct keyboard access by mapping it to an address
in XRAM.

.. code-block:: C

  xreg(0x0, 0x0, 0x00, xaddr);  // enable
  xreg(0x0, 0x0, 0x00, 0xFFFF); // disable
  xreg_ria_keyboard(xaddr);     // macro shortcut

The RIA continuously updates XRAM with a bit array of USB HID keyboard
keycodes, which are not PS/2 scancodes. Each keycode is one bit in the
array: bit N is 1 while the key with HID keycode N is pressed. The first
four keycodes are special:

- 0 - No key pressed
- 1 - Num Lock on
- 2 - Caps Lock on
- 3 - Scroll Lock on

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define KEYBOARD_NO_KEY 0
      #define KEYBOARD_NUM_LOCK 1
      #define KEYBOARD_CAPS_LOCK 2
      #define KEYBOARD_SCROLL_LOCK 3

      #define KEYBOARD_PRESSED(keys, code) ((keys)[(code) >> 3] & (1 << ((code) & 7)))

      #define xreg_ria_keyboard(...) xreg(0x0, 0x0, 0x00, __VA_ARGS__)

      typedef struct
      {
          uint8_t keys[32];
      } keyboard_t; /* layout */

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      KEYBOARD_NO_KEY      = 0
      KEYBOARD_NUM_LOCK    = 1
      KEYBOARD_CAPS_LOCK   = 2
      KEYBOARD_SCROLL_LOCK = 3

      .macro xreg_ria_keyboard addr
          xreg $0, $0, $00, addr
      .endmacro

      .struct keyboard_t
          keys .res 32
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      KEYBOARD_NO_KEY      = 0
      KEYBOARD_NUM_LOCK    = 1
      KEYBOARD_CAPS_LOCK   = 2
      KEYBOARD_SCROLL_LOCK = 3

      .macro xreg_ria_keyboard addr
          xreg $0, $0, $00, \addr
      .endm

      KEYBOARD_KEYS = 0
      KEYBOARD_SIZE = 32

The keycodes are listed by name below, from the Keyboard/Keypad page of
the USB HID Usage Tables. Copy the ones you need or the whole block into
a file of its own, ``hidkeys.h`` or ``hidkeys.inc``.

.. tab:: C

   .. code-block:: C
      :caption: hidkeys.h

      #ifndef HIDKEYS_H
      #define HIDKEYS_H

      #define HID_KEY_A 0x04
      #define HID_KEY_B 0x05
      #define HID_KEY_C 0x06
      #define HID_KEY_D 0x07
      #define HID_KEY_E 0x08
      #define HID_KEY_F 0x09
      #define HID_KEY_G 0x0A
      #define HID_KEY_H 0x0B
      #define HID_KEY_I 0x0C
      #define HID_KEY_J 0x0D
      #define HID_KEY_K 0x0E
      #define HID_KEY_L 0x0F
      #define HID_KEY_M 0x10
      #define HID_KEY_N 0x11
      #define HID_KEY_O 0x12
      #define HID_KEY_P 0x13
      #define HID_KEY_Q 0x14
      #define HID_KEY_R 0x15
      #define HID_KEY_S 0x16
      #define HID_KEY_T 0x17
      #define HID_KEY_U 0x18
      #define HID_KEY_V 0x19
      #define HID_KEY_W 0x1A
      #define HID_KEY_X 0x1B
      #define HID_KEY_Y 0x1C
      #define HID_KEY_Z 0x1D

      #define HID_KEY_1 0x1E
      #define HID_KEY_2 0x1F
      #define HID_KEY_3 0x20
      #define HID_KEY_4 0x21
      #define HID_KEY_5 0x22
      #define HID_KEY_6 0x23
      #define HID_KEY_7 0x24
      #define HID_KEY_8 0x25
      #define HID_KEY_9 0x26
      #define HID_KEY_0 0x27

      #define HID_KEY_ENTER 0x28
      #define HID_KEY_ESCAPE 0x29
      #define HID_KEY_BACKSPACE 0x2A
      #define HID_KEY_TAB 0x2B
      #define HID_KEY_SPACE 0x2C
      #define HID_KEY_MINUS 0x2D
      #define HID_KEY_EQUAL 0x2E
      #define HID_KEY_BRACKET_LEFT 0x2F
      #define HID_KEY_BRACKET_RIGHT 0x30
      #define HID_KEY_BACKSLASH 0x31
      #define HID_KEY_EUROPE_1 0x32
      #define HID_KEY_SEMICOLON 0x33
      #define HID_KEY_APOSTROPHE 0x34
      #define HID_KEY_GRAVE 0x35
      #define HID_KEY_COMMA 0x36
      #define HID_KEY_PERIOD 0x37
      #define HID_KEY_SLASH 0x38

      #define HID_KEY_CAPS_LOCK 0x39
      #define HID_KEY_F1 0x3A
      #define HID_KEY_F2 0x3B
      #define HID_KEY_F3 0x3C
      #define HID_KEY_F4 0x3D
      #define HID_KEY_F5 0x3E
      #define HID_KEY_F6 0x3F
      #define HID_KEY_F7 0x40
      #define HID_KEY_F8 0x41
      #define HID_KEY_F9 0x42
      #define HID_KEY_F10 0x43
      #define HID_KEY_F11 0x44
      #define HID_KEY_F12 0x45

      #define HID_KEY_PRINT_SCREEN 0x46
      #define HID_KEY_SCROLL_LOCK 0x47
      #define HID_KEY_PAUSE 0x48
      #define HID_KEY_INSERT 0x49
      #define HID_KEY_HOME 0x4A
      #define HID_KEY_PAGE_UP 0x4B
      #define HID_KEY_DELETE 0x4C
      #define HID_KEY_END 0x4D
      #define HID_KEY_PAGE_DOWN 0x4E
      #define HID_KEY_ARROW_RIGHT 0x4F
      #define HID_KEY_ARROW_LEFT 0x50
      #define HID_KEY_ARROW_DOWN 0x51
      #define HID_KEY_ARROW_UP 0x52

      #define HID_KEY_NUM_LOCK 0x53
      #define HID_KEY_KEYPAD_DIVIDE 0x54
      #define HID_KEY_KEYPAD_MULTIPLY 0x55
      #define HID_KEY_KEYPAD_SUBTRACT 0x56
      #define HID_KEY_KEYPAD_ADD 0x57
      #define HID_KEY_KEYPAD_ENTER 0x58
      #define HID_KEY_KEYPAD_1 0x59
      #define HID_KEY_KEYPAD_2 0x5A
      #define HID_KEY_KEYPAD_3 0x5B
      #define HID_KEY_KEYPAD_4 0x5C
      #define HID_KEY_KEYPAD_5 0x5D
      #define HID_KEY_KEYPAD_6 0x5E
      #define HID_KEY_KEYPAD_7 0x5F
      #define HID_KEY_KEYPAD_8 0x60
      #define HID_KEY_KEYPAD_9 0x61
      #define HID_KEY_KEYPAD_0 0x62
      #define HID_KEY_KEYPAD_DECIMAL 0x63

      #define HID_KEY_EUROPE_2 0x64
      #define HID_KEY_APPLICATION 0x65
      #define HID_KEY_POWER 0x66
      #define HID_KEY_KEYPAD_EQUAL 0x67

      #define HID_KEY_F13 0x68
      #define HID_KEY_F14 0x69
      #define HID_KEY_F15 0x6A
      #define HID_KEY_F16 0x6B
      #define HID_KEY_F17 0x6C
      #define HID_KEY_F18 0x6D
      #define HID_KEY_F19 0x6E
      #define HID_KEY_F20 0x6F
      #define HID_KEY_F21 0x70
      #define HID_KEY_F22 0x71
      #define HID_KEY_F23 0x72
      #define HID_KEY_F24 0x73

      #define HID_KEY_EXECUTE 0x74
      #define HID_KEY_HELP 0x75
      #define HID_KEY_MENU 0x76
      #define HID_KEY_SELECT 0x77
      #define HID_KEY_STOP 0x78
      #define HID_KEY_AGAIN 0x79
      #define HID_KEY_UNDO 0x7A
      #define HID_KEY_CUT 0x7B
      #define HID_KEY_COPY 0x7C
      #define HID_KEY_PASTE 0x7D
      #define HID_KEY_FIND 0x7E
      #define HID_KEY_MUTE 0x7F
      #define HID_KEY_VOLUME_UP 0x80
      #define HID_KEY_VOLUME_DOWN 0x81

      #define HID_KEY_LOCKING_CAPS_LOCK 0x82
      #define HID_KEY_LOCKING_NUM_LOCK 0x83
      #define HID_KEY_LOCKING_SCROLL_LOCK 0x84
      #define HID_KEY_KEYPAD_COMMA 0x85
      #define HID_KEY_KEYPAD_EQUAL_SIGN 0x86

      #define HID_KEY_KANJI1 0x87
      #define HID_KEY_KANJI2 0x88
      #define HID_KEY_KANJI3 0x89
      #define HID_KEY_KANJI4 0x8A
      #define HID_KEY_KANJI5 0x8B
      #define HID_KEY_KANJI6 0x8C
      #define HID_KEY_KANJI7 0x8D
      #define HID_KEY_KANJI8 0x8E
      #define HID_KEY_KANJI9 0x8F

      #define HID_KEY_LANG1 0x90
      #define HID_KEY_LANG2 0x91
      #define HID_KEY_LANG3 0x92
      #define HID_KEY_LANG4 0x93
      #define HID_KEY_LANG5 0x94
      #define HID_KEY_LANG6 0x95
      #define HID_KEY_LANG7 0x96
      #define HID_KEY_LANG8 0x97
      #define HID_KEY_LANG9 0x98

      #define HID_KEY_ALTERNATE_ERASE 0x99
      #define HID_KEY_SYSREQ_ATTENTION 0x9A
      #define HID_KEY_CANCEL 0x9B
      #define HID_KEY_CLEAR 0x9C
      #define HID_KEY_PRIOR 0x9D
      #define HID_KEY_RETURN 0x9E
      #define HID_KEY_SEPARATOR 0x9F
      #define HID_KEY_OUT 0xA0
      #define HID_KEY_OPER 0xA1
      #define HID_KEY_CLEAR_AGAIN 0xA2
      #define HID_KEY_CRSEL_PROPS 0xA3
      #define HID_KEY_EXSEL 0xA4

      #define HID_KEY_KEYPAD_00 0xB0
      #define HID_KEY_KEYPAD_000 0xB1
      #define HID_KEY_THOUSANDS_SEPARATOR 0xB2
      #define HID_KEY_DECIMAL_SEPARATOR 0xB3
      #define HID_KEY_CURRENCY_UNIT 0xB4
      #define HID_KEY_CURRENCY_SUBUNIT 0xB5
      #define HID_KEY_KEYPAD_LEFT_PARENTHESIS 0xB6
      #define HID_KEY_KEYPAD_RIGHT_PARENTHESIS 0xB7
      #define HID_KEY_KEYPAD_LEFT_BRACE 0xB8
      #define HID_KEY_KEYPAD_RIGHT_BRACE 0xB9
      #define HID_KEY_KEYPAD_TAB 0xBA
      #define HID_KEY_KEYPAD_BACKSPACE 0xBB
      #define HID_KEY_KEYPAD_A 0xBC
      #define HID_KEY_KEYPAD_B 0xBD
      #define HID_KEY_KEYPAD_C 0xBE
      #define HID_KEY_KEYPAD_D 0xBF
      #define HID_KEY_KEYPAD_E 0xC0
      #define HID_KEY_KEYPAD_F 0xC1
      #define HID_KEY_KEYPAD_XOR 0xC2
      #define HID_KEY_KEYPAD_CARET 0xC3
      #define HID_KEY_KEYPAD_PERCENT 0xC4
      #define HID_KEY_KEYPAD_LESS_THAN 0xC5
      #define HID_KEY_KEYPAD_GREATER_THAN 0xC6
      #define HID_KEY_KEYPAD_AMPERSAND 0xC7
      #define HID_KEY_KEYPAD_DOUBLE_AMPERSAND 0xC8
      #define HID_KEY_KEYPAD_VERTICAL_BAR 0xC9
      #define HID_KEY_KEYPAD_DOUBLE_VERTICAL_BAR 0xCA
      #define HID_KEY_KEYPAD_COLON 0xCB
      #define HID_KEY_KEYPAD_HASH 0xCC
      #define HID_KEY_KEYPAD_SPACE 0xCD
      #define HID_KEY_KEYPAD_AT 0xCE
      #define HID_KEY_KEYPAD_EXCLAMATION 0xCF
      #define HID_KEY_KEYPAD_MEMORY_STORE 0xD0
      #define HID_KEY_KEYPAD_MEMORY_RECALL 0xD1
      #define HID_KEY_KEYPAD_MEMORY_CLEAR 0xD2
      #define HID_KEY_KEYPAD_MEMORY_ADD 0xD3
      #define HID_KEY_KEYPAD_MEMORY_SUBTRACT 0xD4
      #define HID_KEY_KEYPAD_MEMORY_MULTIPLY 0xD5
      #define HID_KEY_KEYPAD_MEMORY_DIVIDE 0xD6
      #define HID_KEY_KEYPAD_PLUS_MINUS 0xD7
      #define HID_KEY_KEYPAD_CLEAR 0xD8
      #define HID_KEY_KEYPAD_CLEAR_ENTRY 0xD9
      #define HID_KEY_KEYPAD_BINARY 0xDA
      #define HID_KEY_KEYPAD_OCTAL 0xDB
      #define HID_KEY_KEYPAD_DECIMAL_2 0xDC
      #define HID_KEY_KEYPAD_HEXADECIMAL 0xDD

      #define HID_KEY_CONTROL_LEFT 0xE0
      #define HID_KEY_SHIFT_LEFT 0xE1
      #define HID_KEY_ALT_LEFT 0xE2
      #define HID_KEY_GUI_LEFT 0xE3
      #define HID_KEY_CONTROL_RIGHT 0xE4
      #define HID_KEY_SHIFT_RIGHT 0xE5
      #define HID_KEY_ALT_RIGHT 0xE6
      #define HID_KEY_GUI_RIGHT 0xE7

      #endif

.. tab:: ca65

   .. code-block:: ca65
      :caption: hidkeys.inc

      .ifndef HIDKEYS_INC
      HIDKEYS_INC = 1

      HID_KEY_A = $04
      HID_KEY_B = $05
      HID_KEY_C = $06
      HID_KEY_D = $07
      HID_KEY_E = $08
      HID_KEY_F = $09
      HID_KEY_G = $0A
      HID_KEY_H = $0B
      HID_KEY_I = $0C
      HID_KEY_J = $0D
      HID_KEY_K = $0E
      HID_KEY_L = $0F
      HID_KEY_M = $10
      HID_KEY_N = $11
      HID_KEY_O = $12
      HID_KEY_P = $13
      HID_KEY_Q = $14
      HID_KEY_R = $15
      HID_KEY_S = $16
      HID_KEY_T = $17
      HID_KEY_U = $18
      HID_KEY_V = $19
      HID_KEY_W = $1A
      HID_KEY_X = $1B
      HID_KEY_Y = $1C
      HID_KEY_Z = $1D

      HID_KEY_1 = $1E
      HID_KEY_2 = $1F
      HID_KEY_3 = $20
      HID_KEY_4 = $21
      HID_KEY_5 = $22
      HID_KEY_6 = $23
      HID_KEY_7 = $24
      HID_KEY_8 = $25
      HID_KEY_9 = $26
      HID_KEY_0 = $27

      HID_KEY_ENTER         = $28
      HID_KEY_ESCAPE        = $29
      HID_KEY_BACKSPACE     = $2A
      HID_KEY_TAB           = $2B
      HID_KEY_SPACE         = $2C
      HID_KEY_MINUS         = $2D
      HID_KEY_EQUAL         = $2E
      HID_KEY_BRACKET_LEFT  = $2F
      HID_KEY_BRACKET_RIGHT = $30
      HID_KEY_BACKSLASH     = $31
      HID_KEY_EUROPE_1      = $32
      HID_KEY_SEMICOLON     = $33
      HID_KEY_APOSTROPHE    = $34
      HID_KEY_GRAVE         = $35
      HID_KEY_COMMA         = $36
      HID_KEY_PERIOD        = $37
      HID_KEY_SLASH         = $38

      HID_KEY_CAPS_LOCK = $39
      HID_KEY_F1        = $3A
      HID_KEY_F2        = $3B
      HID_KEY_F3        = $3C
      HID_KEY_F4        = $3D
      HID_KEY_F5        = $3E
      HID_KEY_F6        = $3F
      HID_KEY_F7        = $40
      HID_KEY_F8        = $41
      HID_KEY_F9        = $42
      HID_KEY_F10       = $43
      HID_KEY_F11       = $44
      HID_KEY_F12       = $45

      HID_KEY_PRINT_SCREEN = $46
      HID_KEY_SCROLL_LOCK  = $47
      HID_KEY_PAUSE        = $48
      HID_KEY_INSERT       = $49
      HID_KEY_HOME         = $4A
      HID_KEY_PAGE_UP      = $4B
      HID_KEY_DELETE       = $4C
      HID_KEY_END          = $4D
      HID_KEY_PAGE_DOWN    = $4E
      HID_KEY_ARROW_RIGHT  = $4F
      HID_KEY_ARROW_LEFT   = $50
      HID_KEY_ARROW_DOWN   = $51
      HID_KEY_ARROW_UP     = $52

      HID_KEY_NUM_LOCK        = $53
      HID_KEY_KEYPAD_DIVIDE   = $54
      HID_KEY_KEYPAD_MULTIPLY = $55
      HID_KEY_KEYPAD_SUBTRACT = $56
      HID_KEY_KEYPAD_ADD      = $57
      HID_KEY_KEYPAD_ENTER    = $58
      HID_KEY_KEYPAD_1        = $59
      HID_KEY_KEYPAD_2        = $5A
      HID_KEY_KEYPAD_3        = $5B
      HID_KEY_KEYPAD_4        = $5C
      HID_KEY_KEYPAD_5        = $5D
      HID_KEY_KEYPAD_6        = $5E
      HID_KEY_KEYPAD_7        = $5F
      HID_KEY_KEYPAD_8        = $60
      HID_KEY_KEYPAD_9        = $61
      HID_KEY_KEYPAD_0        = $62
      HID_KEY_KEYPAD_DECIMAL  = $63

      HID_KEY_EUROPE_2     = $64
      HID_KEY_APPLICATION  = $65
      HID_KEY_POWER        = $66
      HID_KEY_KEYPAD_EQUAL = $67

      HID_KEY_F13 = $68
      HID_KEY_F14 = $69
      HID_KEY_F15 = $6A
      HID_KEY_F16 = $6B
      HID_KEY_F17 = $6C
      HID_KEY_F18 = $6D
      HID_KEY_F19 = $6E
      HID_KEY_F20 = $6F
      HID_KEY_F21 = $70
      HID_KEY_F22 = $71
      HID_KEY_F23 = $72
      HID_KEY_F24 = $73

      HID_KEY_EXECUTE     = $74
      HID_KEY_HELP        = $75
      HID_KEY_MENU        = $76
      HID_KEY_SELECT      = $77
      HID_KEY_STOP        = $78
      HID_KEY_AGAIN       = $79
      HID_KEY_UNDO        = $7A
      HID_KEY_CUT         = $7B
      HID_KEY_COPY        = $7C
      HID_KEY_PASTE       = $7D
      HID_KEY_FIND        = $7E
      HID_KEY_MUTE        = $7F
      HID_KEY_VOLUME_UP   = $80
      HID_KEY_VOLUME_DOWN = $81

      HID_KEY_LOCKING_CAPS_LOCK   = $82
      HID_KEY_LOCKING_NUM_LOCK    = $83
      HID_KEY_LOCKING_SCROLL_LOCK = $84
      HID_KEY_KEYPAD_COMMA        = $85
      HID_KEY_KEYPAD_EQUAL_SIGN   = $86

      HID_KEY_KANJI1 = $87
      HID_KEY_KANJI2 = $88
      HID_KEY_KANJI3 = $89
      HID_KEY_KANJI4 = $8A
      HID_KEY_KANJI5 = $8B
      HID_KEY_KANJI6 = $8C
      HID_KEY_KANJI7 = $8D
      HID_KEY_KANJI8 = $8E
      HID_KEY_KANJI9 = $8F

      HID_KEY_LANG1 = $90
      HID_KEY_LANG2 = $91
      HID_KEY_LANG3 = $92
      HID_KEY_LANG4 = $93
      HID_KEY_LANG5 = $94
      HID_KEY_LANG6 = $95
      HID_KEY_LANG7 = $96
      HID_KEY_LANG8 = $97
      HID_KEY_LANG9 = $98

      HID_KEY_ALTERNATE_ERASE  = $99
      HID_KEY_SYSREQ_ATTENTION = $9A
      HID_KEY_CANCEL           = $9B
      HID_KEY_CLEAR            = $9C
      HID_KEY_PRIOR            = $9D
      HID_KEY_RETURN           = $9E
      HID_KEY_SEPARATOR        = $9F
      HID_KEY_OUT              = $A0
      HID_KEY_OPER             = $A1
      HID_KEY_CLEAR_AGAIN      = $A2
      HID_KEY_CRSEL_PROPS      = $A3
      HID_KEY_EXSEL            = $A4

      HID_KEY_KEYPAD_00                  = $B0
      HID_KEY_KEYPAD_000                 = $B1
      HID_KEY_THOUSANDS_SEPARATOR        = $B2
      HID_KEY_DECIMAL_SEPARATOR          = $B3
      HID_KEY_CURRENCY_UNIT              = $B4
      HID_KEY_CURRENCY_SUBUNIT           = $B5
      HID_KEY_KEYPAD_LEFT_PARENTHESIS    = $B6
      HID_KEY_KEYPAD_RIGHT_PARENTHESIS   = $B7
      HID_KEY_KEYPAD_LEFT_BRACE          = $B8
      HID_KEY_KEYPAD_RIGHT_BRACE         = $B9
      HID_KEY_KEYPAD_TAB                 = $BA
      HID_KEY_KEYPAD_BACKSPACE           = $BB
      HID_KEY_KEYPAD_A                   = $BC
      HID_KEY_KEYPAD_B                   = $BD
      HID_KEY_KEYPAD_C                   = $BE
      HID_KEY_KEYPAD_D                   = $BF
      HID_KEY_KEYPAD_E                   = $C0
      HID_KEY_KEYPAD_F                   = $C1
      HID_KEY_KEYPAD_XOR                 = $C2
      HID_KEY_KEYPAD_CARET               = $C3
      HID_KEY_KEYPAD_PERCENT             = $C4
      HID_KEY_KEYPAD_LESS_THAN           = $C5
      HID_KEY_KEYPAD_GREATER_THAN        = $C6
      HID_KEY_KEYPAD_AMPERSAND           = $C7
      HID_KEY_KEYPAD_DOUBLE_AMPERSAND    = $C8
      HID_KEY_KEYPAD_VERTICAL_BAR        = $C9
      HID_KEY_KEYPAD_DOUBLE_VERTICAL_BAR = $CA
      HID_KEY_KEYPAD_COLON               = $CB
      HID_KEY_KEYPAD_HASH                = $CC
      HID_KEY_KEYPAD_SPACE               = $CD
      HID_KEY_KEYPAD_AT                  = $CE
      HID_KEY_KEYPAD_EXCLAMATION         = $CF
      HID_KEY_KEYPAD_MEMORY_STORE        = $D0
      HID_KEY_KEYPAD_MEMORY_RECALL       = $D1
      HID_KEY_KEYPAD_MEMORY_CLEAR        = $D2
      HID_KEY_KEYPAD_MEMORY_ADD          = $D3
      HID_KEY_KEYPAD_MEMORY_SUBTRACT     = $D4
      HID_KEY_KEYPAD_MEMORY_MULTIPLY     = $D5
      HID_KEY_KEYPAD_MEMORY_DIVIDE       = $D6
      HID_KEY_KEYPAD_PLUS_MINUS          = $D7
      HID_KEY_KEYPAD_CLEAR               = $D8
      HID_KEY_KEYPAD_CLEAR_ENTRY         = $D9
      HID_KEY_KEYPAD_BINARY              = $DA
      HID_KEY_KEYPAD_OCTAL               = $DB
      HID_KEY_KEYPAD_DECIMAL_2           = $DC
      HID_KEY_KEYPAD_HEXADECIMAL         = $DD

      HID_KEY_CONTROL_LEFT  = $E0
      HID_KEY_SHIFT_LEFT    = $E1
      HID_KEY_ALT_LEFT      = $E2
      HID_KEY_GUI_LEFT      = $E3
      HID_KEY_CONTROL_RIGHT = $E4
      HID_KEY_SHIFT_RIGHT   = $E5
      HID_KEY_ALT_RIGHT     = $E6
      HID_KEY_GUI_RIGHT     = $E7

      .endif

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: hidkeys.inc
      :force:

      .ifndef HIDKEYS_INC
      HIDKEYS_INC = 1

      HID_KEY_A = $04
      HID_KEY_B = $05
      HID_KEY_C = $06
      HID_KEY_D = $07
      HID_KEY_E = $08
      HID_KEY_F = $09
      HID_KEY_G = $0A
      HID_KEY_H = $0B
      HID_KEY_I = $0C
      HID_KEY_J = $0D
      HID_KEY_K = $0E
      HID_KEY_L = $0F
      HID_KEY_M = $10
      HID_KEY_N = $11
      HID_KEY_O = $12
      HID_KEY_P = $13
      HID_KEY_Q = $14
      HID_KEY_R = $15
      HID_KEY_S = $16
      HID_KEY_T = $17
      HID_KEY_U = $18
      HID_KEY_V = $19
      HID_KEY_W = $1A
      HID_KEY_X = $1B
      HID_KEY_Y = $1C
      HID_KEY_Z = $1D

      HID_KEY_1 = $1E
      HID_KEY_2 = $1F
      HID_KEY_3 = $20
      HID_KEY_4 = $21
      HID_KEY_5 = $22
      HID_KEY_6 = $23
      HID_KEY_7 = $24
      HID_KEY_8 = $25
      HID_KEY_9 = $26
      HID_KEY_0 = $27

      HID_KEY_ENTER         = $28
      HID_KEY_ESCAPE        = $29
      HID_KEY_BACKSPACE     = $2A
      HID_KEY_TAB           = $2B
      HID_KEY_SPACE         = $2C
      HID_KEY_MINUS         = $2D
      HID_KEY_EQUAL         = $2E
      HID_KEY_BRACKET_LEFT  = $2F
      HID_KEY_BRACKET_RIGHT = $30
      HID_KEY_BACKSLASH     = $31
      HID_KEY_EUROPE_1      = $32
      HID_KEY_SEMICOLON     = $33
      HID_KEY_APOSTROPHE    = $34
      HID_KEY_GRAVE         = $35
      HID_KEY_COMMA         = $36
      HID_KEY_PERIOD        = $37
      HID_KEY_SLASH         = $38

      HID_KEY_CAPS_LOCK = $39
      HID_KEY_F1        = $3A
      HID_KEY_F2        = $3B
      HID_KEY_F3        = $3C
      HID_KEY_F4        = $3D
      HID_KEY_F5        = $3E
      HID_KEY_F6        = $3F
      HID_KEY_F7        = $40
      HID_KEY_F8        = $41
      HID_KEY_F9        = $42
      HID_KEY_F10       = $43
      HID_KEY_F11       = $44
      HID_KEY_F12       = $45

      HID_KEY_PRINT_SCREEN = $46
      HID_KEY_SCROLL_LOCK  = $47
      HID_KEY_PAUSE        = $48
      HID_KEY_INSERT       = $49
      HID_KEY_HOME         = $4A
      HID_KEY_PAGE_UP      = $4B
      HID_KEY_DELETE       = $4C
      HID_KEY_END          = $4D
      HID_KEY_PAGE_DOWN    = $4E
      HID_KEY_ARROW_RIGHT  = $4F
      HID_KEY_ARROW_LEFT   = $50
      HID_KEY_ARROW_DOWN   = $51
      HID_KEY_ARROW_UP     = $52

      HID_KEY_NUM_LOCK        = $53
      HID_KEY_KEYPAD_DIVIDE   = $54
      HID_KEY_KEYPAD_MULTIPLY = $55
      HID_KEY_KEYPAD_SUBTRACT = $56
      HID_KEY_KEYPAD_ADD      = $57
      HID_KEY_KEYPAD_ENTER    = $58
      HID_KEY_KEYPAD_1        = $59
      HID_KEY_KEYPAD_2        = $5A
      HID_KEY_KEYPAD_3        = $5B
      HID_KEY_KEYPAD_4        = $5C
      HID_KEY_KEYPAD_5        = $5D
      HID_KEY_KEYPAD_6        = $5E
      HID_KEY_KEYPAD_7        = $5F
      HID_KEY_KEYPAD_8        = $60
      HID_KEY_KEYPAD_9        = $61
      HID_KEY_KEYPAD_0        = $62
      HID_KEY_KEYPAD_DECIMAL  = $63

      HID_KEY_EUROPE_2     = $64
      HID_KEY_APPLICATION  = $65
      HID_KEY_POWER        = $66
      HID_KEY_KEYPAD_EQUAL = $67

      HID_KEY_F13 = $68
      HID_KEY_F14 = $69
      HID_KEY_F15 = $6A
      HID_KEY_F16 = $6B
      HID_KEY_F17 = $6C
      HID_KEY_F18 = $6D
      HID_KEY_F19 = $6E
      HID_KEY_F20 = $6F
      HID_KEY_F21 = $70
      HID_KEY_F22 = $71
      HID_KEY_F23 = $72
      HID_KEY_F24 = $73

      HID_KEY_EXECUTE     = $74
      HID_KEY_HELP        = $75
      HID_KEY_MENU        = $76
      HID_KEY_SELECT      = $77
      HID_KEY_STOP        = $78
      HID_KEY_AGAIN       = $79
      HID_KEY_UNDO        = $7A
      HID_KEY_CUT         = $7B
      HID_KEY_COPY        = $7C
      HID_KEY_PASTE       = $7D
      HID_KEY_FIND        = $7E
      HID_KEY_MUTE        = $7F
      HID_KEY_VOLUME_UP   = $80
      HID_KEY_VOLUME_DOWN = $81

      HID_KEY_LOCKING_CAPS_LOCK   = $82
      HID_KEY_LOCKING_NUM_LOCK    = $83
      HID_KEY_LOCKING_SCROLL_LOCK = $84
      HID_KEY_KEYPAD_COMMA        = $85
      HID_KEY_KEYPAD_EQUAL_SIGN   = $86

      HID_KEY_KANJI1 = $87
      HID_KEY_KANJI2 = $88
      HID_KEY_KANJI3 = $89
      HID_KEY_KANJI4 = $8A
      HID_KEY_KANJI5 = $8B
      HID_KEY_KANJI6 = $8C
      HID_KEY_KANJI7 = $8D
      HID_KEY_KANJI8 = $8E
      HID_KEY_KANJI9 = $8F

      HID_KEY_LANG1 = $90
      HID_KEY_LANG2 = $91
      HID_KEY_LANG3 = $92
      HID_KEY_LANG4 = $93
      HID_KEY_LANG5 = $94
      HID_KEY_LANG6 = $95
      HID_KEY_LANG7 = $96
      HID_KEY_LANG8 = $97
      HID_KEY_LANG9 = $98

      HID_KEY_ALTERNATE_ERASE  = $99
      HID_KEY_SYSREQ_ATTENTION = $9A
      HID_KEY_CANCEL           = $9B
      HID_KEY_CLEAR            = $9C
      HID_KEY_PRIOR            = $9D
      HID_KEY_RETURN           = $9E
      HID_KEY_SEPARATOR        = $9F
      HID_KEY_OUT              = $A0
      HID_KEY_OPER             = $A1
      HID_KEY_CLEAR_AGAIN      = $A2
      HID_KEY_CRSEL_PROPS      = $A3
      HID_KEY_EXSEL            = $A4

      HID_KEY_KEYPAD_00                  = $B0
      HID_KEY_KEYPAD_000                 = $B1
      HID_KEY_THOUSANDS_SEPARATOR        = $B2
      HID_KEY_DECIMAL_SEPARATOR          = $B3
      HID_KEY_CURRENCY_UNIT              = $B4
      HID_KEY_CURRENCY_SUBUNIT           = $B5
      HID_KEY_KEYPAD_LEFT_PARENTHESIS    = $B6
      HID_KEY_KEYPAD_RIGHT_PARENTHESIS   = $B7
      HID_KEY_KEYPAD_LEFT_BRACE          = $B8
      HID_KEY_KEYPAD_RIGHT_BRACE         = $B9
      HID_KEY_KEYPAD_TAB                 = $BA
      HID_KEY_KEYPAD_BACKSPACE           = $BB
      HID_KEY_KEYPAD_A                   = $BC
      HID_KEY_KEYPAD_B                   = $BD
      HID_KEY_KEYPAD_C                   = $BE
      HID_KEY_KEYPAD_D                   = $BF
      HID_KEY_KEYPAD_E                   = $C0
      HID_KEY_KEYPAD_F                   = $C1
      HID_KEY_KEYPAD_XOR                 = $C2
      HID_KEY_KEYPAD_CARET               = $C3
      HID_KEY_KEYPAD_PERCENT             = $C4
      HID_KEY_KEYPAD_LESS_THAN           = $C5
      HID_KEY_KEYPAD_GREATER_THAN        = $C6
      HID_KEY_KEYPAD_AMPERSAND           = $C7
      HID_KEY_KEYPAD_DOUBLE_AMPERSAND    = $C8
      HID_KEY_KEYPAD_VERTICAL_BAR        = $C9
      HID_KEY_KEYPAD_DOUBLE_VERTICAL_BAR = $CA
      HID_KEY_KEYPAD_COLON               = $CB
      HID_KEY_KEYPAD_HASH                = $CC
      HID_KEY_KEYPAD_SPACE               = $CD
      HID_KEY_KEYPAD_AT                  = $CE
      HID_KEY_KEYPAD_EXCLAMATION         = $CF
      HID_KEY_KEYPAD_MEMORY_STORE        = $D0
      HID_KEY_KEYPAD_MEMORY_RECALL       = $D1
      HID_KEY_KEYPAD_MEMORY_CLEAR        = $D2
      HID_KEY_KEYPAD_MEMORY_ADD          = $D3
      HID_KEY_KEYPAD_MEMORY_SUBTRACT     = $D4
      HID_KEY_KEYPAD_MEMORY_MULTIPLY     = $D5
      HID_KEY_KEYPAD_MEMORY_DIVIDE       = $D6
      HID_KEY_KEYPAD_PLUS_MINUS          = $D7
      HID_KEY_KEYPAD_CLEAR               = $D8
      HID_KEY_KEYPAD_CLEAR_ENTRY         = $D9
      HID_KEY_KEYPAD_BINARY              = $DA
      HID_KEY_KEYPAD_OCTAL               = $DB
      HID_KEY_KEYPAD_DECIMAL_2           = $DC
      HID_KEY_KEYPAD_HEXADECIMAL         = $DD

      HID_KEY_CONTROL_LEFT  = $E0
      HID_KEY_SHIFT_LEFT    = $E1
      HID_KEY_ALT_LEFT      = $E2
      HID_KEY_GUI_LEFT      = $E3
      HID_KEY_CONTROL_RIGHT = $E4
      HID_KEY_SHIFT_RIGHT   = $E5
      HID_KEY_ALT_RIGHT     = $E6
      HID_KEY_GUI_RIGHT     = $E7

      .endif


Mouse
=====

.. note::

   The `Tablet`_ interface is almost always the better choice. It gives a
   canvas pixel position for a mouse, pen, or touchscreen. Raw mouse input
   is still useful for devices that act like a mouse but are not a pointer,
   such as spinners.

The RIA can give applications direct access to mouse data. Enable and
disable it by mapping it to an address in XRAM.

.. code-block:: C

  xreg(0x0, 0x0, 0x01, xaddr);  // enable
  xreg(0x0, 0x0, 0x01, 0xFFFF); // disable
  xreg_ria_mouse(xaddr);        // macro shortcut

This sets the XRAM address of a structure holding the live mouse input.

Compute movement by subtracting the previous value from the current one.
VSYNC timing (60 Hz) is period-correct but slow by modern standards. For
precise mouse input, poll from an ISR at 8 ms or faster (125 Hz).

Account for canvas resolution when interpreting movement. At 640x480 and
640x360, one unit equals one pixel; at 320x240 and 320x180, two units
equal one pixel.

.. code-block:: C

  int8_t delta_x = current_x - prev_x;
  int8_t delta_y = current_y - prev_y;

Mouse buttons are a bitfield:

- 0 - LEFT
- 1 - RIGHT
- 2 - MIDDLE
- 3 - BACKWARD
- 4 - FORWARD

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define MOUSE_BUTTON_LEFT 0x01
      #define MOUSE_BUTTON_RIGHT 0x02
      #define MOUSE_BUTTON_MIDDLE 0x04
      #define MOUSE_BUTTON_BACKWARD 0x08
      #define MOUSE_BUTTON_FORWARD 0x10

      #define xreg_ria_mouse(...) xreg(0x0, 0x0, 0x01, __VA_ARGS__)

      typedef struct
      {
          uint8_t buttons;
          uint8_t x;
          uint8_t y;
          uint8_t wheel;
          uint8_t pan;
          uint8_t pad; // alignment, unused
      } mouse_t; /* layout */

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      MOUSE_BUTTON_LEFT     = $01
      MOUSE_BUTTON_RIGHT    = $02
      MOUSE_BUTTON_MIDDLE   = $04
      MOUSE_BUTTON_BACKWARD = $08
      MOUSE_BUTTON_FORWARD  = $10

      .macro xreg_ria_mouse addr
          xreg $0, $0, $01, addr
      .endmacro

      .struct mouse_t
          buttons .byte
          x_pos   .byte
          y_pos   .byte
          wheel   .byte
          pan     .byte
          pad     .byte
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      MOUSE_BUTTON_LEFT     = $01
      MOUSE_BUTTON_RIGHT    = $02
      MOUSE_BUTTON_MIDDLE   = $04
      MOUSE_BUTTON_BACKWARD = $08
      MOUSE_BUTTON_FORWARD  = $10

      .macro xreg_ria_mouse addr
          xreg $0, $0, $01, \addr
      .endm

      MOUSE_BUTTONS = 0
      MOUSE_X       = 1
      MOUSE_Y       = 2
      MOUSE_WHEEL   = 3
      MOUSE_PAN     = 4
      MOUSE_PAD     = 5
      MOUSE_SIZE    = 6


.. _ria-tablet:

Tablet
======

The RIA can give applications an *absolute* pointer — a "tablet" — instead of
the relative mouse. It reports a canvas pixel position directly: a plain mouse
is integrated and clamped to the canvas, and an absolute digitizer or
touchscreen is scaled to it. Enable and disable it by mapping it to an address
in XRAM.

.. code-block:: C

  xreg(0x0, 0x0, 0x03, xaddr);  // enable
  xreg(0x0, 0x0, 0x03, 0xFFFF); // disable
  xreg_ria_tablet(xaddr);       // macro shortcut

The block is a four-byte header followed by eight contact records for
multi-touch; a mouse or pen uses only the first. The layout always reserves
the whole block, ``tablet_t``, because the RIA writes all eight contacts. A
program for a mouse or pen reads only the header and the first contact,
``tablet_pointer_t``.

``wheel`` and ``pan`` are scroll counters in the same format as the
mouse's: subtract the previous reading to get the change. Reading them
once per VSYNC is enough for normal use.

Each coordinate is 12 bits. ``y_lo`` and ``x_lo`` hold the low bytes, and
``yx_hi`` holds the high four bits of Y in its upper half and the high four
bits of X in its lower half. On the 320x240 and 320x180 canvases the high bits
of Y are always 0, so ``x_lo`` and ``yx_hi`` are X as a little-endian 16-bit
value. A released contact has flags of 0 and keeps its last position.

.. code-block:: C

  x = (c.yx_hi & 0x0F) << 8 | c.x_lo;
  y = (c.yx_hi >> 4) << 8 | c.y_lo;

Contact flags are a bitfield:

- 0 - LEFT / tip
- 1 - RIGHT
- 2 - MIDDLE
- 3 - BACKWARD
- 4 - FORWARD
- 7 - HOVER

HOVER is set when the contact tracks a position without a press. It is
always set for a mouse, set for a pen while the pen is in range, and clear
for a touchscreen.

The application and the RIA exchange pointer preferences through the header.
``status`` bit 0 (host cursor) is set only for a mouse on the :doc:`emu`
or on the :doc:`web`, where the host can draw a cursor for the
application. The bit is always clear on the :doc:`pico` and the
:doc:`fpga`, in :ref:`RetroArch <emu-retroarch>`, and for touch input.
``control`` selects the host cursor shape, or hides the cursor so the
application can draw its own. Mapping the tablet sets it to ARROW.

- 0 - OFF (host cursor hidden; the application draws its own pointer)
- 1 - ARROW
- 2 - CROSSHAIR
- 3 - IBEAM
- 4 - HAND
- 5 - RESIZE_EW
- 6 - RESIZE_NS

When the host cursor bit is clear the application must draw its own
pointer, and ``control`` has no effect.

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define TABLET_CONTACTS 8

      #define TABLET_STATUS_HOST_CURSOR 0x01

      #define TABLET_FLAG_LEFT 0x01
      #define TABLET_FLAG_RIGHT 0x02
      #define TABLET_FLAG_MIDDLE 0x04
      #define TABLET_FLAG_BACKWARD 0x08
      #define TABLET_FLAG_FORWARD 0x10
      #define TABLET_FLAG_HOVER 0x80

      #define TABLET_CURSOR_OFF 0
      #define TABLET_CURSOR_ARROW 1
      #define TABLET_CURSOR_CROSSHAIR 2
      #define TABLET_CURSOR_IBEAM 3
      #define TABLET_CURSOR_HAND 4
      #define TABLET_CURSOR_RESIZE_EW 5
      #define TABLET_CURSOR_RESIZE_NS 6

      #define xreg_ria_tablet(...) xreg(0x0, 0x0, 0x03, __VA_ARGS__)

      typedef struct
      {
          uint8_t flags;
          uint8_t y_lo;
          uint8_t x_lo;
          uint8_t yx_hi;
      } tablet_contact_t;

      typedef struct
      {
          uint8_t control;
          uint8_t status;
          uint8_t wheel;
          uint8_t pan;
          tablet_contact_t contact;
      } tablet_pointer_t;

      typedef struct
      {
          uint8_t control;
          uint8_t status;
          uint8_t wheel;
          uint8_t pan;
          tablet_contact_t contact[TABLET_CONTACTS];
      } tablet_t; /* layout */

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      TABLET_CONTACTS = 8

      TABLET_STATUS_HOST_CURSOR = $01

      TABLET_FLAG_LEFT     = $01
      TABLET_FLAG_RIGHT    = $02
      TABLET_FLAG_MIDDLE   = $04
      TABLET_FLAG_BACKWARD = $08
      TABLET_FLAG_FORWARD  = $10
      TABLET_FLAG_HOVER    = $80

      TABLET_CURSOR_OFF       = 0
      TABLET_CURSOR_ARROW     = 1
      TABLET_CURSOR_CROSSHAIR = 2
      TABLET_CURSOR_IBEAM     = 3
      TABLET_CURSOR_HAND      = 4
      TABLET_CURSOR_RESIZE_EW = 5
      TABLET_CURSOR_RESIZE_NS = 6

      .macro xreg_ria_tablet addr
          xreg $0, $0, $03, addr
      .endmacro

      .struct tablet_pointer_t
          control .byte
          status  .byte
          wheel   .byte
          pan     .byte
          contact .struct
              flags .byte
              y_lo  .byte
              x_lo  .byte
              yx_hi .byte
          .endstruct
      .endstruct

      .struct tablet_t
          control .byte
          status  .byte
          wheel   .byte
          pan     .byte
          contact .struct
              flags .byte
              y_lo  .byte
              x_lo  .byte
              yx_hi .byte
          .endstruct
          .res (::TABLET_CONTACTS - 1) * .sizeof(contact)
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      TABLET_CONTACTS = 8

      TABLET_STATUS_HOST_CURSOR = $01

      TABLET_FLAG_LEFT     = $01
      TABLET_FLAG_RIGHT    = $02
      TABLET_FLAG_MIDDLE   = $04
      TABLET_FLAG_BACKWARD = $08
      TABLET_FLAG_FORWARD  = $10
      TABLET_FLAG_HOVER    = $80

      TABLET_CURSOR_OFF       = 0
      TABLET_CURSOR_ARROW     = 1
      TABLET_CURSOR_CROSSHAIR = 2
      TABLET_CURSOR_IBEAM     = 3
      TABLET_CURSOR_HAND      = 4
      TABLET_CURSOR_RESIZE_EW = 5
      TABLET_CURSOR_RESIZE_NS = 6

      .macro xreg_ria_tablet addr
          xreg $0, $0, $03, \addr
      .endm

      TABLET_CONTROL = 0
      TABLET_STATUS  = 1
      TABLET_WHEEL   = 2
      TABLET_PAN     = 3
      TABLET_CONTACT = 4

      TABLET_CONTACT_FLAGS = 0
      TABLET_CONTACT_Y_LO  = 1
      TABLET_CONTACT_X_LO  = 2
      TABLET_CONTACT_YX_HI = 3
      TABLET_CONTACT_SIZE  = 4

      TABLET_SIZE = TABLET_CONTACT + TABLET_CONTACTS * TABLET_CONTACT_SIZE
      TABLET_POINTER_SIZE = TABLET_CONTACT + TABLET_CONTACT_SIZE

XRAM is atomic for single bytes only, so the RIA can write the block while a
program reads it, and that read mixes two positions. ``tablet_read`` copies the
block, then reads it again to check that the RIA did not write it during the
first read. Writes are at least 1 ms apart, so when the two reads differ, a
third read will not overlap one. All three versions have the same C
prototype, ``void tablet_read(tablet_pointer_t *tablet)``, so a C program can
call an assembly version in place of the C one. A multi-touch program reads a
``tablet_t`` in place of ``tablet_pointer_t``.

.. tab:: C

   .. code-block:: C

      // Read the block again to check that the host did not write it during the
      // read. Writes are at least 1 ms apart, so a third read will not overlap one.
      void tablet_read(tablet_pointer_t *tablet)
      {
          tablet_pointer_t check;

          xram0_read(tablet, XRAM_TABLET, sizeof(tablet_pointer_t));
          xram0_read(&check, XRAM_TABLET, sizeof(tablet_pointer_t));
          if (memcmp(tablet, &check, sizeof(tablet_pointer_t)))
              xram0_read(tablet, XRAM_TABLET, sizeof(tablet_pointer_t));
      }

.. tab:: ca65

   .. code-block:: ca65

      .importzp ptr1
      .export _tablet_read

      ; void tablet_read(tablet_pointer_t *tablet);
      ; Read the block again to check that the host did not write it during the
      ; read. Writes are at least 1 ms apart, so a third read will not overlap one.
      _tablet_read:
          sta ptr1
          stx ptr1+1
          lda #1
          sta RIA_STEP0
          jsr @read
          jsr @read
          beq @done           ; Done when the two reads match, else read a third time
      @read:
          lda #<XRAM_TABLET
          sta RIA_ADDR0
          lda #>XRAM_TABLET
          sta RIA_ADDR0+1
          ldx #0
          ldy #0
      @loop:
          lda RIA_RW0
          cmp (ptr1),y
          beq @same
          inx                 ; A byte changed
      @same:
          sta (ptr1),y
          iny
          cpy #.sizeof(tablet_pointer_t)
          bne @loop
          txa
      @done:
          rts

.. tab:: llvm-mc

   .. code-block:: ca65
      :force:

      .include "imag.inc"
      .globl tablet_read

      ; void tablet_read(tablet_pointer_t *tablet);
      ; Read the block again to check that the host did not write it during the
      ; read. Writes are at least 1 ms apart, so a third read will not overlap one.
      tablet_read:
          lda #1
          sta RIA_STEP0
          jsr 1f
          jsr 1f
          beq 4f              ; Done when the two reads match, else read a third time
      1:
          lda #(XRAM_TABLET & $FF)
          sta RIA_ADDR0
          lda #((XRAM_TABLET >> 8) & $FF)
          sta RIA_ADDR0+1
          ldx #0
          ldy #0
      2:
          lda RIA_RW0
          cmp (__rc2),y
          beq 3f
          inx                 ; A byte changed
      3:
          sta (__rc2),y
          iny
          cpy #TABLET_POINTER_SIZE
          bne 2b
          txa
      4:
          rts


.. _ria-gamepads:

Gamepads
========

The RIA supports up to four gamepads. Where the layout comes from, and
how a game works with nearly every gamepad, is covered in the
:ref:`Gamepads <port-gamepads>` section of :doc:`port`.

Enable and disable the RIA gamepad data by setting its extended
register. The register value is the XRAM start address of the gamepad
data.

.. code-block:: C

  xreg(0x0, 0x0, 0x02, xaddr);  // enable
  xreg(0x0, 0x0, 0x02, 0xFFFF); // disable
  xreg_ria_gamepad(xaddr);      // macro shortcut

The RIA continuously updates extended memory with gamepad state. The
10-byte structure below repeats four times — 40 bytes total, one block
per gamepad.

The upper bits of the DPAD register report readiness and type. The
connected bit is high when a gamepad occupies that player slot.

.. list-table::
   :widths: 1 1 1 1 1
   :header-rows: 1

   * - Type
     - BTN0 bit 0
     - BTN0 bit 1
     - BTN0 bit 3
     - BTN0 bit 4
   * - 1 Western AB
     - A, south
     - B, east
     - X, west
     - Y, north
   * - 2 Eastern BA
     - A, east
     - B, south
     - X, north
     - Y, west
   * - 3 PlayStation
     - Cross, south
     - Circle, east
     - Square, west
     - Triangle, north

The sticks bit is high when the gamepad has both analog sticks. Some
retro-style gamepads indicate they have sticks when they do not. They may
also map buttons in unusual ways. The RIA does the best it can with the
provided metadata.

Both digital and analog values are available for the sticks and the
L2/R2 triggers.

Some gamepads report only digital data; in that case, code that uses L2
and R2 should expect analog values of just 0 or 255.

.. list-table::
   :widths: 1 1 20
   :header-rows: 1

   * - Offset
     - Name
     - Description
   * - 0
     - DPAD
     - * bit 0: Direction pad up
       * bit 1: Direction pad down
       * bit 2: Direction pad left
       * bit 3: Direction pad right
       * bits 4-5: Button type. 0=unknown, 1=Western AB,
         2=Eastern BA, 3=PlayStation
       * bit 6: Both analog sticks present
       * bit 7: Connected
   * - 1
     - STICKS
     - * bit 0: Left stick up
       * bit 1: Left stick down
       * bit 2: Left stick left
       * bit 3: Left stick right
       * bit 4: Right stick up
       * bit 5: Right stick down
       * bit 6: Right stick left
       * bit 7: Right stick right
   * - 2
     - BTN0
     - * bit 0: A or Cross
       * bit 1: B or Circle
       * bit 2: C or Right Paddle
       * bit 3: X or Square
       * bit 4: Y or Triangle
       * bit 5: Z or Left Paddle
       * bit 6: L1
       * bit 7: R1
   * - 3
     - BTN1
     - * bit 0: L2
       * bit 1: R2
       * bit 2: Select/Back
       * bit 3: Start/Menu
       * bit 4: Home button
       * bit 5: L3
       * bit 6: R3
       * bit 7: Undefined
   * - 4
     - LX
     - Left analog stick X position. -128=left, 0=center, 127=right
   * - 5
     - LY
     - Left analog stick Y position. -128=up, 0=center, 127=down
   * - 6
     - RX
     - Right analog stick X position. -128=left, 0=center, 127=right
   * - 7
     - RY
     - Right analog stick Y position. -128=up, 0=center, 127=down
   * - 8
     - L2
     - Left analog trigger position. 0-255
   * - 9
     - R2
     - Right analog trigger position. 0-255

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define GAMEPAD_PLAYERS 4

      #define GAMEPAD_DPAD_UP 0x01
      #define GAMEPAD_DPAD_DOWN 0x02
      #define GAMEPAD_DPAD_LEFT 0x04
      #define GAMEPAD_DPAD_RIGHT 0x08

      #define GAMEPAD_FEAT_TYPE_MASK 0x30
      #define GAMEPAD_TYPE_UNKNOWN 0x00
      #define GAMEPAD_TYPE_WESTERN 0x10
      #define GAMEPAD_TYPE_EASTERN 0x20
      #define GAMEPAD_TYPE_PLAYSTATION 0x30
      #define GAMEPAD_FEAT_STICKS 0x40
      #define GAMEPAD_FEAT_CONNECTED 0x80

      #define GAMEPAD_LSTICK_UP 0x01
      #define GAMEPAD_LSTICK_DOWN 0x02
      #define GAMEPAD_LSTICK_LEFT 0x04
      #define GAMEPAD_LSTICK_RIGHT 0x08
      #define GAMEPAD_RSTICK_UP 0x10
      #define GAMEPAD_RSTICK_DOWN 0x20
      #define GAMEPAD_RSTICK_LEFT 0x40
      #define GAMEPAD_RSTICK_RIGHT 0x80

      #define GAMEPAD_BTN0_A 0x01
      #define GAMEPAD_BTN0_B 0x02
      #define GAMEPAD_BTN0_C 0x04
      #define GAMEPAD_BTN0_X 0x08
      #define GAMEPAD_BTN0_Y 0x10
      #define GAMEPAD_BTN0_Z 0x20
      #define GAMEPAD_BTN0_L1 0x40
      #define GAMEPAD_BTN0_R1 0x80

      #define GAMEPAD_BTN1_L2 0x01
      #define GAMEPAD_BTN1_R2 0x02
      #define GAMEPAD_BTN1_SELECT 0x04
      #define GAMEPAD_BTN1_START 0x08
      #define GAMEPAD_BTN1_HOME 0x10
      #define GAMEPAD_BTN1_L3 0x20
      #define GAMEPAD_BTN1_R3 0x40

      #define xreg_ria_gamepad(...) xreg(0x0, 0x0, 0x02, __VA_ARGS__)

      typedef struct
      {
          uint8_t dpad;
          uint8_t sticks;
          uint8_t btn0;
          uint8_t btn1;
          int8_t lx;
          int8_t ly;
          int8_t rx;
          int8_t ry;
          uint8_t l2;
          uint8_t r2;
      } gamepad_player_t;

      typedef struct
      {
          gamepad_player_t player[GAMEPAD_PLAYERS];
      } gamepad_t; /* layout */

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      GAMEPAD_PLAYERS = 4

      GAMEPAD_DPAD_UP    = $01
      GAMEPAD_DPAD_DOWN  = $02
      GAMEPAD_DPAD_LEFT  = $04
      GAMEPAD_DPAD_RIGHT = $08

      GAMEPAD_FEAT_TYPE_MASK   = $30
      GAMEPAD_TYPE_UNKNOWN     = $00
      GAMEPAD_TYPE_WESTERN     = $10
      GAMEPAD_TYPE_EASTERN     = $20
      GAMEPAD_TYPE_PLAYSTATION = $30
      GAMEPAD_FEAT_STICKS      = $40
      GAMEPAD_FEAT_CONNECTED   = $80

      GAMEPAD_LSTICK_UP    = $01
      GAMEPAD_LSTICK_DOWN  = $02
      GAMEPAD_LSTICK_LEFT  = $04
      GAMEPAD_LSTICK_RIGHT = $08
      GAMEPAD_RSTICK_UP    = $10
      GAMEPAD_RSTICK_DOWN  = $20
      GAMEPAD_RSTICK_LEFT  = $40
      GAMEPAD_RSTICK_RIGHT = $80

      GAMEPAD_BTN0_A  = $01
      GAMEPAD_BTN0_B  = $02
      GAMEPAD_BTN0_C  = $04
      GAMEPAD_BTN0_X  = $08
      GAMEPAD_BTN0_Y  = $10
      GAMEPAD_BTN0_Z  = $20
      GAMEPAD_BTN0_L1 = $40
      GAMEPAD_BTN0_R1 = $80

      GAMEPAD_BTN1_L2     = $01
      GAMEPAD_BTN1_R2     = $02
      GAMEPAD_BTN1_SELECT = $04
      GAMEPAD_BTN1_START  = $08
      GAMEPAD_BTN1_HOME   = $10
      GAMEPAD_BTN1_L3     = $20
      GAMEPAD_BTN1_R3     = $40

      .macro xreg_ria_gamepad addr
          xreg $0, $0, $02, addr
      .endmacro

      .struct gamepad_t
          player .struct
              dpad   .byte
              sticks .byte
              btn0   .byte
              btn1   .byte
              lx     .byte
              ly     .byte
              rx     .byte
              ry     .byte
              l2     .byte
              r2     .byte
          .endstruct
          .res (::GAMEPAD_PLAYERS - 1) * .sizeof(player)
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      GAMEPAD_PLAYERS = 4

      GAMEPAD_DPAD_UP    = $01
      GAMEPAD_DPAD_DOWN  = $02
      GAMEPAD_DPAD_LEFT  = $04
      GAMEPAD_DPAD_RIGHT = $08

      GAMEPAD_FEAT_TYPE_MASK   = $30
      GAMEPAD_TYPE_UNKNOWN     = $00
      GAMEPAD_TYPE_WESTERN     = $10
      GAMEPAD_TYPE_EASTERN     = $20
      GAMEPAD_TYPE_PLAYSTATION = $30
      GAMEPAD_FEAT_STICKS      = $40
      GAMEPAD_FEAT_CONNECTED   = $80

      GAMEPAD_LSTICK_UP    = $01
      GAMEPAD_LSTICK_DOWN  = $02
      GAMEPAD_LSTICK_LEFT  = $04
      GAMEPAD_LSTICK_RIGHT = $08
      GAMEPAD_RSTICK_UP    = $10
      GAMEPAD_RSTICK_DOWN  = $20
      GAMEPAD_RSTICK_LEFT  = $40
      GAMEPAD_RSTICK_RIGHT = $80

      GAMEPAD_BTN0_A  = $01
      GAMEPAD_BTN0_B  = $02
      GAMEPAD_BTN0_C  = $04
      GAMEPAD_BTN0_X  = $08
      GAMEPAD_BTN0_Y  = $10
      GAMEPAD_BTN0_Z  = $20
      GAMEPAD_BTN0_L1 = $40
      GAMEPAD_BTN0_R1 = $80

      GAMEPAD_BTN1_L2     = $01
      GAMEPAD_BTN1_R2     = $02
      GAMEPAD_BTN1_SELECT = $04
      GAMEPAD_BTN1_START  = $08
      GAMEPAD_BTN1_HOME   = $10
      GAMEPAD_BTN1_L3     = $20
      GAMEPAD_BTN1_R3     = $40

      .macro xreg_ria_gamepad addr
          xreg $0, $0, $02, \addr
      .endm

      GAMEPAD_PLAYER = 0

      GAMEPAD_PLAYER_DPAD   = 0
      GAMEPAD_PLAYER_STICKS = 1
      GAMEPAD_PLAYER_BTN0   = 2
      GAMEPAD_PLAYER_BTN1   = 3
      GAMEPAD_PLAYER_LX     = 4
      GAMEPAD_PLAYER_LY     = 5
      GAMEPAD_PLAYER_RX     = 6
      GAMEPAD_PLAYER_RY     = 7
      GAMEPAD_PLAYER_L2     = 8
      GAMEPAD_PLAYER_R2     = 9
      GAMEPAD_PLAYER_SIZE   = 10

      GAMEPAD_SIZE = GAMEPAD_PLAYER + GAMEPAD_PLAYERS * GAMEPAD_PLAYER_SIZE


.. _ria-psg:

Programmable Sound Generator
============================

The RIA includes a Programmable Sound Generator (PSG), configured
through extended register device 0, channel 1, address 0x00.

* Eight 16-bit oscillator channels.
* Five waveforms: Sine, Square, Sawtooth, Triangle, Noise.
* ADSR envelope: Attack, Decay, Sustain, Release.
* Stereo panning.
* PWM for all waveforms.

Each of the eight oscillators uses eight bytes of XRAM for
configuration. The structure size is a power of two, so indexing into
the oscillator array is a bit shift.

Enable and disable the PSG by setting its extended register. The value
is the XRAM start address for the 64 bytes of config; it must be
int-aligned and must not cross a page boundary. Only one sound generator
plays at a time, so enabling the PSG disables the OPL2.

.. code-block:: C

  xreg(0x0, 0x1, 0x00, xaddr);  // enable
  xreg(0x0, 0x1, 0x00, 0xFFFF); // disable
  xreg_ria_psg(xaddr);          // macro shortcut

Configuration changes take effect immediately, which opens the door to
panning, slide instruments, and other CPU-driven shenanigans.

.. list-table::
   :widths: 5 90
   :header-rows: 1

   * - Name
     - Description
   * - freq
     - 0-65535 Oscillator frequency as Hertz * 3. This results in a
       resolution of 1/3 Hz.
   * - duty
     - 0-255 (0-100%) Duty cycle of oscillator. This affects all
       waveforms.
   * - attack
     - Attack phase volume and rate.

       * bits 7-4 - 0-15 volume attenuation.
       * bits 3-0 - 0-15 attack rate.

   * - decay
     - Decay phase volume and rate.

       * bits 7-4 - 0-15 volume attenuation.
       * bits 3-0 - 0-15 decay rate.

   * - release_wave
     - Waveform and release rate.

       * bits 7-4 - 0=sine, 1=square, 2=sawtooth, 3=triangle,
         4=noise.
       * bits 3-0 - 0-15 release rate.

   * - pan_gate
     - Stereo pan and gate.

       * bits 7-1 - Pan -63(left) to 63(right).
       * bit 0 - 1=attack/decay/sustain, 0=release.

Value table. ADR rates are the time it takes for a full volume change.
Volume attenuation is logarithmic.

.. list-table::
   :widths: 1 1 1 20
   :header-rows: 1

   * - Value
     - Attack
     - Decay/Release
     - Attenuation Multiplier
   * - 0
     - 2ms
     - 6ms
     - 256/256 (loud)
   * - 1
     - 8ms
     - 24ms
     - 204/256
   * - 2
     - 16ms
     - 48ms
     - 168/256
   * - 3
     - 24ms
     - 72ms
     - 142/256
   * - 4
     - 38ms
     - 114ms
     - 120/256
   * - 5
     - 56ms
     - 168ms
     - 102/256
   * - 6
     - 68ms
     - 204ms
     - 86/256
   * - 7
     - 80ms
     - 240ms
     - 73/256
   * - 8
     - 100ms
     - 300ms
     - 61/256
   * - 9
     - 250ms
     - 750ms
     - 50/256
   * - 10
     - 500ms
     - 1.5s
     - 40/256
   * - 11
     - 800ms
     - 2.4s
     - 31/256
   * - 12
     - 1s
     - 3s
     - 22/256
   * - 13
     - 3s
     - 9s
     - 14/256
   * - 14
     - 5s
     - 15s
     - 7/256
   * - 15
     - 8s
     - 24s
     - 0/256 (silent)

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define PSG_CHANNELS 8

      #define PSG_WAVE_SINE 0x00
      #define PSG_WAVE_SQUARE 0x10
      #define PSG_WAVE_SAWTOOTH 0x20
      #define PSG_WAVE_TRIANGLE 0x30
      #define PSG_WAVE_NOISE 0x40

      #define PSG_GATE 0x01

      #define PSG_FREQ_HZ(hz) ((hz) * 3u)
      #define PSG_PAN(pan) ((uint8_t)((pan) * 2))

      #define xreg_ria_psg(...) xreg(0x0, 0x1, 0x00, __VA_ARGS__)

      typedef struct
      {
          uint16_t freq;
          uint8_t duty;
          uint8_t attack;
          uint8_t decay;
          uint8_t release_wave;
          uint8_t pan_gate;
          uint8_t reserved;
      } psg_channel_t;

      typedef struct
      {
          psg_channel_t channel[PSG_CHANNELS];
      } psg_t; /* layout */

      /* After the XRAM_ names: PSG_PAGE_CHECK(XRAM_PSG); */
      #define PSG_PAGE_CHECK(addr) \
          _Static_assert((addr) % 256 + sizeof(psg_t) <= 256, #addr " crosses a page.")

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      PSG_CHANNELS = 8

      PSG_WAVE_SINE     = $00
      PSG_WAVE_SQUARE   = $10
      PSG_WAVE_SAWTOOTH = $20
      PSG_WAVE_TRIANGLE = $30
      PSG_WAVE_NOISE    = $40

      PSG_GATE = $01

      .macro xreg_ria_psg addr
          xreg $0, $1, $00, addr
      .endmacro

      .struct psg_t
          channel .struct
              freq         .word
              duty         .byte
              attack       .byte
              decay        .byte
              release_wave .byte
              pan_gate     .byte
              reserved     .byte
          .endstruct
          .res (::PSG_CHANNELS - 1) * .sizeof(channel)
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      PSG_CHANNELS = 8

      PSG_WAVE_SINE     = $00
      PSG_WAVE_SQUARE   = $10
      PSG_WAVE_SAWTOOTH = $20
      PSG_WAVE_TRIANGLE = $30
      PSG_WAVE_NOISE    = $40

      PSG_GATE = $01

      .macro xreg_ria_psg addr
          xreg $0, $1, $00, \addr
      .endm

      PSG_CHANNEL = 0

      PSG_CHANNEL_FREQ         = 0
      PSG_CHANNEL_DUTY         = 2
      PSG_CHANNEL_ATTACK       = 3
      PSG_CHANNEL_DECAY        = 4
      PSG_CHANNEL_RELEASE_WAVE = 5
      PSG_CHANNEL_PAN_GATE     = 6
      PSG_CHANNEL_RESERVED     = 7
      PSG_CHANNEL_SIZE         = 8

      PSG_SIZE = PSG_CHANNEL + PSG_CHANNELS * PSG_CHANNEL_SIZE


.. _ria-opl2:

Yamaha OPL2 FM Sound Generator
==============================

The RIA includes a YM3812 FM Sound Generator (OPL2), configured through
extended register device 0, channel 1, address 0x01.

Enable and disable the OPL2 by setting its extended register. The value
is the XRAM start address for the 256 OPL2 registers, which must begin
on a page boundary. So if xaddr is 0x4200, the 256 OPL2 registers map into
XRAM from 0x4200 to 0x42FF. Enabling the OPL2 disables the PSG.

.. code-block:: C

  xreg(0x0, 0x1, 0x01, xaddr);  // enable
  xreg(0x0, 0x1, 0x01, 0xFFFF); // disable
  xreg_ria_opl(xaddr);          // macro shortcut


Timers, interrupts, and the status register are not supported. Those
features existed mainly to cost-reduce consumer devices; computers of
the era had their own timers and rarely used the chip's.

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_ria_opl(...) xreg(0x0, 0x1, 0x01, __VA_ARGS__)

      typedef struct
      {
          uint8_t reg[256];
      } opl_t; /* layout */

      /* After the XRAM_ names: OPL_PAGE_CHECK(XRAM_OPL); */
      #define OPL_PAGE_CHECK(addr) \
          _Static_assert((addr) % 256 == 0, #addr " does not start a page.")

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_ria_opl addr
          xreg $0, $1, $01, addr
      .endmacro

      .struct opl_t
          reg .res 256
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_ria_opl addr
          xreg $0, $1, $01, \addr
      .endm

      OPL_REG  = 0
      OPL_SIZE = 256


Console
=======

The system console is the terminal connected to the RIA, and the
`UART`_ registers above are its rawest form. The OS wraps that same port as
``stdin``, ``stdout``, ``stderr``, and the ``CON:`` and ``TTY:`` device
names. See :doc:`term` for cooked and raw reads, the non-blocking
variants, and the line editor.
