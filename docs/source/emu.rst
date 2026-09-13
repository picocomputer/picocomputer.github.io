============================
RP6502-EMU
============================

RP6502 - Emulator


Introduction
============

This page documents the software hosts. The :doc:`fpga` is the host made
of gates, and the :doc:`pico` is a standalone machine you can build.

An emulator is a first-class Picocomputer rather than a facsimile.
It runs the same 6502 code, responds to the same registers, and maps its
own errors onto the same errno values every other host reports.

What differs between the software hosts:

.. list-table::
   :widths: 28 22 18 16 16
   :header-rows: 1

   * -
     - Linux, macOS, Windows
     - Browser
     - Android
     - RetroArch
   * - On-screen debugger
     - yes
     - no
     - no
     - no
   * - DAP debug adapter
     - yes
     - no
     - no
     - no
   * - Scripting
     - yes
     - no
     - no
     - no
   * - Arguments
     - command line
     - config block
     - none
     - none
   * - Drop a ROM on the window
     - yes
     - no
     - no
     - no
   * - Save states
     - by script
     - no
     - no
     - yes, with rewind and netplay


Install
=======

Pre-built emulators are on the `releases page
<https://github.com/picocomputer/rp6502/releases/latest>`__. A project made from
the :doc:`sdk` template will fetch the right one into ``tools/``, so
you may have it already.

- **Windows** — ``rp6502-emu.exe`` is the program itself, not an installer.
  Requires  a GPU with Direct3D 11. It isn't code signed, so SmartScreen
  warns on first launch; choose "More info" then "Run anyway".
- **macOS** — drag ``rp6502-emu.app`` to Applications.
  It isn't signed or notarized, so Gatekeeper blocks
  the first launch — allow it under System Settings > Privacy & Security >
  "Open Anyway", or ``xattr -dr com.apple.quarantine rp6502-emu.app``.
- **Linux** — built on Ubuntu 22.04, so it needs glibc 2.35 or
  later plus the GL, X11, and ALSA runtime libraries.
  The tarball preserves the execute bit; if something
  along the way stripped it, ``chmod +x rp6502-emu``.
- **Android** — the APK from the same release.
- **RetroArch** — the core is in the Online Updater, under
  "Picocomputer 6502"; see `RetroArch`_ below.


Running Software
================

6502 software is distributed as files ending in ``.rp6502``. Find them on
Discord, which has a forum for ROMs, or on itch.io under the RP6502 tag:

- https://discord.gg/TC6X8kTr6d
- https://itch.io/games/tag-rp6502

Start the emulator with a ROM, or drag one onto the window.

.. code-block:: text

  rp6502-emu game.rp6502


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
   * - ``--help``
     - \-
     - Print the options and the script commands, then exit.
     - all
   * - ``--screenshot``
     - ``file.png``
     - Run headlessly, render the frames to PNG, and exit.
     - all
   * - ``--crc``
     - \-
     - Run headlessly, render the frames, print the canvas as a CRC-32
       on stdout, and exit.
     - all
   * - ``--frames``
     - number
     - Frames to run before the screenshot or the CRC. Default 120.
     - all
   * - ``--scale``
     - number
     - Window scale, fractional allowed. Default 1.5.
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
     - See `Scripting`_.
     - desktop
   * - ``--headless``
     - \-
     - No window and no picture. The program reads and writes the host's
       stdin, stdout and stderr, and its exit code becomes the emulator's.
       Implies ``--stdin``.
     - desktop
   * - ``--stdin``
     - \-
     - The host's stdin becomes the machine's console input. A terminal
       there becomes the console itself. Implied by ``--headless``. See
       `Standard Streams`_.
     - desktop
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
     - 6502 clock, 100 to 8000. Default 8000. ``0`` runs unpaced: the
       machine goes as fast as the host can take it.
     - all
   * - ``--cp``
     - number
     - OEM code page. 437, 720, 737, 771, 775, 850, 852, 855, 857,
       860-866, or 869. Default 437.
     - all
   * - ``--seed``
     - number
     - Fixed seed for the run, covering both the memory fill and the
       random numbers a program draws, so a run repeats exactly.
     - all
   * - ``--fill``
     - ``random``,
       or a byte
     - What RAM and XRAM hold before anything writes them. The default
       is ``random``. Supply a byte, as ``$00`` or ``0``, to start with
       known memory.
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
     - Where the debugger keeps its window layout.
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


Standard Streams
----------------

A program's ``stdout`` and ``stderr`` both show on the VGA
terminal, so someone at the screen sees an error even when the streams
are redirected somewhere else. On the desktop hosts they also reach
the process: ``stdout`` goes to the host's stdout and ``stderr`` to
the host's stderr, so a console program written for the Picocomputer
runs in a shell pipeline.

Host stdin becomes the machine's console input under ``--stdin``, which
``--headless`` implies. A pipe's end of file reaches the
program. Once the input is gone, a read of ``stdin`` returns 0 bytes.

