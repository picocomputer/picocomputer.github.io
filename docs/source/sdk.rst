============================
RP6502-SDK
============================

RP6502 - Software Development Kit


Introduction
============

Picocomputer software is distributed as a ROM, one file ending in
``.rp6502`` that holds the program, its assets, and the 6502 vectors.
The SDK builds one of those, puts it on a machine, and debugs it while
it runs.

The `RP6502 project template <https://github.com/picocomputer/rp6502-sdk>`__
is scaffolding for a new Picocomputer 6502 program. It builds with either
6502 compiler, cc65 or llvm-mos. Three "Hello, world!" examples are included
to start from — one in C that builds with either compiler, and the same
program in each assembler's syntax.


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
emulator for your system then build hello world and run it in the
emulator. It will also create the ``.rp6502`` settings file described
below. It is expected that you commit these tools to your repository and
update them manually as needed, either from a task or the command line.
The emulator executable and settings file are ignored by git.

Your debugger may take focus when the program stops so make sure to
check if the emulator hides behind your debugger or editor window.


Running and Debugging
=====================

"Start Debugging" (F5) offers two configurations. Use the "Run and Debug"
side panel to select which.

**RP6502 (Emulator)** is the default. It builds your project and runs it
with source-level debugging in the :doc:`emu`.

**RP6502 (Hardware)** builds your project and runs it on an :doc:`pico`.
Connect with telnet, or with a USB cable to the VGA module's USB port.

Breakpoints, stepping, the call stack, and watch expressions work only on
the emulator. Debugging on hardware provides a terminal instead. llvm-mos
provides type information and cc65 does not; the :doc:`emu` has the details.


The .rp6502 Settings File
=========================

The settings file is a dotfile called ``.rp6502`` in your project root.
Edit the first section with the correct communications port
or IP address and key of a :doc:`pico` you want to test with.

.. code-block:: text

  [RP6502][Launch]
  emulator = tools/rp6502-emu
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
     - Path to the emulator, written for you as ``tools/rp6502-emu`` when
       the tools fetched one. A relative path is resolved against this
       file's own folder first, so the project folder stays portable.
       Anything not found there is left to the operating system, where a
       bare name is looked up on the PATH.
   * - ``device``
     - The serial port the machine appears on, or a hostname to
       reach it over telnet.
   * - ``key``
     - Passkey for telnet. See :ref:`Telnet Console <ria-w-telnet-console>`.
   * - ``workdir``
     - Remote directory to work in.
   * - ``args``
     - Arguments passed to your ROM, reaching it through
       :ref:`ARGV <os-argv>`. A launch configuration that carries its own
       arguments overrides these.
   * - ``term``
     - Attach a console terminal when running on hardware.

The emulator keeps its debugger window layout here too, so each project
remembers where you left its windows.


Building a ROM
==============

The ROMs a project builds are described in ``CMakeLists.txt``, three calls
per ROM. ``add_executable()`` names it, ``target_sources()`` lists the
source files, and ``rp6502_executable()`` packages the linker output into
a ``.rp6502`` file, together with the assets added to the target. The
template starts you with all three, and the ROM is named after the
target, so this one builds ``hello.rp6502``.

.. code-block:: cmake

  add_executable(hello)
  rp6502_executable(hello DATA default RESET default)
  target_sources(hello PRIVATE
      src/main.c
  )

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
the 6502 starts.

Anything else is a name, and named assets become part of the filesystem
while your ROM runs. Prefix the name with ``ROM:`` and open it like any
other file. They're read-only, and you can have several open at once.

.. code-block:: C

  open("ROM:help", O_RDONLY);

Some names are special. The ``help`` asset is what an :doc:`pico`
monitor's HELP and INFO commands display.

Every ``rp6502_asset()`` has to come before ``rp6502_executable()``.


.. _sdk-ram-memory-map:

RAM Memory Map
==============

Each compiler includes a linker script for the Picocomputer:
``cfg/rp6502.cfg`` for cc65 and ``mos-platform/rp6502/link.ld`` for
llvm-mos. For a different layout, copy the script into your project, change
the copy, and pass it to the linker with ``target_link_options``.
The default linker script gives the full 63.75K of RAM over to the linker to
manage automatically. Most projects will not need a custom script.

