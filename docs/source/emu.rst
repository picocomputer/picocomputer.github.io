============================
RP6502-EMU
============================

RP6502 - Emulator


Space Raiders
=============

.. raw:: html

   <iframe class="emu-frame"
           src="_static/emu/index.html"
           title="Space Raiders on the Picocomputer 6502"
           width="640" height="480"
           allow="gamepad; fullscreen; autoplay"
           allowfullscreen></iframe>

- ``1`` one player, ``2`` two players, ``p`` pause,  ``r`` restart.
- Arrows move. Space, up, or down fires.
- Gamepads: left stick to move, any button to fire.

That is a real Picocomputer 6502 running a real ROM. It is the same
WebAssembly build you can put on your own page or share on `itch.io
<https://itch.io/games/tag-rp6502>`__, and the rest of this page covers
how to do that.


Introduction
============

The Picocomputer 6502 is a machine, and a **host** binds it to a thin
wrapper that translates IO and OS services. There are eight hosts today:
Linux on x86_64 and aarch64, macOS, Windows, the browser, Android, the
:doc:`fpga`, and a pair of real Picos. Every one of them runs the same
machine.

This page documents the software hosts. The :doc:`fpga` is the host made
of gates, and the :doc:`pico` is a standalone machine you can build.

An emulator here is an RP6502 rather than something that resembles one.
It runs the same 6502 code, answers the same registers, and maps its own
errors onto the same errno values every other host reports.

What differs between the software hosts:

.. list-table::
   :widths: 30 25 25 20
   :header-rows: 1

   * -
     - Linux, macOS, Windows
     - Browser
     - Android
   * - On-screen debugger
     - yes
     - no
     - no
   * - DAP debug adapter
     - yes
     - no
     - no
   * - Scripting
     - yes
     - no
     - no
   * - Arguments
     - command line
     - config block
     - none
   * - Drop a ROM on the window
     - yes
     - no
     - no

The browser build is three files — ``index.html``, ``rp6502.js``, and
``rp6502.wasm`` — and they are **one matched set from a single build**.
Everything you configure therefore lives in one block at the top of the
page, so upgrading is a matter of copying three files and re-applying
that block.


Install
=======

Pre-built emulators are on the `releases page
<https://github.com/picocomputer/rp6502/releases/latest>`__. A project made from
the :doc:`sdk` template already fetched the right one into ``tools/``, so
you may have it already.

- **Linux** — a tarball. Built on Ubuntu 22.04, so it needs glibc 2.35 or
  later plus the GL, X11, and ALSA runtime libraries.
  The tarball preserves the execute bit; if something
  along the way stripped it, ``chmod +x rp6502-emu``.
- **macOS** — drag ``rp6502-emu.app`` to Applications. Apple silicon,
  macOS 11 or later. It isn't signed or notarized, so Gatekeeper blocks
  the first launch — allow it under System Settings > Privacy & Security >
  "Open Anyway", or ``xattr -dr com.apple.quarantine rp6502-emu.app``.
- **Windows** — ``rp6502-emu.exe`` is the program itself, not an installer.
  Requires  a GPU with Direct3D 11. It isn't code signed, so SmartScreen
  warns on first launch; choose "More info" then "Run anyway".
- **Android** — the APK from the same release.

6502 software is distributed as files ending in ``.rp6502``. Find them on
Discord, which has a forum for ROMs, or on itch.io under the RP6502 tag:

- https://discord.gg/TC6X8kTr6d
- https://itch.io/games/tag-rp6502


Running Software
================

Hand the emulator a ROM, or drag one onto the window.

.. code-block:: text

  rp6502-emu game.rp6502

``--rom`` installs a ROM on the null drive instead of booting it, where it
can be reached as ``:basename`` — the same way an installed ROM works on
real hardware. It repeats up to sixteen times, and the first one boots if
you didn't name a ROM to run.

.. code-block:: text

  rp6502-emu --rom menu.rp6502 --rom game.rp6502

``MSC0:`` is the directory you ran from, so a program's saves land in the
same directory. Everything after a bare ``--`` becomes the ROM's
``argv[1..]``, reaching the program through `ARGV <os.html#argv>`__.

.. code-block:: text

  rp6502-emu editor.rp6502 -- notes.txt


