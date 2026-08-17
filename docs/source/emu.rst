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

That's a real Picocomputer 6502 running a real ROM, and it's the same
WebAssembly build you can put on your own page or share on `itch.io
<https://itch.io/games/tag-rp6502>`__. The rest of this page is how.


Introduction
============

The Picocomputer 6502 is a machine, and a **host** is bound with a thin
wrapper that translates IO and OS services. There are eight hosts today —
Linux on x86_64 and aarch64, macOS, Windows, the browser, Android, the
:doc:`fpga`, and a pair of real Picos — and every one of them runs the
same machine.

This page is the software hosts. :doc:`fpga` is the one made of gates.
:doc:`pico` is a standalone machine you can build.

An emulator is expected to *be* an RP6502, not merely resemble one. It
runs the same 6502 code, answers the same registers, and maps its own
errors onto the same errno values the real hardware reports.

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
It's why everything you configure lives in one block at the top of the page:
upgrading is copying three files and re-applying that block.


Install
=======

Pre-built emulators are on the `releases page
<https://github.com/picocomputer/rp6502/releases/latest>`__. A project made from
the :doc:`sdk` template already fetched the right one into ``tools/``, so
you may have it already.

- **Linux** — a tarball. Built on Ubuntu 22.04, so it wants glibc 2.35 or
  later plus the GL, X11, and ALSA runtime libraries your desktop already
  has. The tarball preserves the execute bit; if something along the way
  stripped it, ``chmod +x rp6502-emu``.
- **macOS** — drag ``rp6502-emu.app`` to Applications. Apple silicon,
  macOS 11 or later. It isn't signed or notarized, so Gatekeeper blocks
  the first launch — allow it under System Settings > Privacy & Security >
  "Open Anyway", or ``xattr -dr com.apple.quarantine rp6502-emu.app``.
- **Windows** — ``rp6502-emu.exe`` needs no installer and a GPU with
  Direct3D 11. It isn't code signed, so SmartScreen warns on first launch;
  choose "More info" then "Run anyway".
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

``MSC0:`` is the directory you ran from, so a program's saves land beside
you. ``--tmpdrive`` swaps that for a fresh throwaway instead, which is how
you keep a ROM from writing anywhere you care about.

Everything after a bare ``--`` becomes the ROM's ``argv[1..]``, reaching
the program through `ARGV <os.html#argv>`__.

.. code-block:: text

  rp6502-emu --tmpdrive editor.rp6502 -- notes.txt


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
     - Drive input and check results. See `Scripting`_. Headless unless a
       window is also asked for.
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
     - Fixed seed for the random number generator, for runs that repeat
       exactly. Default is host entropy.
     - all
   * - ``--mute``
     - \-
     - No synthesis and no audio device opened at all.
     - all
   * - ``--debug``
     - \-
     - The on-screen machine debugger. Also holds the window open after
       the program exits, so you can look at where it stopped.
     - desktop
   * - ``--dap``
     - \-
     - Act as a DAP debug adapter on stdio. Implies ``--debug``.
     - desktop
   * - ``--ini``
     - ``file``
     - Where the debugger keeps its window layout. Defaults to your
       config directory; a project points it at ``.rp6502``.
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

``--dap`` and ``--script`` both want to drive the machine and both may
want stdin, so asking for both is an error rather than a race.


Web Builds
==========

The itch.io package in the `releases
<https://github.com/picocomputer/rp6502/releases/latest>`__ is a ready-to-publish
HTML5 project that plays one Picocomputer program in a browser. It's
generic on purpose — the page is the same for everyone, and the program
is yours.

Unpack it and you get the matched trio plus a sample program. Everything
you change lives in one block near the top of ``index.html``:

.. code-block:: text

  var CONFIG = {
    rom:    'adventure.rp6502',          // your program, next to this file
    title:  'Colossal Cave Adventure',   // browser tab title
    bg:     '000000',                    // letterbox fill, no '#'
    filter: 'sharp',                     // nearest | linear | sharp
    db:      '',    // save database name; blank = the rom filename
    persist: false, // true = saves are kept in the player's browser
  };

Those turn into the same arguments the command line takes, so ``bg`` and
``filter`` mean exactly what ``--bgcolor`` and ``--filter`` mean. Drop
your ``.rp6502`` next to ``index.html``, point ``rom`` at it, and delete
the sample.

