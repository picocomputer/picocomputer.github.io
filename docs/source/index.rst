.. toctree::
   :hidden:
   :caption: Machine

   RP6502-PICO <pico>
   RP6502-EMU <emu>
   RP6502-FPGA <fpga>

.. toctree::
   :hidden:
   :caption: Reference

   RP6502-SDK <sdk>
   RP6502-RIA <ria>
   RP6502-RIA-W <ria_w>
   RP6502-VGA <vga>
   RP6502-TERM <term>
   RP6502-OS <os>

==================
Picocomputer 6502
==================

Pure 6502. No governor. No speed limits.

The **Picocomputer 6502** is an open source, modern-retro gaming computer
built around a WDC 65C02. The design philosophy is simple: keep the
soul of programming a 6502 and 6522, then rethink everything else. The
hardware and the software are both open, and the whole design is friendly
to DIY builds.

.. image:: _static/ria-w-sandwich.jpg
   :width: 600
   :alt: RP6502-PICO Photo


Community
=========

Most of the action is on Discord, where you can also grab ROMs. Subscribe to
the YouTube channel and share the project around while you're at it.

- **Discord:** https://discord.gg/TC6X8kTr6d
- **Wiki:** https://github.com/picocomputer/community/wiki
- **GitHub Q&A:** https://github.com/picocomputer/community/discussions
- **YouTube:** https://www.youtube.com/@rumbledethumps


Specs (:doc:`pico`)
===================

- **Core** — WDC 65C02 CPU and 65C22 VIA, variable from 0.1 to 8.0 MHz
- **RAM** — 64 KB system plus 64 KB extended
- **ROM** — 1 MB of onboard flash for installing and auto-booting
- **Video** — VGA and HD output, 16-bit color tile and sprite engine
- **Sound** — PSG (8 voices) or OPL2 FM (9 voices)
- **Storage** — Full Speed USB flash and 3.5" floppy drives
- **Clock** — real-time clock with automatic Daylight Saving Time
- **TRNG** — true random number generator


Connections (:doc:`pico`)
=========================

- **Console manifold** — reach the console over telnet, serial, or direct
  attach
- **Wi-Fi** — NTP time sync, telnet server, and Hayes modem emulation
- **Bluetooth LE** — keyboards, mice, and gamepads
- **USB host** — keyboards, mice, gamepads, hubs, UART serial, MIDI, NFC,
  floppy and flash drives
- **USB device** — serial console access with no driver needed (CDC ACM)


Writing Software
================

A **ROM** here is one ``.rp6502`` file holding a program, its assets, and
the 6502 vectors. Nothing is burned into a chip — this file prepares RAM
before the 6502 starts and delivers assets to the program.

- **Protected OS** — 32-bit operating system that uses no 6502 RAM
- **FAT filesystem** — read and write files on the machine's drive
- **POSIX-like API** — a familiar C library for portable code
- **cc65 and llvm-mos** — :doc:`SDK <sdk>` for either 6502 compiler
- **International** — keyboard layouts and OEM code pages


Get a Machine
=============

The original idea — use a modern CPU to remove the friction of enjoying
the best parts of the 6502 — carries forward on every host. What changes
is which modern CPU, and how much of the machine it is asked to be.

- :doc:`pico`: the one you build. 100% through-hole construction, no IC
  programmer required. Hundreds of people have built one, typically for
  under $100 USD. Prefer not to solder? You can have a unit manufactured
  in China instead. Every part is currently in production, and the
  Raspberry Pi Pico 2 is guaranteed through at least January 2040.
- :doc:`emu`: software emulation, for Windows, macOS, Linux, Android, and
  the browser. The host CPU runs everything natively except a small
  emulator for the 6502 and 6522. There's a playable one on that page —
  you can be running 6502 code in about two seconds.
- :doc:`fpga`: hardware emulation. The whole machine in gates, on an
  Analogue Pocket today and MiSTer next. Mostly RTL, with a RISC-V
  embedded to run the OS bridge to the host platform.

All machine types are treated equally. Our unit and functional CI testing
framework runs all code against the same tests whether it's declarative
RTL or imperative C. The guarantees all machine types support all sound
systems and video modes equally.

Things that matter, the 6502, 6522, and video timing, are cycle accurate
on all machines. But some hosts may have unusual limitations or
advantages. For example, the :doc:`emu` is often run on a machine with
NVMe storage many orders of magnitude faster than a, :doc:`pico`'s 12 Mbps
USB.


Read the docs
=============

- :doc:`sdk`: writing software, from a new project to a running program.
  Start here.
- :doc:`ria`: the register map and every device reached through it — the
  interface adapter, in the spirit of the classic CIA, VIA, and ACIA
  chips. Assumes you are comfortable at the bus level.
- :doc:`ria_w`: setting up Wi-Fi, Bluetooth, telnet, and the Hayes modem.
- :doc:`vga`: canvases, video modes, sprites, and the scanline programming
  underneath.
- :doc:`term`: the console, its escape sequences, and the line editor.
- :doc:`os`: the system calls, the ABI, and the C library sitting on them.