Arguments
=========

.. note::

   Arguments are beta and may change.

There are no short options. Both ``--opt value`` and ``--opt=value``
work.

.. list-table::
   :widths: 20 25 45 10
   :header-rows: 1

   * - Option
     - Value
     - Description
     - Hosts
   * - ``--screenshot``
     - ``file.png``
     - Run headlessly, render one frame to PNG, and exit.
     - all
   * - ``--frames``
     - number
     - Frames to run before the screenshot. Default 120.
     - all
   * - ``--scale``
     - number
     - Window scale, fractional allowed. Default 1.5.
     - desktop
   * - ``--vsync``
     - \-
     - Sync presentation to the display. The default.
     - desktop
   * - ``--no-vsync``
     - \-
     - Present uncapped, pacing the machine in software instead.
     - desktop
   * - ``--filter``
     - ``nearest``,
       ``linear``,
       ``sharp``
     - How pixels are scaled to the window. Default ``sharp``, which
       prescales by an integer and then interpolates.
     - all
   * - ``--script``
     - ``file``, or
       ``-``
     - Drive input and check results. See `Scripting`_. Always headless,
       and the script controls all timing.
     - desktop
   * - ``--tmpdrive``
     - \-
     - Make ``MSC0:`` a fresh throwaway instead of the current directory.
     - all
   * - ``--rom``
     - ``file``
     - Install a ROM on the null drive, reached as ``:basename``.
       Repeatable to sixteen; the first one boots.
     - all
   * - ``--bgcolor``
     - ``RRGGBB``
     - Letterbox and pillarbox fill. Default ``000000``.
     - all
   * - ``--phi2``
     - kHz
     - 6502 clock, 100 to 8000. Default 8000.
     - all
   * - ``--cp``
     - number
     - OEM code page. 437, 720, 737, 771, 775, 850, 852, 855, 857,
       860-866, or 869. Default 437.
     - all
   * - ``--seed``
     - number
     - Fixed seed for the run, covering both the memory fill and the
       random numbers a program draws, so a run repeats exactly. The
       default is host entropy, and a run that uses it reports the seed
       it chose.
     - all
   * - ``--fill``
     - ``random``,
       or a byte
     - What RAM and XRAM hold before anything writes them. The default
       is ``random``, which is what the hardware gives a program. Supply
       a byte, as ``$00`` or ``0``, to start with known memory.
     - all
   * - ``--mute``
     - \-
     - No synthesis and no audio device opened at all.
     - all
   * - ``--debug``
     - \-
     - The on-screen machine debugger. It also holds the window open
       after the program exits, so you can examine where it stopped.
     - desktop
   * - ``--dap``
     - \-
     - Act as a DAP debug adapter on stdio. Implies ``--debug``.
     - desktop
   * - ``--ini``
     - ``file``
     - Where the debugger keeps its window layout. Defaults to your
       config directory; an :doc:`sdk` project points it at ``.rp6502``
       in the project root.
     - desktop
   * - ``--credits``
     - \-
     - Print third-party credits and licenses, then exit.
     - all
   * - ``--version``
     - \-
     - Print the version and exit.
     - all
   * - ``--``
     - words
     - Pass everything after this to the ROM as ``argv[1..]``.
     - all

``--dap`` and ``--script`` both drive the machine and both may need
stdin, so requesting both is an error.


Web Builds
==========

The itch.io package in the `releases
<https://github.com/picocomputer/rp6502/releases/latest>`__ is a ready-to-publish
HTML5 project that plays one Picocomputer ROM in a browser. The page
is deliberately generic: it is the same for everyone, and the ROM is
provided by you.

Unpack it to get the three matched files plus a sample program.
Everything you change lives in one block near the top of ``index.html``:

.. code-block:: text

  var CONFIG = {
    rom:    'adventure.rp6502',          // your program, next to this file
    title:  'Colossal Cave Adventure',   // browser tab title
    bg:     '000000',                    // letterbox fill, no '#'
    filter: 'sharp',                     // nearest | linear | sharp
    db:      '',    // save database name; blank = the rom filename
    persist: false, // true = saves are kept in the player's browser
  };