Neither the package nor the tester works from a ``file://`` URL. The
browser needs an HTTP origin to fetch a ROM or stream the WebAssembly.
Any local server will do.

.. code-block:: text

  python3 -m http.server 8000

Gamepads work with nothing to configure. So does paste — Ctrl-V or Cmd-V
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

``MSC0:/db`` is the working directory, and with ``persist: true`` anything
your program writes there lands in an IndexedDB database in the player's
browser, which is how players keep saved games and high scores. Without
it, saves last until the player leaves the page and nothing touches
browser storage at all.

itch.io serves every HTML game from one shared origin, and IndexedDB is
per-origin, so your database name shares a namespace with every other
itch.io game the player runs. Two unrelated games that both ship
``game.rp6502`` will read and write each other's saves. Set ``db`` to
something unique — ``yourname-yourgame`` — and the problem goes away.
You can use this on purpose. Give several of your pages the same ``db``
and their programs share one ``MSC0:`` drive.


Debugging
=========

The emulator is a DAP debug adapter, so any editor that speaks the Debug
Adapter Protocol can do source-level debugging of 6502 code. :doc:`sdk`
covers the VS Code side, which is already wired up.

Both compilers get breakpoints on a source line, conditional and
hit-count breakpoints, logpoints, breakpoints on a function or an
instruction, watchpoints on data, stepping in and over and out, a call
stack with file and line, locals and globals and registers, watch and
hover expressions, assignment to a variable, reading and writing memory,
and disassembly.

What you don't get depends on which compiler you chose.

cc65 emits no DWARF, so the adapter reads the debug file ld65 writes
instead. That file carries no C type information at all — widths are
inferred from how the symbols sit in memory — and it describes no call
frames, so the call stack is walked by inspection rather than read. A
parameter passed in a register doesn't appear at all, and locals are
trustworthy where you stopped rather than part-way through an expression.

llvm-mos emits ELF with DWARF, so variables are typed, arrays and structs
and pointers expand, and the call stack is read rather than guessed.

Neither offers XRAM or XSTACK as variable scopes. Use the memory views.

Fuller DWARF for llvm-mos is being worked on upstream, and there are two
places to go look. The `DWARF overview
<https://llvm-mos.org/wiki/DWARF_overview>`__ on the llvm-mos wiki is the
write-up. The code is on the numbered ``feature/debug`` branches of `the
fork it's developed in
<https://github.com/johnwbyrd/llvm-mos/branches/all?query=feature%2Fdebug>`__,
highest number newest. Nothing is released, so trying it means building
LLVM from source.

The on-screen debugger
----------------------

``--debug`` opens the machine debugger over the emulated screen: the CPU
and VIA with their pins, the RIA's registers, an audio scope,
disassembly, execution history, breakpoints, a stopwatch, memory editors
for RAM and XRAM and XSTACK, a memory heatmap, and the linker's segments.
Options sets window and UI scale, the theme, and shows the loaded ROM's
own help.

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Key
     - Action
   * - ``F5``
     - Continue
   * - ``F6``
     - Break
   * - ``F8``
     - Step one cycle
   * - ``F9``
     - Toggle a breakpoint at the program counter
   * - ``F10``
     - Step over
   * - ``F11``
     - Step into

The Debug Adapter Protocol
--------------------------

``--dap`` speaks DAP on stdio. There's no port to connect to — the editor
launches the emulator and talks to it over the pipe.

The launch request takes ``program``, ``args``, and optionally ``elf`` or
``dbg`` to name the debug information. ``stopOnEntry`` breaks
before the first instruction. ``stopOnExit`` is on by default and keeps
the session alive after the program ends, so the final screen is still
there to look at.


Scripting
=========

.. note::

   Scripting is beta and may change.

``--script`` drives the machine with nobody at the keyboard. It types,
works the gamepads and the pointer, waits for the console to say
something, and checks what came out — enough to turn a ROM into a test
that either passes or fails.

.. code-block:: text

  rp6502-emu --mute --seed 1 --script adventure.txt adventure.rp6502

Given ``-`` instead of a filename it reads stdin a line at a time, which
is what lets a driver written in any language work the machine with no
protocol to implement. The machine waits for each line, so the driver is
the clock.

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
     - Let frames elapse. Default 1.
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

Reproducibility is the other half. ``--seed`` fixes the random number
generator, ``--mute`` takes the audio device out of the picture,
``--tmpdrive`` isolates the filesystem, and ``--frames`` with
``--screenshot`` renders without a window at all.
