============================
RP6502-SDK
============================

RP6502 - Software Development Kit


Introduction
============

The SDK turns your source into a ROM. Picocomputer software is
distributed as one file ending in ``.rp6502`` — the program, its assets,
and the 6502 vectors in a single package — and the SDK builds one of
those, puts it on a machine, and debugs it while it runs.

The `RP6502 project template <https://github.com/picocomputer/rp6502-sdk>`__
is scaffolding for a new Picocomputer 6502 program. It builds with either
6502 compiler, cc65 or llvm-mos, and switching between them is one
setting. Three "Hello, world!" examples are included to start from — one
in C that builds with either compiler, and the same program in each
assembler's syntax.


Three Layers
============

The SDK has three layers, and only the bottom one is required. The
layers are ordinary files in your repository. Nothing is installed and
nothing is hidden, so you can read any layer and delete the ones you
don't want.

.. code-block:: text
   :class: diagram

   ┌───────────────────────────────────────────────────────────┐
   │ .vscode/                                                  │
   │   Launch configurations, tasks, recommended extensions.   │
   ├───────────────────────────────────────────────────────────┤
   │ CMakeLists.txt  CMakePresets.json  tools/rp6502.cmake     │
   │   The CMake build system works with many other editors.   │
   ├───────────────────────────────────────────────────────────┤
   │ tools/rp6502.py                                 Python 3  │
   │   Packages the ROM with its assets and communicates with  |
   |   :doc:`pico` and :doc:`emu` machines for debugging.      |
   └───────────────────────────────────────────────────────────┘


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

**3. Choose a compiler.** You will be prompted the first time you open
up a new project. You may change it later from the CMake side panel.

**4. Press F5 to debug.** This will download the latest tools and
emulator for your system then build hello world and run it in the emulator.
It will also create the ``.rp6502`` settings file described in the next
section. It is expected that you commit these tools to yout repository
and update them manually as needed, either from a task or the command line.
The emulator executable and settings file are ignored by git.

.. code-block:: text

  cmake -P tools/rp6502.cmake

Your debugger may take focus when the program stops so make sure to
check if the emulator hides behind your debugger or editor window.


The .rp6502 Settings File
=========================

The settings file is a dotfile called ``.rp6502`` in your project root.
Edit the first section with the correct communications port
or IP address and key of a :doc:`pico` you want to test with.

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
     - Path to the emulator. A bare filename will search the PATH.
   * - ``device``
     - The serial port your Picocomputer appears on, or a hostname to
       reach it over telnet.
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
window layout here too, so each project remembers where you left its
windows.


Running and Debugging
=====================

"Start Debugging" (F5) offers two configurations.

**RP6502 (Emulator)** is the default. It builds your project and runs it
with source-level debugging in the :doc:`emu`. No hardware needed.

**RP6502 (Hardware)** builds your project and runs it on a real
Picocomputer 6502. Connect with telnet, or with a USB cable plugged into
the RP6502-VGA USB port.

Breakpoints, stepping, the call stack, and watch expressions work only on
the emulator. Debugging on hardware provides a terminal instead. What
a debugger can see depends on which compiler you chose. llvm-mos provides
type information and cc65 does not; the :doc:`emu` has the details.


Adding Assets
=============

Your program is rarely just code. Graphics, level data, help text, and
anything else you want to ship travel inside the same ``.rp6502`` file,
added in ``CMakeLists.txt``.

.. code-block:: cmake

  rp6502_asset(hello 0x10000 img/intro.bin)
  rp6502_asset(hello help src/help.txt)

A numeric address is a memory chunk. The file is loaded straight into RAM
(``$0000-$FEFF``) or XRAM (``$10000-$1FFFF``) when the ROM loads, before
the 6502 starts, so it is already in place when your program runs.

Anything else is a name, and named assets become part of the filesystem
while your ROM runs. Prefix the name with ``ROM:`` and open it like any
other file. They're read-only, and you can have several open at once.

.. code-block:: C

  open("ROM:help", O_RDONLY);

Some names are special. The ``help`` asset is what the monitor's HELP and
INFO commands display.

Every ``rp6502_asset()`` has to come before ``rp6502_executable()``.


Linker Configuration
====================

``rp6502_executable()`` packages the linker output into a .rp6502 ROM file
with all the assets you speficied.

.. code-block:: cmake

  rp6502_executable(hello DATA default RESET default)

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Keyword
     - Description
   * - ``DATA``
     - Where the linker output loads. Omit it and the linker output
       isn't included at all, which builds a ROM of only assets.
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

  # cc65:
  target_link_options(hello PRIVATE -C ${CMAKE_SOURCE_DIR}/src/hello.cfg)
  # llvm-mos:
  target_link_options(hello PRIVATE -T ${CMAKE_SOURCE_DIR}/src/hello.cfg)


