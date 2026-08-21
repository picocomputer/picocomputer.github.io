============================
RP6502-FPGA
============================

RP6502 - Field Programmable Gate Array


Introduction
============

The RP6502-FPGA is the Picocomputer 6502 in programmable logic. The
65C02, the 65C22, the :doc:`ria`, and the :doc:`vga` video system are RTL,
and the operating system runs on a Hazard3 RISC-V soft CPU executing
the same C firmware all other machines run. It keeps the same split between
a 6502 and a modern processor, which is what defines a Picocomputer.


The Analogue Pocket Core
========================

The Pocket core is the entire machine on a handheld. It has every video
mode, the PSG and the OPL2, the dock, the keyboard layouts, the mouse,
sleep, the memories, and the microSD card as ``MSC0:``.

Install
-------

Copy ``Cores``, ``Platforms``, ``Saves``, and ``Assets`` onto the microSD
card in the same folder structure. They merge with what's already there
and nothing replaces another core's files. Then open the core from the
Pocket menu under openFPGA.

ROMs
----

Put ``.rp6502`` files in ``Assets/rp6502/common/`` and the core asks you
to pick one when it opens. Find them on Discord, which has a forum for
ROMs, or on itch.io under the RP6502 tag:

- https://discord.gg/TC6X8kTr6d
- https://itch.io/games/tag-rp6502

Saves
-----

``Saves/rp6502/common/`` is the core's working directory, so a program's
plain ``open("game.save", ...)`` resolves there the same way it resolves
in the working directory on any other host.

Core Settings
-------------

The core menu has four entries: the keyboard layout, and a UTC offset
split across three of them.

- **Keyboard** selects the layout.

- **UTC offset** is three entries: a side, an hour, and a quarter hour.
  The Pocket knows nothing about time zones, so the offset and DST changes
  have to be set by hand. A list limit of sixteen options requires this
  setting to be split across three entries.


The Dock
========

The Pocket supports four controller slots, and the core passes all
four to the firmware as HID reports of buttons and axes. Keyboard and
mouse is fully supported as well.


Internals
=========

.. code-block:: text
   :class: diagram

   ┌─ the Pocket ─ APF shell, core_bridge_cmd ─── clk_74a 74.25 MHz ─────┐
   │ data slots · savestate · RTC · four controller slots · the scaler · │
   │ the I2S codec · the pad ring. Analogue's, unmodified.               │
   └──┬───────────────────────────────────────────────────────────┬──────┘
      │ bridge writes, target commands, controller state          │
      │                                     picture, sound, log   │
   ┌──┴───────────────────────────────────────────────────────────┴──────┐
   │ src/host/pocket — the wrapper                     clk_sys 50.4 MHz  │
   │ pocket_bridge  pocket_file  pocket_sst   pocket_video  pocket_i2s   │
   │ pocket_sdram   pocket_sram  pocket_dbg   pocket_dbglog  pocket_fifo │
   │ pocket_bars    pocket_pll: clk_sys ──> altclkctrl ──> clk_mach      │
   │                                                                     │
   │ ┌─────────────────────────────────────────────────────────────────┐ │
   │ │ src/rtl — the machine, platform independent                     │ │
   │ │                                                                 │ │
   │ │  ┌────────┐       ┌────────┐   w65c22 VIA at $FFD0-$FFDF        │ │
   │ │  │ w65c02 ├───────┤ w65c22 │   RP6502-RIA at $FFE0-$FFFF        │ │
   │ │  └───┬────┘       └────────┘                                    │ │
   │ │      │                                                          │ │
   │ │  ┌───┴────┐                                                     │ │
   │ │  │ria_regs│   phi2_div makes PHI2 — 0.1 to 8.0 MHz, exact       │ │
   │ │  └───┬────┘                                                     │ │
   │ │      │                                                          │ │
   │ │  ┌───┴─────────────────────────────────┐  clk_rv 25.2 MHz —     │ │
   │ │  │ rv_soc — Hazard3 RISC-V, 96 KB TCM  │  half clk_sys, off the │ │
   │ │  │ a trimmed build of src/ria firmware │  PLL, rising with it   │ │
   │ │  └───┬─────────────────────────────────┘                        │ │
   │ │      │ one system bus, one master                               │ │
   │ │  xram64k   vid_timing  vid_prog  vid_sched  vid_fill  vid_mode  │ │
   │ │  vid_mode0 vid_mode1 vid_mode2 vid_mode3 vid_mode4 vid_mode5    │ │
   │ │  vid_pixtail  vid_sprite  vid_sbuf  vid_palcache  vid_palram    │ │
   │ │  vid_font  vid_compose   aud_psg  aud_opl  aud_rsmp             │ │
   │ │  sst_engine, the serializer, on clk_sys, never gated            │ │
   │ └────┬────────────────────────────────┬───────────────────────────┘ │
   │      │ stage port,                    │ ram_a is the 6502's port,   │
   │      │ through pocket_sdram           │ ram_b the soft CPU's window,│
   │      │                                │ both through pocket_sram    │
   └──────┼────────────────────────────────┼─────────────────────────────┘
          │                                │
   ┌──────┴───────┐                 ┌──────┴──────────┐
   │ 64 MB SDRAM  │                 │ 256 KB SRAM     │  asynchronous,
   │ staging store│                 │ the 6502's 64 KB│  55 ns access
   │ ROM, fonts,  │                 └─────────────────┘
   │ code pages,  │                 the board's third chip, 16 MB of
   │ layouts      │                 PSRAM, is tied off and unused
   └──────────────┘

The RISC-V runs at half speed because its frontend is the one block
that can't make 50.4 MHz. Performance of this processor is not
critical - it only needs to keep up with IO to the Pocket.


MiSTer
======

Planned. The project needs a significant amount of review and reorganization
before additional platforms get added.
