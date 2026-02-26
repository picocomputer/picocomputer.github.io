====================
RP6502-RIA
====================

RP6502 - RP6502 Interface Adapter


Introduction
============

The RP6502 Interface Adapter (RIA) is a Raspberry Pi Pico 2 with
RP6502-RIA firmware. The RIA provides all essential services to
support a WDC W65C02S microprocessor.

The RIA must be installed at $FFE0-$FFFF and must be in control of
RESB and PHI2. These are the only requirements. Everything else about
your Picocomputer can be customized. Even the :doc:`vga` is optional.

A new RIA boots to the RP6502 monitor, accessible from the console in
one of three ways: from a VGA monitor with a USB or Bluetooth keyboard
when using a :doc:`vga`; from the USB CDC device the :doc:`vga`
presents when plugged into a host PC; or from the UART RX/TX
(115200 8N1) pins on the RIA when not using a :doc:`vga`. The monitor
is not documented here beyond a few common commands. The built-in help
is extensive and always up-to-date. Type ``help`` to get started, and
explore deep help such as ``help set phi2``.

The RP6502 monitor is not an operating system shell - it is analogous to a
UEFI shell. Its primary purpose is loading ROMs, with a small amount of
hardware and locale configuration kept intentionally minimal.

Use the ``load`` command to load ROMs in .rp6502 format.
These aren't ROMs in the traditional (obsolete) sense. A ROM is a file
that contains a memory image to be loaded in RAM before starting the
6502. The RIA includes 1MB of flash which you can ``install`` ROMs to.
Once a ROM is installed, you can run it directly or ``set boot`` so it
loads when the RIA boots.

Some monitor commands, such as ``upload`` and ``binary``, target
developer tools. The rp6502.py script, included with the examples and
templates, automates ROM packaging and execution.


Reset
=====

Think of reset as two states, not a pulse on RESB. When reset is low,
the 6502 is stopped and the console connects to the RP6502 monitor.
When reset is high, the 6502 runs and the console connects to both
stdio in the :doc:`os` and the UART TX/RX registers described below.

If you want to move reset from low to high, either ``load`` a ROM with
a reset vector, or use the ``reset`` command if you have prepared RAM
some other way.

To move reset from high to low and return to the monitor, even with a
crashed or halted 6502, you have two options:

1. Using a Bluetooth or USB keyboard, press CTRL-ALT-DEL.
2. Send a break to the RIA UART.

.. warning::

   Do not hook up a physical button to RESB. The RIA must remain
   in control of RESB. What you probably want is the reset that happens
   from the RIA RUN pin. We call this a ``reboot``. The reference hardware
   reboot button is hooked up to the RIA RUN pin. Rebooting the RIA
   like this will cause any configured boot ROM to load, like at power
   on. Resetting the 6502 from keyboard or UART will only return you to
   the RP6502 console.


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
     - Increments every 1/60 second when PIX VGA device 1 is
       connected.
   * - $FFE4
     - RW0
     - Read or write the XRAM referenced by ADDR0.
   * - $FFE5
     - STEP0
     - Signed byte added to ADDR0 after every access to RW0.
   * - | $FFE6 -
       | $FFE7
     - ADDR0
     - Address of XRAM for RW0.
   * - $FFE8
     - RW1
     - Read or write the XRAM referenced by ADDR1.
   * - $FFE9
     - STEP1
     - Signed byte added to ADDR1 after every access to RW1.
   * - | $FFEA -
       | $FFEB
     - ADDR1
     - Address of XRAM for RW1.
   * - $FFEC
     - XSTACK
     - 512 bytes for OS call stack.
   * - $FFED
     - ERRNO_LO
     - Low byte of errno. All errors fit in this byte.
   * - $FFEE
     - ERRNO_HI
     - Ensures errno is optionally a 16-bit int.
   * - $FFEF
     - OP
     - Write the OS operation id here to begin an OS call.
   * - $FFF0
     - IRQ
     - Set bit 0 high to enable VSYNC interrupts. To clear the
       interrupt, first verify the source by checking the VSYNC
       counter, then read or write this register.
   * - $FFF1
     - RETURN
     - Always $80 (the BRA opcode). JSR here to spin-wait for an
       OS call: the CPU loops on this BRA until BUSY clears, then
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

