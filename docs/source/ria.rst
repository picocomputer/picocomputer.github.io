====================
RP6502-RIA
====================

RP6502 - RP6502 Interface Adapter


Introduction
============

The RP6502 Interface Adapter (RIA) is a Raspberry Pi Pico 2 running
RP6502-RIA firmware. It provides every essential service a WDC W65C02S
microprocessor needs to run.

The RIA must live at $FFE0-$FFFF and must control RESB and PHI2. Those
are the only hard requirements — everything else about your Picocomputer
is yours to customize. Even the :doc:`vga` is optional.

A fresh RIA boots into the RP6502 monitor. The easiest way to get started
is the standard setup: a :doc:`vga` module for the display and a USB
keyboard plugged into the RIA. The monitor runs on the console, which
isn't tied to any single device — other terminals fan in through the
`console manifold <term.html#console-manifold>`__, including USB serial,
telnet, and the RIA's bare UART pins (115200 8N1). The monitor itself is
documented here only by a few common commands — its built-in help is
extensive and always current. Type ``help`` to get started, then dig into
deep help like ``help set phi2``.

The RP6502 monitor is not an operating-system shell; think of it more
like a UEFI shell. Its main job is loading ROMs, with just enough
hardware and locale configuration to get going — kept deliberately
minimal.

Use the ``load`` command to load ROMs in ``.rp6502`` format. These
aren't ROMs in the traditional (obsolete) sense: a ROM here is a file
holding a memory image that's loaded into RAM before the 6502 starts.
The RIA has 1 MB of flash you can ``install`` ROMs into. Once installed,
a ROM can be run directly, or you can ``set boot`` to load it whenever
the RIA boots.

A few monitor commands, such as ``upload`` and ``binary``, exist for
developer tools. The ``rp6502.py`` script that ships with the examples
and templates automates ROM packaging and execution.


Reset
=====

Think of reset as two states rather than a pulse on RESB. While reset
is low, the 6502 is stopped and the console talks to the RP6502 monitor.
While reset is high, the 6502 runs and the console manifold connects to both
the :doc:`os` and the UART TX/RX registers described below.

To bring reset from low to high, either ``load`` a ROM that has a reset
vector, or use the ``reset`` command if you've prepared RAM some other
way.

To drop reset from high to low and return to the monitor — even from a
crashed or halted 6502 — use any terminal on the `console manifold
<term.html#console-manifold>`__:

1. Press Alt-F4 or Ctrl-Alt-Del from a keyboard.
2. Send a break from a serial terminal.
3. Send a break from a telnet terminal.

.. caution::

   Don't wire a physical button to RESB — the RIA must stay in control
   of it. What you probably want is the reset driven by the RIA RUN pin,
   which we call a ``reboot``. The reference hardware's reboot button is
   wired to the RIA RUN pin, and rebooting this way loads any configured
   boot ROM, just like at power-on. Resetting the 6502 from a terminal
   only returns you to the RP6502 monitor.


Registers
=========

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
     - Always $80 (the BRA opcode). JSR here (``RIA_SPIN``) to spin-wait
       for an OS call: the CPU loops on this BRA until BUSY clears, then
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

UART
----

The RIA's UART RX/TX pins are directly accessible at $FFE0-$FFE2. The
ready flags on bits 6-7 let you test with the BIT operator. Use these or
the :doc:`os` stdio — but not both at once: driving the UART directly
while a stdio OS function is in progress is undefined behavior. The UART
runs at 115200 bps, 8-bit words, no parity, 1 stop bit.

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

Extended Stack (XSTACK)
-----------------------

This is a 512-byte, top-down, last-in-first-out stack used by the
fastcall mechanism described in the :doc:`os`. Reading past the end is
guaranteed to return zeros. Write to push, read to pull.

Extended Registers (XREG)
-------------------------

The RIA is both the host of the PIX bus (documented below) and device 0
on it.

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
  * - $0:1:00
    - PSG
    - See `Programmable Sound Generator`_ section


Pico Information Exchange (PIX)
===============================

The Raspberry Pi Pico has only so many GPIO pins, so high-bandwidth
devices like video systems needed a bus of their own. PIX is that bus:
an addressable broadcast system that any number of devices can listen
to.

Physical layer
--------------

The Pico's PIO decodes the physical layer easily, since PIO is
essentially a shift register. The signals are PHI2 and PIX0-3. This is a
double-data-rate bus: it shifts PIX0-3 left on both transitions of PHI2,
so a 32-bit frame travels in just 4 PHI2 cycles.

