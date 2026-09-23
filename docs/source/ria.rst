====================
RP6502-RIA
====================

RP6502 - RP6502 Interface Adapter


Introduction
============

The RP6502 Interface Adapter (RIA) is the interface between a host and a
WDC W65C02S microprocessor. It provides every essential service needed to
run: the clock, reset, file and I/O services, and another 64K (XRAM) that
services video, audio, and direct access to peripherals.

The RIA must live at $FFE0-$FFFF and must control RESB and PHI2. Those
are the only hard requirements. Everything else is yours to customize if
you're designing your own hardware.


Implementations
===============

- :doc:`pico` — The RIA software fits entirely on a Raspberry Pi Pico 2.
  Registers are implemented in PIO for connecting to a 65C02.
- :doc:`fpga` — The same software on a Hazard3 RISC-V soft CPU. The 65C02,
   65C22, and registers are in fabric.
- :doc:`emu` — RIA software runs natively on the host CPU along with a
  a 65C02 and 65C22 software emulator.

A Picocomputer always has a companion CPU and Operating System. For example,
one :doc:`emu` runs on Linux with an ARM processor. The :doc:`pico` is
special because it hosts itself. The :doc:`os` is an abstraction on all
other hosts, but it is the native Operating System on the :doc:`pico`.

One other special feature of the :doc:`pico` is its monitor. Every ``load``,
``install``, ``set``, ``status``, and ``help`` command on this page applies
only to an :doc:`pico`. The :doc:`emu` takes command-line arguments instead,
and the :doc:`fpga` uses the Pocket's own menus.


Reset
=====

Think of reset as two states rather than a pulse on RESB. While reset
is low, the 6502 is stopped. On an :doc:`pico`, the monitor is connected
to the console while in reset. On the Pocket, the system waits for a new
ROM to be loaded from the settings menu. On :doc:`emu`, some hosts wait
for a new ROM to load while others exit the host process.

Reset is mostly handled automatically and this works well for all hosts
except the :doc:`pico`. Here we need a way to stop a wedged 6502. The monitor
also provides two commands that will bring reset high.
Either ``load`` a ROM that has a reset vector, or use the ``reset`` command
if you've prepared RAM some other way.
To drop reset from high to low and return to the monitor, even from a
wedged 6502, use any terminal on the
:ref:`console manifold <term-console-manifold>`:

1. Press Ctrl-Alt-Del from a USB keyboard.
2. Send a break from a serial terminal.
3. Send a break from a telnet terminal.


.. _ria-registers:

Registers
=========

The RIA registers are mapped into 32 bytes of the 6502's address space at
$FFE0-$FFFF. The last six are the 6502's own vectors; which present as RAM.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $FFE0
     - READY
     - Flow control for UART FIFO.

       * bit 7 - TX FIFO not full. OK to send.
       * bit 6 - RX FIFO has data ready.

   * - $FFE1
     - TX
     - Write bytes to the UART.
   * - $FFE2
     - RX
     - Read bytes from the UART.
   * - $FFE3
     - VSYNC
     - Increments every 1/60 second when :doc:`PIX VGA <vga>` device 1 is
       connected.
   * - $FFE4
     - RW0
     - Read or write the `Extended RAM (XRAM)`_ referenced by ADDR0.
   * - $FFE5
     - STEP0
     - Signed byte added to ADDR0 after every access to RW0.
   * - | $FFE6 -
       | $FFE7
     - ADDR0
     - Address of `Extended RAM (XRAM)`_ for RW0.
   * - $FFE8
     - RW1
     - Read or write the `Extended RAM (XRAM)`_ referenced by ADDR1.
   * - $FFE9
     - STEP1
     - Signed byte added to ADDR1 after every access to RW1.
   * - | $FFEA -
       | $FFEB
     - ADDR1
     - Address of `Extended RAM (XRAM)`_ for RW1.
   * - $FFEC
     - XSTACK
     - 512 bytes for `Extended Stack (XSTACK)`_.
   * - $FFED
     - ERRNO_LO
     - Low byte of errno. All errors fit in this byte.
   * - $FFEE
     - ERRNO_HI
     - Ensures errno is optionally a 16-bit int.
   * - $FFEF
     - OP
     - Write the :doc:`OS <os>` operation id here to begin an OS call.
   * - $FFF0
     - IRQ
     - Interrupt enable mask. Reading returns the triggered signals
       as bits and clears them. Writing sets the enable mask and
       also clears any triggered signals.

       * bit 7 - VSYNC
       * bit 6 - SIGINT

   * - $FFF1
     - SPIN
     - Always $80 (the BRA opcode). JSR here to spin-wait
       for an OS call. The CPU loops on this BRA until BUSY clears, then
       falls through to LDA and LDX below.
   * - $FFF2
     - BUSY
     - Bit 7 high while OS operation is running.
   * - $FFF3
     - LDA
     - Always $A9 (the LDA immediate opcode). Part of the
       spin-loop return sequence.
   * - $FFF4
     - A
     - OS call register A.
   * - $FFF5
     - LDX
     - Always $A2 (the LDX immediate opcode). Part of the
       spin-loop return sequence.
   * - $FFF6
     - X
     - OS call register X.
   * - $FFF7
     - RTS
     - Always $60 (the RTS opcode). Ends the spin-loop return
       sequence, returning to the caller with A and X loaded.
   * - | $FFF8 -
       | $FFF9
     - SREG
     - 32-bit extension to AX - AXSREG.
   * - | $FFFA -
       | $FFFB
     - NMIB
     - 6502 vector.
   * - | $FFFC -
       | $FFFD
     - RESB
     - 6502 vector.
   * - | $FFFE -
       | $FFFF
     - BRK/IRQB
     - 6502 vector.