Easy and direct access to the UART RX/TX pins of the RIA is
available from $FFE0-$FFE2. The ready flags on bits 6-7 enable testing
with the BIT operator. You may choose to use these or stdio
from the :doc:`os`. Using the UART directly while a stdio
OS function is in progress will result in undefined behavior.
The UART hardware runs at 115200 bps, 8 bit words, no parity, 1 stop bit.

Extended RAM (XRAM)
-------------------

RW0 and RW1 are two portals to the same 64K XRAM. Having only one
portal would make moving XRAM very slow since data would have to
buffer in 6502 RAM. Ideally, you won't move XRAM and can use the pair
for better optimizations.

STEP0 and STEP1 default to 1 after reset. Both are signed, so
negative values traverse XRAM in reverse. These auto-increment
adders enable very fast sequential access, which more than offsets
the slightly slower random access compared to 6502 system RAM.

Extended Stack (XSTACK)
-----------------------

This is 512 bytes of last-in, first-out, top-down stack used for the
fastcall mechanism described in the :doc:`os`. Reading past the end
is guaranteed to return zeros. Simply write to push and read to pull.

Extended Registers (XREG)
-------------------------

The RIA is both the host of the PIX bus (documented below)
and device 0 on the PIX bus.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:0:00
    - KEYBOARD
    - See Keyboard section
  * - $0:0:01
    - MOUSE
    - See Mouse section
  * - $0:0:02
    - GAMEPADS
    - See Gamepads section
  * - $0:1:00
    - PSG
    - See Programmable Sound Generator section


Pico Information Exchange (PIX)
===============================

The limited number of GPIO pins on the Raspberry Pi Pico required
creating a new bus for high bandwidth devices like video systems. This
is an addressable broadcast system which any number of devices can
listen to.

Physical layer
--------------

Pi Pico PIO decodes the physical layer easily - PIO is essentially a
shift register. The signals are PHI2 and PIX0-3. This double data rate
bus shifts PIX0-3 left on both transitions of PHI2. A frame is 32 bits
transmitted over 4 PHI2 cycles.

Bit 28 (0x10000000) is the framing bit, set in every message. An
all-zero payload repeats on device ID 7 when the bus is idle. A
receiver synchronizes by ensuring PIX0 is high on a low transition of
PHI2; if not, stall until the next clock cycle.

Bits 31-29 (0xE0000000) indicate the device ID number for a message.

Device 0 is allocated to the RIA. Device 0 is also overloaded to
broadcast XRAM.

Device 1 is allocated to :doc:`vga`.

Devices 2-6 are available for user expansion.

Device 7 is used for synchronization. Because 0xF0000000 is hard to
miss on test equipment.

Bits 27-24 (0x0F000000) indicate the channel ID number for a message.
Each device can have 16 channels.

Bits 23-16 (0x00FF0000) indicate the register address in the channel
on the device.

Bits 15-0 (0x0000FFFF) is a value to store in the register.

PIX Extended RAM (XRAM)
-----------------------

The RIA broadcasts all changes to its 64KB of XRAM to PIX device 0.
Bits 15-0 carry the XRAM address. Bits 23-16 carry the XRAM data.

PIX devices maintain a local replica of the XRAM they use. Typically,
all 64K is replicated and an XREG set by a 6502 application will
install virtual hardware at a location in XRAM.

PIX Extended Registers (XREG)
-----------------------------

PIX devices may use bits 27-0 however they choose. The suggested
division of these bits is:

Bits 27-24 indicate a channel. For example, the RIA device has a
channel for audio, a channel for keyboard, a channel for mice, and so
on. Bits 23-16 contain an extended register address. Bits 15-0 contain
the value to be stored.

So we have seven PIX devices, each with 16 internal channels having 256
16-bit registers. The idea is to use these extended registers to
configure virtual hardware and map it into extended memory.