.. code-block:: cmake

  # cc65:
  target_link_options(hello PRIVATE -C ${CMAKE_SOURCE_DIR}/src/hello.cfg)
  # llvm-mos:
  target_link_options(hello PRIVATE -T ${CMAKE_SOURCE_DIR}/src/hello.ld)

The `ld65 documentation <https://cc65.github.io/doc/ld65.html>`__
describes the cc65 script format, and the llvm-mos wiki page `Linker Script
<https://llvm-mos.org/wiki/Linker_Script>`__ describes the llvm-mos format.


.. _sdk-xram-memory-map:

XRAM Memory Map
===============

XRAM is 64 KB of memory outside the 6502's address space, reached through
the RIA's :ref:`XRAM portals <ria-extended-ram>`. It holds the data
for the virtual devices: keyboard, mouse, tablet and gamepad input, the PSG
and OPL2 sound generators, VGA mode configurations, and the pixels, tiles
and sprites the modes draw. XRAM has no fixed map. You decide where each
device goes, and your program sets the device's XREG to that address.

You keep that map in one file, ``xram.h`` for C or ``xram.inc`` for
assembly. It holds the structure for each device you use and a layout that
places them in XRAM, with a name for each address. The file changes as your
program does. Add a device's structure when you start using the device, and
rearrange the layout as your data grows.

The structures are in the :doc:`ria` and :doc:`vga` datasheets. Each one is
in a code block labeled ``xram.h`` or ``xram.inc``, together with its
constants and XREG macros. Choose the C, ca65 or llvm-mc tab, then use the
"Copy to clipboard" button in the corner of the block to copy the whole
block into your file.

The structures are not part of ``rp6502.h`` or ``rp6502.inc``. Your program
builds from your own copy, so a name that changes in the docs does not break
your build. The ABI is stable, because registers, offsets, and sizes stay the
same. Only the names can change, and you can rename anything in your copy.

This example is for a program that uses only the keyboard. The keyboard
definitions are the :ref:`Keyboard <ria-keyboard>` block from the
:doc:`ria` datasheet, and the layout after them places the keyboard at
address 0.

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #ifndef XRAM_H
      #define XRAM_H

      #include <rp6502.h>
      #include <stdbool.h>
      #include <stddef.h>
      #include <stdint.h>

      #define KEYBOARD_NO_KEY 0
      #define KEYBOARD_NUM_LOCK 1
      #define KEYBOARD_CAPS_LOCK 2
      #define KEYBOARD_SCROLL_LOCK 3

      #define KEYBOARD_PRESSED(keys, code) ((keys)[(code) >> 3] & (1 << ((code) & 7)))

      #define xreg_ria_keyboard(...) xreg(0, 0, 0, __VA_ARGS__)

      typedef struct
      {
          uint8_t keys[32];
      } keyboard_t;

      typedef struct
      {
          keyboard_t keyboard;
      } xram_layout_t;

      #define XRAM_KEYBOARD offsetof(xram_layout_t, keyboard)

      #endif

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .ifndef XRAM_INC
      XRAM_INC = 1

      KEYBOARD_NO_KEY      = 0
      KEYBOARD_NUM_LOCK    = 1
      KEYBOARD_CAPS_LOCK   = 2
      KEYBOARD_SCROLL_LOCK = 3

      .macro xreg_ria_keyboard addr
          xreg 0, 0, 0, addr
      .endmacro

      .struct keyboard_t
          keys .res 32
      .endstruct

      .struct xram_layout_t
          keyboard .tag keyboard_t
      .endstruct

      XRAM_KEYBOARD = xram_layout_t::keyboard

      .endif

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .ifndef XRAM_INC
      XRAM_INC = 1

      KEYBOARD_NO_KEY      = 0
      KEYBOARD_NUM_LOCK    = 1
      KEYBOARD_CAPS_LOCK   = 2
      KEYBOARD_SCROLL_LOCK = 3

      .macro xreg_ria_keyboard addr
          xreg 0, 0, 0, \addr
      .endm

      KEYBOARD_KEYS = 0
      KEYBOARD_SIZE = 32

      XRAM_KEYBOARD = 0

      .endif