.. _ria-uart:

UART
----

The UART behind $FFE0-$FFE2 is reached directly through these registers,
and the ready flags on bits 6-7 let you test with the BIT operator. Use
these or the :doc:`os` stdio, but not both at once. Driving the UART
directly while a stdio OS function is in progress is undefined behavior.
The line runs at 115200 bps, 8-bit words, no parity, 1 stop bit.

.. _ria-extended-ram:

Extended RAM (XRAM)
-------------------

RW0 and RW1 are two portals into the same 64 KB of XRAM. A single
portal would make moving XRAM slow, since data would have to buffer
through 6502 RAM. Ideally you won't move XRAM at all and can use the
pair for smarter optimizations.

STEP0 and STEP1 default to 1 after reset. Both are signed, so negative
values walk XRAM in reverse. These auto-increment adders make sequential
access very fast — more than enough to offset the slightly slower random
access compared to 6502 system RAM.

.. code-block:: C

  RIA.addr0 = 0x1000;
  RIA.step0 = 1;
  RIA.rw0 = 0x12; /* $1000 */
  RIA.rw0 = 0x34; /* $1001 */

Extended Stack (XSTACK)
-----------------------

This is a 512-byte, top-down, last-in-first-out stack used by the
fastcall mechanism described in the :doc:`os`. Reading past the end is
guaranteed to return zeros. Write to push, read to pull.

Extended Registers (XREG)
-------------------------

The RIA is both the host of the PIX bus (documented below) and device 0
on it. Addresses are written $device:$channel:register, so every register
in the table below begins with $0.

Extended registers are how the XRAM is configured. For example, if you
want direct access to gamepad input, you would set an extended register
with the starting address of where you want the gamepad registers. You
can then read that range of XRAM to see the status of the gamepads.

A C program sets an extended register with :ref:`xreg() <os-xreg>`, and an
assembly program with the ``xreg`` macro in ``rp6502.inc``. Both take the
device, the channel, the address, and then one or more 16-bit values.

Each register below maps a device into XRAM at the address written to
it. Writing ``$FFFF`` turns the device off and always succeeds. Any other
address that is invalid for the device also turns it off, and the call
fails with ``EINVAL``.


.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:0:00
     - KEYBOARD
     - See `Keyboard`_ section
   * - $0:0:01
     - MOUSE
     - See `Mouse`_ section
   * - $0:0:02
     - GAMEPADS
     - See `Gamepads`_ section
   * - $0:0:03
     - TABLET
     - See `Tablet`_ section
   * - $0:1:00
     - PSG
     - See `Programmable Sound Generator`_ section
   * - $0:1:01
     - OPL
     - See `Yamaha OPL2 FM Sound Generator`_ section


.. _ria-keyboard:

Keyboard
========

The RIA can provide applications direct access to keyboard data, which is
what you want when you need key-up and key-down events or the modifier
keys. If you don't need that, the UART or stdin works just as well.

