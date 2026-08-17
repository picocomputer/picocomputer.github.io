============================
RP6502-SDK
============================

RP6502 - Software Development Kit


Introduction
============

The `RP6502 project template <https://github.com/picocomputer/rp6502-sdk>`__
is scaffolding for a new Picocomputer 6502 program. It builds with either
6502 compiler, cc65 or llvm-mos, and switching between them is one
setting. Three "Hello, world!" examples are included to start from — one
in C that builds with either compiler, and the same program in each
assembler's syntax.

Its README covers installing the tools and driving everything from a
command line. This page picks up where that leaves off, in VS Code.

VS Code is strongly recommended and the template is set up for it, but
nothing here is required. Everything works from a command line and any
editor.


Getting Started
===============

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
small script in ``tools/``, which goes and gets the ROM packager, the
CMake commands your project calls, and the toolchain files. The emulator
for your machine comes down at the same time.

They're ordinary files in your repository after that, so commit them
along with everything else — except the emulator, which is a binary that
won't work for other developers and is in ``.gitignore`` instead. Nothing
is fetched behind your back afterwards: configuring a project that
already has its tools never goes to the network, and a tool you delete
stays deleted.

**5. Press F7 to build.** That leaves a ROM at
``build/<compiler>/<config>/hello.rp6502``.

**6. Press F5 to debug.** The first time, this creates the ``.rp6502``
settings file described next.


The .rp6502 File
================

Everything about *running* your program lives in one file in the project
root. It's created the first time you Start Debugging and is ignored by
git, because it describes your machine rather than your project.

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
with source-level debugging in the :doc:`emu`. Nothing has to be plugged
in.

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
instead. Once you've moved the load address, ``default`` is no longer the
right answer — use ``file`` or say the address outright.


Packaging Multiple Artifacts
============================

A linker configuration can write more than one output file, and CMake's
``add_executable()`` only models one of them. In an ld65 config, every
memory area with a ``file`` of its own is another file the linker writes.
``%O`` is the one CMake knows about; a literal name is one it doesn't.

.. code-block:: text

  MEMORY {
      RAM:  file = %O,         start = $0200,  size = $7E00;
      XRAM: file = "xram.bin", start = $10000, size = $10000;
  }

Nothing depends on ``xram.bin``, nothing cleans it, and nothing rebuilds
when it changes, because as far as the build is concerned it doesn't
exist. ``rp6502_byproducts()`` is how you say that it does.

.. code-block:: cmake

  rp6502_byproducts(hello ${CMAKE_CURRENT_BINARY_DIR}/xram.bin)

From there it's an ordinary input, and goes into the ROM like anything
else — as an asset at an address, as a named asset, or as an extra ROM
merged by ``rp6502_executable()``. One linker configuration, several
output files, one ``.rp6502``.

Packaging Multiple ROMs
=======================

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
- `Examples <https://github.com/picocomputer/examples>`__ — dozens of
  small programs, each one a working ``CMakeLists.txt`` entry.
