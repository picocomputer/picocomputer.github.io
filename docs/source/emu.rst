============================
RP6502-EMU
============================

RP6502 - Emulator


Introduction
============

The RP6502-EMU is the machine on the device you use every day, a
Picocomputer 6502 hosted on a desktop or laptop running Windows, macOS or
Linux. It plays ``.rp6502`` games and applications in a window, with the
keyboard, mouse and gamepads of that computer. A RetroArch core of the
emulator adds save states, rewind and netplay.

The emulator is also the development machine. A project made from the
:doc:`sdk` template runs in it from VS Code, with breakpoints, stepping
and variables in the C or assembly source. ``--debug`` opens a debugger
for the whole machine over the emulated screen. A script works the
keyboard, gamepads and pointer and checks the results, and a headless run
puts a 6502 program in a shell pipeline.

The debug adapter, a script read from ``-`` and a headless run all use
standard input and output. With the SDK, they give an AI assistant a full
path down to the 6502: the assistant can build a program, run it, stop it
at a breakpoint, read its memory and check the screen.


Install
=======

Pre-built emulators are on the `releases page
<https://github.com/picocomputer/rp6502/releases/latest>`__. A project made from
the :doc:`sdk` template will fetch the right one into ``tools/``, so
you may have it already.

- **Windows** — ``rp6502-emu.exe`` is the program itself, not an installer.
  Requires a GPU with Direct3D 11. It isn't code signed, so SmartScreen
  warns on first launch; choose "More info" then "Run anyway".
- **macOS** — drag ``rp6502-emu.app`` to Applications.
  It isn't signed or notarized, so Gatekeeper blocks the first launch.
  Allow it under System Settings > Privacy & Security >
  "Open Anyway", or ``xattr -dr com.apple.quarantine rp6502-emu.app``.
- **Linux** — built on Ubuntu 22.04, so it needs glibc 2.35 or
  later plus the GL, X11, and ALSA runtime libraries.
  The tarball preserves the execute bit; if something
  along the way stripped it, ``chmod +x rp6502-emu``.
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


In a Browser
============

The RP6502-WEB is the machine for the web. It plays one ROM on a web
page, so anyone can play the program without installing anything.
``rp6502_web()`` builds a web player into a zip, ready to upload, and the
web zip on the `releases page
<https://github.com/picocomputer/rp6502/releases/latest>`__ is a sample.
The steps, and those for GitHub Pages and other web servers, are in
:doc:`web`.


RetroArch
=========

The RP6502-EMU is also a libretro core. Install it from Online Updater >
Core Downloader, under "Picocomputer 6502", then load a ``.rp6502`` ROM
the way you would a cartridge.

The core runs the ROM by its full path, so argv[0] is the absolute path
of the file. A ROM whose path no program could name runs from the null
drive as ``:name`` instead, as described in :ref:`Installed ROMs
<port-installed-roms>`. ``SAVE:`` files go in an ``rp6502`` folder
inside the RetroArch save folder, or in the working directory when the
ROM starts if RetroArch has no save folder. The core never changes the
working directory, so a program starts in the working directory of
RetroArch.


.. _emu-toolchain:

In a Toolchain
==============

With ``--headless``, a ROM runs as a command-line program on the host, so
a 6502 program can be one step of a build, a script or a test. The
program reads the host's stdin and writes the host's stdout and stderr,
and its exit code becomes the exit code of the emulator. Errors from the
host's filesystem are mapped to the ``errno`` values of the program's C
library, cc65 or llvm-mos, so the program's error handling needs no
change. ``--phi2 0`` removes the speed limit.

.. code-block:: text

  rp6502-emu --headless --phi2 0 tool.rp6502 < input.txt > output.txt
  rp6502-emu --headless adventure.rp6502
  rp6502-emu --stdin game.rp6502           # a window, and the terminal too

With a window, ``stdout`` and ``stderr`` go to the host's streams and
also show on the VGA terminal, so an error is on the screen even when the
streams are redirected. ``--stdin`` makes the host's stdin the console
input while the window stays open. Once the input is gone, a read of
``stdin`` returns 0 bytes.


.. _emu-arguments:

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
       `In a Toolchain`_.
     - desktop
   * - ``--install``
     - ``file``
     - Install a file on the null drive, reached as ``:basename``. A
       program runs an installed ROM with EXEC and opens any other
       installed file for reading. Repeatable to sixteen. When no ROM is
       named, the first one boots.
     - all
   * - ``--save-dir``
     - ``folder``
     - The folder that holds ``SAVE:`` files. It is created the first
       time a program creates a save. The default is
       ``$XDG_DATA_HOME/rp6502``, or ``~/.local/share/rp6502``, on Linux,
       ``~/Library/Application Support/io.github.picocomputer.rp6502-emu``
       on macOS, and ``Saved Games\rp6502`` on Windows.
     - all
   * - ``--bgcolor``
     - ``RRGGBB``
     - Letterbox and pillarbox fill. Default ``000000``.
     - all
   * - ``--phi2``
     - kHz
     - 6502 clock, 100 to 8000. Default 8000. ``0`` is for
       ``--headless``, and runs the 6502 with no speed limit.
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


.. _emu-debugging:

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

.. _emu-dap:

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
red.


.. _emu-scripting:

Scripting
=========

.. note::

   Scripting is beta and may change.

``--script`` drives the machine with no one at the keyboard. It types,
works the gamepads and the pointer, waits for expected console output,
and checks what the program produced, which is enough to turn a ROM into
a test that passes or fails.