Enable and disable direct keyboard access by mapping it to an address
in XRAM.

.. code-block:: C

  xreg(0, 0, 0x00, xaddr);  // enable
  xreg(0, 0, 0x00, 0xFFFF); // disable
  xreg_ria_keyboard(xaddr); // macro shortcut

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

      #define xreg_ria_keyboard(...) xreg(0, 0, 0, __VA_ARGS__)

      typedef struct
      {
          uint8_t keys[32];
      } keyboard_t;

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      KEYBOARD_NO_KEY      = 0
      KEYBOARD_NUM_LOCK    = 1
      KEYBOARD_CAPS_LOCK   = 2
      KEYBOARD_SCROLL_LOCK = 3

      .macro xreg_ria_keyboard addr
          xreg 0, 0, 0, addr
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
          xreg 0, 0, 0, \addr
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

  xreg(0, 0, 0x01, xaddr);  // enable
  xreg(0, 0, 0x01, 0xFFFF); // disable
  xreg_ria_mouse(xaddr);    // macro shortcut

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

      #define xreg_ria_mouse(...) xreg(0, 0, 1, __VA_ARGS__)

      typedef struct
      {
          uint8_t buttons;
          uint8_t x;
          uint8_t y;
          uint8_t wheel;
          uint8_t pan;
          uint8_t pad; // alignment, unused
      } mouse_t;

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      MOUSE_BUTTON_LEFT     = $01
      MOUSE_BUTTON_RIGHT    = $02
      MOUSE_BUTTON_MIDDLE   = $04
      MOUSE_BUTTON_BACKWARD = $08
      MOUSE_BUTTON_FORWARD  = $10

      .macro xreg_ria_mouse addr
          xreg 0, 0, 1, addr
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
          xreg 0, 0, 1, \addr
      .endm

      MOUSE_BUTTONS = 0
      MOUSE_X       = 1
      MOUSE_Y       = 2
      MOUSE_WHEEL   = 3
      MOUSE_PAN     = 4
      MOUSE_PAD     = 5
      MOUSE_SIZE    = 6


Tablet
======

The RIA can give applications an *absolute* pointer — a "tablet" — instead of
the relative mouse. It reports a canvas pixel position directly: a plain mouse
is integrated and clamped to the canvas, and an absolute digitizer or
touchscreen is scaled to it. Enable and disable it by mapping it to an address
in XRAM.

.. code-block:: C

  xreg(0, 0, 0x03, xaddr);  // enable
  xreg(0, 0, 0x03, 0xFFFF); // disable
  xreg_ria_tablet(xaddr);   // macro shortcut

The block is a four-byte header followed by eight contact records for
multi-touch; a mouse or pen uses only the first.

``wheel`` and ``pan`` are scroll counters in the same format as the
mouse's: subtract the previous reading to get the change. Reading them
once per VSYNC is enough for normal use.

Each axis is a set of single-byte *windows*: exactly one is non-zero, and it
alone carries the value. Decode by taking the first non-zero byte. This unusal
decode is because XRAM is atomic for 8-bits only. The single retry is enough
to guarantee safety because updates are 1ms or more apart while the retry
happens in a few microseconds.

.. code-block:: C

  if (c.x0) x = c.x0 - 1;
  else if (c.x1) x = c.x1 + 254;
  else if (c.x2) x = c.x2 + 509;
  else { /* read the contact once more, then keep the previous X */ }

  if (c.y0) y = c.y0 - 1;
  else if (c.y1) y = c.y1 + 254;
  else { /* read the contact once more, then keep the previous Y */ }

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
``status`` bit 0 (host cursor) is set only when the host can draw a cursor
for the application, which is the :doc:`emu` with a mouse, in a window or a
browser. The bit is always clear on real hardware and for touch input.
``control`` selects the host cursor shape, or hides the cursor so the
application can draw its own.

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

      #define xreg_ria_tablet(...) xreg(0, 0, 3, __VA_ARGS__)

      typedef struct
      {
          uint8_t control;
          uint8_t status;
          uint8_t wheel;
          uint8_t pan;
          struct
          {
              uint8_t flags;
              uint8_t x0, x1, x2;
              uint8_t y0, y1;
          } contact[TABLET_CONTACTS];
      } tablet_t;

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
          xreg 0, 0, 3, addr
      .endmacro

      .struct tablet_t
          control .byte
          status  .byte
          wheel   .byte
          pan     .byte
          contact .struct
              flags .byte
              x0    .byte
              x1    .byte
              x2    .byte
              y0    .byte
              y1    .byte
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
          xreg 0, 0, 3, \addr
      .endm

      TABLET_CONTROL = 0
      TABLET_STATUS  = 1
      TABLET_WHEEL   = 2
      TABLET_PAN     = 3
      TABLET_CONTACT = 4

      TABLET_CONTACT_FLAGS = 0
      TABLET_CONTACT_X0    = 1
      TABLET_CONTACT_X1    = 2
      TABLET_CONTACT_X2    = 3
      TABLET_CONTACT_Y0    = 4
      TABLET_CONTACT_Y1    = 5
      TABLET_CONTACT_SIZE  = 6

      TABLET_SIZE = TABLET_CONTACT + TABLET_CONTACTS * TABLET_CONTACT_SIZE


