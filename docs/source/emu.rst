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
wrapper that translates IO and OS services. There are nine hosts today:
Linux on x86_64 and aarch64, macOS, Windows, the browser, Android,
RetroArch, the :doc:`fpga`, and a pair of Pi Picos. Every one of them
runs the same machine.

This page documents the software hosts. The :doc:`fpga` is the host made
of gates, and the :doc:`pico` is a standalone machine you can build.

An emulator here is an RP6502 rather than something that resembles one.
It runs the same 6502 code, answers the same registers, and maps its own
errors onto the same errno values every other host reports.

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
- **RetroArch** — the core is in the Online Updater, under
  "Picocomputer 6502". The release page carries one zip holding every
  platform we build, for a frontend without an updater; see `RetroArch`_
  below.

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
can be reached as ``:basename`` — the same way an :doc:`pico` reaches a
ROM installed in its flash. It repeats up to sixteen times, and the
first one boots if
you didn't name a ROM to run.

.. code-block:: text

  rp6502-emu --rom menu.rp6502 --rom game.rp6502

The directory you ran from is the working directory, so a program's saves
land in the same directory. Paths are the host's own: ``getcwd`` answers
``/home/me`` here and ``C:/Users/me`` on Windows, and ``FS:`` is a name
the drive answers to rather than one it puts in front of a path. Everything after a bare ``--`` becomes the ROM's
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
       on stdout, and exit. Combines with ``--screenshot``.
     - all
   * - ``--frames``
     - number
     - Frames to run before the screenshot or the CRC. Default 120. Only
       with ``--screenshot`` or ``--crc``; a script's frames are its own,
       see ``run``.
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
     - Drive input and check results. See `Scripting`_. Always headless,
       and the script controls all timing.
     - desktop
   * - ``--headless``
     - \-
     - No window and no picture. Host stdin, stdout, and stderr are the
       program's, and the exit code is the program's. Implies ``--stdin``.
       See `Standard Streams`_. Paced like a window; add ``--phi2 0`` for
       a console program that should run flat out.
     - desktop
   * - ``--stdin``
     - \-
     - The host's stdin is the machine's console input. A terminal there
       becomes the console itself. Implied by ``--headless``; give it by
       name to hook a terminal up to a run that also has a window. See
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
       machine goes as fast as the host can take it, and every clock in
       it warps with it.
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
       is ``random``, which is what a machine gives a program. Supply
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
stdin, so requesting both is an error. ``--headless`` is the program
alone on the host's streams, so it takes none of ``--script``,
``--screenshot``, ``--crc``, ``--dap``, or ``--debug``. ``--stdin``
wants the same stdin as ``--script`` and ``--dap``, and answers on the
stdout that ``--crc`` prints its value to, so it takes none of those
three either.

Standard Streams
----------------

A program's ``stdout`` and ``stderr`` both show on the emulated
terminal, so an error is never hidden from someone at the screen. On
the desktop hosts they also reach the process: ``stdout`` goes to the
host's stdout and ``stderr`` to the host's stderr, as UTF-8 with no
newline translation, so a console program written for the Picocomputer
runs in a shell pipeline. Host stdout stays the emulator's own under
``--script`` (the replies), ``--dap`` (the wire), and ``--crc`` (the
value).

Host stdin is the machine's console input under ``--stdin``, which
``--headless`` implies. It arrives where the hardware's serial console
arrives, so all three ways of reading it work: the ``$FFE0`` and
``$FFE2`` registers, ``stdin`` through the line editor, and ``TTY:``
opened by name and read raw. A pipe's end of file is the program's:
once the input is gone, a read of ``stdin`` answers 0 bytes.

Nothing is translated on the way in. The wire carries what the far end
sent, byte for byte, the way a serial console does: no code page
conversion, and no rewriting of line endings. The line editor ends a
line on either spelling, so a terminal sending a return for Enter and a
file holding line feeds both work. What stdin *is* still matters. A
terminal is typed at: its keys reach the machine as they are struck,
whatever stdout is, and a Ctrl-C is both the byte and a SIGINT the
program can catch. A pipe or a file is read only as fast as the program
takes it, so nothing in it is lost, and a ``0x03`` in it is a byte and
nothing more.