Bit 28 (0x10000000) is the framing bit, set in every message. When the
bus is idle, an all-zero payload repeats on device ID 7. A receiver
synchronizes by checking that PIX0 is high on a falling transition of
PHI2; if it isn't, stall until the next clock cycle.

Bits 31-29 (0xE0000000) carry the device ID for a message:

- **Device 0** — the RIA. It's also overloaded to broadcast XRAM.
- **Device 1** — the :doc:`vga`.
- **Devices 2-6** — open for user expansion.
- **Device 7** — synchronization. (0xF0000000 is hard to miss on test equipment.)

The remaining bits address a register within a device:

- **Bits 27-24** (0x0F000000) — the channel ID; each device can have 16 channels.
- **Bits 23-16** (0x00FF0000) — the register address within that channel.
- **Bits 15-0** (0x0000FFFF) — the value to store in the register.

PIX Extended RAM (XRAM)
-----------------------

The RIA broadcasts every change to its 64 KB of XRAM on PIX device 0.
Bits 15-0 carry the XRAM address; bits 23-16 carry the XRAM data.

Each PIX device keeps a local replica of the XRAM it uses. Typically all
64 KB is replicated, and an XREG set by a 6502 application installs
virtual hardware at some location in XRAM.

PIX Extended Registers (XREG)
-----------------------------

PIX devices may use bits 27-0 however they like. The suggested split
is:

- **Bits 27-24** — a channel. The RIA, for example, has separate channels for audio, keyboard, mice, and so on.
- **Bits 23-16** — an extended register address.
- **Bits 15-0** — the value to store.

That gives seven PIX devices, each with 16 channels of 256 16-bit
registers. The idea is to use these extended registers to configure
virtual hardware and map it into extended memory.


Keyboard
========

The RIA can hand applications direct access to keyboard data, which is
what you want when you need key-up and key-down events or the modifier
keys. If you don't need that, the UART or stdin works just as well.

Enable and disable direct keyboard access by mapping it to an address
in XRAM.

.. code-block:: C

  xreg(0, 0, 0x00, xaddr);  // enable
  xreg(0, 0, 0x00, 0xFFFF); // disable
  xreg_ria_keyboard(xaddr); // macro shortcut

The RIA continuously updates XRAM with a bit array of USB HID keyboard
keycodes — note these are HID keycodes, not PS/2 scancodes. Each keycode
is one bit in the array: bit N is 1 while the key with HID keycode N is
pressed. The first four keycodes are special:

- 0 - No key pressed
- 1 - Num Lock on
- 2 - Caps Lock on
- 3 - Scroll Lock on

.. code-block:: C

  uint8_t keyboard[32];
  #define key(code) (keyboard[code >> 3] & \
                    (1 << (code & 7)))


Mouse
=====

The RIA can give applications direct access to mouse data. Enable and
disable it by mapping it to an address in XRAM.

.. code-block:: C

  xreg(0, 0, 0x01, xaddr);  // enable
  xreg(0, 0, 0x01, 0xFFFF); // disable
  xreg_ria_mouse(xaddr);    // macro shortcut

This sets the XRAM address of a structure holding the live mouse input.

.. code-block:: C

  struct {
      uint8_t buttons;
      uint8_t x;
      uint8_t y;
      uint8_t wheel;
      uint8_t pan;
  } mouse;

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


Gamepads
========

The RIA supports up to four gamepads, with drivers for Generic HID,
XInput, and PlayStation controllers.

Modern gamepads have all converged on the same layout: four face
buttons, a d-pad, dual analog sticks, select, start, and four shoulders.
The face buttons vary only in labeling — XY/AB, YX/BA, or
Square/Triangle/Cross/Circle. That rarely matters to an application
unless the buttons stand in for directions, in which case the
Square/Triangle/Cross/Circle and XY/AB arrangements are "the official"
RP6502 layout. You're free to do your own thing, of course — ask players
to use a specific gamepad, or offer an "AB or BA" option.

.. note::
   **The RP6502 expects modern gamepads.**

   The RP6502 is not an emulation platform. Sega, NES, SNES, TG16, Atari,
   and other retro-style gamepads are **not supported**.

   Retro-style gamepads are wired with button mappings meant for emulators,
   and emulators in turn expect the layout of a modern gamepad. The two
   don't cancel out — you just end up with wonky mappings that don't follow
   the de facto modern standard.

