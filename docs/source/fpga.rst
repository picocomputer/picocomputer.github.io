============================
RP6502-FPGA
============================

RP6502 - Field Programmable Gate Array


Introduction
============

The RP6502-FPGA is the Picocomputer 6502 in programmable logic. The
65C02, the 65C22, and the entire :doc:`vga` video system are RTL, and the
RIA's operating system runs on a Hazard3 RISC-V soft CPU executing a
trimmed build of the same firmware C the real machine runs. It keeps the
same split between a 6502 and a modern processor providing its services,
which is what makes this a Picocomputer.

Nothing in the machine depends on a part only WDC makes, or a part only
Raspberry Pi makes. The 6502 is source, the VIA is source, and the
operating system runs on a soft CPU anyone can put in any fabric. The
whole design can be produced from the repository.


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
in the working directory on any other host. An absolute name is used as
given, which is how you reach the package's own folder —
``MSC0:/Assets/rp6502/common/`` is writable too.

The Pocket offers no way to delete, rename, or create a directory, so
neither does the core.

Core Settings
-------------

The core menu has four entries: the keyboard layout, and a UTC offset
split across three of them.

- **Keyboard** selects the layout. One entry covers it, because on real
  hardware reaching the monitor to change layouts interrupts whatever you
  were doing, and this menu is two button presses away.

- **UTC offset** is three entries: a side, an hour, and a quarter hour.
  The Pocket knows nothing about time zones, so the offset has to be set
  by hand, and a list holds at most sixteen options against an offset
  that spans twenty-seven hours.

Sleep
-----

The Power Button sleeps the Pocket and wakes it again. Sleeping produces
a savestate, and the 6502 resumes on the exact cycle it froze. Two things
do not survive, by design:

- The audio engines' internal state. The savestate holds their registers
  but not the synthesis in progress, so a held note is re-keyed on wake
  and you may hear a click.
- Up to sixteen console bytes that had not been read yet. Reading them to
  save them would pop the queue, which would eat a character every time
  you made a savestate.

.. caution::

   Sleeping while a program is reading or writing a file can lose the
   program — the operation comes back EIO. This is a bug, not a
   limitation, and is tracked at `issue #183
   <https://github.com/picocomputer/rp6502/issues/183>`__.


The Dock
========

The Pocket hands the core four controller slots, and the core passes all
four to the firmware as HID reports of buttons and axes, which is what
the Picocomputer expects. The keyboard, the mouse, and up to four
controllers therefore run on the same drivers the real hardware uses,
with international layouts, dead keys, key repeat, the escape sequences a
terminal expects, and four players in slot order.


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
   │ │  ┌────────┐       ┌────────┐   the VIA at $FFD0-$FFDF and the   │ │
   │ │  │ w65c02 ├───────┤ w65c22 │   RIA window at $FFE0-$FFFF, where │ │
   │ │  └───┬────┘       └────────┘   they sit on a real board         │ │
   │ │      │                                                          │ │
   │ │  ┌───┴────┐   phi2_div makes PHI2 a clock enable on clk_mach,   │ │
   │ │  │ria_regs│   not a clock of its own — 0.1 to 8.0 MHz, exact    │ │
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

The boxes nest rather than stack. The top level is Analogue's template
with the project's clocks and one instance of the wrapper in it, the
wrapper holds one instance of the machine, and the machine knows nothing
about either.
Everything the Pocket can say arrives over the APF bridge on its own
clock and is crossed once before the machine sees it.

The inner box holds the same split the real machine has, in gates. The
6502 reaches the VIA at $FFD0 and the RIA's register window at $FFE0
exactly as it does on a board, and behind that window a Hazard3 RISC-V
runs the same firmware C an RP2350 runs, doing the same job: syscalls,
HID, and ROM loading.

The soft CPU runs at half speed because its frontend is the one block
that can't make 50.4 MHz. The 6502's 64 KB lives in the board's
asynchronous SRAM. The SDRAM is the staging store the Pocket writes ROMs,
fonts, code pages, and keyboard layouts into.

The machine is tested against the emulator. It is simulated with
Verilator and run on the same ROMs as ``emu_core``, the same code the
:doc:`emu` is built from, and the two are compared.


MiSTer
======

Planned.