Keyboard
========

The RIA can provide direct access to keyboard data. This is intended
for applications that need to detect both key up and down events or the
modifier keys. You may instead use the UART or stdin if you don't need
this kind of direct access.

Enable and disable direct keyboard access by mapping it to an address
in XRAM.

.. code-block:: C

  xreg(0, 0, 0x00, xaddr);  // enable
  xreg(0, 0, 0x00, 0xFFFF); // disable
  xreg_ria_keyboard(xaddr); // macro shortcut

The RIA continuously updates XRAM with a bit array of USB HID
keyboard keycodes. Note that these are not PS/2 scancodes.
Each keycode is one bit in the array — bit N is 1 when the key
with HID keycode N is currently pressed. The first four keycodes
have special meaning:

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

The RIA can provide direct access to mouse information. Enable and
disable by mapping it to an address in XRAM.

.. code-block:: C

  xreg(0, 0, 0x01, xaddr);  // enable
  xreg(0, 0, 0x01, 0xFFFF); // disable
  xreg_ria_mouse(xaddr);    // macro shortcut

This sets the address in XRAM for a structure containing direct
mouse input.

.. code-block:: C

  struct {
      uint8_t buttons;
      uint8_t x;
      uint8_t y;
      uint8_t wheel;
      uint8_t pan;
  } mouse;

Compute movement by subtracting the previous value from the current
value. Vsync timing (60 Hz) is period-correct but too slow by modern
standards. For precise mouse input, use an ISR at 8 ms or faster
(125 Hz).

Applications should account for canvas resolution when interpreting
movement. At 640x480 and 640x360, one unit equals one pixel. At
320x240 and 320x180, two units equal one pixel.

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

The RIA supports up to four gamepads. There are drivers for Generic HID,
XInput, and Playstation gamepads.

Modern gamepads have all evolved to the same four face buttons, d-pad,
dual analog sticks, select, start, and quad shoulders. The minor variations
of the four face buttons are XY/AB, YX/BA, or Square/Triangle/Cross/Circle.
This is generally of no consequence to the application unless those buttons
are intended to represent a direction. In that case, the
Square/Triangle/Cross/Circle and XY/AB layouts are "the official" layout
of the RP6502. You can, of course, do your own thing and request players
use a specific gamepad or include a "AB or BA" option.

.. attention::
   **The RP6502 expects modern gamepads.**

   The RP6502 is not an emulation platform. Sega, NES, SNES, TG16, Atari,
   and other retro-style gamepads are **not supported**.

   Retro-style gamepads are designed with button mappings for emulators while
   emulators expect the button layout of a modern gamepad. These do not cancel
   each other out. Instead, you end up with wonky button mappings that do not
   follow the de facto standard for modern gamepads.

Enable and disable access to the RIA gamepad XRAM registers by setting
the extended register. The register value is the XRAM start address of
the gamepad data. Any invalid address disables the gamepads.

.. code-block:: C

  xreg(0, 0, 2, xaddr);    // enable
  xreg(0, 0, 2, 0xFFFF);   // disable
  xreg_ria_gamepad(xaddr); // macro shortcut

The RIA continuously updates extended memory with gamepad information.
The 10-byte structure described here repeats four times for a total of
40 bytes representing four gamepads.

The upper bits of the DPAD register indicate gamepad readiness and
type. The connected bit is high when a gamepad is present in that
player slot. The Sony bit indicates the player is using a
PlayStation-style gamepad with Circle/Cross/Square/Triangle button
faces.

Both digital and analog values are available for the left and right
sticks and triggers L2/R2, so applications can ignore the analog
values entirely if desired.

Some gamepads only report digital data; applications supporting L2 and
R2 should expect analog values of only 0 or 255 in that case.

Applications using a simple "one stick and buttons" approach should
support both the d-pad and left stick as merged input.

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

The RIA includes a Programmable Sound Generator (PSG). It is configured
with extended register device 0 channel 1 address 0x00.