Enable and disable the RIA gamepad data by setting its extended
register. The register value is the XRAM start address of the gamepad
data; any invalid address disables the gamepads.

.. code-block:: C

  xreg(0, 0, 2, xaddr);    // enable
  xreg(0, 0, 2, 0xFFFF);   // disable
  xreg_ria_gamepad(xaddr); // macro shortcut

The RIA continuously updates extended memory with gamepad state. The
10-byte structure below repeats four times — 40 bytes total, one block
per gamepad.

The upper bits of the DPAD register report readiness and type. The
connected bit is high when a gamepad occupies that player slot. The Sony
bit indicates a PlayStation-style gamepad with
Circle/Cross/Square/Triangle faces.

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
       * bit 4: Reserved
       * bit 5: Reserved
       * bit 6: Sony button faces
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


Programmable Sound Generator
=============================

The RIA includes a Programmable Sound Generator (PSG), configured
through extended register device 0, channel 1, address 0x00.

* Eight 24 kHz 8-bit oscillator channels.
* Five waveforms: Sine, Square, Sawtooth, Triangle, Noise.
* ADSR envelope: Attack, Decay, Sustain, Release.
* Stereo panning.
* PWM for all waveforms.

Each of the eight oscillators uses eight bytes of XRAM for
configuration. The structure size is a power of two, so indexing into
the oscillator array is a bit shift rather than a multiply.

.. code-block:: C

  typedef struct
  {
      unsigned int freq;
      unsigned char duty;
      unsigned char vol_attack;
      unsigned char vol_decay;
      unsigned char wave_release;
      unsigned char pan_gate;
      unsigned char unused;
  } ria_psg_t;

Enable and disable the PSG by setting its extended register. The value
is the XRAM start address for the 64 bytes of config; it must be
int-aligned and must not cross a page boundary. Any invalid address
disables the PSG.

.. code-block:: C

  xreg(0, 1, 0x00, xaddr); // enable
  xreg(0, 1, 0x00, 0xFFFF); // disable

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


Yamaha OPL2 FM Sound Generator
==============================

The RIA includes a YM3812 FM Sound Generator (OPL2), configured through
extended register device 0, channel 1, address 0x01.

Enable and disable the OPL2 by setting its extended register. The value
is the XRAM start address for the 256 OPL2 registers, which must begin
on a page boundary.

.. code-block:: C

  xreg(0, 1, 0x01, xaddr); // enable
  xreg(0, 1, 0x01, 0xFFFF); // disable

So if xaddr is 0x4200, the 256 OPL2 registers map into XRAM from 0x4200
to 0x42FF.

Timers, interrupts, and the status register are not supported. Those
features existed mainly to cost-reduce consumer devices; computers of
the era had their own timers and rarely used the chip's.

Console Port
============

The RIA's main serial port is the system console. Modern operating
systems layer canonical input and translated output over something
configurable like termios. A full termios is too heavy for an 8-bit
system, but raw and non-blocking I/O still need to be on the table.

The familiar stdin blocks for canonical input: the console user edits a
line, and once they press Enter the stdin read unblocks and returns the
line up to a linefeed.

The familiar stdout and stderr block too, inserting a carriage return
before any newline that lacks one. All of the data is always sent, and
writes block until it has fully drained into the hardware FIFOs.

These interfaces are exactly what a C programmer expects, but they're a
poor fit for a multitasking 6502 program. For that, a non-blocking
interface is available: open the special filename ``"CON:"``. Reads can
return 0 bytes, and writes may send less than you asked for.

Going one step further, the special filename ``"TTY:"`` gives a
non-blocking, raw connection to the console port — no canonical input,
no newline translation. It's exactly what the ``RIA_TX`` and ``RIA_RX``
registers provide, just packaged as stdio for convenience.

``"CON:"`` and ``"TTY:"`` are each locked to their own file descriptor,
which cannot be closed. A second open returns the same file descriptor
as the first, and a close succeeds as a no-op.

Virtual COM Port
================

If you need serial ports beyond the console UART, USB adapters are
available for CMOS/TTL, RS-232, RS-422, and RS-485. The RIA includes
drivers for FTDI, CP210X, CH34X, PL2303, and CDC ACM, and each one
appears as a Virtual COM Port (VCP).

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


Near Field Communications (NFC)
===============================

