.. toctree::
   :hidden:

   Hardware <hardware>
   RP6502-RIA <ria>
   RP6502-RIA-W <ria_w>
   RP6502-VGA <vga>
   RP6502-OS <os>

==================
Picocomputer 6502
==================

Pure 6502. No governor. No speed limits.

The **Picocomputer 6502** is an open source, modern-retro gaming computer
built around a real WDC 65C02. The design philosophy: keep the soul of
programming a 6502 and 6522, then rethink everything else.

.. image:: _static/ria-w-sandwich.jpg
   :width: 600
   :alt: Picocomputer Photo


Community
=========

Most of the activity is on Discord, where you can also get the

- **Discord:** https://discord.gg/TC6X8kTr6d
- **Forums:** https://github.com/picocomputer/community/discussions
- **Wiki:** https://github.com/picocomputer/community/wiki
- **GitHub:** https://github.com/picocomputer
- **YouTube:** https://youtube.com/playlist?list=PLvCRDUYedILfHDoD57Yj8BAXNmNJLVM2r


Specs
=====

- **Core** — WDC 65C02 CPU and WDC 65C22 VIA; variable 0.1-8.0 MHz
- **RAM** — 64 KB system + 64 KB extended
- **ROM** — 1 MB of onboard flash for installing and auto-booting ROMs
- **Video** — VGA and HD output; 16-bit color with alpha
- **Sound** — PSG (8 voices) or OPL2 FM (9 voices)
- **Clock** — Real-Time Clock with Daylight Savings Time
- **TRNG** — True random number generator


Quality of Life
===============
- **Open by Design** — DIY-friendly with fully open source hardware and software
- **Fan-inout Console** — Telnet, serial, and direct access to the console
- **Storage** — Fast >512 KB/sec USB flash drive reads and writes
- **Keyboard** — International keyboard layout support
- **Fonts** — Built-in code pages for international character sets


Connectivity
============

- **WiFi** — NTP time sync, telnet server, and Hayes modem emulation
- **Bluetooth LE** — keyboard, mouse, and gamepads
- **USB Host** — keyboard, mouse, gamepads, hubs, UART serial, NFC, floppy drives, and flash drives
- **USB Device** — driverless CDC ACM for console access (can operate headless)


Programming
===========

- **Protected OS** — 32-bit operating system; uses no 6502 RAM
- **FAT filesystem** — read and write files on any USB flash or floppy drive
- **API** — POSIX-like C library for familiar, portable programming
- **cc65** — `VS Code integration for cc65 <https://github.com/picocomputer/vscode-cc65>`__
- **llvm-mos** — `VS Code integration for llvm-mos <https://github.com/picocomputer/vscode-llvm-mos>`__
- **AI Assistance** — The latest models via VS Code extensions or GitHub Copilot


Build It
========

100% through-hole construction. No IC programmer needed. Hundreds of people
have built one, typically for under $100 USD. You can also have a unit
manufactured in China — no soldering required. All parts are currently in
production; the Raspberry Pi Pico 2 is guaranteed until at least January 2040.

- :doc:`hardware`: Schematic and manufacturing information.


Documentation
=============

The Picocomputer 6502 is a reference design for RP6502 modular hardware.
The only required module is the RP6502-RIA.

- :doc:`ria`: Interface adapter for the 6502, akin to CIA, VIA, and ACIA devices.
- :doc:`ria_w`: Wireless features available when using the "Pico 2 W".
- :doc:`vga`: Optional video adapter.
- :doc:`os`: The operating system and application programming interface.


`Please contribute to this documentation.
<https://github.com/picocomputer/picocomputer.github.io>`_