.. code-block:: text

  rp6502-emu --script adventure.txt adventure.rp6502

Given ``-`` instead of a filename it reads stdin a line at a time, so a
driver written in any language can work the machine. The machine waits
for each line, so the driver sets the pace. See `Driving it from a
program`_.

A script always runs headless, and nothing paces
it against the host's clock. Frames elapse only when the script asks for
them, so ``run 600`` is six hundred frames and six hundred VSYNCs every
time.

One command per line. ``#`` starts a comment anywhere outside quotes.
Text is always in double quotes and takes the C escapes, so ``\n`` is a
newline, ``\\`` and ``\"`` are themselves, and ``\x03`` or ``\3`` is a
control byte. Hex takes up to two digits and octal up to three, and a
string cannot hold ``\0``. Numbers may be decimal, C-style ``0xFF``, or
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
     - Run until the console prints it. Default budget 600 frames.
   * - ``wait [xram:|ram:]<addr> <byte> [frames]``
     - Run until that byte reads that value. The byte is read once a
       frame, at the boundary.
   * - ``type "text" [frames]``
     - Type it. ``\r`` is Enter, ``\t`` is Tab. The text is UTF-8,
       converted to the machine's code page, so a byte that is not UTF-8
       becomes ``?``. Waits for the keyboard ring to take it all;
       default budget 600 frames.
   * - ``key <key>[+ctrl][+shift][+alt]``
     - Send the bytes a terminal sends for that key. See `Key Names`_.
   * - ``press <key>...``,
       ``release <key>...``
     - Set and clear bits in the HID bitmap a program reads. Each key is a
       name or a keycode. See `Key Names`_.
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
     - Work the mouse. The mask is one bit per button, 0 left, 1 right,
       2 middle, 3 back, 4 forward.
   * - ``tablet at <x> <y> [buttons]``,
       ``tablet touch <x>,<y>...``,
       ``tablet wheel <n> [pan]``,
       ``tablet clear``
     - Work the absolute pointer, including multi-touch up to eight
       contacts. The buttons are the same bits as the mouse. A pointer
       placed with ``at`` always reports hover, and a ``touch`` never
       does. Each ``at`` moves the pointer in a single update, so a
       program that reads during that update can get the old X with the
       new Y. With a real pointer that is imperceptible lag, so it is
       not a program bug.
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
     - Install a file on the null drive as ``:NAME``, and remove it
       again. The default name is the basename of the file.
   * - ``load "path"``
     - Boot a program. The machine must be stopped, since loading writes
       the memory a running program is using.
   * - ``sys run|stop|break``
     - Start the machine, stop it, or interrupt it the way a break at
       the console would.
   * - ``reply [on|off]``
     - Answer every command on stdout. See `Driving it from a program`_.

A failed check names the script and the line it was on, then exits 1.

Memory starts random, as it often does on the :doc:`pico`. This will catch
uninitialized memory usage... eventually. ``--fill 00`` gives a test
known memory when it needs it.


Key Names
---------

A ``<key>`` is one name out of one list, whichever command reads it.
Letters are ``a`` to ``z``, digits are ``0`` to ``9``, function keys are
``f1`` to ``f12``, and keypad digits are ``kp0`` to ``kp9``. The rest have
a name of their own, because only letters and digits are written as
themselves. Case does not matter.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Group
     - Names
   * - Typing
     - ``enter`` ``escape`` ``backspace`` ``tab`` ``space``
   * - Navigation
     - ``insert`` ``delete`` ``home`` ``end`` ``pageup`` ``pagedown``
       ``up`` ``down`` ``left`` ``right``
   * - Punctuation
     - ``minus`` ``equal`` ``leftbracket`` ``rightbracket`` ``backslash``
       ``semicolon`` ``apostrophe`` ``grave`` ``comma`` ``period``
       ``slash``
   * - Locks and system
     - ``capslock`` ``numlock`` ``scrolllock`` ``printscreen`` ``pause``
       ``menu``
   * - Keypad
     - ``kpenter`` ``kpdivide`` ``kpmultiply`` ``kpsubtract`` ``kpadd``
       ``kpdecimal`` ``kpequal``
   * - Modifiers
     - ``lctrl`` ``lshift`` ``lalt`` ``lsuper`` ``rctrl`` ``rshift``
       ``ralt`` ``rsuper``

``press`` and ``release`` take any key, because they set and clear bits
in the HID bitmap. They also take a keycode from 4 to 255 in place of a
name, written as ``0x2C``, ``$2C`` or decimal. These are the keyboard
usage codes from the USB HID specification, not PS/2 scancodes, and bit N
of the bitmap is the key with keycode N. A bare single digit is the digit
key rather than a keycode, so ``press 4`` is the 4 key and ``press $04``
is the a key.

``key`` sends what a terminal sends, so it takes the keys that type a
character and the keys that have an escape sequence. ``+shift`` types the
shifted character, ``+alt`` prefixes ESC, and ``+ctrl`` sends the control
byte, which makes ``key c+ctrl`` Ctrl-C and ``key leftbracket+ctrl`` an
ESC. Those characters are a US keyboard's, whatever layout the machine is
set to, so that a script sends the same bytes under every layout.

A key that types nothing is an error, which
covers ``capslock``, ``numlock``, ``scrolllock``, ``printscreen``,
``pause``, ``menu`` and the modifiers. So is a ``+ctrl`` on a key that has
no control byte, such as ``key 1+ctrl``.


Driving it from a program
-------------------------

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

The arithmetic and the assertions belong in your driver program, which is
why you don't see any in this scripting language.
