============================
RP6502-SDK
============================

RP6502 - Software Development Kit


Introduction
============

The SDK is what turns your source into a ROM. Picocomputer software is
distributed as one file ending in ``.rp6502`` — the program, its assets,
and the 6502 vectors in a single package — and everything here exists to
build one of those, put it on a machine, and debug it while it runs.

The `RP6502 project template <https://github.com/picocomputer/rp6502-sdk>`__
is scaffolding for a new Picocomputer 6502 program. It builds with either
6502 compiler, cc65 or llvm-mos, and switching between them is one
setting. Three "Hello, world!" examples are included to start from — one
in C that builds with either compiler, and the same program in each
assembler's syntax.


Three Layers
============

The SDK is three of them, and only the bottom one is required. Each is
ordinary files in your repository — nothing is installed, nothing is
hidden — so you can read any layer, and throw away the ones you don't
want.

.. code-block:: text
   :class: diagram

   ┌───────────────────────────────────────────────────────────┐
   │ .vscode/                                         optional │
   │   launch configurations, tasks, recommended extensions    │
   ├───────────────────────────────────────────────────────────┤
   │ CMakeLists.txt  CMakePresets.json                optional │
   │   tools/rp6502.cmake — a preset per compiler and config,  │
   │   rp6502_asset(), rp6502_executable()                     │
   ├───────────────────────────────────────────────────────────┤
   │ tools/rp6502.py                                  required │
   │   packs the ROM, sends it to a machine, gives you a       │
   │   console. Python 3 and nothing else.                     │
   └───────────────────────────────────────────────────────────┘

**VS Code** is the top layer, and it's a folder. The launch
configurations behind F5, the three tasks, and the list of extensions the
project asks you to install. It is strongly recommended and the template
is set up for it, but nothing below it knows it's there — delete the
folder and the project still builds.

**CMake** is the middle layer, and it's where the rest of this page
lives. ``CMakePresets.json`` carries a preset per compiler and
configuration; ``tools/rp6502.cmake`` adds the commands your
``CMakeLists.txt`` calls, finds a compiler, and packages the result.
Drive it from a command line with any editor you like — VS Code's CMake
panel is a front end for the same presets, running the same builds into
the same directories.

**The Python tool** is the bottom layer and the only one you can't do
without. ``tools/rp6502.py`` packs a ROM, sends it to a Picocomputer,
uploads files, and attaches a console, and it needs Python 3 and nothing
else. Every ROM the layer above builds is built by calling it. You can
call it yourself instead — though by the time that appeals, you could
probably write the `ROM File Format <ria.html#rom-file-format>`__ out
yourself and skip it too.


Getting Started
===============

Install the required software using the README in the `template
<https://github.com/picocomputer/rp6502-sdk>`__. Information about tools
and other requirements is kept in the README so that it may carry forward
with your project if desired. Once you have a compiler and tools installed,
you may return here.

**1. Make a project.** Go to the `template
<https://github.com/picocomputer/rp6502-sdk>`__ and select "Use this
template" then "Create a new repository". GitHub makes a clean project
for you. Clone it and open the folder in VS Code.

**2. Install the recommended extensions** when prompted. That's CMake
Tools, the C/C++ pack, lldb-dap for debugging in the emulator, and
debugpy for the Python tool that runs your ROM on hardware.

**3. Choose a compiler.** The choice is a CMake preset, and there are
four: a Debug and a Release of each compiler, each building into its own
directory so you can switch back and forth without starting over. Pick
one from the CMake side panel.

**4. Let the first configure finish.** A new project starts with only a
small script in ``tools/``, which downloads the latest tools and an
emulator if one is available for your system.

They're ordinary files in your repository after that, so commit them
along with everything else. Updating ``tools/`` is a CMake script you
run directly or as a VS Code task.

.. code-block:: text

  cmake -P tools/rp6502.cmake

**5. Press F7 to build.** That leaves a ROM at
``build/<compiler>/<config>/hello.rp6502``.

**6. Press F5 to debug.** The first time, this creates the ``.rp6502``
settings file described next.


The .rp6502 Settings File
=========================

Everything about *running* your program lives in one file in the project
root. It's created the first time you Start Debugging and is ignored by
git, because it describes your machine rather than your project.

The settings file is a dotfile called ``.rp6502``. The
Python tool reads the settings with ``-c``, and the settings are the same
things it takes as command-line flags, which is why both layers above it
can use one file.

