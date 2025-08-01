RP6502-RIA
##########

Rumbledethumps Picocomputer 6502 Interface Adapter.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The RP6502 Interface Adapter (RIA) is a Raspberry Pi Pico 2 with
RP6502-RIA firmware. The RIA provides all essential services to support a
WDC W65C02S microprocessor.

1.1. Features of the RP6502-RIA
-------------------------------

* Advanced CMOS process technology for low power consumption
* Real time clock with automatic daylight savings time
* 6502 reset and clock management
* ROM loader instead of ROM chips
* A proper UART
* Stereo audio
* USB keyboards and mice
* USB mass storage aka thumb drives
* USB gamepads for up to four player fun
* PIX bus for GPUs like the RP6502-VGA

2. Functional Description
=========================

The RIA must be installed at $FFE0-$FFFF and must be in control of RESB
and PHI2. These are the only requirements. Everything else about your
Picocomputer can be customized.

A new RIA will boot to the console interface. This console can be accessed
in one of three ways: from a VGA monitor and USB keyboard if you are using
an RP6502-VGA; from the USB CDC device which the RP6502-VGA presents when
plugged into a host PC like a development system; or from UART RX/TX
(115200 8N1) pins on the RIA if you aren't using an RP6502-VGA. The
console interface is not currently documented here. The built-in help is
extensive and always up-to-date. Type ``help`` to get started and don't
forget there is deep help like ``help set phi2``.

The console interface is not meant to be an operating system CLI.
Everything about its design is meant to achieve two goals. The first is to
enable installing ROM files to the RIA EEPROM which can then boot on power
up—this delivers the instant-on experience of early home computers. The
other goal is to enable easy development and experimentation—you can load
ROMs directly from a USB drive or send them from a development system.

2.1. Reset
----------

When the 6502 is in reset, meaning RESB is low and it is not running, the
RIA console is available for use. If the 6502 has crashed or the current
application has no way to exit, you can put the 6502 back into reset in
two ways.

Using a USB keyboard, press CTRL-ALT-DEL. The USB stack runs on the Pi
Pico so this will work even if the 6502 has crashed.

Over the UART, send a break. The tools included with the "Hello, world!"
project templates use this to stop the 6502, upload a new ROM, and execute
the new ROM. All with the push of one button.

WARNING! Do not hook up a physical button to RESB. The RIA must remain in
control of RESB. What you probably want is the reset that happens from the
RIA RUN pin. We call this a reboot. The reference hardware reboot button
is hooked up to the RIA RUN pin. Rebooting the Pi Pico RIA like this will
cause any configured boot ROM to load, like at power on. Resetting the
6502 from keyboard or UART will only return you to the console interface,
which is great for development and hacking.


2.2. Registers
--------------

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
     - Increments every 1/60 second when PIX VGA device is connected.
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
     - 512 bytes for passing call parameters.
   * - $FFED
     - ERRNO_LO
     - Low byte of errno. All errors fit in this byte.
   * - $FFEE
     - ERRNO_HI
     - Ensures errno is optionally a 16-bit int.
   * - $FFEF
     - OP
     - Write the API operation id here to begin a kernel call.
   * - $FFF0
     - IRQ
     - Set bit 0 high to enable VSYNC interrupts. Verify source with
       VSYNC then read or write this register to clear interrupt.
   * - $FFF1
     - RETURN
     - Always $80, BRA. Entry to blocking API return.
   * - $FFF2
     - BUSY
     - Bit 7 high while operation is running.
   * - $FFF3
     - LDA
     - Always $A9.
   * - $FFF4
     - A
     - Kernel register A.
   * - $FFF5
     - LDX
     - Always $A2.
   * - $FFF6
     - X
     - Kernel register X.
   * - $FFF7
     - RTS
     - Always $60.
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


2.3. UART
---------