Gamepads
========

The RIA supports up to four gamepads. :doc:`pico` firmware carries drivers
for Generic HID, XInput, and PlayStation controllers.

Modern gamepads have all converged on the same layout: four face
buttons, a d-pad, dual analog sticks, select, start, and four shoulders.
The face buttons vary only in labeling — XY/AB, YX/BA, or
Square/Triangle/Cross/Circle. Each button reports in the same place
whatever it is called, so that rarely matters to an application until it
prints a button's name, or the buttons stand in for directions.
For those, the DPAD register reports which labeling the gamepad has
when the RIA can be sure of it. You're free to do your own thing, of
course — ask players to use a specific gamepad, or offer an "AB or BA"
option.

Enable and disable the RIA gamepad data by setting its extended
register. The register value is the XRAM start address of the gamepad
data.

.. code-block:: C

  xreg(0, 0, 2, xaddr);    // enable
  xreg(0, 0, 2, 0xFFFF);   // disable
  xreg_ria_gamepad(xaddr); // macro shortcut

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
L2/R2 triggers, so applications can ignore the analog values entirely if
they like.

Some gamepads report only digital data; in that case, code that uses L2
and R2 should expect analog values of just 0 or 255.

Applications taking the simple "one stick and buttons" approach should
merge the d-pad and left stick into a single input.

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

      #define xreg_ria_gamepad(...) xreg(0, 0, 2, __VA_ARGS__)

      typedef struct
      {
          struct
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
          } player[GAMEPAD_PLAYERS];
      } gamepad_t;

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
          xreg 0, 0, 2, addr
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
          xreg 0, 0, 2, \addr
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


Programmable Sound Generator
=============================

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
int-aligned and must not cross a page boundary.

.. code-block:: C

  xreg(0, 1, 0x00, xaddr);  // enable
  xreg(0, 1, 0x00, 0xFFFF); // disable
  xreg_ria_psg(xaddr);      // macro shortcut

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
   * - vol_attack
     - Attack phase volume and rate.

       * bits 7-4 - 0-15 volume attenuation.
       * bits 3-0 - 0-15 attack rate.

   * - vol_decay
     - Decay phase volume and rate.

       * bits 7-4 - 0-15 volume attenuation.
       * bits 3-0 - 0-15 decay rate.

   * - wave_release
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

      #define xreg_ria_psg(...) xreg(0, 1, 0, __VA_ARGS__)

      typedef struct
      {
          struct
          {
              uint16_t freq;
              uint8_t duty;
              uint8_t vol_attack;
              uint8_t vol_decay;
              uint8_t wave_release;
              uint8_t pan_gate;
              uint8_t reserved;
          } channel[PSG_CHANNELS];
      } psg_t;

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
          xreg 0, 1, 0, addr
      .endmacro

      .struct psg_t
          channel .struct
              freq         .word
              duty         .byte
              vol_attack   .byte
              vol_decay    .byte
              wave_release .byte
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
          xreg 0, 1, 0, \addr
      .endm

      PSG_CHANNEL = 0

      PSG_CHANNEL_FREQ         = 0
      PSG_CHANNEL_DUTY         = 2
      PSG_CHANNEL_VOL_ATTACK   = 3
      PSG_CHANNEL_VOL_DECAY    = 4
      PSG_CHANNEL_WAVE_RELEASE = 5
      PSG_CHANNEL_PAN_GATE     = 6
      PSG_CHANNEL_RESERVED     = 7
      PSG_CHANNEL_SIZE         = 8

      PSG_SIZE = PSG_CHANNEL + PSG_CHANNELS * PSG_CHANNEL_SIZE