These become the same arguments the command line takes, so ``bg`` and
``filter`` mean exactly what ``--bgcolor`` and ``--filter`` mean. Drop
your ``.rp6502`` next to ``index.html``, point ``rom`` at it, and delete
the sample.

Neither the package nor the tester works from a ``file://`` URL. The
browser needs an HTTP origin to fetch a ROM or stream the WebAssembly.
Any local server will do.

.. code-block:: text

  python3 -m http.server 8000

Gamepads need no configuration. Neither does paste — Ctrl-V or Cmd-V
types the clipboard into the emulated keyboard.

Publishing to itch.io
---------------------

Zip the *contents* of the folder so ``index.html`` sits at the root of the
archive, not inside a subfolder. Create a project, set the kind to HTML,
upload the zip, and tick "This file will be played in the browser".

For the embed settings, set the size manually to 640x480 or 640x360 — 320
wide programs scale up. Leave scrollbars off and leave SharedArrayBuffer
off.

Please tag your project **RP6502** so it turns up alongside everything
else at https://itch.io/games/tag-rp6502.

Saves and browser storage
-------------------------

``MSC0:/db`` is the working directory. With ``persist: true``, anything
your program writes there lands in an IndexedDB database in the player's
browser, which is how players keep saved games and high scores. Without
it, saves last until the player leaves the page and nothing touches
browser storage at all.

itch.io serves every HTML game from one shared origin, and IndexedDB is
per-origin, so your database name shares a namespace with every other
itch.io game the player runs. Two unrelated games that both ship
``game.rp6502`` will read and write each other's saves. Set ``db`` to
something unique, such as ``yourname-yourgame``, to avoid this.

The same behavior is useful deliberately. Give several of your pages the
same ``db`` and their programs share one ``MSC0:`` drive.


Debugging
=========

The emulator is a DAP debug adapter, so any editor that speaks the Debug
Adapter Protocol can do source-level debugging of 6502 code. :doc:`sdk`
covers the VS Code side, which is already wired up.

Both compilers support breakpoints on a source line, conditional and
hit-count breakpoints, logpoints, breakpoints on a function or an
instruction, watchpoints on data, stepping in and over and out, a call
stack with file and line, locals and globals and registers, watch and
hover expressions, assignment to a variable, reading and writing memory,
and disassembly.

The limitations depend on which compiler you chose.

cc65 emits no DWARF, so the adapter reads the debug file ld65 writes
instead. That file carries no C type information, so widths are inferred
from how the symbols sit in memory, and it describes no call frames, so
the call stack is walked by inspection rather than read. A parameter
passed in a register does not appear at all, and locals are trustworthy
where you stopped rather than part-way through an expression.

llvm-mos emits ELF with DWARF, so variables are typed, arrays and structs
and pointers expand, and the call stack is read rather than guessed.

Neither offers XRAM or XSTACK as variable scopes. Use the memory views.

Fuller DWARF for llvm-mos is being worked on upstream. The `DWARF
overview <https://llvm-mos.org/wiki/DWARF_overview>`__ on the llvm-mos
wiki describes the work, and the code is on the numbered
``feature/debug`` branches of `the fork it's developed in
<https://github.com/johnwbyrd/llvm-mos/branches/all?query=feature%2Fdebug>`__.
Nothing is released, so trying it means building LLVM from source.

The on-screen debugger
----------------------

``--debug`` opens the machine debugger over the emulated screen: the CPU
and VIA with their pins, the RIA's registers, an audio scope,
disassembly, execution history, breakpoints, a stopwatch, memory editors
for RAM and XRAM and XSTACK, a memory heatmap, and the linker's segments.
The Options menu sets window and UI scale and the theme, and it shows the
loaded ROM's own help.

The Debug Adapter Protocol
--------------------------

``--dap`` speaks DAP on stdio. There is no port to connect to; the editor
launches the emulator and talks to it over the pipe.

The launch request takes ``program``, ``args``, and optionally ``elf`` or
``dbg`` to name the debug information. ``stopOnEntry`` breaks
before the first instruction. ``stopOnExit`` is on by default and keeps
the session alive after the program ends, so the final screen remains on
display.


Scripting
=========

.. note::

   Scripting is beta and may change.

