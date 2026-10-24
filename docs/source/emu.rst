============================
RP6502-EMU
============================

RP6502 - Emulator

.. note::

   This page still needs a major review to bring it up to the standard of
   the manual.


Introduction
============

The RP6502-EMU is the machine on the device you use every day, a
Picocomputer 6502 hosted on a desktop or laptop running Windows, macOS or
Linux. It plays ``.rp6502`` games and applications in a window, with the
keyboard, mouse and gamepads of that computer. The same emulator is a
RetroArch core, which reaches Android phones, tablets and TVs, and
iPhone, iPad and Apple TV, and adds save states, rewind and netplay.

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


.. _emu-retroarch:

RetroArch
=========

The RP6502-EMU is also a libretro core. RetroArch reaches devices that a
dedicated emulator would make no sense for: Android phones, tablets and
TVs, iPhone, iPad and Apple TV, and Linux on ARM boards. Install the core
from Online Updater > Core Downloader, under "Picocomputer 6502", then
load a ``.rp6502`` ROM the way you would a cartridge. Save states are deterministic, so rewind,
run-ahead and netplay all work.

The core runs the ROM by its full path, so argv[0] is the absolute path
of the file. A ROM whose path no program could name runs from the null
drive as ``:name`` instead, as described in :ref:`Installed ROMs
<port-installed-roms>`. ``SAVE:`` files go in an ``rp6502`` folder
inside the RetroArch save folder, or in the working directory when the
ROM starts if RetroArch has no save folder. The core never changes the
working directory, so a program starts in the working directory of
RetroArch.

Each of the four ports is a **Gamepad** by default. **Gamepad (Analog)**
adds the analog sticks. **Lightgun** is the Picocomputer's tablet,
because a lightgun is libretro's only absolute pointing device.

libretro was built for consoles with gamepads, and a core cannot work
around these limits:

- **Keyboard** — RetroArch maps the keys to its virtual RetroPad and its
  own hotkeys, so typing reaches the program only with Game Focus on.
  Game Focus is the Scroll Lock key by default. The core cannot turn Game
  Focus on or ask whether it is on, so it shows "Enable Game Focus for
  Keyboard and Mouse." the first time a program asks for the keyboard.
  Settings > Input > Auto Enable 'Game Focus' Mode > Detect turns Game
  Focus on whenever the core is loaded.