Easy and direct access to the UART RX/TX pins of the :doc:`ria` is
available from $FFE0-$FFE2. The ready flags on bits 6-7 enable testing
with the BIT operator. You may choose to use these or STDIN and STDOUT
from the :doc:`api`. Using the UART directly while a STDIN or STDOUT
kernel function is in progress will result in undefined behavior.

2.4. Extended RAM (XRAM)
------------------------

RW0 and RW1 are two portals to the same 64K XRAM. Having only one portal
would make moving XRAM very slow since data would have to buffer in 6502
RAM. Ideally, you won't move XRAM and can use the pair for better
optimizations.

STEP0 and STEP1 are reset to 1. These are signed so you can go backwards
and reverse data. These adders allow for very fast sequential access,
which typically makes up for the slightly slower random access compared
to 6502 RAM.

RW0 and RW1 are latching. This is important to remember when other systems
change XRAM. For example, when using read_xram() to load XRAM from a mass
storage device, this will not work as expected:

.. code-block:: C

  RIA_ADDR0 = 0x1000;
  read_xram(0x1000, 1, fd);
  uint8_t result = RIA_RW0; // wrong

Setting ADDR after the expected XRAM change will latch RW to the latest
value.

.. code-block:: C

  read_xram(0x1000, 1, fd);
  RIA_ADDR0 = 0x1000;
  uint8_t result = RIA_RW0; // correct

2.5. Extended Stack (XSTACK)
----------------------------

This is 512 bytes of last-in, first-out, top-down stack used for the
fastcall mechanism described in the :doc:`api`. Reading past the end is
guaranteed to return zeros. Simply write to push and read to pull.

2.6. Extended Registers (XREG)
------------------------------

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


3. Pico Information Exchange (PIX)
==================================

The limited number of GPIO pins on the Raspberry Pi Pico required creating
a new bus for high bandwidth devices like video systems. This is an
addressable broadcast system which any number of devices can listen to.

3.1. Physical layer
-------------------

The physical layer is designed to be easily decoded by Pi Pico PIO, which
is just a fancy shift register. The signals used are PHI2 and PIX0-3.
This is a double data rate bus with PIX0-3 shifted left on both
transitions of PHI2. A frame consists of 32 bits transmitted over 4 cycles
of PHI2.

Bit 28 (0x10000000) is the framing bit. This bit will be set in all
messages. An all-zero payload is repeated on device ID 7 when the bus is
idle. A receiver will synchronize by ensuring PIX0 is high on a low
transition of PHI2. If it is not, stall until the next clock cycle.

Bits 31-29 (0xE0000000) indicate the device ID number for a message.

Device 0 is allocated to :doc:`ria`. Device 0 is also overloaded to
broadcast XRAM.

Device 1 is allocated to :doc:`vga`.

Devices 2-6 are available for user expansion.

Device 7 is used for synchronization. Because 0xF0000000 is hard to miss
on test equipment.

Bits 27-24 (0x0F000000) indicate the channel ID number for a message.
Each device can have 16 channels.

Bits 23-16 (0x00FF0000) indicate the register address in the channel on
the device.

Bits 15-0 (0x0000FFFF) is a value to store in the register.

3.2. PIX Extended RAM (XRAM)
----------------------------

All changes to the 64KB of XRAM on the RIA will be broadcast on PIX
device 0. Bits 15-0 contain the XRAM address. Bits 23-16 contain the XRAM
data. This goes out on the wire, but is never seen by the SDK. Device 0,
as seen by the SDK, is the RIA itself and has no need to go out on the
wire.

PIX devices will maintain a replica of the XRAM they use. Typically, all
64K is replicated and an XREG set by the application will point to a
configuration structure in XRAM.

3.3. PIX Extended Registers (XREG)
----------------------------------

PIX devices may use bits 27-0 however they choose. The suggested division
of these bits is:

Bits 27-24 indicate a channel. For example, the RIA device has a channel
for audio, a channel for keyboard and mouse, a channel for Wifi, and so
on. Bits 23-16 contain an extended register address. Bits 15-0 contain the
payload.

