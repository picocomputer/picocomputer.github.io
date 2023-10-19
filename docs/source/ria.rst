RP6502-RIA
##########

Rumbledethumps Picocomputer 6502 Interface Adapter.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The RP6502 Interface Adapter (RIA) is a Raspberry Pi Pico with RP6502-RIA firmware. The RIA provides all essential services to support a WDC W65C02S microprocessor.

1.1. Features of the RP6502-RIA
-------------------------------

* Advanced CMOS process technology for low power consumption
* Reset and clock management
* ROM loader
* UART
* Stereo audio
* USB MSC - Hard drives and flash drives
* USB HID - Keyboards, mice, and game controllers
* PIX bus for GPUs like the RP6502-VGA

2. Functional Description
=========================

The RIA must be installed at $FFE0-$FFFF and must be in control of RESB and PHI2. These are the only requirements. Everything else about your Picocomputer can be customized.

A new RIA will boot to the the kernel CLI. This CLI can be accessed from VGA and keyboard, or from the serial console. The kernel CLI is not currently documented here. The built-in help is extensive and always up-to-date. Type 'help'.

The kernel CLI can be used in two ways. There are commands to install ROM files to the RIA EEPROM which can boot on power up. You may also use the CLI to load programs from a USB drive or development system.

If not using the :doc:`vga` system, the UART can be directly connected to. Use 115200 8N1.

2.1. Reset
----------

When the 6502 is in reset, meaning RESB is low and it is not running, the kernel monitor CLI is available for use. If the 6502 has crashed or the current application has no way to exit, you can put the 6502 back into reset in two ways.

Using a USB keyboard, press CTRL-ALT-DEL. The USB stack runs on the Pi Pico so this will work even if the 6502 has crashed.

Over the UART, send a break. This can be used by a build system to upload and test programs.

MacOS isn't capable of sending a break with its CDC driver. A common workaround is to drop the baud rate significantly so a bit sequence of zeros will look like a break. The :doc:`vga` CDC implementation has a hack to detect a full byte of zeros within 100ms of changing the baud rate to 1200.

.. code-block:: bash

  stty -F /dev/ttyACM0 1200 && echo -ne '\0' > /dev/ttyACM0

WARNING! Do not hook up a physical button to RESB. The RIA must remain in control of RESB. What you probably want is the reset that happens from the RIA RUN pin. We call this a reboot. The reference hardware reboot button is hooked up to the RIA RUN pin. Rebooting the Pi Pico RIA like this will cause any configured boot ROM to load, like at power on. Resetting the 6502 from keyboard or UART will only return you to the kernel CLI, which is great for devlopment and hacking.


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
         * bit 7 - TX FIFO not full. Ok to send.
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
     - 256 bytes for passing kernel parameters.
   * - $FFED
     - ERRNO_LO
     - Low byte of errno. All errors fit in this byte.
   * - $FFEE
     - ERRNO_HI
     - Ensures errno is an optionally a 16-bit int.
   * - $FFEF
     - OP
     - Write the API operation id here to begin a kernel call.
   * - $FFF0
     - NOP
     - Always $EA.
   * - $FFF1
     - RETURN
     - Always $80, BRA. Entry to blocking API return.
   * - $FFF2
     - BUSY
     - Bit 7 high while operation is running.
   * - $FFF3
     - LDX
     - Always $A2.
   * - $FFF4
     - X
     - Kernel register X.
   * - $FFF5
     - LDA
     - Always $A9.
   * - $FFF6
     - A
     - Kernel register A.
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

Easy and direct access to the UART RX/TX pins of the :doc:`ria` is available from $FFE0-$FFE2. The ready flags on bits 6-7 enable testing with the BIT operator. You may choose to use these or STDIN and STDOUT from the :doc:`api`. Using the UART directly while a STDIN or STDOUT kernel function is in progress will result in undefined behavior.

2.4. Extended RAM (XRAM)
------------------------

RW0 and RW1 are two portals to the same 64K XRAM. Having only one portal would make moving XRAM very slow since data would have to buffer in 6502 RAM. Ideally, you won't move XRAM and can use the pair for better optimizations.

STEP0 and STEP1 are reset to 1. These are signed so you can go backwards and reverse data. These adders allow for very fast sequential access, which typically make up for the slightly slower random access as compared to 6502 RAM.

RW0 and RW1 are latching. This is important to remember when other systems change XRAM. For example, when using readx() to load XRAM from a mass storage device, this will not work as expected:

.. code-block:: C

  RIA_ADDR0 = 0x1000;
  readx(0x1000, 1, 3);
  uint8_t result = RIA_RW0; // wrong