- **Mouse** — libretro has no way to share the host's cursor, so the
  core reports no host cursor and the program draws its own. With Game
  Focus off, RetroArch shows its own cursor as well. With Game Focus on,
  RetroArch captures the mouse, and the edges of the screen are hard to
  reach.


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
   :widths: 20 25 55
   :header-rows: 1

   * - Option
     - Value
     - Description
   * - ``--help``
     - \-
     - Print the options and the script commands, then exit.
   * - ``--screenshot``
     - ``file.png``
     - Run headlessly, render the frames to PNG, and exit.
   * - ``--crc``
     - \-
     - Run headlessly, render the frames, print the canvas as a CRC-32
       on stdout, and exit.
   * - ``--frames``
     - number
     - Frames to run before the screenshot or the CRC. Default 120.
   * - ``--scale``
     - number
     - Window scale, fractional allowed. Default 1.5.
   * - ``--filter``
     - ``nearest``,
       ``linear``,
       ``sharp``
     - How pixels are scaled to the window. Default ``sharp``, which
       prescales by an integer and then interpolates.
   * - ``--script``
     - ``file``, or
       ``-``
     - See `Scripting`_.
   * - ``--headless``
     - \-
     - No window and no picture. The program reads and writes the host's
       stdin, stdout and stderr, and its exit code becomes the emulator's.
       Implies ``--stdin``.
   * - ``--stdin``
     - \-
     - The host's stdin becomes the machine's console input. A terminal
       there becomes the console itself. Implied by ``--headless``. See
       `In a Toolchain`_.
   * - ``--install``
     - ``file``
     - Install a file on the null drive, reached as ``:basename``. A
       program runs an installed ROM with EXEC and opens any other
       installed file for reading. Repeatable to sixteen. When no ROM is
       named, the first one boots.
   * - ``--save-dir``
     - ``folder``
     - The folder that holds ``SAVE:`` files. It is created the first
       time a program creates a save. The default is
       ``$XDG_DATA_HOME/rp6502``, or ``~/.local/share/rp6502``, on Linux,
       ``~/Library/Application Support/io.github.picocomputer.rp6502-emu``
       on macOS, and ``Saved Games\rp6502`` on Windows.
   * - ``--bgcolor``
     - ``RRGGBB``
     - Letterbox and pillarbox fill, with or without ``#``. Default
       ``000000``.
   * - ``--phi2``
     - kHz
     - 6502 clock, 100 to 8000. Default 8000. ``0`` is for
       ``--headless``, and runs the 6502 with no speed limit.
   * - ``--cp``
     - number
     - OEM code page. 437, 720, 737, 771, 775, 850, 852, 855, 857,
       860-866, or 869. Default 437.
   * - ``--memseed``
     - number
     - The seed of the random fill of RAM and XRAM, 0 to 4294967295.
       Without it, the seed is new on every run.
   * - ``--memfill``
     - byte
     - Fill RAM and XRAM with one byte, such as ``$00`` or ``0``, in place
       of the random fill. The emulator takes ``--memseed`` or
       ``--memfill``, not both.
   * - ``--mute``
     - \-
     - No synthesis and no audio device opened at all.
   * - ``--debug``
     - \-
     - The on-screen machine debugger. It also holds the window open
       after the program exits, so you can examine where it stopped.
   * - ``--dap``
     - \-
     - Act as a DAP debug adapter on stdio. Implies ``--debug``.
   * - ``--ini``
     - ``file``
     - Where the debugger keeps its window layout.
   * - ``--credits``
     - \-
     - Print third-party credits and licenses, then exit.
   * - ``--version``
     - \-
     - Print the version and exit.
   * - ``--``
     - words
     - Pass everything after this to the ROM as ``argv[1..]``.


.. _emu-debugging:

Debugging
=========

The emulator is a DAP debug adapter, so any editor that supports the Debug
Adapter Protocol can do source-level debugging of 6502 code. The
:doc:`sdk` covers the VS Code side, which the project template already
configures.

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

.. _emu-overlay:

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
works the gamepads and the pointer, waits for what the program writes to
stdout and stderr and for what reaches the screen, and checks what the
program produced, which is enough to turn a ROM into a test that passes or
fails.

.. code-block:: text

  rp6502-emu --script adventure.txt adventure.rp6502

Given ``-`` instead of a filename it reads stdin a line at a time, so a
driver written in any language can work the machine. The machine waits
for each line, so the driver sets the pace. See `Driving it from a
program`_.

A script always runs headless, and nothing paces it against the host's
clock. Frames elapse only when the script asks for them, so ``run 600`` is
six hundred frames and six hundred VSYNCs every time.

A command that waits, such as ``wait``, runs frames until what it waits for
happens. Its budget is the largest number of frames that it runs. When the
budget runs out, the line fails, so a script that waits for something that
never happens ends instead of hanging. The default budget is 600 frames, ten
seconds of the machine's time. ``run`` and ``wav`` run the number of frames in
their argument. Every other command runs no frames, so ``expect``, ``peek``,
and the other checks read the machine as it is at that line.

One command per line. ``#`` at the start of a word, outside quotes, starts a
comment. Text is always in double quotes and takes the C escapes, so ``\n`` is
a newline, ``\\`` and ``\"`` are themselves, and ``\x03`` or ``\3`` is a
control byte. Hex takes up to two digits and octal up to three. A program can
write a zero byte, so ``wait`` and ``expect`` take ``\0``, and no other string
can hold one. A number is an expression, such as ``255``, ``$FF``, or
``XRAM_PSG+5``. Spaces separate a command's arguments, so an expression with
spaces must be in parentheses, as in ``xram:(XRAM_PSG + 5)``. See `Symbols and
expressions`_.

Text is UTF-8, and so is what ``wait`` and ``expect`` search, converted
from the machine's code page as it is written. ``stdout`` and ``stderr``
are the bytes the program wrote, before the console puts a carriage return
in front of each newline, so a line the program prints ends in ``\n``.
``console`` is what reaches the screen: those bytes with the carriage
returns, the line editor's echo of what is typed, and the system's own
messages. An escape from ``\x80`` to ``\xFF`` is a byte of UTF-8, so
``"caf\xC3\xA9"`` is ``"café"``.