So we have seven PIX devices, each with 16 internal channels having 256
16-bit registers. The idea is to use extended registers to point to
structures in XRAM. Changing XREG is setup; changing XRAM causes the
device to respond.


4. Keyboard
===========

The RIA can provide direct access to keyboard data. This is intended for
applications that need to detect both key up and down events or the
modifier keys. You may instead use the UART or stdin if you don't need
this kind of direct access.

Enable and disable direct keyboard access by mapping it to an address in
extended RAM.

.. code-block:: C

  xreg(0, 0, 0x00, xaddr);  // enable
  xreg(0, 0, 0x00, 0xFFFF); // disable

Extended RAM will be continuously updated with a bit array of USB HID
keyboard codes. Note that these are not the same as PS/2 scancodes. Each
bit represents one key with the first four bits having special meaning:

| * 0 - No key pressed
| * 1 - Overflow - too many keys pressed
| * 2 - Num Lock on
| * 3 - Caps Lock on

.. code-block:: C

  uint8_t keyboard[32];
  #define key(code) (keyboard[code >> 3] & \
                    (1 << (code & 7)))


5. Mouse
========

The RIA can provide direct access to mouse information. Enable and disable
by mapping it to an address in extended RAM.

.. code-block:: C

  xreg(0, 0, 0x01, xaddr);  // enable
  xreg(0, 0, 0x01, 0xFFFF); // disable

This sets the address in extended RAM for a structure containing direct
mouse input.

.. code-block:: C

  struct {
      uint8_t buttons;
      uint8_t x;
      uint8_t y;
      uint8_t wheel;
      uint8_t pan;
  } mouse;

The amount of movement is computed by keeping track of the previous values
and subtracting from the current value. Vsync timing (60Hz) isn't always
fast enough. For perfect mouse input with fast mice, use an ISR at 8ms or
faster (125Hz).

.. code-block:: C

  int8_t delta_x = current_x - prev_x;

| Mouse buttons are a bitfield:
| * 0 - LEFT
| * 1 - RIGHT
| * 2 - MIDDLE
| * 3 - BACKWARD
| * 4 - FORWARD


6. Gamepads
===========

The RIA supports up to four gamepads connected via USB. There is no way to
support all controllers without writing three different classes of drivers:
XInput, Sony, and HID. So that's what's in the RIA. Even so, there is no
standard button layout for HID so ``des.c`` will need to be adjusted to
support new gamepads.

Therefore, the recommended gamepads for the Picocomputer are: Xbox 360, Xbox
One/Series, DualShock 4, and DualSense 5. There are plenty of third-party
Xbox and PlayStation controllers which should work fine as well.

If your HID or third-party gamepad doesn't work, it probably needs to be
added to ``des.c``. Any issues submitted in this regard cannot be resolved
by Rumbledethumps—who doesn't have your gamepad. The community needs to
step up here if excellent third-party and HID controller support is
desired.

Be aware that this project pushes TinyUSB to its limit. Okay, let's be
frank here: the TinyUSB stack is janky as hell and doesn't have any
documentation. If you do a lot of plugging and unplugging it will
eventually crash. Some devices will also break the boot sequence. Any
issues submitted in this regard cannot be resolved by Rumbledethumps. The
community needs to step up here if an excellent USB stack is desired.

Enable and disable access to the RIA gamepad XRAM registers by setting the
extended register. The register value is the XRAM start address of the
gamepad registers. Any invalid address disables the gamepads.

.. code-block:: C

  xreg(0, 0, 2, xaddr);  // enable
  xreg(0, 0, 2, 0xFFFF); // disable

Extended memory will be continuously updated with gamepad information. The
10-byte structure described here repeats for a total of 40 bytes
representing four gamepads.

The upper bits of the DPAD register are used to indicate if a gamepad is
ready for use and what kind of gamepad it is. The connected bit is high
when a gamepad for that player slot is connected. The Sony bit indicates
that the player is using a PlayStation-style gamepad with
Circle/Cross/Square/Triangle button faces.