.. code-block:: text

  rp6502-emu --headless --phi2 0 tool.rp6502 < input.txt > output.txt
  rp6502-emu --headless adventure.rp6502
  rp6502-emu --stdin game.rp6502           # a window, and the terminal too


Web Builds
==========

The itch.io package in the `releases
<https://github.com/picocomputer/rp6502/releases/latest>`__ is a ready-to-publish
HTML5 project that plays one Picocomputer ROM in a browser. The zip file
is deliberately correct for itch.io but is generic enough to use anywhere.
The game on the :doc:`home page <index>` is this package.

Unpack it to get the three matched files plus a sample program.
Everything you change lives in one block near the top of ``index.html``:

.. code-block:: text

  var CONFIG = {
    rom:    'adventure.rp6502',          // change to your program
    title:  'Colossal Cave Adventure',   // browser tab title
    bg:     '000000',                    // letterbox fill, no '#'
    filter: 'sharp',                     // nearest | linear | sharp
    db:      '',    // save database name; blank = the rom filename
    persist: false, // true = saves are kept in the player's browser
  };

Neither the package nor the tester works from a ``file://`` URL. The
browser needs an HTTP origin to fetch a ROM or stream the WebAssembly.
Any local server will do.

.. code-block:: text

  python3 -m http.server 8000

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

``/db`` is the working directory. With ``persist: true``, anything
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
same ``db`` and their programs share one filesystem.


RetroArch
=========

The Picocomputer is also a libretro core, which is how it reaches
RetroArch and the launchers built on it. Install it from Online Updater >
Core Downloader, under "Picocomputer 6502", then load a ``.rp6502`` ROM
as content the way you would a cartridge.


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
display. The program's ``stdout`` and ``stderr`` reach the Debug Console
as output events of those two categories, so VS Code shows ``stderr`` in
red; the emulated terminal in the window shows both.


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
driver written in any language can work the machine. The machine waits
for each line, so the driver sets the pace. See `Driving it from a
program`_.

A script always runs headless, and nothing paces
it against the host's clock. Frames elapse only when the script asks for
them, so ``run 600`` is six hundred frames and six hundred VSYNCs every
time.

One command per line. ``#`` starts a comment anywhere outside quotes.
Text is always in double quotes and takes ``\n``, ``\r``, ``\t``,
``\\``, and ``\"``. Numbers may be decimal, C-style ``0xFF``, or
MOS-style ``$FF``.

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
   * - ``wait [xram:|ram:]<addr> <byte> [frames]``
     - Run until that byte reads that value. The byte is read once a
       frame, at the boundary.
   * - ``type "text" [frames]``
     - Type it. ``\r`` is Enter, ``\t`` is Tab. Waits for the keyboard
       ring to take it all; default budget 600 frames.
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
   * - ``mark``,
       ``expect-same``,
       ``expect-changed``
     - Remember the screen, then check it against what you remembered.
   * - ``shot "file.png"``
     - Write the screen.
   * - ``state save "file"``,
       ``state load "file"``
     - Save the whole machine to a file, and load it back.
   * - ``seed``
     - Print the seed this run filled memory with.
   * - ``install "path" [NAME]``,
       ``remove <NAME>``
     - Install a ROM on the null drive as ``:NAME``, and remove it again.
       The default name is the file's own basename.
   * - ``load "path"``
     - Boot a program. The machine must be stopped, since loading writes
       the memory a running program is using.
   * - ``sys run|stop|break``
     - Start the machine, stop it, or interrupt it the way a break at
       the console would.
   * - ``reply [on|off]``
     - Answer every command on stdout. See `Driving it from a program`_.

A failed check names the script and the line it was on, then exits 1,
which is what a test runner needs.

Memory starts random, as it often does on real hardware. This will catch
uninitialize memory usage... eventually. ``--fill 00`` gives a test
known memory when it needs it.


Driving it from a program
-------------------------

.. note::

   Scripting is beta and may change.

A script file is a list of commands that drive the emulator. ``--script -``
is the other half: the machine reads one line at a time and waits, so a
program on the other end of the pipe can test the machine.

``reply`` turns on one line of answer per command — ``ok``, ``ok <values>``
for ``dump`` and ``crc``, or ``fail <why>``. It is off until asked, so a
driver writes its whole preamble without waiting for anything and reads the
``ok`` for ``reply`` itself as the moment the machine starts answering.

An answer comes when the command **finishes**, not when it parses. The
``ok`` for ``run 600`` arrives six hundred frames later, and the one for
``wait $0200 $07`` arrives when that byte reads 7.

.. code-block:: text

  reply                    -> ok
  run 60                   -> ok            (sixty frames later)
  pad 0 connect            -> ok
  pad 0 press start        -> ok
  run 10                   -> ok
  dump xram:$FF00 4        -> ok 80 00 00 08
  peek xram:$FF00 $99      -> fail $FF00+0 is $80, expected $99

Any language that can write a pipe and read a line back can drive the emulator.
The arithmetic and the assertions belong in your driver program, which is
why you don't see any in this scripting lanugage.