.. code-block:: text

  wait "Colossal Cave Adventure"
  wait "Would you like instructions?"
  type "no\r"
  wait "standing at the end of a road"
  type "take lamp\r"
  wait "I see no lamp here"

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Command
     - Description
   * - ``run [frames]``
     - Let exactly that many frames elapse, one VSYNC each. Default 1.
   * - ``wait [stdout|stderr|console] "text" [frames]``
     - Run until it appears on that stream, stdout if none is named.
   * - ``wait [xram:|ram:]<addr> <byte> [frames]``
     - Run until that byte reads that value. The byte is read once a
       frame, at the boundary.
   * - ``wait exit [frames]``
     - Run until the program exits.
   * - ``type "text" [frames]``
     - Type it. ``\r`` is Enter, ``\t`` is Tab. The text is UTF-8,
       converted to the machine's code page, so a byte that is not UTF-8
       becomes ``?``. The command waits until the keyboard ring takes it
       all.
   * - ``eof [frames]``
     - End the program's stdin, the way a piped ``--stdin`` ends. It
       waits until the program is reading stdin and has taken everything
       typed. That read gets what is left of the line, and every read after
       it returns 0 bytes until the next program starts.
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
       does. A program that reads the block while an ``at`` is applied
       can get the old X with the new Y, unless it reads the block as
       :ref:`Tablet <ria-tablet>` on the RIA page shows.
   * - ``expect [stdout|stderr|console] "text"``,
       ``expect-not [stdout|stderr|console] "text"``
     - Check the stream since its last match, stdout if none is named. A
       match consumes up to and including it. Each stream is checked
       separately. The line editor's echo of typed text is only on the
       console, but a program that echoes its own input writes that echo
       to stdout.
   * - ``expect exit <code>``,
       ``expect-not exit <code>``
     - Check the exit code of the program. The check fails while the
       program runs, so put ``wait exit`` first.
   * - ``discard [stdout|stderr|console]``
     - Drop what the program printed on that stream after the last match,
       or on all three streams without a stream name. ``load`` keeps the captured output, so
       discard it before you start a program again.
   * - ``peek [xram:|ram:]<addr> <byte>...``
     - Compare memory.
   * - ``poke [xram:|ram:|bus:|xbus:]<addr> <byte>...``
     - Write memory. The program reads what you wrote, so a test can
       skip ahead to the state it needs to exercise. Each byte goes to
       the next address.
   * - ``dump [xram:|ram:]<addr> [count]``
     - Print memory as hex.
   * - ``status``
     - Print the status of the machine on one line.
   * - ``crc``
     - Print the screen as a CRC-32.
   * - ``mark``,
       ``expect-same``,
       ``expect-changed``
     - Remember the screen, then check it against what you remembered.
   * - ``shot "file.png"``
     - Write the screen.
   * - ``wav "file.wav" [frames]``
     - Run that many frames, default 1, and record their sound as 16-bit
       stereo at 48 kHz. With ``--mute`` the recording is silent.
   * - ``state save "file"``,
       ``state load "file"``
     - Save the whole machine to a file, and load it back.
   * - ``install "path" [NAME]``,
       ``remove <NAME>``
     - Install a file on the null drive as ``:NAME``, and remove it
       again. The default name is the basename of the file.
   * - ``load "path"``
     - Boot a program. The machine must be stopped, since loading writes
       the memory a running program is using. The new program's ``.sym``
       replaces the symbols.
   * - ``seed <n>``
     - Set the seed of the random numbers that the program draws, 0 to
       4294967295. The program gets the new stream at its next draw, and a
       program can draw in its first frame. To give a program the stream from
       its start, set the seed before the first command that runs frames: on
       the first line, or just before or after ``load``. ``state load``
       replaces the stream.
   * - ``sys run|stop|break``
     - Start the machine, stop it, or interrupt it the way a break at
       the console would.
   * - ``reply [on|off]``
     - Answer every command on stdout. See `Driving it from a program`_.
   * - ``let name = expr``
     - Set a variable that later lines can use in numbers. See `Symbols
       and expressions`_.