``--script`` drives the machine with no one at the keyboard. It types,
works the gamepads and the pointer, waits for expected console output,
and checks what the program produced, which is enough to turn a ROM into
a test that passes or fails.

.. code-block:: text

  rp6502-emu --mute --seed 1 --script adventure.txt adventure.rp6502

Given ``-`` instead of a filename it reads stdin a line at a time, so a
driver written in any language can work the machine with no protocol to
implement. The machine waits for each line, so the driver sets the pace.

A script always runs headless, and nothing paces
it against the host's clock. Frames elapse only when the script asks for
them, so ``run 600`` is six hundred frames and six hundred VSYNCs every
time.

One command per line. ``#`` starts a comment. Text is always in double
quotes and takes ``\n``, ``\r``, ``\t``, ``\\``, and ``\"``. Numbers may
be decimal, C-style ``0xFF``, or MOS-style ``$FF``.

.. code-block:: text

  wait "Colossal Cave Adventure"
  wait "Would you like instructions?"
  type "no\n"
  wait "standing at the end of a road"
  type "take lamp\n"
  wait "I see no lamp here"

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Command
     - Description
   * - ``run [frames]``
     - Let exactly that many frames elapse, one VSYNC each. Default 1.
   * - ``wait "text" [frames]``
     - Run until the console says it. Default budget 600 frames.
   * - ``type "text"``
     - Type it. ``\n`` is Enter, ``\t`` is Tab.
   * - ``key <name>[+ctrl][+shift][+alt]``
     - Send a key's escape sequence.
   * - ``press <key>...``,
       ``release <key>...``
     - The direct HID bitmap, by name or usage ID.
   * - ``lock num|caps|scroll``
     - Toggle a lock LED.
   * - ``pad <n> connect [western|eastern|playstation] [sticks]``,
       ``pad <n> disconnect``
     - Attach or detach one of four gamepads, optionally saying how its
       buttons are labeled.
   * - ``pad <n> press|release <button>...``
     - ``a b c x y z l1 r1 l2 r2 l3 r3 select start home up down left
       right``
   * - ``pad <n> stick <lx> <ly> <rx> <ry>``
     - Each -128 to 127.
   * - ``pad <n> trigger <lt> <rt>``
     - Each 0 to 255.
   * - ``mouse move <dx> <dy>``,
       ``mouse wheel <n> [pan]``,
       ``mouse buttons <mask>``
     - Work the mouse.
   * - ``tablet at <x> <y> [buttons]``,
       ``tablet touch <x>,<y>...``,
       ``tablet wheel <n> [pan]``,
       ``tablet clear``
     - Work the absolute pointer, including multi-touch.
   * - ``expect "text"``,
       ``expect-not "text"``
     - Check the console since the last check. A match consumes up to and
       including it.
   * - ``expect-exit <code> [frames]``
     - Run until the program exits, then check its code.
   * - ``peek [xram:|ram:]<addr> <byte>...``
     - Compare memory.
   * - ``poke [xram:|ram:]<addr> <byte>...``
     - Write memory. The program reads what you wrote, so a test can
       skip ahead to the state it needs to exercise.
   * - ``dump [xram:|ram:]<addr> [count]``
     - Print memory as hex.
   * - ``crc``
     - Print the screen as a CRC-32.
   * - ``expect-crc <hash>``
     - Compare the screen against a known one.
   * - ``mark``,
       ``expect-same``,
       ``expect-changed``
     - Remember the screen, then check it against what you remembered.
   * - ``shot "file.png"``
     - Write the screen.

A failed check names the script and the line it was on, then exits 1,
which is all a test runner needs.

Memory starts random, as it does on real hardware. The 6502's SRAM keeps
whatever was last in it, and neither the RIA nor the VGA clears XRAM, so
a program that reads a byte it never wrote fails here instead of only on
hardware. ``--fill 00`` gives a test known memory when it needs it.

``--seed`` fixes both the fill and the numbers ``lrand`` returns, and it
fixes them independently — the same seed gives a program the same random
sequence whatever ``--fill`` says. An unseeded run reports its seed on
stderr, so a failure
found by a random fill can be repeated. ``--mute`` removes the audio
device, ``--tmpdrive`` isolates the filesystem, and ``--frames`` with
``--screenshot`` renders without a window at all.
