RP6502-VGA
##########

Rumbledethumps Picocomputer 6502 Video Graphics Array.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The Video Graphics Array is a Raspberry Pi Pico with RP6502-VGA firmware. Its primary connection is to a :doc:`ria` over a 5-wire PIX bus. More than one VGA module can be put on a PIX bus. Note that all VGA modules share the same 64K of XRAM and only one module can generate frame numbers and vsync interrupts.

2. Video Programming
====================

This is the current implementation. This is leftovers from validating the PIX bus. The bitmap modes are 4 bpp starting at VRAM 0x0000 with a fixed palette of ANSI colors. This is being replaced with :doc:`rfc1`

 .. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:00
     - MODE
     - Select a graphics mode.
         * 0 - 80 Column Terminal mode.
         * 1 - 320x240 16 colors (4:3)
         * 2 - 320x180 16 colors (16:9)
   * - $F:FF
     - RESET
     - Always returns to terminal mode.

3. Backchannel
==============

Because the PIX bus is unidirectional, it can't be used for sending data from the VGA system back to the RIA. Using the UART Rx path is undesirable since there would be framing overhead or unusable control characters. Since there is a lot of unused bandwidth on the PIX bus, which is only used when the 6502 is writing to XRAM, it can be used for the UART Tx path allowing the UART Tx pin to switch directions.

This is not interesting to the 6502 programmer as it happens automatically. RIA Kernel developers can extend its usefulness. The backchannel is simply a UART implemented in PIO so it sends 8-bit values.

Values 0x00 to 0x7F are used to send a version string as ASCII terminated with a 0x0D or 0x0A. This must be sent immediately after the backchannel enable message is received for it to be displayed as part of the boot message. It may be updated any time after that and inspected with the STATUS CLI command, but currently there is no reason to do so.

When bit 0x80 is set, the 0x70 bits indicate the command type, and the 0x0F bits are a scalar for the command.

0x80 VSYNC - The scalar will increment and be used for the LSB of the RIA_VSYNC register.

0x90 OP_ACK - Some XREG locations are triggers for remote calls which may fail or take time to complete. This acknowledges a successful completion.

0xA0 OP_NAK - This acknowledges a failure.
