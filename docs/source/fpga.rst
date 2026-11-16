============================
RP6502-FPGA
============================

RP6502 - Field Programmable Gate Array


Introduction
============

The RP6502-FPGA is the machine in fabric, a Picocomputer 6502 built from
programmable logic. It runs on the Analogue Pocket, a handheld with an
FPGA, as a core for openFPGA. It plays ``.rp6502`` games and applications
from the microSD card, with the buttons of the Pocket as a gamepad. An
Analogue Dock puts the picture on a TV and adds a keyboard, a mouse, and
more gamepads. The Pocket can sleep in the middle of a program and wake
where it stopped, and a Memory saves a running program to return to
later.

An :doc:`pico` is built from chips and two Pico 2 boards, and the
:doc:`emu` models those chips in software. In the RP6502-FPGA, the chips
are circuits in one FPGA: the 65C02, the 65C22, the registers of the
:doc:`ria`, the renderer of the :doc:`vga` system, and the sound
generators. The 6502 runs at up to 8 MHz. The rest of the RIA is the same
software that the other machines run, on a small RISC-V processor that is
also a circuit in the FPGA.


.. _fpga-install:

Install
=======

The core needs an Analogue Pocket with firmware 2.3 or later.

Download ``rp6502-<version>-pocket.zip`` from the `releases page
<https://github.com/picocomputer/rp6502/releases/latest>`__ and unpack it
to the root of the microSD card. To update the core, unpack a newer zip
over the old one.

A program that manages the openFPGA cores of a microSD card can also
install and update the core, which is in the lists of those programs.


.. _fpga-running:

Running Software
================

6502 software is distributed as files ending in ``.rp6502``. Find them on
Discord, which has a forum for ROMs, or on itch.io under the RP6502 tag:

- https://discord.gg/TC6X8kTr6d
- https://itch.io/games/tag-rp6502

Put the ROMs in ``Assets/rp6502/common/`` on the card. Open the core from
the Pocket menu under openFPGA, and pick a ROM from the list shown when
the core opens. Another ROM can be picked from the menu of the core while
a program runs.


.. _fpga-saves:

Saves
=====

The files that a program saves are in ``Saves/rp6502/common/`` on the
card. A program writes them through ``SAVE:``, as :ref:`Saves
<port-save>` on the :doc:`port` page shows. That directory is also the
working directory, so a file that a program opens by its file name alone
is there too. :ref:`Compatibility <port-compatibility>` on the
:doc:`port` page shows how files on the Pocket differ from the other
machines.


.. _fpga-sleep:

Sleep and Memories
==================

The Pocket turns the FPGA off to sleep, so the core saves the whole
machine before a sleep and loads it again on waking. A Memory is the same
save, kept by the Pocket in a file. The save holds the state of the 6502,
the VIA, and the RIA, with 6502 RAM, XRAM, the picture, and the sound, so
the program continues from where it stopped. The files that the program
had open are opened again by name, each at the position it had.

The core refuses a sleep or a Memory while a program has a file open for
writing. An update of the core can change what a save holds, and a Memory
made before such an update does not load. When a load is refused, the
screen shows ``bad savestate`` and the reason.


.. _fpga-input:

Gamepads, Keyboard, and Mouse
=============================

The buttons of the Pocket are a gamepad, as :ref:`Gamepads
<ria-gamepads>` on the RIA page describes.

With an Analogue Dock, the core takes up to four devices, and each can be
a gamepad, a keyboard, or a mouse. The keyboard has the layout of the
Keyboard setting in `Core Settings`_. The mouse also drives the
:ref:`tablet <ria-tablet>`.


.. _fpga-settings:

Core Settings
=============

The Pocket keeps these settings for the core. A change takes effect at
once, without a restart.

.. list-table::
   :widths: 25 30 45
   :header-rows: 1

   * - Setting
     - Values
     - Description
   * - Keyboard
     - DK, DE, FR, PL-PROG, SE, US, US-INTL
     - The layout of the keyboard. Default US.
   * - UTC offset side
     - East of Zulu +, West of Zulu -
     - Whether local time is ahead of UTC or behind it. Default east.
   * - UTC offset hours
     - 0 to 14
     - The hours of the offset. Default 0.
   * - UTC offset minutes
     - :00, :15, :30, :45
     - The minutes of the offset. Default :00.

The clock that is set in the menus of the Pocket is local time, already
adjusted for daylight saving time. The core uses the UTC offset settings
to work that time back to UTC, which the time functions of a program
need.


.. _fpga-inside:

Inside the Core
===============

The FPGA of the Pocket is an Intel Cyclone V. The machine runs on a clock
of 50.4 MHz, which is twice the 25.2 MHz pixel clock of VGA timing.

- **6502.** The 65C02 and the 65C22 are logic. The 6502 steps on chosen
  cycles of the 50.4 MHz clock. Each 6502 cycle is a whole number of
  those cycles, and the average speed is exactly the PHI2 speed that a
  program sets.
- **Memory.** 6502 RAM and XRAM are each 64 KB of the block memory inside
  the FPGA. The 64 MB SDRAM of the Pocket holds the ROM, the software of
  the RIA, and the save of a sleep or a Memory.
- **Host.** The host is a soft CPU that runs at 50.4 MHz. It is a
  Hazard3, an open source 32-bit RISC-V processor. Its software is
  ``firmware.bin``, which the Pocket loads into the SDRAM when the core
  opens. The soft CPU runs it from there through an 8 KB cache.
- **Video.** The VGA system is a hardware renderer. The software writes a
  table of what to draw on each scanline, and the logic draws the canvas
  with the timing of 640x480 at 60 Hz.
- **Sound.** The PSG, the OPL2, and the PCM player are logic, mixed at
  48 kHz.