Yamaha OPL2 FM Sound Generator
==============================

The RIA includes a YM3812 FM Sound Generator (OPL2), configured through
extended register device 0, channel 1, address 0x01.

Enable and disable the OPL2 by setting its extended register. The value
is the XRAM start address for the 256 OPL2 registers, which must begin
on a page boundary. So if xaddr is 0x4200, the 256 OPL2 registers map into
XRAM from 0x4200 to 0x42FF.

.. code-block:: C

  xreg(0, 1, 0x01, xaddr);  // enable
  xreg(0, 1, 0x01, 0xFFFF); // disable
  xreg_ria_opl(xaddr);      // macro shortcut


Timers, interrupts, and the status register are not supported. Those
features existed mainly to cost-reduce consumer devices; computers of
the era had their own timers and rarely used the chip's.

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_ria_opl(...) xreg(0, 1, 1, __VA_ARGS__)

      typedef struct
      {
          uint8_t reg[256];
      } opl_t;

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_ria_opl addr
          xreg 0, 1, 1, addr
      .endmacro

      .struct opl_t
          reg .res 256
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_ria_opl addr
          xreg 0, 1, 1, \addr
      .endm

      OPL_REG  = 0
      OPL_SIZE = 256


Console
=======

The system console is the terminal the RIA and the 6502 talk to, and the
`UART`_ registers above are its rawest form. The OS wraps that same port as
``stdin``, ``stdout``, ``stderr``, and the ``CON:`` and ``TTY:`` device
names. See :doc:`term` for cooked and raw reads, the non-blocking
variants, and the line editor behind them.

Virtual COM Port
================

If you need serial ports beyond the console UART, USB adapters are
available for CMOS/TTL, RS-232, RS-422, and RS-485, and each one appears
as a Virtual COM Port (VCP). :doc:`pico` firmware carries drivers for FTDI,
CP210X, CH34X, PL2303, and CDC ACM.

The ``status`` command lists any connected VCP devices. Open one like a
file, using a special name. By default ``"VCP0:"`` opens at 115200 bps
with 8 data bits, no parity, and 1 stop bit. Set the baud rate with
``"VCP0:115200"``, or the full bit configuration with
``"VCP0:115200,8N1"``. The file won't open if your hardware can't
support the requested configuration, and the open flags are ignored.

.. code-block:: C

  open("VCP0:1200,7E2", 0);
  // then read and write

Generous FIFO buffers serve both directions, and both reads and writes
are non-blocking. Reads can return 0 bytes, and writes may send less than
you asked for — resubmit any remaining bytes on a later call.


MIDI
====

MIDI instruments attached to the machine appear as devices, and the
``status`` command lists them. :doc:`pico` firmware carries a USB MIDI
host driver, so a USB instrument plugs right in. Each virtual cable is
its own device — ``"MIDI0:"`` onward, assigned in the order cables
appear, up to four at a time. A simple keyboard is one cable (1X1); a
multi-port interface is several. Open one like a file.

A cable opens in one of two modes, chosen by the open name. Bare
``"MIDI0:"`` is **raw** — reads and writes are plain wire MIDI, the same
bytes a 5-pin DIN cable carries, with no timing and nothing added or
removed. Give a division instead, ``"MIDI0:480"``, and the cable is
**timed**: the RIA handles timing for you using the event format from
Standard MIDI Files, prefixing every message with a variable length
quantity delta time measured in ticks. The rest of this section is the
timed format.

In timed mode, time starts at the open. The first byte in either
direction is a delta measuring from the open itself, and a delta of zero
means right now. Writes are scheduled — the RIA holds each message and
sends it to the instrument exactly on time, so your program only needs to
keep the buffer fed. Reads are a recording — incoming messages arrive
with delta times measuring when they actually happened, ready to store in
a file or play back later.

The division is ticks per quarter note, the value an SMF carries in its
header. It accepts 1 to 32767 and is fixed while open; reopen between songs
to change it. The open flags are ignored. A cable can be input, output, or both;
reading an output-only cable or writing an input-only one returns an
error.

