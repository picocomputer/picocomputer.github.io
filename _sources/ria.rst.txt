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
* PIX bus for GPUs

1. Functional Description
=========================

The RIA must be installed at $FFE0-$FFFF and must be in control of RESB and PHI2. These are the only requirements. Everything else about your Picocomputer can be customized.

RW0 and RW1 are two portals to the same VRAM. Having only one would make moving VRAM very slow since data would have to buffer in 6502 RAM. Having two allows moving VRAM to be slightly faster than moving 6502 RAM. Ideally, you won't move VRAM and can use the pair for better optimizations.

.. list-table:: Title
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
     - Read or write the VRAM referenced by ADDR0.
   * - $FFE5
     - STEP0
     - Signed byte added to ADDR0 after every access to RW0.
   * - | $FFE6 -
       | $FFE7
     - ADDR0
     - Address of VRAM for RW0.
   * - $FFE8
     - RW1
     - Read or write the VRAM referenced by ADDR1.
   * - $FFE9
     - STEP1
     - Signed byte added to ADDR1 after every access to RW1.
   * - | $FFEA -
       | $FFEB
     - ADDR1
     - Address of VRAM for RW1.
   * - $FFEC
     - VSTACK
     - 256 bytes for passing kernel paramaters.
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