Note that there are both digital and analog values for the left and right
analog sticks and analog triggers L2/R2. This lets an application
completely ignore the analog values if it desires.

Applications that want to use a simple "one stick and buttons" approach
are encouraged to support both the dpad and left stick (merged). This is
because gamepads without analog sticks usually present their direction
pad as an emulated left analog stick. It also gives players using modern
gamepads the option of using the dpad or analog stick.

Applications supporting L2 and R2 should be aware that some gamepads
will only present digital information so the analog values will only
ever be 0 or 255. This is seen on 8BitDo controllers in Dinput mode—
see your controller's manual to learn how to switch to Xinput mode which
will give you the analog information.

Note that the DPAD and STICKS registers are 8-way. You wouldn't see a
4-way joystick on an early home computer unless it was custom made.
Some games, like Pac-Man and Donkey Kong, are well known for using
4-way joysticks. It's easy to decode the analog stick values into
quadrants using only the 8-bit adder of a 6502, so go ahead and port
your favorite 4-way game without worry.

.. list-table::
   :widths: 1 1 20
   :header-rows: 1

   * - Offset
     - Name
     - Description
   * - 0
     - DPAD
     -
         * bit 0: Direction pad up
         * bit 1: Direction pad down
         * bit 2: Direction pad left
         * bit 3: Direction pad right
         * bit 4: Reserved
         * bit 5: Reserved
         * bit 6: Sony button faces
         * bit 7: Connected
   * - 1
     - STICKS
     -
         * bit 0: Left stick up
         * bit 1: Left stick down
         * bit 2: Left stick left
         * bit 3: Left stick right
         * bit 4: Right stick up
         * bit 5: Right stick down
         * bit 6: Right stick left
         * bit 7: Right stick right
   * - 2
     - BTN0
     -
         * bit 0: A or Cross
         * bit 1: B or Circle
         * bit 2: X or Square
         * bit 3: Y or Triangle
         * bit 4: L1
         * bit 5: R1
         * bit 6: Select/Back
         * bit 7: Start/Menu
   * - 3
     - BTN1
     -
         * bit 0: L2
         * bit 1: R2
         * bit 2: L3
         * bit 3: R3
         * bit 4: Home button
         * bit 5: Undefined
         * bit 6: Undefined
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


7. Programmable Sound Generator
===============================

The RIA includes a Programmable Sound Generator (PSG). It is configured
with extended register device 0 channel 1 address 0x00.

* Eight 24kHz 8-bit oscillator channels.
* Five waveforms: Sine, Square, Sawtooth, Triangle, Noise.
* ADSR envelope: Attack, Decay, Sustain, Release.
* Stereo panning.
* PWM for all waveforms.

Each of the eight oscillators requires eight bytes of XRAM for
configuration. The unused byte is padding so multiplication is a fast bit
shift.

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

Internally, the audio is generated by Pulse Width Modulation. A decoupling
and low-pass filter circuit converts the digital signal into line-level
analog.

Enable and disable the RIA PSG by setting the extended register. The
register value is the XRAM start address for the 64 bytes of config. This
start address must be int-aligned. Any invalid address disables the PSG.

.. code-block:: C

  xreg(0, 1, 0x00, xaddr); // enable
  xreg(0, 1, 0x00, 0xFFFF); // disable

All configuration changes take effect immediately. This allows for effects
like panning, slide instruments, and other CPU-driven shenanigans.

The gate is checked at the sample rate of 24kHz. If, for example, you
unset and set it between one pair of audio output samples, then it will
not begin a new ADSR cycle.

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
     - Attack volume and rate.
         * bits 7-4 - 0-15 volume attenuation.
         * bits 3-0 - 0-15 attack rate.
   * - vol_decay
     - Decay volume and rate.
         * bits 7-4 - 0-15 volume attenuation.
         * bits 3-0 - 0-15 decay rate.
   * - wave_release
     - Waveform and release rate.
         * bits 7-4 - 0=sine, 1=square, 2=sawtooth, 3=triangle, 4=noise.
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
