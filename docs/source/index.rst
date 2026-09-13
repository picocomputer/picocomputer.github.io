:og:description: Write games for a real 6502 computer. Run them in your browser, or build the hardware for under $100.

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

.. raw:: html

   <iframe src="_static/emu/index.html"
           title="Space Raiders on the Picocomputer 6502"
           allow="gamepad; fullscreen; autoplay"
           allowfullscreen
           style="display: block; box-sizing: border-box;
                  width: 100%; max-width: 640px;
                  aspect-ratio: 4 / 3; max-height: 75vh;
                  margin: 0 auto 1em; background: #000;
                  border: 1px solid var(--color-background-border)"></iframe>

- Arrows move. Space, up, or down fires. Gamepads work too.
- ``1`` one player, ``2`` two players, ``p`` pause, ``r`` restart.


Why a Picocomputer
==================

Modern computers are astonishingly powerful, and that power creates
distance. Write a few lines of code and you're immediately standing on
top of millions of lines of software — enormous APIs, operating systems,
frameworks, layers of abstraction. AI makes that distance greater still:
you can ask a machine to produce something impressive without
necessarily understanding what happened.

The Picocomputer goes the other way. It's simple enough to learn
completely, and every layer under your program is documented on this site
for you to take on one at a time.

It's also powerful enough that you won't outgrow it. Your 6502 program
drives a video system and a sound system modeled on the arcades and home
computers of the 8-bit and 16-bit era, with far more headroom than those
machines ever had. Your game can throw hundreds of sprites across the
screen and pull in megabytes of art and music.


Write a Game
============

Start from the project template, open it in VS Code, and press F5. Hello
world builds and runs in the emulator, with breakpoints and a call
stack. No hardware, and nothing to buy.

When it's good, edit a couple of lines and upload it to itch.io, where
anyone can play it in a browser.

:doc:`sdk` has the details, from installing a compiler to debugging on
real hardware.


The Whole Machine
=================

- **CPU** — WDC 65C02 and a 65C22 VIA, 0.1 to 8.0 MHz, cycle accurate on
  every host
- **Memory** — 64 KB of RAM and 64 KB of XRAM, loaded by DMA at up to
  800 KB/sec while the 6502 keeps running. No ROM, nothing reserved, and
  zero page is yours
- **I/O** — 32 registers, and that's all of them. A modern processor
  sits behind them running the USB, the files, and the network, so the
  6502 never has to
- **Video** — three planes of tiles, bitmaps, and sprites in RGB555,
  programmable per scanline, with affine transforms on 16-bit sprites
- **Sound** — eight 48 kHz oscillators with ADSR and stereo panning, or
  a 9-voice OPL2 FM
- **Storage** — USB flash drives, and 3.5-inch floppy drives if you
  have one
- **Input** — keyboards, mice, tablets, and four gamepads, over USB or
  Bluetooth
- **Also** — Wi-Fi, MIDI, a real-time clock that handles Daylight
  Saving, and a true random number generator

All of it is documented on this site, down to the register.


Get a Machine
=============

You already have one. Games and applications are distributed as
``.rp6502`` ROM files, and every machine runs all of them.

- :doc:`emu` — the browser, Windows, macOS, Linux, Android, and
  RetroArch. Free, and where you start.
- :doc:`pico` — the one you build. 100% through-hole, no IC programmer,
  and you don't even have to solder — but you will plug eight ICs into
  their sockets. Usually under $100 USD.
- :doc:`fpga` — the whole machine in gates, on an Analogue Pocket today
  and MiSTer next.


Community
=========

Most of the action is on Discord, where you can also grab ROMs. Subscribe
to the YouTube channel and share the project around while you're at it.

- **Discord:** https://discord.gg/TC6X8kTr6d
- **Wiki:** https://github.com/picocomputer/community/wiki
- **GitHub Q&A:** https://github.com/picocomputer/community/discussions
- **YouTube:** https://www.youtube.com/@rumbledethumps


Read the Docs
=============

- :doc:`sdk`: writing software, from a new project to a running program.
- :doc:`ria`: the register map and every device reached through it — the
  interface adapter, in the spirit of the classic CIA, VIA, and ACIA
  chips.
- :doc:`ria_w`: setting up Wi-Fi, Bluetooth, telnet, and the Hayes modem.
- :doc:`vga`: canvases, video modes, sprites, and the scanline
  programming underneath.
- :doc:`term`: the console, its escape sequences, and the line editor.
- :doc:`os`: the system calls, the ABI, and the C library sitting on them.