.. code-block:: text

  [RP6502][Launch]
  emulator = /home/you/hello/tools/rp6502-emu
  device = /dev/ttyACM0
  key =
  workdir =
  args =
  term = True

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Setting
     - Description
   * - ``emulator``
     - Path to the emulator, filled in with the one the tools fetched. A
       bare ``rp6502-emu`` means the fetch had nothing for this machine,
       and the name is searched on your PATH.
   * - ``device``
     - The serial port your Picocomputer appears on, or a hostname to
       reach it over telnet. This is the one you'll edit — if you get a
       Python error about the communications device not being found, this
       is why.
   * - ``key``
     - Passkey for telnet. See `Telnet Console
       <ria_w.html#telnet-console>`__.
   * - ``workdir``
     - Remote directory to work in.
   * - ``args``
     - Arguments passed to your ROM, reaching it through `ARGV
       <os.html#argv>`__. A launch configuration that carries its own
       arguments overrides these.
   * - ``term``
     - Attach a console terminal when running on hardware.

The file holds more than these settings. The emulator keeps its debugger
window layout in the same file, so each project remembers where you left
its windows.


Running and Debugging
=====================

"Start Debugging" (F5) offers two configurations.

**RP6502 (Emulator)** is the default. It builds your project and runs it
with source-level debugging in the :doc:`emu`. No hardware needed.

**RP6502 (Hardware)** builds your project and runs it on a real
Picocomputer 6502. Connect with telnet, or with a USB cable plugged into
the RP6502-VGA USB port.

Breakpoints, stepping, the call stack, and watch expressions work only on
the emulator. Debugging on hardware gets you a terminal instead — the ROM
is uploaded and run, and you may interact with it from the console. What a
debugger can see depends on which compiler you chose — :doc:`emu` has the
details, and the short version is that llvm-mos carries type information
and cc65 doesn't.

Three VS Code tasks are set up alongside them:

- **RP6502: update tools** pulls down current versions of everything in
  ``tools/``, leaving a diff you can read before you commit it.
- **RP6502: upload ROM** copies the built ROM to USB storage.
- **RP6502: console terminal** attaches a terminal and nothing else.


Command Line
============

None of that is required. The two layers under the editor are a CMake
project and a Python script, and both are drivable from a shell.

Configure and build. These are the same four presets the CMake panel
offers, building into the same directories.

.. code-block:: text

  cmake --list-presets
  cmake --preset cc65/Debug
  cmake --build --preset cc65/Debug

That leaves a ROM at ``build/cc65/debug/hello.rp6502``. The first
configure is the one that fetches ``tools/`` and the emulator.

Run it on hardware. ``tools/rp6502.py`` uploads the ROM, starts it, and
attaches a terminal — Ctrl-A then X exits, Ctrl-A then B sends a break.

.. code-block:: text

  python3 tools/rp6502.py run build/cc65/debug/hello.rp6502
  python3 tools/rp6502.py term
  python3 tools/rp6502.py upload file...

``-d`` picks the device: a serial port, or a hostname to reach it over
telnet with ``-k`` for the passkey. ``-c`` reads a settings file instead
of flags, which is what the launch configurations do with ``.rp6502``.


Adding Assets
=============

From here down is the middle layer — the commands ``tools/rp6502.cmake``
adds to your ``CMakeLists.txt``. They work the same whether you press F7
or type ``cmake --build``, because the editor isn't in the picture.

Your program is rarely just code. Graphics, level data, help text, and
anything else you want to ship travel inside the same ``.rp6502`` file,
added in ``CMakeLists.txt``.

.. code-block:: cmake

  rp6502_asset(hello 0x10000 img/intro.bin)
  rp6502_asset(hello help src/help.txt)

A numeric address is a memory chunk. The file is loaded straight into RAM
(``$0000-$FEFF``) or XRAM (``$10000-$1FFFF``) when the ROM loads, before
the 6502 starts, so it's simply there when your program runs.

Anything else is a name, and named assets become part of the filesystem
while your ROM runs. Prefix the name with ``ROM:`` and open it like any
other file. They're read-only, and you can have several open at once.

.. code-block:: C

  open("ROM:help", O_RDONLY);

Some names are special. The ``help`` asset is what the monitor's HELP and
INFO commands display, and the on-screen debugger shows it too.

Every ``rp6502_asset()`` has to come before ``rp6502_executable()``. The
order is checked, and the error says so.

.. seealso::

   :doc:`ria` — `ROM File Format <ria.html#rom-file-format>`__ describes
   what these turn into on disk.


Linker Configuration
====================

``rp6502_executable()`` packages your program: where its code loads, and
what goes in the three 6502 vectors.

