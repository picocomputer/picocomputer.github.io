:og:description: Write games for a real 6502 computer. Run them in your browser, or build the standalone machine for under $100.

.. toctree::
   :hidden:
   :caption: Manual

   SDK <sdk>
   API <api>
   RIA <ria>
   VGA <vga>
   TERM <term>
   PORT <port>

.. toctree::
   :hidden:
   :caption: Machine

   RP6502-PICO <pico>
   RP6502-PICO-W <ria_w>
   RP6502-FPGA <fpga>
   RP6502-EMU <emu>
   RP6502-WEB <web>

.. toctree::
   :hidden:
   :caption: Links

   GitHub <https://github.com/picocomputer?view_as=public>
   Discord <https://discord.gg/TC6X8kTr6d>
   YouTube <https://www.youtube.com/@rumbledethumps>

==================
Picocomputer 6502
==================

.. raw:: html

   <div class="showcase">
     <iframe src="_static/emu/index.html"
             title="Star Hopper on the Picocomputer 6502"
             allow="gamepad; fullscreen; autoplay"
             allowfullscreen></iframe>
     <div>
       <p>WASD, arrows, or numpad to move, any other key to fire. Gamepads work too.</p>
       <p><a href="https://jasonrowe.org/picocomputer/index.html">See more games by Dr. Jason Rowe</a></p>
     </div>
   </div>


Why a Picocomputer
==================

Modern computers are astonishingly powerful, and that power creates
distance. Write a few lines of code and you're immediately standing on
top of millions of lines of software, from enormous APIs and operating
systems to frameworks and layers of abstraction. AI makes that distance
greater still. You can ask a machine to produce something impressive
without necessarily understanding what happened.

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

You write in C or 6502 assembly, with either compiler, cc65 or llvm-mos,
or in Microsoft BASIC. The template comes with a hello world in each.

When it's good, publish it as a web page, where anyone can play it in a
browser. The steps are in :doc:`web`. For the ultimate flex, build an
:doc:`pico`.

The :doc:`sdk` has the details, from installing a compiler to running a
program on the RP6502-PICO.


The Machine
===========

A Picocomputer is any machine where a 6502 has access to a host that
handles modern I/O. The first host was built on the very affordable
Raspberry Pi Pico, which gave the project its name, but a Picocomputer
can exist on any host.

These are the features of the standalone machine, the :doc:`pico`:

- **CPU** — WDC 65C02 and a 65C22 VIA, 0.1 to 8.0 MHz, cycle accurate on
  every host
- **Memory** — 64 KB of RAM and 64 KB of XRAM, loaded by DMA at up to
  800 KB/sec while the 6502 keeps running. Nothing in RAM is reserved,
  not even zero page
- **I/O** — 32 registers, and that's all of them. Through them the 6502
  has access to the host, which handles USB, files, and the network
- **Video** — three planes of tiles, bitmaps, and sprites in RGB555,
  programmable per scanline, with affine transforms on 16-bit sprites
- **Sound** — eight oscillators with ADSR and stereo panning, or
  a 9-voice OPL2 FM
- **Storage** — USB flash drives, and 3.5-inch floppy drives if you
  have one
- **Input** — keyboards, mice, tablets, and four gamepads, over USB or
  Bluetooth
- **Also** — Wi-Fi, MIDI, a real-time clock that handles Daylight
  Saving, and a true random number generator


Read the Manual
===============

Start with the :doc:`sdk`, then the :doc:`api`. The datasheets after
them are for the parts of a Picocomputer. Read the datasheet for a part
when a program starts to use that part. Read :doc:`port` before the
program is published.

- :doc:`sdk`: writing software, from a new project to a running program.
- :doc:`api`: the system calls, the ABI, and the C library built on them.
- :doc:`ria`: direct access to keyboards, mice and gamepads, and the
  PSG and OPL2 sound generators.
- :doc:`vga`: canvases, video modes, sprites, and the scanline
  programming underneath.
- :doc:`term`: the console, its escape sequences, and the line editor.
- :doc:`port`: handling gamepads and files, which come from the host.


Get a Machine
=============

The standalone machine, the machine in fabric, the machine on the
device you use every day, and the machine for the web are all
Picocomputers.

- :doc:`pico` — the standalone machine, which you build yourself. 100%
  through-hole, no IC programmer, and you don't even have to solder.
  Built with a Pi Pico 2 W, it is the :doc:`ria_w`, with Wi-Fi and
  Bluetooth.
- :doc:`fpga` — the machine in fabric, on an Analogue Pocket today and
  MiSTer next.
- :doc:`emu` — the machine on the device you use every day, for
  Windows, macOS, Linux, and RetroArch.
- :doc:`web` — the machine for the web. Your program on a web page,
  playable in the browser.


Community
=========

Most of the action is on Discord, where you can also grab ROMs. Subscribe
to the YouTube channel and share the project on social media.

- **YouTube:** https://www.youtube.com/@rumbledethumps
- **Discord:** https://discord.gg/TC6X8kTr6d
- **Wiki:** https://github.com/picocomputer/.github/wiki
- **GitHub Q&A:** https://github.com/picocomputer/community/discussions
