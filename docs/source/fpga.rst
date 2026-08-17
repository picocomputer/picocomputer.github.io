============================
RP6502-FPGA
============================

RP6502 - Field Programmable Gate Array


Introduction
============

The whole machine, in fabric. The 65C02, the 65C22, and the entire
:doc:`vga` video system are RTL, and the RIA's operating system runs on a
Hazard3 RISC-V soft CPU executing a trimmed build of the same firmware C
the real machine runs. That isn't a reimplementation of the Picocomputer
— it's the Picocomputer, with the same split between a 6502 and something
modern minding the store.

Which means the Picocomputer 6502 is now entirely ours. Nothing in the
machine depends on a part only WDC makes, or a part only Raspberry Pi
makes. The 6502 is source. The VIA is source. The operating system runs
on a soft CPU anyone can put in any fabric. The design can be produced
whole from the repository, and nobody is in a position to end it.


The Analogue Pocket Core
========================

Everything the machine does, on a handheld. Every video mode, the PSG and
the OPL2, the dock, the keyboard layouts, the mouse, sleep, memories,
and the microSD card as ``MSC0:``.

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
plain ``open("game.save", ...)`` lands in the same place here as it does
everywhere else. An absolute name travels untouched, which is how you
reach the package's own folder — ``MSC0:/Assets/rp6502/common/`` is
writable too.

There is no delete, rename, or mkdir. The Pocket doesn't offer them.

Core Settings
-------------

Four entries, and the reasons are worth knowing.

**Keyboard** picks the layout. There's one entry rather than a list plus
an alternate, because on real hardware reaching the monitor to change
layouts interrupts whatever you were doing, and this menu is two button
presses away.

**UTC offset** is three entries — a side, an hour, and a quarter hour.
The Pocket knows nothing about time zones, so the offset has to be set by
hand, and a list holds at most sixteen options against an offset that
spans twenty-seven hours.

Sleep
-----

Sleeping produces a savestate, and the 6502 resumes on the exact cycle it
froze. Two things don't survive, both on purpose:

- The audio engines' internal state. The registers come back and a held
  note is re-keyed, but what the engines had made of them starts again —
  you may hear a click.
- Up to sixteen console bytes that hadn't been read yet. Reading them to
  save them would pop the queue, which would eat a character every time
  you made a savestate.

.. caution::

   Sleeping while a program is reading or writing a file can lose the
   program — the operation comes back EIO. This is a bug rather than a
   limit, tracked at `issue #183
   <https://github.com/picocomputer/rp6502/issues/183>`__.


The Dock
========

The Pocket hands the core four controller slots, and the core hands all
four straight to the firmware as HID reports — buttons and axes, exactly
what the Picocomputer expects. So the keyboard, the mouse, and
up to four controllers all work through the same drivers the real
hardware uses: international layouts, dead keys, key repeat, the escape
sequences a terminal expects, and four players in slot order.


Internals
=========

.. code-block:: text
   :class: diagram

   ┌─ the Pocket ─ APF shell, core_bridge_cmd ─── clk_74a 74.25 MHz ─────┐
   │ data slots · savestate · RTC · four controller slots · the scaler · │
   │ the I2S codec · the pad ring. Analogue's, and unchanged.            │
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
   │ staging store│                 │ the 6502's 64 KB│  55 ns every time
   │ ROM, fonts,  │                 └─────────────────┘
   │ code pages,  │                 the board's third chip, 16 MB of
   │ layouts      │                 PSRAM, is tied off and unused
   └──────────────┘

Read the boxes as nesting, not stacking. The top level is Analogue's
template with our clocks and one instance of the wrapper in it; the
wrapper holds one instance of the machine; and the machine knows nothing
about either. Everything the Pocket can say arrives over the APF bridge
on its own clock and is crossed once before the machine sees it.

The triangle in the middle is the real machine's split, in gates. The
6502 reaches the VIA at $FFD0 and the RIA's register window at $FFE0
exactly as it does on a board, and behind that window sits a Hazard3
RISC-V running the same firmware C an RP2350 runs, doing the same job:
syscalls, HID, and ROM loading. It's also the only master of the system
bus that reaches everything else, so every block below it hangs off one
line.

Two clocks and two chips finish the picture. The soft CPU runs at half
speed because its frontend is the one block that can't make 50.4 MHz, and
its clock comes from the PLL rather than a divider in the fabric. The
6502's 64 KB lives in the board's asynchronous SRAM, which answers in
55 ns every time — no rows, no refresh, nothing a program can do to make
it slower. For a machine whose promise is that the clock you asked for is
the clock you get, deterministic beats fast on average. The SDRAM is the
staging store the Pocket writes ROMs, fonts, code pages, and keyboard
layouts into, and the machine reads back a byte at a time.

All of it is checked against the emulator. The machine is simulated with
Verilator and run on the same ROMs as ``emu_core``, the same code the
:doc:`emu` is built from, and the two are compared.

What sleep takes away
---------------------

Closing the lid is a savestate, and a savestate is one clock gate.

.. code-block:: text
   :class: diagram

                     clk_sys 50.4 MHz, straight from the PLL
                                      │
                ┌─────────────────────┴─────────────────────┐
                │ one altclkctrl, ena taken on the falling  │
                │ edge, so no period is ever shortened      │
                └─────────────────────┬─────────────────────┘
                                      │ clk_mach
   ┌──────────────────────────────────┴─────────────────────────────────┐
   │ stopped, all of it, on the same missing edge — w65c02, w65c22,     │
   │ ria_regs, phi2_div, the bus, every vid_*, every aud_*, and the     │
   │ pixel and sample queues in pocket_video and pocket_i2s             │
   └────────────────────────────────────────────────────────────────────┘

     still clocked, because they still have work: the SDRAM controller,
     which refreshes itself; sst_engine and every array it owns; the APF
     bridge; and rv_soc, which is not gated at all — it is halted at its
     debug port and its registers are spilled through it a few injected
     instructions at a time.

Stopping the machine at the source is what makes this coherent. Every
register freezes on the same missing edge and resumes on the same
returned one, so there's no boundary condition to get wrong and no
special case for an instruction that was already waiting. Nothing inside
is gated, and nothing inside knows.


Building It
===========

A bitstream needs Quartus and ``gcc-riscv64-unknown-elf``, and nothing
else — no simulator and no test suite.

.. code-block:: text

  cd src/rtl
  cmake --preset pocket
  cmake --build --preset "Card package"

That assembles the whole card tree, ready to zip. The ``Bitstream``
preset stops one step earlier if that's all you want.

Placing and routing takes about nine minutes and happens when the RTL or
the constraints change. Putting new soft-CPU firmware into an existing
bitstream takes about twenty seconds, because firmware is the initial
contents of memory rather than logic — it places nothing and routes
nothing. CMake knows which of those your edit touched, so there's one
target to ask for and no decision to make.

Simulation is where development actually happens, and it wants Verilator,
Ninja, and a RISC-V toolchain with picolibc.

.. code-block:: text

  cd src/rtl
  cmake --preset verilator/Release
  cmake --build --preset Tests
  ctest --preset verilator/Release

See the `repository <https://github.com/picocomputer/rp6502>`__ for the
dependency lists.


MiSTer
======

Planned. It arrives as one more host directory and one more line in the
build, and the machine doesn't change. Every host is named explicitly for
exactly that reason.