An address is in the 6502's address space, RAM at $0000-$FEFF, the VIA
at $FFD0-$FFDF and the RIA at $FFE0-$FFFF, unless ``xram:`` puts it in
XRAM. ``ram:`` is the same as no prefix. The part after the prefix can be
an expression, as in ``xram:XRAM_PSG+5``. Nothing answers at
$FF00-$FFCF, so an address there is an error. ``peek``, ``dump`` and
``wait`` find a register as a read would, without what the read does,
so RX keeps its byte, XSTACK keeps its top and IRQ keeps its flags.
``poke`` sets what a read finds and does nothing else. With ``bus:``,
``poke`` stores the byte the way the program does, so a register does
what a store to it does: ``poke bus:$FFE1 $41`` sends an ``A`` to stdout.
``xbus:`` writes XRAM the way RW0 and RW1 write it, so the PSG or OPL
hears a byte written to its block, which ``poke xram:`` changes without
telling it.

``status`` prints these fields in this order, each as ``NAME=value``, with
a space between fields. ``status`` leaves out a field that does not apply,
so check for a field before you read it.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Field
     - Value
   * - ``PC A X Y SP P``
     - The 6502's registers. A frame can end partway through an
       instruction, so PC may be past its first byte.
   * - ``OP``, ``BUSY``
     - The RIA's OP and BUSY registers.
   * - ``RESB``
     - 1 while the 6502 runs, and 0 while the RIA holds it in reset.
   * - ``EXIT``
     - The exit code of the program. It appears after the program exits,
       but not after ``sys stop`` or ``sys break``.
   * - ``SEED``
     - The seed of the random numbers that the program draws, from the
       last ``seed``, or the seed that the emulator chose at startup.
   * - ``MEMSEED``, ``MEMFILL``
     - ``MEMSEED`` is the seed of the random fill of RAM and XRAM.
       ``MEMFILL`` is the byte of ``--memfill``, and appears in place of
       ``MEMSEED``.
   * - ``ROM``
     - The path of the ROM that runs, or that ran last. It is always the
       last field, and its value runs to the end of the line, so a path
       with spaces needs no quotes.

When a check fails, the emulator prints two lines on stderr: the script, the
line, and the reason, then the fields of ``status``. To repeat the failed run,
put ``seed <n>`` with the ``SEED`` value first in a script that sets no seed.
Then run the script with ``--memseed`` and the ``MEMSEED`` value, or with
``--memfill`` and the ``MEMFILL`` value. A script that runs frames before its
first ``seed`` cannot repeat the draws before that seed. Then the emulator
prints to stdout what the program printed after the last match, in UTF-8, and
exits 1. Once that output reaches 64 KB, the emulator keeps only the newest
part, so it can start partway through a line. The program's stderr goes to
stderr as the program writes it, all through the run.

A program must treat RAM and XRAM as uninitialized, because they hold unknown
values until the program writes them. To help find a program that reads memory
before writing it, the emulator fills RAM and XRAM from a new random seed on
every run, so a program that gets lucky with an uninitialized value on one run
is not lucky on the next. For a test, ``--memseed`` repeats the fill, and
``--memfill`` fills memory with a known byte, such as ``--memfill 00``. No seed
controls the clock, the files on ``SAVE:``, or a program that seeds its own
random numbers.


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
ESC. Ctrl with a digit from 2 to 8, with Space or with / sends what xterm
sends, so ``key 2+ctrl`` is a zero byte. Those characters are a US keyboard's, whatever layout the machine is
set to, so that a script sends the same bytes under every layout.

A key that types nothing is an error, which
covers ``capslock``, ``numlock``, ``scrolllock``, ``printscreen``,
``pause``, ``menu`` and the modifiers. So is a ``+ctrl`` on a key that has
no control byte, such as ``key 1+ctrl``.


.. _emu-symbols:

Symbols and expressions
-----------------------

A ``.sym`` file beside the ROM, with the same name, lists the program's
addresses and constants by name. Every build of a project made with the
:doc:`sdk` writes one. Each line is a name, one space and a whole number:

.. code-block:: text

  XRAM_DATA_TAB 0x1100
  XRAM_PSG 0x1200

A script can use these symbols wherever a command takes a number. The
emulator reads them from the ``.sym`` of the ROM that boots, and ``load``
replaces them with the new program's. Without a ``.sym`` there are none.
A name on two lines is ambiguous, and a script fails only when it uses
that name.

Spaces separate a command's arguments, so an expression with spaces must
be in parentheses, as in ``poke xram:(XRAM_PSG + 5) ($80 | 3)``. Without
spaces, as in ``poke xram:XRAM_PSG+5 $83``, no parentheses are needed.
Where an argument could be a keyword, the emulator reads it as the
keyword, so a name in that place needs parentheses. C programs have a
global named ``stdout``, so ``wait stdout "done"`` waits for text and
``wait (stdout) 1`` waits until the byte at ``stdout`` is 1. In
``press`` and ``release`` the emulator reads key names and single digits
as keys, so ``press 4`` is the 4 key and ``press (4)`` is keycode 4.

``let name = expr`` sets a variable, and later lines can use the variable
in numbers. The rest of the line after ``=`` is the expression, so it
needs no parentheses even with spaces. A symbol can't be set. ``load``
keeps the variables, and a variable whose name is also in the new
``.sym`` becomes ambiguous.

Expressions use whole numbers only. Expressions follow Python 3's rules
for whole numbers, so an expression has the same value as in Python, or
it is an error. The list below shows where these rules differ from C.

- Numbers are written as in Python, or with ``$`` for hex: ``255``,
  ``0xFF``, ``$FF``, ``0b1111_1111`` and ``0o377``. Digits can be
  separated with ``_``. A number can't start with 0 unless it is 0, so
  ``010`` is an error, not octal as in C. Write ``0o10`` for octal. A
  float such as ``1.5`` or ``2e3`` is an error.
- The operators, from lowest to highest precedence, are ``or``, ``and``,
  ``not``, the comparisons ``< <= > >= == !=``, ``|``, ``^``, ``&``,
  ``<< >>``, ``+ -``, ``* // %``, the unary ``- + ~``, and ``**``.
  ``**`` raises to a power, so ``2 ** 8`` is 256, and ``-2 ** 2`` is -4.
  Unlike C, ``| ^ &`` have higher precedence than the comparisons, so
  ``x & 1 == 0`` means ``(x & 1) == 0``.
- ``/`` is not allowed, because in Python it makes a float, even for
  ``6 / 2``. Divide with ``//``, which is integer division. With a
  negative number it differs from C: ``-7 // 2`` is -4 where C gives -3,
  and ``-7 % 2`` is 1 where C gives -1. A negative power such as
  ``2 ** -1`` makes a float, so it is not allowed either.
- A comparison is 1 or 0. ``1 < x < 5`` means ``1 < x and x < 5``, not
  ``(1 < x) < 5`` as in C.
- ``not`` is C's ``!`` with a lower precedence, so ``not x + 1`` means
  ``!(x + 1)``. ``a or b`` is C's ``a ? a : b``, so ``0 or 3`` is 3.
  ``a and b`` is C's ``a ? b : a``, so ``2 and 3`` is 3. In C,
  ``0 || 3`` and ``2 && 3`` are both 1.
- Whole numbers are 64-bit and signed. A result that doesn't fit in 64
  bits is an error. In C, signed overflow is undefined.
- A name is a letter or ``_``, then letters, digits, ``_`` and ``.``, so
  an llvm-mos static such as ``draw.image`` is one name. Names are
  case-sensitive.
- There are no strings, function calls, casts, ``?:``, ``&&``, ``||`` or
  ``!``. Write ``and`` for ``&&``, ``or`` for ``||``, ``not`` for ``!``,
  and 1 and 0 for true and false.

A failure message shows the expression as it is written in the script,
without the ``xram:``, ``xbus:``, ``bus:`` or ``ram:`` in front and
without parentheses around all of it. For ``let`` it is the expression
after ``=``.