.. code-block:: cmake

  rp6502_executable(hello DATA default RESET default)

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Keyword
     - Description
   * - ``DATA``
     - Where the linker output loads. Omit it entirely and the executable
       isn't included at all, which builds a ROM of nothing but assets.
   * - ``RESET``
     - Stored at ``$FFFC-$FFFD``. Required.
   * - ``IRQ``
     - Stored at ``$FFFE-$FFFF``. Optional.
   * - ``NMI``
     - Stored at ``$FFFA-$FFFB``. Optional.

Each takes an address, which may be a literal like ``0x200``, the word
``file`` to read it out of the linker output, or the word ``default`` to
take whatever convention your compiler uses.

When you outgrow the stock layout, give the linker a configuration of
your own.

.. code-block:: cmake

  target_link_options(hello PRIVATE -C ${CMAKE_SOURCE_DIR}/src/hello.cfg)

That's ld65's config for cc65; llvm-mos takes a linker script with ``-T``
instead. Once you've moved the load address, use ``file`` or the
address outright.


Multiple Compiler Artifacts
===========================

A linker configuration can write more than one output file, and CMake's
``add_executable()`` models exactly one. In an ld65 config, every memory
area with a ``file`` of its own is another file the linker writes. ``%O``
is the one CMake knows about; every other name is one it doesn't.
``rp6502_byproducts()`` closes the gap. It tells CMake that building
``<target>`` is what produces these files.

.. code-block:: cmake

  rp6502_byproducts(<target> <file>...)

From there they're ordinary build outputs: you can name them as inputs,
they're regenerated when the target relinks, and a clean removes them.

Microsoft BASIC is the real case. Its image is three loads at three
addresses with nothing contiguous between them — the ``CHRGET`` routine
in zero page, the init code, and the interpreter — so its linker
configuration writes three files, each named off ``%O``.

.. code-block:: text

  MEMORY {
      ZP:       start = $0000, size = $00E7, file = "";
      CHRGETZP: start = $00E8, size = $0018, file = "%O.00E8";
      INITROM:  start = $1000, size = $8000, file = "%O.1000";
      BASROM:   start = $C000, size = $3DDE, file = "%O.C000";
      # areas with file = "" write nothing; trimmed here
      TOUCH:    start = $0000, size = $0000, file = %O;
  }

``TOUCH`` is a zero-size area whose file is ``%O``, and it's there so the
linker still writes the output CMake was told to expect. It costs
nothing, and it keeps the target CMake is modeling from going missing.

The three real files are then declared as byproducts, added at the
addresses their memory areas named, and packaged.

.. code-block:: cmake

  rp6502_byproducts(basic
      ${CMAKE_CURRENT_BINARY_DIR}/basic.00E8
      ${CMAKE_CURRENT_BINARY_DIR}/basic.1000
      ${CMAKE_CURRENT_BINARY_DIR}/basic.C000
  )
  rp6502_asset(basic help src/help.txt)
  rp6502_asset(basic 0x00E8 ${CMAKE_CURRENT_BINARY_DIR}/basic.00E8)
  rp6502_asset(basic 0x1000 ${CMAKE_CURRENT_BINARY_DIR}/basic.1000)
  rp6502_asset(basic 0xC000 ${CMAKE_CURRENT_BINARY_DIR}/basic.C000)
  rp6502_executable(basic RESET 0x1000)

Note what isn't in that last line. There's no ``DATA``, because the
linker output is the empty ``TOUCH`` file. The whole ROM is built from
assets. One linker configuration, several output files, one ``.rp6502``.

Multiple ROMs
=============

Call ``add_executable()`` and ``rp6502_executable()`` once for each.
Every program gets its own ROM, and the CMake launch target chooses
which one F5 runs.

.. code-block:: cmake

  add_executable(hello)
  rp6502_executable(hello DATA default RESET default)
  target_sources(hello PRIVATE src/hello.c)

  add_executable(setup)
  rp6502_asset(setup help src/setup.hlp)
  rp6502_executable(setup DATA default RESET default)
  target_sources(setup PRIVATE src/setup.c)


Where To Go Next
================

- :doc:`os` — the system calls and the ABI your C library sits on.
- :doc:`ria` — the register map, and every device reached through it.
- :doc:`vga` — the video modes.
- :doc:`emu` — the debugger's reach, and how to put your program on the
  web.
- `The template's README
  <https://github.com/picocomputer/rp6502-sdk#readme>`__ — installing the
  compilers, and every command on this page in one place.
- `Examples <https://github.com/picocomputer/examples>`__ — dozens of
  small programs, each one a working ``CMakeLists.txt`` entry.