Tempo changes on the fly with the standard SMF Set Tempo meta event,
which the RIA consumes locally and never forwards to the instrument. The
event is ``FF``, a type, a length, then that many data bytes:

.. list-table::
   :widths: 32 68
   :header-rows: 1

   * - Control event
     - Effect
   * - ``FF 51 03 tt tt tt``
     - Set tempo in microseconds per quarter note — the standard SMF
       event. The tick rate becomes tempo × 1000 ÷ division.
   * - ``FF FF``
     - A wire System Reset. The doubled escape is the whole event, with no
       length byte. Unlike the others, it is sent to the instrument.

Tempo defaults to 500000 µs per quarter note — 120 BPM, a 1041667 ns
tick at 480 PPQN. Every other ``FF`` event, including the rest of the
SMF meta set, is swallowed without effect, so a Standard MIDI File track
plays through nearly verbatim — division from the file header, tempo
events straight from the track:

.. code-block:: C

  open("MIDI0:96", 0); // division from the MThd header
  // FF 51 03 07 A1 20  tempo = 500000 (120 BPM at 96 PPQN)
  // then delta-timed events; the RIA paces them and tracks tempo changes

The RIA echoes every tempo event onto the read stream at the moment it
takes effect, so a recording is self-describing. A rejected event is
malformed, or carries a value of zero or out of range. The RIA echoes it
with its value zeroed and the tempo unchanged; zero is never a valid tempo,
so it unambiguously marks an event that didn't apply. Your read parser must
handle ``FF``: a second ``FF`` is a System Reset, and anything else is
a meta type and length to skip.

The stream carries raw wire MIDI messages after each delta time: channel
voice messages (running status accepted on writes), system common, and
single-byte real-time messages F8-FE. System Reset travels as the
``FF FF`` escape in both directions: write a delta then ``FF FF`` to
send one, and a reset from the instrument is recorded the same way. The
undefined bytes F4 and F5 are quietly dropped.

System Exclusive, or sysex, is how instruments move the big stuff, like
patch banks and sample dumps, in one long message: ``F0``, any number of
data bytes, then ``F7`` to finish. Only the opening ``F0`` takes a delta
time; the data bytes flow without timing until the ``F7``, on writes and
recordings alike. Real MIDI lets real-time messages like clock barge
into the middle of a sysex — the RIA passes them through in place, so
expect the occasional F8-FE byte inside a recorded dump. And if a tempo
echo comes due during a dump, the recording closes the sysex early and
reopens it after — everything arrives, just split into two
``F0`` ... ``F7`` fragments.

Delta times measure from the previous event, so timing stays exact over
any song length. Events are anchored to an absolute tick count, and
ticks are kept internally in nanoseconds, holding arithmetic rounding
below one part per million. The error left over comes from the machine's
clock and transport. Where the RIA is paced by a crystal-driven microsecond
timer and delivers over USB full speed, the crystal drifts single-digit
milliseconds over a several-minute song and framing sets the
moment-to-moment jitter near one millisecond — the same pace as the
classic MIDI wire itself.

If your program stops feeding the buffer and resumes, messages already
past due play immediately and the timeline continues from there. If you
stop reading, the recording drops whole messages rather than backing up,
and the timing of everything that survives stays exact. Reads and writes
are non-blocking with the same short read/write rules as other
non-blocking devices.

Closing a timed output cable blocks until its buffered tail has played
out on schedule. The final notes reach the instrument before close returns,
along with the note-offs that end them, and nothing is left ringing.
``sync`` does the same without closing. It waits for the schedule to catch
up between songs. Both follow the timeline, so a far-future delta
still in the buffer makes them wait that long. If a sysex is still open
when a timed cable closes, the RIA sends its ``F7`` so the instrument is
not left waiting mid-dump. A raw cable has no schedule, so close and
``sync`` flush what is buffered, and they inject no ``F7``.


Near Field Communications (NFC)
===============================

NFC cards have become a popular media replacement in the retro
community, and they map neatly onto the RP6502's use of "ROM files" in
place of "ROM cartridges". In 1983 you might have grabbed a cartridge
with colorful stickers to home in on the exact dopamine hit you were
after. NFC cards are cheap and just as easy to decorate, whether with
stickers or direct printing. Grab a card, tap it on the reader, and the
ROM you want loads instantly.