.. list-table::
   :widths: 45 55
   :header-rows: 1

   * - Failure
     - Why
   * - ``unknown name 'XRAM_PSGG'``
     - No symbol or variable has that name.
   * - ``ambiguous name 'L0010'``
     - The ``.sym`` has it on two lines, or a symbol and a variable share
       it after a ``load``.
   * - ``cannot assign symbol 'XRAM_PSG'``
     - A symbol can't be set.
   * - ``base + 6 / 2: floats are not allowed, use //``
     - The expression has a ``/``.
   * - ``1.5 * 2: floats are not allowed``
     - The expression has a number with a point or an exponent, or a
       negative power such as ``2 ** -1``.
   * - ``base // 0 divides by zero``
     - A ``//`` or ``%`` has 0 on its right, or 0 is raised to a negative
       power.
   * - ``1 << 63 overflows 64 bits``
     - A number or a result doesn't fit in 64 bits.
   * - ``1 << -1 shifts by a negative count``
     - A ``<<`` or ``>>`` has a negative number on its right.
   * - ``bad expression 'base+'``
     - The expression has a syntax error, or something that expressions
       don't have, such as ``010``, ``x && y`` or a function call.
   * - ``missing ) in '(base + 4 $00'``
     - A ``(`` has no matching ``)``, so the argument continues to the end
       of the line.

With ``reply`` on, as in `Driving it from a program`_, a driver that
starts ``rp6502-emu --memfill 0 --script -`` on a program whose ``.sym`` has
``XRAM_DATA_TAB`` writes:

.. code-block:: text

  reply
  let base = XRAM_DATA_TAB
  peek xram:base+4 $00
  poke xram:(base + 6 // 2) $01
  peek xram:(base + 6 / 2) $01

and reads:

.. code-block:: text

  ok
  ok
  ok
  ok
  fail base + 6 / 2: floats are not allowed, use //
  PC=$0000 A=$00 X=$00 Y=$00 SP=$00 P=$02 OP=$00 BUSY=$00 RESB=1 SEED=1556577197 MEMFILL=$00 ROM=FS:/home/user/game/build/game.rp6502


Driving it from a program
-------------------------

``reply`` turns on one line of answer per command — ``ok``, ``ok <values>``
for ``dump``, ``crc``, and ``status``, or ``fail <why>``. It is off
until asked, so a driver writes its whole preamble without waiting for
anything and reads the ``ok`` for ``reply`` itself as the moment the
machine starts answering.

In a project made with the :doc:`sdk`, ``rp6502.Emu`` in
``tools/rp6502.py`` is such a driver. See :ref:`Testing <sdk-testing>`.

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
                              PC=$0307 A=$30 X=$01 Y=$00 SP=$F7 P=$86 OP=$01 BUSY=$00 RESB=1 SEED=513216670 MEMSEED=3088541612 ROM=FS:/home/user/game/build/game.rp6502

A ``fail`` ends the run, so there is no asking ``status`` after one.
Instead, the line after the ``fail`` line is the status line. Everything
after it, up to the end of stdout, is what the program printed after the
last match, in UTF-8. The program's stderr is on stderr.

This driver never answers the question. It writes:

.. code-block:: text

  reply
  wait "Would you like instructions?"
  run 60
  status
  wait "end of a road" 60

and reads:

.. code-block:: text

  ok
  ok
  ok
  ok PC=$FFF1 A=$16 X=$00 Y=$00 SP=$F1 P=$25 OP=$16 BUSY=$FE RESB=1 SEED=1215796064 MEMSEED=2788390211 ROM=FS:/home/user/adventure.rp6502
  fail timed out waiting for "end of a road"
  PC=$FFF3 A=$16 X=$00 Y=$00 SP=$F1 P=$25 OP=$16 BUSY=$FE RESB=1 SEED=1215796064 MEMSEED=2788390211 ROM=FS:/home/user/adventure.rp6502


  >

PC is in the RIA's spin loop, BUSY says an API call is running, and OP
$16 is READ_XSTACK, the call under ``read()``. The last three lines are
the program's stdout after the question: two empty lines and the ``>``
prompt where it waits for the answer.

Arithmetic in a script gives the same answer as Python, so a driver can
do the math either way. Loops, decisions and anything beyond arithmetic
belong in your driver program.
