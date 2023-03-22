RP6502-VGA
##########

Rumbledethumps Picocomputer 6502 Video Graphics Array.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The Video Graphics Array is a Raspberry Pi Pico with RP6502-VGA firmware. Its primary connection is to a :doc:`ria` over a 5-wire PIX bus. More than one VGA module can be put on a PIX bus. Note that all VGA modules share the same 64K of VRAM and only one module can generate frame numbers and vsync interrupts.

1. VRAM and VREG
================

Virtual RAM (VRAM) is R/W memory that is accessed with the two VRAM portals provided by the :doc:`ria`. There is 64KB of shared VRAM.

Virtual registers (VREG) are set with an :doc:`api` call. Each VGA module has its own 256 16-bit registers.