Each ``XRAM_`` name is the address of one part of the layout, and your
program uses those names wherever it needs an XRAM address. This code maps
the keyboard to its address and waits for a key to be pressed.

.. tab:: C
   :new-set:

   .. code-block:: C

      xreg_ria_keyboard(XRAM_KEYBOARD);
      RIA.addr0 = XRAM_KEYBOARD;
      RIA.step0 = 0;
      while (RIA.rw0 & (1 << KEYBOARD_NO_KEY))
          ;

.. tab:: ca65

   .. code-block:: ca65

          xreg_ria_keyboard XRAM_KEYBOARD
          lda #<XRAM_KEYBOARD
          sta RIA_ADDR0
          lda #>XRAM_KEYBOARD
          sta RIA_ADDR0+1
          lda #0
          sta RIA_STEP0
      :   lda RIA_RW0
          and #1 << KEYBOARD_NO_KEY
          bne :-

.. tab:: llvm-mc

   .. code-block:: ca65
      :force:

          xreg_ria_keyboard XRAM_KEYBOARD
          lda #(XRAM_KEYBOARD & $FF)
          sta RIA_ADDR0
          lda #((XRAM_KEYBOARD >> 8) & $FF)
          sta RIA_ADDR0+1
          lda #0
          sta RIA_STEP0
      1:  lda RIA_RW0
          and #(1 << KEYBOARD_NO_KEY)
          bne 1b


Addresses in CMake
------------------

``rp6502_xram()`` reads the header and gives CMake the same names, so the
layout is written once. Without it the same address sits in both the header
and the CMake file, and the two drift apart the first time the layout
changes.

.. code-block:: cmake

  rp6502_xram(<header> <regex> [<unaligned_regex>])

.. code-block:: cmake

  rp6502_xram(src/xram.h "XRAM_.*")
  rp6502_asset(hello XRAM_BITMAP_DATA img/logo.bin)

The regular expression chooses which names to take and has to match a whole
name. Only ``#define`` lines whose value starts with ``offsetof`` are read,
so the rest of the header is yours. Call ``rp6502_xram()`` before
the ``rp6502_asset()`` calls that use
its names. Each name is an ordinary CMake variable too, so
``${XRAM_BITMAP_DATA}`` works anywhere else you need it.

Editing the header configures your project again, so these addresses can
never go stale. A layout too big for the 64K of XRAM stops the build.

``rp6502_xram()`` reads C only. For an assembly project, pass
``rp6502_asset()`` the address as a number, such as ``0x10000`` plus the
offset, or set a CMake variable to it.

Alignment
---------

Neither compiler pads a structure, so a member starts wherever the members
before it end. Mode configurations, palettes, and the PSG are read in 16-bit
values, so they need an even address. Every address is checked, and an odd
one stops the build.

.. code-block:: text

  xram.h: XRAM_BITMAP_CONFIG is unaligned at $9A1D. To allow, use the
  [<unaligned_regex>] in rp6502_xram.

Pixel data, fonts, tiles, sprite images, and the keyboard, mouse, gamepad
and tablet blocks work at any address, so the check on those is advice
rather than a hardware rule. Follow it anyway. Some hosts are faster for
it.

The 64 bytes of the PSG must also stay within one page, and the OPL2
registers must start on a page. These are the only two things not checked,
so make sure of them yourself.


Multiple Compiler Artifacts
===========================

A linker configuration can write more than one output file, and CMake's
``add_executable()`` models only one. In an ld65 config, every memory
area with a ``file`` of its own is another file the linker writes. CMake
knows only about the ``%O`` file. ``rp6502_byproducts()`` tells
CMake that building ``<target>`` produces additional files.

.. code-block:: cmake

  rp6502_byproducts(<target> <file>...)

Microsoft BASIC is a working example. Its image is three loads at three
addresses with nothing contiguous between them. The ``CHRGET`` routine sits
in zero page, then the init code, then the interpreter, so its linker
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

That writes one ``plvm.rp6502`` holding three memory chunks and two named
assets. The chunks are the code at ``$0400``, the reset vector at ``$FFFC``,
and the splash at ``$10000``, and the assets are ``help`` and ``level1``.


.. _sdk-rom-file-format:

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
       At most 1024, and a chunk may not cross a 64 KB boundary.
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
