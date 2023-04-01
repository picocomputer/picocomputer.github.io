RP6502-VGA
##########

Rumbledethumps Picocomputer 6502 Video Graphics Array.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The Video Graphics Array is a Raspberry Pi Pico with RP6502-VGA firmware. Its primary connection is to a :doc:`ria` over a 5-wire PIX bus. More than one VGA module can be put on a PIX bus. Note that all VGA modules share the same 64K of XRAM and only one module can generate frame numbers and vsync interrupts.

2. PIX Registers
================

PIX Registers (XREG) are set with an :doc:`api` call. The standard VGA module is PIX ID 1.

This will expanded greatly in the future. Sprites with affine transforms seem possible. For now, there's just a few test modes. The bitmap modes are 4 bpp starting at VRAM 0x0000 with a fixed palette of ANSI colors. This is leftovers from testing the PIX bus, not a model for future development.

 .. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0
     - MODE
     - Select a graphics mode.
         * 0 - 80 Column Terminal mode.
         * 1 - 320x240 16 colors (4:3)
         * 2 - 320x180 16 colors (16:9)
   * - $FFF
     - RESET
     - Always returns to terminal mode.