Setting ADDR after the expected XRAM change will latch RW to the latest value.

.. code-block:: C

  readx(0x1000, 1, 3);
  RIA_ADDR0 = 0x1000;
  uint8_t result = RIA_RW0; // correct

2.5. Extended Stack (XSTACK)
----------------------------

This is 256 bytes of last-in, first-out, top-down stack used for the fastcall mechanism described in the :doc:`api`. Reading past the end is guaranteed to return zeros.

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
    - | Sets the address in extended RAM for a bit array of USB HID keyboard codes. Note that these are not the same as PS/2 scancodes. Each bit represents one key with the first four bits having special meaning.
      | * 0 - No key pressed
      | * 1 - Overflow - too many keys pressed
      | * 2 - Unused - POST error
      | * 3 - Unused - Undefined error
      | This is intended for applications that need to detect both key up and down events or the modifier keys. Use the UART or stdin if you don't need this kind of direct access.

      .. code-block:: C

        uint8_t keyboard[32];
        #define key(code) (keyboard[code >> 3] & \
                           (1 << (code & 7)))
  * - $0:0:01
    - MOUSE
    - | Sets the address in extended RAM for a structure containing direct mouse input.

      .. code-block:: C

        struct {
            uint8_t buttons;
            uint8_t x;
            uint8_t y;
            uint8_t wheel;
            uint8_t pan;
        } mouse;

      | The amount of movement is computed by keeping track of the previous values and subtracting from the current value. Vsync timing (60Hz) isn't always fast enough. For perfect mouse input with fast mice, use an ISR at 8ms or faster (125Hz).

      .. code-block:: C

        int8_t delta_x = current_x - prev_x;

      | Mouse buttons are a bitfield:
      | 0 - LEFT
      | 1 - RIGHT
      | 2 - MIDDLE
      | 3 - BACKWARD
      | 4 - FORWARD


1. Pico Information Exchange (PIX)
==================================

The limited numbers of GPIO pins on the Raspberry Pi Pico required creating a new bus for high bandwidth devices like video systems. This is an addressable broadcast system which any number of devices can listen to.

3.1. Physical layer
-------------------

The physical layer is designed to be easily decoded by Pi Pico PIO, which is just a fancy shift register. The signals used are PHI2 and PIX0-3. This is a double data rate bus with PIX0-3 shifted left on both transitions of PHI2. A frame consists of 32 bits transmitted over 4 cycles of PHI2.

Bit 28 (0x10000000) is the framing bit. This bit will be set in all messages. An all zero payload is repeated on device ID 7 when the bus is idle. A receiver will synchronize by ensuring PIX0 is high on a low transition of PHI2. If it is not, stall until the next clock cycle.

Bits 31-29 (0xE0000000) indicate the device ID number for a message.

Device 0 is allocated to :doc:`ria`. Device 0 is also overloaded to broadcast XRAM.

Device 1 is allocated to :doc:`vga`.

Devices 2-6 are available for user expansion.

Device 7 is used for synchronization. Because 0xF0000000 is hard to miss on test equipment.

Bits 27-24(0x0F000000) indicate the channel ID number for a message. Each device can have 16 channels.

Bits 23-16(0x00FF0000) indicate the register address in the channel on the device.

Bits 15-0(0x0000FFFF) is a value to store in the register.

3.2. PIX Extended RAM (XRAM)
----------------------------

All changes to the 64KB of XRAM on the RIA will be broadcast on PIX device 0. Bits 15-0 is the XRAM address. Bits 23-16 is the XRAM data. This goes out on the wire, but is never seen by the SDK. Device 0, as seen by the SDK, is the RIA itself and has no need to go out the wire.

PIX devices will maintain a replica of the XRAM they use. Typically, all 64K is replicated and an XREG set by the application will point to a configuration structure in XRAM.

3.3. PIX Extended Registers (XREG)
----------------------------------

PIX devices may use bits 27-0 however they choose. The suggest division of this bits is:

Bits 27-24 indicate a channel. For example, the RIA device has a channel for audio, a channel for keyboard and mouse, a channel for Wifi, and so on. Bits 23-16 is an extended register address. Bits 15:0 for the payload.

So we have seven PIX devices, each with 16 internal channels having 256 16-bit registers. The idea is to use extended registers to point to structures in XRAM. Changing XREG is setup, changing XRAM causes the device to respond.

4. FM Audio Synthesizer
=======================

The RIA will include an FM Audio Synthesizer on PIX device 0 channel 0.
