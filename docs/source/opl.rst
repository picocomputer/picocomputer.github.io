RP6502-OPL
##########

Rumbledethumps Picocomputer 6502 FM Operator Type-L.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The is the sound system.

2. VRAM and VREG
================

Virtual RAM (VRAM) is R/W memory that is accessed with the two VRAM portals provided by the :doc:`ria`. There is 64KB of shared VRAM.

Virtual registers (VREG) are set with an :doc:`api` call. The OPL built in to the RIA is PIX ID 0.