You'll need a PN532 card reader with a USB interface. It's the only
reader RIA firmware drives, and it's cheap — around $10 USD. You'll also want a
card (or fob, or sticker) for each ROM you plan to support. New to NFC?
Buy a pack of NTAG215 cards and a sharpie.

Do **not** buy a kit of separate USB-to-UART and PN532 boards unless you
want an unsupported project on your hands. Buy a single board with
everything already engineered and ready to use.

With the reader plugged in, run the monitor command ``SET NFC 2`` to
start USB detection. It may probe your other VCP devices with PN532 data
along the way; that's normal. You'll hear an error buzz, or two beeps for
success. You can also run ``status`` to see whether ``(NFC)`` is listed
next to one of your VCP devices.

``SET NFC 1`` turns the reader on and ``SET NFC 0`` turns it off; the
choice persists across reboots (a successful ``SET NFC 2`` also leaves it
on). ``SET NFC 86`` forgets the paired reader so a later ``SET NFC 2`` can
pair a different one.

From now on, scanning a card produces one of three sounds: an error buzz
if something went wrong, two beeps for success, or a single beep for a
partial success.

Program each card with the filename and arguments of the ROM to launch.
If you'd load the ROM with ``LOAD /jigsaw.rp6502``, put an NDEF TEXT
record on the card holding just ``/jigsaw.rp6502`` — no load command. A
card may also name an installed ROM, ``:NAME``, which skips the drive
scan below. The machine either has it or the tap fails. A leading ``/``
is implied if you leave it off, and the current working directory is
ignored.

Paths with spaces need quotes, and you can include arguments:
``"/My Games/jigsaw.rp6502" cat.bmp``

When a card is read, every mounted drive is scanned for the ROM file. On
a match, you get two beeps, the 6502 stops, the current drive and
directory switch to the ROM's location, and the new ROM starts loading.
If that ROM is already running, you get a single beep and nothing else
happens.

To search just one drive, name it in the text record:
``MSC0:/encabulator.rp6502``

NFC Device API
--------------

Applications can take over the NFC reader for advanced uses, or to help
program NFC tags. While the ``"NFC:"`` device is open, automatic ROM
launching is suppressed.

.. code-block:: text

   int fd = open("NFC:", O_RDWR);

The PN532 reader runs autonomously on the RIA. The 6502 arms operations
with ``write()`` and polls results with ``read()``: ``NFC_CMD_READ``
returns the current tag data immediately, ``NFC_CMD_WRITE`` arms a write,
and ``NFC_CMD_CANCEL`` disarms a pending one. State changes and write
completions are posted to ``read()`` automatically.

write() -- Commands
~~~~~~~~~~~~~~~~~~~

``write()`` is non-blocking and streaming. A call may consume less than
you passed; resubmit the remaining bytes on a later call.

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Byte
     - Command
   * - ``NFC_CMD_WRITE`` (0x01), page, lenLo, lenHi, tag data...
     - Arm a write
   * - ``NFC_CMD_CANCEL`` (0x02)
     - Disarm pending write
   * - ``NFC_CMD_READ`` (0x03)
     - Return current tag data
   * - ``NFC_CMD_SUCCESS1`` (0x04)
     - Play success tone 1
   * - ``NFC_CMD_SUCCESS2`` (0x05)
     - Play success tone 2
   * - ``NFC_CMD_ERROR`` (0x06)
     - Play error tone

The ``NFC_CMD_WRITE`` payload starts with the start page, a two-byte
length, then the tag data. ``page`` is the NTAG page to begin writing at
(page 4 is the start of user data). Data is written in 4-byte pages, and
the final page is zero-padded if the payload isn't a multiple of 4. The
write arms once the full payload arrives and runs on the current card or
the next one presented. A second ``NFC_CMD_WRITE`` overwrites the first.

The payload may be at most 888 bytes; a longer length is rejected with the
error tone and never armed. A write also fails (error tone) if it would run
past the card's NDEF data area or target a page below 4, and a zero-length
payload completes immediately as a no-op.

``NFC_CMD_READ`` always returns ``NFC_RESP_READ`` on the next ``read()``;
if no card data is available, the length is zero.

read() -- Responses
~~~~~~~~~~~~~~~~~~~