Multiple Compiler Artifacts
===========================

A linker configuration can write more than one output file, and CMake's
``add_executable()`` models only one. In an ld65 config, every memory
area with a ``file`` of its own is another file the linker writes. CMake
knows only about about the ``%O`` file. ``rp6502_byproducts()`` tells
CMake that building ``<target>`` produces additional files.

.. code-block:: cmake

  rp6502_byproducts(<target> <file>...)

Microsoft BASIC is a working example. Its image is three loads at three
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

``TOUCH`` is a zero-size area to touch the file ``%O`` which signals
the build system of a successful compile.
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

That last line has no ``DATA``, because the linker output is the empty
``TOUCH`` file.


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


Command Line
============

The editor is the intended way to work, and everything above assumes it.
This section is for the cases it doesn't cover: a build server, an editor
that isn't VS Code, or a 6502 image that comes from a toolchain other
than cc65 and llvm-mos.

Building
--------

The CMake system is configured from presets. These commands do the same
thing as selecting a preset from the VS Code side panel.

.. code-block:: text

  cmake --list-presets
  cmake --preset cc65/Debug
  cmake --build --preset cc65/Debug

That leaves a ROM at ``build/cc65/debug/hello.rp6502``.

Running on Hardware
-------------------

``tools/rp6502.py`` with the run option uploads the ROM, starts it, and
attaches a terminal — Ctrl-A then X exits, Ctrl-A then B sends a break.

.. code-block:: text

  python3 tools/rp6502.py run build/cc65/debug/hello.rp6502

You will need additional arguments depending on how your device is connected.
By choosing to bypass both CMake and VS Code, you have put yourself on
the road less travelled. You will need to use the help.

.. code-block:: text

  python3 tools/rp6502.py --help


Packaging a ROM by Hand
-----------------------

``rp6502.py create`` builds a ``.rp6502`` from files, and it is what
``rp6502_executable()`` calls underneath. Use it directly when your 6502
image comes from somewhere CMake isn't driving, such as a macro assembler
that emits a fully linked binary.


Here is a whole program: an assembler's linked binary that loads at
``$0400``, a help file, a data file, and a splash image staged in XRAM.

.. code-block:: text

  # The help text, as a named asset.
  python3 tools/rp6502.py -a help -o help.rp6502 create plvm.help

  # A data file the program opens as ROM:level1.
  python3 tools/rp6502.py -a level1 -o level1.rp6502 create level1.dat

  # A binary staged in XRAM before the 6502 starts.
  python3 tools/rp6502.py -a 0x10000 -o splash.rp6502 create splash.bin

  # The assembler output at $0400 with a reset vector, merging the rest.
  python3 tools/rp6502.py -a 0x0400 -r 0x0400 -o plvm.rp6502 \
      create plvm.bin help.rp6502 level1.rp6502 splash.rp6502

That writes one ``plvm.rp6502`` holding three memory chunks — the code at
``$0400``, the reset vector at ``$FFFC``, and the splash at ``$10000`` —
and two named assets, ``help`` and ``level1``.


ROM File Format
===============

A ROM file begins with a shebang line, followed by any number of assets.
Text lines end with ``\r``, ``\n``, or both, and numbers may be written
in decimal (255), C-style hex (0xFF), or MOS-style hex ($FF).

**Shebang** — first line of every ROM file:

.. code-block:: text

  #!RP6502

**Null-named asset** — a group of memory chunks loaded directly into RAM:

.. code-block:: text

  #>len crc

Followed by one or more memory chunks, each a header line plus ``len``
bytes of raw binary data:

.. code-block:: text

  addr len crc

.. list-table::
   :widths: 1 20
   :header-rows: 1

   * - Field
     - Description
   * - ``addr``
     - Destination address in 6502 RAM (0x0000-0xFEFF) or XRAM
       (0x10000-0x1FFFF).
   * - ``len``
     - Number of raw binary bytes that immediately follow this line.
   * - ``crc``
     - CRC of the binary payload.

**Named asset** — a raw binary blob identified by name:

.. code-block:: text

  #>len crc name

Followed immediately by ``len`` bytes of raw binary data. Assets repeat
until end of file.

.. list-table::
   :widths: 1 20
   :header-rows: 1

   * - Field
     - Description
   * - ``len``
     - Number of raw binary bytes that immediately follow this line.
   * - ``crc``
     - CRC of the binary payload.
   * - ``name``
     - Asset identifier string.

There's no enforced limit on the number or size of named assets. Opening
a file is a linear search; it skips over the data, but how many seeks and
string compares your application can tolerate is up to you.