* Eight 24kHz 8-bit oscillator channels.
* Five waveforms: Sine, Square, Sawtooth, Triangle, Noise.
* ADSR envelope: Attack, Decay, Sustain, Release.
* Stereo panning.
* PWM for all waveforms.

Each of the eight oscillators uses eight bytes of XRAM for
configuration. The structure size is a power of two so indexing
into the oscillator array is a bit shift rather than a multiply.

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

Enable and disable the RIA PSG by setting the extended register. The
register value is the XRAM start address for the 64 bytes of config.
This start address must be int-aligned. The 64 bytes of config must
not cross a page boundary. Any invalid address disables the PSG.

.. code-block:: C

  xreg(0, 1, 0x00, xaddr); // enable
  xreg(0, 1, 0x00, 0xFFFF); // disable

All configuration changes take effect immediately. This allows for
effects like panning, slide instruments, and other CPU-driven
shenanigans.

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

The RIA includes a YM3812 FM Sound Generator (OPL2). It is configured
with extended register device 0 channel 1 address 0x01.

Enable and disable the RIA OPL2 by setting the extended register. The
extended register value is the XRAM start address for the 256 OPL2
registers. The OPL2 registers must begin on a page boundary.

.. code-block:: C

  xreg(0, 1, 0x01, xaddr); // enable
  xreg(0, 1, 0x01, 0xFFFF); // disable

If, for example, xaddr is 0x4200 then the 256 registers of an OPL2 chip
are mapped into XRAM from 0x4200 to 0x42FF.

Timers, interrupts, and the status register are not supported.
These features existed in Yamaha OPL chips primarily to help
cost-reduce consumer devices; computers of the era had their own
timers and rarely used them.


Virtual Communications Port
===========================

If you need more serial communications beyond the console UART, USB adapters
are available to CMOS/TTL, RS-232, RS-422, and RS-485. The RIA includes drivers
for FTDI, CP210X, CH34X, PL2303, and CDC ACM.

The ``status`` command lists any connected VCP devices. Open them like
any file using a special name. By default, "VCP0:" opens at 115200
baud, 8 data bits, no parity, and 1 stop bit. Specify the baud rate
with "VCP0:115200" or the full bit configuration with
"VCP0:115200,8N1". The file will not open if your hardware does not
support the requested configuration. The open flags are ignored.

.. code-block:: C

  open("VCP0:1200,7E2", 0);
  // then read and write

Generous FIFO buffers service both reading and writing. Both operations
are non-blocking. Reads can return 0 bytes, and writes may send less
than the requested amount. Resubmit any remaining bytes in a subsequent
call.


ROM File Format
===============

A ROM file begins with a shebang line, followed by any number of assets.
All text lines end with ``\r`` or ``\n`` or both. All numbers may be
specified in decimal (255), C-style hex (0xFF), or MOS-style hex ($FF).

**Shebang** — first line of every ROM file:

.. code-block:: text

  #!RP6502

**Null-named asset** — a group of memory chunks loaded directly into RAM:

.. code-block:: text

  #>len crc

Followed by one or more memory chunks, each consisting of a header line
and ``len`` bytes of raw binary data:

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

The rp6502.py tool, part of the templates for new projects, handles
these details and integrates with the CMake system. Adding assets is
straightforward. In this example the image data is packed into the ROM
as memory chunks, which load into RAM/XRAM when the ROM loads.

.. code-block:: cmake

  rp6502_asset(your_project 0x10000 img/intro.bin)

The ROM can also hold named assets of raw data. Some names have special
meanings. The help asset is shown with the HELP and INFO console commands.

.. code-block:: cmake

  rp6502_asset(your_project help src/help.txt)

All ROM assets become part of the filesystem while the ROM runs.
Precede the asset name with "ROM:" and open it like any other file.
ROM assets are read-only, but you can have multiple open simultaneously.

.. code-block:: C

  open("ROM:help", O_RDONLY)

There's no enforced limit to the number or size of named assets. Opening
files is a linear search. The search will skip over the data, but how many
seeks and string compares your application can tolerate is up to you.