``read()`` is non-blocking and streaming. It returns 0 bytes when there's
nothing new. Responses may be split across multiple calls, so callers
must buffer and reassemble them. State changes are sent once per change,
including once right after ``open()``. Only the latest state is tracked, so
a rapid transition (such as ``NFC_RESP_CARD_INSERTED`` immediately followed
by ``NFC_RESP_CARD_READY``) may be coalesced to the later state if you don't
``read()`` in between.

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Byte
     - Meaning
   * - ``NFC_RESP_READ`` (0x01), lenLo, lenHi, tag data...
     - Read result
   * - ``NFC_RESP_WRITE`` (0x02)
     - Armed write complete
   * - ``NFC_RESP_NO_READER`` (0x03)
     - State: no reader attached
   * - ``NFC_RESP_NO_CARD`` (0x04)
     - State: no card present
   * - ``NFC_RESP_CARD_INSERTED`` (0x05)
     - State: card present, tag data not ready
   * - ``NFC_RESP_CARD_READY`` (0x06)
     - State: card present, tag data ready

The ``NFC_RESP_READ`` payload is a two-byte length followed by raw tag
data starting at page 0, and it may span multiple ``read()`` calls.
In the page layout, pages 0-2 are UID/lock bytes, page 3 is the Capability
Container (CC[2] * 8 = max NDEF bytes), and pages 4+ are user data
(TLV-wrapped NDEF records terminated with ``0xFE``).

After ``NFC_RESP_READ`` or ``NFC_RESP_WRITE``, send one or more tone
commands or play your own sounds. Typically you request reads on
``NFC_RESP_CARD_READY`` and arm writes on ``NFC_RESP_NO_CARD``, but you
can also arm a write after reading and verifying a card. The cached
tag image is not refreshed by a write, so re-present the card before the
next ``NFC_CMD_READ`` if you want to read back what you wrote.


Peripheral Information Exchange (PIX)
=====================================

None of this is needed to program the machine. What follows is the bus
itself, for anyone building a device to put on it.

High-bandwidth devices like video systems need a bus of their own. PIX
is that bus: an addressable broadcast system that any number of devices
can listen to, narrow enough to fit the GPIO budget of a Raspberry Pi
Pico, wide enough to move data as fast as the 6502 writes.

Physical layer
--------------

The signals are PHI2 and PIX0-3. This is a double-data-rate bus. It
shifts PIX0-3 left on both transitions of PHI2, so a 32-bit frame travels
in just 4 PHI2 cycles. On an :doc:`pico` a PIO block decodes it, since
PIO is essentially a shift register.

Bit 28 (0x10000000) is the framing bit, set in every message. When the
bus is idle, an all-zero payload repeats on device ID 7. A receiver
synchronizes by checking that PIX0 is high on a falling transition of
PHI2; if it isn't, stall until the next clock cycle.

Bits 31-29 (0xE0000000) carry the device ID for a message:

- **Device 0** — the RIA. It's also overloaded to broadcast XRAM.
- **Device 1** — the :doc:`vga`.
- **Devices 2-6** — open for user expansion.
- **Device 7** — synchronization. (0xF0000000 is hard to miss on test
  equipment.)

The remaining bits address a register within a device:

- **Bits 27-24** (0x0F000000) — the channel ID; each device can have 16
  channels.
- **Bits 23-16** (0x00FF0000) — the register address within that channel.
- **Bits 15-0** (0x0000FFFF) — the value to store in the register.

PIX Extended RAM (XRAM)
-----------------------

The RIA broadcasts every change to its 64 KB of XRAM on PIX device 0.
Bits 15-0 carry the XRAM address; bits 23-16 carry the XRAM data.

Each PIX device keeps a local replica of the XRAM it uses. Typically all
64 KB is replicated, and an XREG set by a 6502 application installs
virtual hardware at some location in XRAM.

.. _ria-xreg:

PIX Extended Registers (XREG)
-----------------------------

PIX devices may use bits 27-0 however they like. The suggested split
is:

- **Bits 27-24** — a channel. The RIA, for example, has separate channels
  for audio, keyboard, mice, and so on.
- **Bits 23-16** — an extended register address.
- **Bits 15-0** — the value to store.

That gives seven PIX devices, each with 16 channels of 256 16-bit
registers. The idea is to use these extended registers to configure
virtual hardware and map it into extended memory.
