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

When the 6502 is in reset, meaning RESB is low and it is not running, the kernel CLI is available for use. If the 6502 has stopped running or the current application has no way to exit, you can put the 6502 back into reset in two ways.

Using a USB keyboard, press CTRL-ALT-DEL. The USB stack runs on the Pi Pico so this will work even if the 6502 has crashed.

Over the UART, send a break. This can be used by a build system to upload and test programs.

MacOS currently can not send a break using the RP6502-VGA due to a known issue with TinyUSB.

WARNING! Do not hook up a physical button to RESB. If you really need one for some reason, have the button pull UART RX low (a break). But what you probably want is the reset that happens from the RUN pin. Resetting the Pi Pico with RUN will cause the boot ROM to load, like at power on. Resetting the 6502 from keyboard or UART will only return you to the kernel CLI.


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
     -
     - Reserved. To be used for video frame counter.
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

Easy and direct access to the UART RX/TX pins of the :doc:`ria` is available from $FFE0-$FFE2. The ready flags on bits 6-7 enable testing with the BIT operator. You may choose to use these or STDIN and STDOUT from the :doc:`api`. Using the UART directly while a STDIN or STDOUT kernel function is in progress will result in undefined behavior.

2.4. Extended RAM (XRAM)
------------------------

RW0 and RW1 are two portals to the same 64K XRAM. Having only one portal would make moving XRAM very slow since data would have to buffer in 6502 RAM. Ideally, you won't move XRAM and can use the pair for better optimizations.

STEP0 and STEP1 are reset to 1. These are signed so you can go backwards and reverse data. These adders allow for very fast sequential access, which typically make up for the slightly slower random access as compared to 6502 RAM.

2.5. Extended Stack (XSTACK)
----------------------------

This is 256 bytes of last-in, first-out, top-down stack used for the fastcall mechanism described in the :doc:`api`. Reading past the end is guaranteed to return zeros.


3. Pico Information Exchange (PIX)
==================================

The limited numbers of GPIO pins on the Raspberry Pi Pico required creating a new bus for high bandwidth devices like video systems. This is an addressable broadcast system which any numbers of devices can listen to.

3.1. Physical layer
-------------------

The physical layer is designed to be easily decoded by Pi Pico PIO, which is just a fancy shift register. The signals used are PHI2 and PIX0-3. This is a double data rate bus with PIX0-3 shifted left on both transitions of PHI2. A frame consists of 32 bits transmitted over 4 cycles of PHI2.

Bit 28 (0x10000000) is the framing bit. This bit will be sent in all messages. An all zero payload is repeated on channel 7 when the bus is idle. A receiver will synchronize by ensuring PIX0 is high on a low transition of PHI2. If it is not, stall until the next clock cycle.

Bits 31-29 (0xE0000000) indicate the channel number for a message.

Channel 0 broadcasts XRAM. Bits 15-0 is the XRAM address. Bits 23-16 is the XRAM data.

Channels 1-6 carry device specific information, typically XREG.  Bits 27-16 is the XREG address. Bits 15-0 is the XREG data.

Channel 7 is used for synchronization. Because 0xF0000000 is hard to miss on test equipment.

3.2. Extended RAM (XRAM)
------------------------

All changes to the 64KB of XRAM on the RIA will be broadcast on PIX channel 0. PIX devices will maintain a replica of the XRAM they use. Typically, all 64K is replicated and an XREG set by the application will point to XRAM.

3.3. PIX Registers (XREG)
-------------------------

Channels 1-6 are used to address the registers of specific PIX devices. For example, channel 1 is used by :doc:`vga`. The remaining channels are suitable for additional video and sound devices.

Each register is 16 bits, the perfect length to point to XRAM. PIX devices may have up to 4096 unique registers.

3.4. PIX Halt
-------------

A halt message is sent upon initial boot and every time the 6502 returns to the kernel CLI. This is sent to all 6 device channels in XREG 0xFFF. This data is a bitfield with configuration information from the RIA. A PIX device should reset itself upon receiving this message.

Bits 0-1: Monitor type.
  | 0x0 - SD 4:3 640x480
  | 0x1 - HD 16:9 640x480 and 1280x720
  | 0x2 - SXGA 5:4 1280x1024


4. FM Audio Synthesizer
=======================

The RIA includes an FM Audio Synthesizer on PIX channel 0.

Note that XREGs for PIX device 0 do not actually get broadcast on the PIX bus. This is a special device built-in to the RIA. Overloading channel 0, which is also used for XRAM, is done to provide an extra hardware address.

Note that audio software hasn't been written yet.