NFC cards have become a popular media replacement in the retro
community, and they map neatly onto the RP6502's use of "ROM files" in
place of "ROM cartridges". In 1983 you might have grabbed a cartridge
with colorful stickers to home in on the exact dopamine hit you were
after. NFC cards are cheap and just as easy to decorate, whether with
stickers or direct printing. Grab a card, tap it on the reader, and the
ROM you want loads instantly. Here's how it works.

You'll need a PN532 card reader with a USB interface. It's the only
reader supported, and it's cheap — around $10 USD. You'll also want a
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

From now on, scanning a card produces one of three sounds: an error buzz
if something went wrong, two beeps for success, or a single beep for a
partial success.

Program each card with the filename and arguments of the ROM to launch.
If you'd load the ROM with ``LOAD /jigsaw.rp6502``, put an NDEF TEXT
record on the card holding just ``/jigsaw.rp6502`` — no load command. A
leading ``/`` is implied if you leave it off, and the current working
directory is ignored.

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
the next one presented. A second ``NFC_CMD_WRITE`` overwrites the first —
last write wins.

``NFC_CMD_READ`` always returns ``NFC_RESP_READ`` on the next ``read()``;
if no card data is available, the length is zero.

read() -- Responses
~~~~~~~~~~~~~~~~~~~

``read()`` is non-blocking and streaming. It returns 0 bytes when there's
nothing new. Responses may be split across multiple calls, so callers
must buffer and reassemble them. State changes are sent once per change,
including once right after ``open()``.

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
data starting at page 0, and it may span multiple ``read()`` calls. The
page layout is: pages 0-2 are UID/lock bytes, page 3 is the Capability
Container (CC[2] * 8 = max NDEF bytes), and pages 4+ are user data
(TLV-wrapped NDEF records terminated with ``0xFE``).

After ``NFC_RESP_READ`` or ``NFC_RESP_WRITE``, send one or more tone
commands or play your own sounds. Typically you request reads on
``NFC_RESP_CARD_READY`` and arm writes on ``NFC_RESP_NO_CARD``, but you
can also arm a write after reading and verifying a card. The state
changes give you flexibility in how you sequence operations.


ROM File Format
===============

A ROM file begins with a shebang line, followed by any number of assets.
Text lines end with ``\r``, ``\n``, or both, and numbers may be written
in decimal (255), C-style hex (0xFF), or MOS-style hex ($FF).

**Shebang** — first line of every ROM file:

.. code-block:: text

  #!RP6502

**Null-named asset** — a group of memory chunks loaded directly into RAM:

.. code-block:: text

  #>len crc

Followed by one or more memory chunks, each a header line plus ``len``
bytes of raw binary data:

.. code-block:: text

  addr len crc

.. list-table::
   :widths: 1 20
   :header-rows: 1

   * - Field
     - Description
   * - ``addr``
     - Destination address in 6502 RAM (0x0000-0xFEFF) or XRAM
       (0x10000-0x1FFFF).
   * - ``len``
     - Number of raw binary bytes that immediately follow this line.
   * - ``crc``
     - CRC of the binary payload (checked).

**Named asset** — a raw binary blob identified by name:

.. code-block:: text

  #>len crc name

Followed immediately by ``len`` bytes of raw binary data. Assets repeat
until end of file.

.. list-table::
   :widths: 1 20
   :header-rows: 1

   * - Field
     - Description
   * - ``len``
     - Number of raw binary bytes that immediately follow this line.
   * - ``crc``
     - CRC of the binary payload (ignored by RIA).
   * - ``name``
     - Asset identifier string.

The ``rp6502.py`` tool that comes with the new-project templates handles
these details and integrates with CMake, so adding assets is
straightforward. In this example the image data is packed into the ROM
as memory chunks that load into RAM or XRAM when the ROM loads:

.. code-block:: cmake

  rp6502_asset(your_project 0x10000 img/intro.bin)

A ROM can also hold named assets of raw data, and some names are
special — the ``help`` asset is shown by the HELP and INFO monitor
commands.

.. code-block:: cmake

  rp6502_asset(your_project help src/help.txt)

While a ROM runs, its assets become part of the filesystem. Prefix the
asset name with "ROM:" and open it like any other file. ROM assets are
read-only, but you can have several open at once.

.. code-block:: C

  open("ROM:help", O_RDONLY)

There's no enforced limit on the number or size of named assets. Opening
a file is a linear search; it skips over the data, but how many seeks and
string compares your application can tolerate is up to you.