.. code-block:: text

  rp6502-emu --headless --phi2 0 tool.rp6502 < input.txt > output.txt

Paste is the other direction and the other rule: a clipboard is the
host's text, so ``Ctrl-V`` converts it to the machine's code page and
spells its line ends the way the line editor reads them.

When the host's stdin and stdout are the same terminal, that terminal
*is* the console. Both ways, because a terminal on stdin with a file on
stdout is a pipeline, and the machine's screen does not belong in the
file: redirect either one and the program's output goes there instead,
exactly as above. Keys reach the machine as they are struck, so Ctrl-C
is a byte the program can catch rather than something that kills the
emulator; the machine draws its screen on the terminal; and the terminal
answers the queries a program makes about size and cursor, which the
emulated one then stops answering so a program never hears two replies.
The window, if there is one, goes on showing the same screen.

Ctrl-\\ is the way out, and it is the only key held back from the
machine: a program that has stopped listening can still be left. On
Windows the same key is Ctrl-Break, which a console never gives a
program. Either one breaks the machine, so every driver is stopped in
order and the terminal is handed back, whatever a debugger was holding at
the time. The emulator then leaves the way it was asked to, dying of the
signal that asked, so a shell loop or a ``make`` sees a run that was
interrupted rather than one that merely failed. Pressing it a second time
leaves at once, for a machine too wedged to reach its own teardown.
Closing the window breaks the machine the same way, and exits with a code
because a window closing is not a signal.

.. code-block:: text

  rp6502-emu --headless adventure.rp6502
  rp6502-emu --stdin game.rp6502           # a window, and the terminal too


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
RetroArch and the launchers built on it — including the handhelds that
ship one. Install it from Online Updater > Core Downloader, under
"Picocomputer 6502", then load a ``.rp6502`` as content the way you
would a cartridge.

To run a core you have downloaded yourself, take the folder for your
machine out of the release zip — ``linux-x86_64``, ``linux-aarch64``,
``windows-x86_64``, ``macos-arm64`` or ``android-arm64`` — and put the
core in the directory
your frontend keeps cores in, with ``rp6502_libretro.info`` beside it in
the info directory. RetroArch prints both paths under Settings >
Directory. You can also skip installing it:

.. code-block:: text

  retroarch -L rp6502_libretro.so game.rp6502

The Picocomputer is a computer, so a program may want a keyboard as well
as a gamepad, and the keyboard needs one setting before it works.
RetroArch binds keys to its own controller and hotkeys — Enter is Start,
``p`` pauses — so typing does not reach the program until you turn that
off. Press Scroll Lock for Game Focus and the whole keyboard becomes the
computer's; the core says as much on screen when a program loads. To have
it on every time, set Settings > Input > Auto Enable Game Focus to
"Detect", which looks for exactly what this core asks the frontend for.

Gamepads are read as the modern pads the machine expects, as many as the
frontend says it has.

A program that asks for the mouse gets the frontend's mouse. One that
asks for the absolute tablet gets the frontend's pointer, as touches:
the contacts follow a finger, or a held mouse button on a desktop. The
program draws its own pointer, because a libretro frontend has no cursor
to lend one.

A program's saves land in the save directory your frontend chose for it,
and the whole host filesystem is reachable from there.

This host plays a program and stops when the program does. There is no
monitor, no debugger, no scripting, and no save states — a core that
offered save states would be promising rewind and netplay the machine
cannot honor. Everything in that list is on the desktop emulator, and
the same ROM runs there.


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
   * - ``reply [on|off]``
     - Answer every command on stdout. See `Driving it from a program`_.

A failed check names the script and the line it was on, then exits 1,
which is all a test runner needs.

Memory starts random, as it often does on real hardware. This will catch
uninitialize memory usage... eventually. ``--fill 00`` gives a test
known memory when it needs it. The seed will be reported on stderr, so a
failure can be reproduced.

``--seed`` sets both the fill and the numbers ``lrand`` returns. Both will
start with the same seed so a ``--fill`` will not advance ``lrand``.


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
