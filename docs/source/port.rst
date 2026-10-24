============================
PORT
============================

Portability


Introduction
============

Every player should get a great experience from your game, whatever
machine they play it on. The same ROM runs on the :doc:`pico`, the
:doc:`fpga`, the :doc:`emu`, and the :doc:`web`. This page covers what to
plan for so that your game works well on all four: how many sprites fit
on one row of the canvas, how to read gamepads so that any modern one
works, and how files and saves differ between the machines.


.. _port-sprite-limits:

Sprite Limits
=============

In practice, the limits of a game are the 6502 at 8 MHz and the 64 KB of
XRAM, not the sprites. On a 320x240 canvas, the VGA system can usually
draw more sprites than a program can move each frame.

The VGA system draws the canvas one scanline at a time, and it has a fixed
number of clocks to draw the sprites of each scanline. The figures in this
section are for the :doc:`fpga`, where the VGA system is a hardware
renderer built in programmable logic. Its video logic runs at 50.4 MHz,
and the costs in this section are counted in its clocks.

Clocks per Scanline
-------------------

As on the VGA page, a scanline here is one row of pixels of the canvas. A
signal line, one line of the VGA signal, is 800 pixel clocks, of which 640
are visible. The video logic runs at twice the 25.2 MHz pixel clock, so it
has 1,600 clocks in each signal line. A scanline of a 640-wide canvas is
sent as one signal line, so it has 1,600 clocks. A 320-wide canvas is
doubled across and down, so each of its scanlines is sent as two signal
lines and has 3,200 clocks for half as many pixels. Those extra clocks are
the main reason to use a 320-wide canvas for a game.

Sprite Costs
------------

Paletted and custom sprites are the sprites of :ref:`mode 5 <vga-mode-5>`,
and 16-bit and affine sprites are the sprites of :ref:`mode 4
<vga-mode-4>`. To check a scanline, add up these costs and compare the
total with 1,600 clocks at 640 wide or 3,200 at 320 wide:

.. list-table::
   :widths: 40 15 15 15 15
   :header-rows: 1

   * -
     - Paletted
     - Custom
     - 16-bit
     - Affine
   * - Once per scanline
     - 9
     - 9
     - 9
     - 9
   * - Each sprite that could show on the scanline
     - 2
     - 2½
     - 2
     - 5
   * - Each sprite that shows on the scanline
     - 3
     - 3
     - 3
     - 4
   * - Each pixel of a sprite that lands on the scanline
     - ½
     - ½
     - ½
     - 1 to 2
   * - Each palette cache miss (loads two colors)
     - 3
     - 3
     -
     -

For example, one plane is programmed with a sprite array of 10 paletted
8x8 sprites at 1 bit per pixel, and all of them use the same 2-color
palette. 5 of the sprites show on the scanline. The scanline costs:

- 9 clocks once per scanline.
- 20 clocks for the 10 sprites that could show on the scanline, 2 each.
- 15 clocks for the 5 sprites that show on the scanline, 3 each.
- 20 clocks for the 8 pixels of each of those 5 sprites, at half a clock
  a pixel.
- 3 clocks for one palette cache miss. The sprites use only 2 colors, and
  one miss loads both. `Keeping Palettes in the Cache`_ covers palettes
  with more colors.

That is 67 clocks of the 3,200 of a scanline on a 320-wide canvas.

With sprites on more than one plane, each further plane with sprites adds
8 clocks. Skipping a plane without sprites to reach a plane with sprites
adds 2 clocks.

When Sprites Do Not Fit
-----------------------

When the VGA system cannot finish the sprites of a scanline before the
scanline is due:

- On the :doc:`pico`, the scanline shows part blue and part black
  instead of the picture.
- On the :doc:`fpga`, the sprites that do not fit do not show.
- On the :doc:`emu` and the :doc:`web`, every sprite shows, but the
  emulator slows down. It no longer runs at 60 frames a second, and the
  6502 runs slower than real time.

Maximum Sprites
---------------

Working out the clocks of a scanline with sprites of several kinds and
sizes takes some arithmetic. To show when that arithmetic starts to
matter, this table gives the most sprites of one kind and size that fit on
one scanline, with every pixel of every sprite on it. Sprites spread
across different scanlines can number far more. The paletted figures
include 768 clocks of palette cache misses, which load all 512 colors of
the cache. Custom sprites are not in the table. Each one costs half a
clock more than a paletted sprite of the same size.

.. list-table:: Maximum sprites on one scanline
   :widths: 40 30 30
   :header-rows: 1

   * -
     - 320 wide
     - 640 wide
   * - 16-bit, 8x8
     - 354
     - 176
   * - 16-bit, 16x16
     - 245
     - 122
   * - 16-bit, 32x32
     - 151
     - 75
   * - Paletted, 8x8
     - 269
     - 91
   * - Paletted, 16x16
     - 186
     - 63
   * - Paletted, 32x32
     - 115
     - 39
   * - Affine, 8x8
     - 145
     - 72
   * - Affine, 16x16
     - 83
     - 41
   * - Affine, 32x32
     - 45
     - 22

Keeping Palettes in the Cache
-----------------------------

The RP6502-FPGA reads the colors of paletted sprites through a palette
cache of 1 KB, and one cache serves the whole scanline. Paletted sprites
draw fastest when the palettes of every sprite on a scanline fit in the
cache together. Keep the palettes in one structure and check it with
``MODE5_PALETTE_CHECK()``, as :ref:`Mode 5 <vga-mode-5>` on the VGA page
shows.


.. _port-gamepads:

Gamepads
========

The RIA reports every gamepad in the same layout, which :ref:`Gamepads
<ria-gamepads>` on the RIA page describes. The report has a bit for each
of fifteen buttons, in the order that Linux and Android use for a generic
gamepad, so each button of a gamepad sold as Android-compatible sets the
bit of the same name. Xbox and PlayStation gamepads work too. Together
they are nearly every gamepad sold today. A modern gamepad whose buttons
do not map to the bits of the same name is a defect, and worth reporting.
A controller made for something other than the major consoles, such as a
controller built for emulation, is unlikely to get support, even when
someone reports it.

The order has C and Z because the Linux names were chosen around 2000,
when six-button gamepads were as common as four-button ones. Most gamepads
today have four face buttons and report nothing in the C and Z bits, or
report other buttons there, such as rear paddles. C and Z stay in the
report for programs that let players map buttons themselves.

The four face buttons vary only in labeling: XY/AB, YX/BA, or
Square/Triangle/Cross/Circle. The labeling rarely matters to a game until
it prints a button's name, or the buttons stand in for directions. For
those, the type bits of DPAD give the labeling of gamepad models with a
known layout, such as Xbox, Nintendo, and PlayStation pads. Many gamepads
report type 0, unknown, including every gamepad in RetroArch, the pads on
an Analogue Pocket dock, and most generic USB gamepads. For a gamepad of
type 0, a game can print which gamepad it was made for, or provide a
setting.

Home is the Guide button on an Xbox gamepad and the PS button on a
PlayStation one. Steam, Windows, and macOS can open a menu when Home is
pressed, and nothing in the report shows when that happens. In RetroArch
and on the Pocket, the Home bit is never set. So a portable game does not
use Home.

A game that uses one stick and one or two buttons works with nearly every
gamepad when it merges the d-pad with the left stick and gives each
action more than one face button. The low four bits of DPAD and of STICKS
are up, down, left, and right in the same order, so a bitwise OR merges
them, and the ``GAMEPAD_DPAD_`` names test the result. A and X are side
by side on every layout, and so are B and Y, so a game can map both A and
X to jump and both B and Y to fire. This code reads player 1, with the
names from the code block of :ref:`Gamepads <ria-gamepads>` in your
``xram.h``:

.. code-block:: C

  gamepad_player_t p1;
  unsigned char dirs;

  xreg_ria_gamepad(XRAM_GAMEPAD);

  xram0_read(&p1, XRAM_GAMEPAD, sizeof(p1));
  dirs = p1.dpad | p1.sticks;
  if (dirs & GAMEPAD_DPAD_LEFT)
      move_left();
  if (dirs & GAMEPAD_DPAD_RIGHT)
      move_right();
  if (p1.btn0 & (GAMEPAD_BTN0_A | GAMEPAD_BTN0_X))
      jump();
  if (p1.btn0 & (GAMEPAD_BTN0_B | GAMEPAD_BTN0_Y))
      fire();

The report has digital bits for every stick and trigger as well as their
analog values. A game that reads only the digital bits works with every
gamepad, including those without analog sticks or triggers.


.. _port-filesystems:

Filesystems
===========

A program that reads its data from ``ROM:`` and keeps its saves in
``SAVE:`` opens its files the same way on every machine. `Data Files`_
and `Saves`_ show how, and `Durability`_ says when a save is stored.

The subsections after Durability are for a program that opens the user's
own files, such as an editor or a shell. On every machine, the characters
of a name follow the rules of FAT, the filesystem of USB drives and memory
cards. The machines keep their files in different places, though, and
differ in a few details.

Data Files
----------

Graphics, levels, and other data that a program reads are most portable
as named assets inside the ROM, added with ``rp6502_asset()`` as shown in
:ref:`Adding Assets <sdk-assets>`. A program opens one as ``ROM:`` plus
its name on every machine, wherever the ROM is and whatever the working
directory is.

Files beside the ROM are less portable. A program can open them by
replacing the file name at the end of argv[0], the absolute path of the
ROM. argv[0] starts with the drive, however the ROM was started:
``MSC0:/games/hopper.rp6502``, ``C:/games/hopper.rp6502``, or
``FS:/home/user/hopper.rp6502``. A short device name typed before an
absolute path, as in ``0:/games/hopper.rp6502``, stays short. A ROM from
the null drive has ``:name`` in argv[0] and no directory, as `Installed
ROMs`_ describes. A web player has no directory beside its ROM either.
The files that its ``install`` setting names are on the null drive.

.. _port-save:

Saves
-----

The working directory can be any directory: the one a shell was in when
it started the emulator, the one a launcher left, or on the Pocket the
Assets directory that holds the ROMs. So a portable program does not build
the path of a save from the working directory. A path that starts with
``SAVE:`` names a save, a file in the save directory of the machine, and
each machine keeps that directory where saves belong. On an
:doc:`pico`, the save directory is the working directory when the ROM
starts.

This program keeps a high score in ``SAVE:hopper.hiscore``. It reads the
score when it starts, and it writes a new one when the player beats it.

.. code-block:: C

   #include <fcntl.h>
   #include <stdio.h>
   #include <unistd.h>

   unsigned hiscore;

   void hiscore_load(void)
   {
       int fd = open("SAVE:hopper.hiscore", O_RDONLY);
       if (fd < 0)
           return;
       if (read(fd, &hiscore, sizeof hiscore) != sizeof hiscore)
           hiscore = 0;
       close(fd);
   }

   void hiscore_save(void)
   {
       int fd = open("SAVE:hopper.hiscore", O_WRONLY | O_CREAT | O_TRUNC);
       if (fd < 0)
           return;
       write(fd, &hiscore, sizeof hiscore);
       syncfs(fd);
       close(fd);
   }

   int main(void)
   {
       unsigned score = 0;
       int c;
       hiscore_load();
       printf("High score %u. Type a line, one point a letter.\n", hiscore);
       while ((c = getchar()) != '\n' && c != EOF)
           ++score;
       if (score > hiscore)
       {
           hiscore = score;
           hiscore_save();
           puts("New high score!");
       }
       return 0;
   }

On the first run there is no save yet, so the open fails and the high
score stays 0. O_TRUNC empties the file before the new score is written,
so a save never keeps the end of a longer one. ``syncfs()`` returns once
the save is stored, as `Durability`_ describes.

A save is opened with :ref:`OPEN <api-open>` and O_RDONLY, O_WRONLY, or
O_RDWR, plus any of O_CREAT, O_TRUNC, O_EXCL, and O_APPEND. The program
can then read, write, seek within the file, call syncfs, and close it.
Only an open works on a ``SAVE:`` path. Every other call on one, such as
STAT, REMOVE, or OPENDIR, fails with ENODEV, or ENOSYS on the Pocket. The
file behind a save is an ordinary file, and on some machines another path
to its directory can stat or unlink it, but the directory differs by
machine and only ``SAVE:`` works on all of them.

A save slot holds a game in progress. It is written the same way, with a
structure in place of the score and the slot number in the name. This
code goes with the program above:

.. code-block:: C

   struct
   {
       unsigned char level;
       unsigned char lives;
       unsigned score;
   } game;

   int slot_open(unsigned slot, int flags)
   {
       char name[24];
       sprintf(name, "SAVE:hopper.slot%u", slot);
       return open(name, flags);
   }

   int slot_save(unsigned slot)
   {
       int fd = slot_open(slot, O_WRONLY | O_CREAT | O_TRUNC);
       if (fd < 0)
           return -1;
       if (write(fd, &game, sizeof game) != sizeof game || syncfs(fd) < 0)
       {
           close(fd);
           return -1;
       }
       return close(fd);
   }

   int slot_load(unsigned slot)
   {
       int n, fd = slot_open(slot, O_RDONLY);
       if (fd < 0)
           return -1;
       n = read(fd, &game, sizeof game);
       close(fd);
       return n == sizeof game ? 0 : -1;
   }

A game with save slots also clears them and shows which are in use.
Because only an open works on a ``SAVE:`` path, a save is cleared by
emptying it with O_TRUNC, and its size is read with
``lseek(fd, 0, SEEK_END)``. An empty slot then loads as no save, the same
as a slot that was never written.

.. code-block:: C

   int slot_clear(unsigned slot)
   {
       int fd = slot_open(slot, O_WRONLY | O_TRUNC);
       if (fd < 0)
           return -1;
       return close(fd);
   }

   long slot_size(unsigned slot)
   {
       long size;
       int fd = slot_open(slot, O_RDONLY);
       if (fd < 0)
           return 0;
       size = lseek(fd, 0, SEEK_END);
       close(fd);
       return size;
   }

A save name is 1 to 32 characters from ``A``–``Z``, ``a``–``z``,
``0``–``9``, ``.``, ``-``, and ``_``. It does not end in ``.``, and it is
not one of the names that Windows reserves for devices, ``CON``, ``PRN``,
``AUX``, ``NUL``, ``COM1`` to ``COM9``, or ``LPT1`` to ``LPT9``, alone or
with an extension. Any other name fails with EINVAL on every machine, so a
name that works on one machine works on all of them. The saves are in one
flat directory, so a name has no directories in it, but
``SAVE:/hopper.slot0`` and ``SAVE:hopper.slot0`` are the same save, so
code that joins a directory and a name with ``/`` works.

Many games can share one save directory, so a save name starts with a
short name for the game. The recommended form is that name, a dot, and a
suffix, such as ``SAVE:hopper.hiscore``, ``SAVE:hopper.slot0``, or
``SAVE:hopper.X42``. Case in a save name matters on some machines and not
on others, as `Names`_ describes, so open a save with the exact case of
its name, and do not create two saves whose names differ only in case.

The save directory is fixed when a ROM starts, so a CHDIR by the program
does not move its saves. A missing directory is created the first time a
program creates a save, so a game that never saves leaves nothing behind.
The Pocket cannot create directories, so its save directory is shipped
with the core. The save directory on each machine is:

- On an :doc:`pico`, the working directory when the ROM starts.
- On the Pocket, ``/Saves/rp6502/common/``.
- On the :doc:`emu` on Linux, the directory given with ``--save-dir``,
  else ``$XDG_DATA_HOME/rp6502/``, which is ``~/.local/share/rp6502/`` by
  default.
- On the RP6502-EMU on macOS, the directory given with ``--save-dir``,
  else ``~/Library/Application Support/io.github.picocomputer.rp6502-emu/``.
- On the RP6502-EMU on Windows, the directory given with ``--save-dir``,
  else ``Saved Games\rp6502\``.
- In RetroArch, ``rp6502/`` in the save directory of RetroArch, or the
  working directory when the ROM starts if RetroArch has no save
  directory.
- On an :doc:`web`, the browser's storage, in the database that the
  ``db`` setting of the web player names, as :ref:`Saves <web-saves>` on
  the RP6502-WEB page describes. Without ``db``, saves last only until the
  page closes.

.. _port-durability:

Durability
----------

Written data is stored in two steps: ``close()`` passes it on for storage,
and ``syncfs()`` returns once it is stored. The examples in `Saves`_ call
``syncfs()`` before ``close()``. What survives a failure differs by
machine:

- On an :doc:`pico`, close and syncfs write the data to the drive.
  The buffers aren't nearly large enough to survive the time it takes
  to reach for and remove a USB drive.
- On the Pocket, a successful syncfs does not mean the data is on the
  card, because the Pocket sends no reply once the data is written.
  But like the :doc:`pico`, buffers are too small to be of concern.
- On the :doc:`emu` on Linux, macOS, and Windows, written data survives a
  crash of the emulator, and syncfs keeps it through a crash of the whole
  computer.
- In RetroArch, a save is as durable as on the system RetroArch runs on.
- On an :doc:`web` with the ``db`` setting, close queues a save to the
  browser's storage, and syncfs waits until the save is stored. Without
  ``db``, nothing outlasts the page.

Drives
------

A program that opens the user's files works with paths, and a path can
start with the device name of a drive. The device name always ends in
``:``, and the path follows the colon directly, as in ``MSC0:/games``. An
:doc:`pico` mounts its USB drives as ``MSC0:`` to ``MSC9:``, and ``0:``
to ``9:`` are short names for the same drives. On the :doc:`emu` on
Windows, the drives are the drive letters, ``A:`` to ``Z:``. Every other
machine has a single root, named ``FS:``, so ``FS:/games`` and ``/games``
are the same directory there. A path with no device name works on every
machine, and a path that names a drive works only where that drive
exists. A path that names a drive the machine lacks fails with ENODEV.

Other device names, such as ``CON:``, ``TTY:``, ``ROM:``, and ``SAVE:``,
name a device that a program opens like a file. These four exist on
every machine, and a device name that a machine lacks fails with ENODEV.

Names
-----

``/`` and ``\`` both separate directories, and ``..`` at the root of a
drive stays at the root. A path is at most 255 bytes, drive included, and
a longer one fails with EINVAL.

A ``:`` anywhere but at the end of a device name makes a path invalid. A
``:`` before the first separator names an unknown drive, and the call
fails with ENODEV. A ``:`` after it fails with EINVAL. The characters
that FAT refuses in a name also fail with EINVAL: ``"``, ``*``, ``<``,
``>``, ``?``, ``|``, a control character, and character 127. These rules
hold on every machine, even on Linux and macOS, which allow most of these
characters in a name. On Windows, a file also cannot be named ``CON``,
``PRN``, ``AUX``, ``NUL``, ``CONIN$``, ``CONOUT$``, ``COM1`` to ``COM9``,
or ``LPT1`` to ``LPT9``, with or without an extension, and those names
fail with EINVAL there.

Text on a Picocomputer uses a code page, a set of 256 characters chosen
with ``RIA_ATTR_CODE_PAGE``. A file put on a drive by another computer can
have a name with a character the code page cannot hold, or one that FAT
refuses, such as ``:``. A listing shows character 127 in place of each
such character, and the file cannot be opened, because character 127 is
refused in a path. On an :doc:`pico`, a name with a character the code
page cannot hold is listed instead by its 8.3 name, a short name that a
FAT drive stores beside each long name: up to eight characters, a dot,
and up to three more, such as ``NOTES~1.TXT``. The 8.3 name opens the
file.

Case in a name is ignored on some machines and matters on others, so
``Save.dat`` and ``save.dat`` are one file on an :doc:`pico` and two on
Linux. No machine changes the case of a name. A portable program opens a
file with the exact case of its name, as if case always mattered, and
picks a name for a new file as if case never mattered, so a new file
cannot replace one whose name differs only in case.

.. _port-files:

Files and Directories
---------------------

A file can be open for reading on several descriptors at once. On a USB
drive of an :doc:`pico`, a file that is open for writing has no other
descriptor: an open of it fails with EBUSY, and so does an open for
writing of a file that is open, and a REMOVE or a RENAME of an open
file. The other machines allow these. A portable program closes a file
before it opens that file again to write it, and before a REMOVE
removes it or a RENAME moves or replaces it. On an :doc:`pico` and on
Windows, a REMOVE of the current directory also fails with EBUSY.

A RENAME that replaces an entry is atomic on Linux and macOS, on the
:doc:`web`, and for a file on Windows. On an :doc:`pico`, and for a
directory on Windows, RENAME removes the entry at the new name first, and
then renames. When the rename fails after that, the entry at the new name
is gone and the old name stays in place.

On the :doc:`emu` on Linux and macOS, and on the :doc:`web`, CHMOD
changes only Read Only, and UTIME sets only the modification date and
time. There, STAT and READDIR report Hidden for a name that starts with
``.``, Archive for every file, and never System. A READDIR of an entry
whose information the host cannot read, such as a broken symbolic link,
fails with ENOENT or EACCES there, and the next READDIR continues with
the next entry.

Working Directory
-----------------

A relative path starts from the current directory of the current drive.
Where that is when a machine starts differs: the root of ``MSC0:`` on an
:doc:`pico`, ``FS:/Assets/rp6502/common`` on the Pocket, the directory
the :doc:`emu` was started from, the working directory of RetroArch when
the core runs there, and the root, ``FS:/``, on an :doc:`web`.

The :doc:`emu` and the :doc:`web` never change the current drive or
directory themselves. Only CHDIR from a program changes them, and a ROM
starts with the drive and directory that the ROM before it left. On an
:doc:`pico`, an :ref:`NFC card <pico-nfc>` is different: the ROM it
names starts in the directory that holds the ROM.

A CHDIR into a directory on another drive also makes that drive current.
Each drive keeps the last directory used on it, so a later CHDIR to the
device name of the drive alone, such as ``MSC1:``, returns to that
directory. On a machine with one drive, a CHDIR to its device name alone
succeeds and changes nothing. The Pocket has one fixed directory, so
every CHDIR fails there with ENOSYS.

.. _port-installed-roms:

Installed ROMs
--------------

The null drive, ``:``, holds ROMs and other files that come from outside
the filesystem. A program runs an installed ROM with EXEC and the name
``:name``, and case does not matter in the name.

How a ROM gets onto the null drive depends on the machine. On an
:doc:`pico`, the INSTALL command of the :ref:`monitor <pico-monitor>`
puts a ROM in flash, where it stays. On the :doc:`emu`, ``--install``
puts a file there for one run, and on the :doc:`web`, the ``install``
setting of the web player puts one there for one visit. The Pocket has no
installed ROMs.

The RP6502-EMU, RetroArch included, and the RP6502-WEB also run a ROM from
the null drive when no program could name its path, as when the path is
longer than 255 bytes, or has a character that the code page cannot hold
or that FAT refuses. That ROM has ``:name`` in argv[0].

On the RP6502-EMU and the RP6502-WEB, a program can also open an
installed file for reading, such as a BASIC program. Every other call on
a ``:`` path fails with ENODEV.

.. _port-compatibility:

Compatibility
-------------

The table sums up how the filesystems of the machines differ. The
RP6502-EMU column holds for RetroArch too, except that its working
directory at start is the working directory of RetroArch, and RetroArch
has no ``--install``.

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20 20

   * -
     - RP6502-PICO
     - RP6502-FPGA
     - RP6502-EMU
     - RP6502-WEB
   * - Drives
     - ``MSC0:``–``MSC9:``, or ``0:``–``9:``
     - ``FS:``
     - ``FS:``, or ``A:``–``Z:`` on Windows
     - ``FS:``
   * - Working directory at start
     - ``MSC0:/``
     - ``FS:/Assets/rp6502/common``
     - the directory the emulator was started from
     - ``FS:/``
   * - Installed ROMs
     - INSTALL, kept in flash
     - none
     - ``--install``, for one run
     - ``install``, for one visit
   * - Volume label
     - the FAT label
     - ENOSYS
     - ENOSYS
     - ENOSYS
   * - GETFREE
     - the FAT volume
     - ENOSYS
     - the host volume
     - the storage estimate of the browser
   * - Case in names
     - ignored
     - ignored
     - matters on Linux, ignored on macOS and Windows
     - matters
   * - Names outside the code page, in a listing or GETCWD
     - the 8.3 name, which opens the file
     - not applicable
     - character 127, and the name cannot be opened
     - character 127, and the name cannot be opened
   * - Durability limit
     - unplugging a drive before close or syncfs loses data
     - the Pocket sends no reply once data is written, so syncfs cannot
       wait for it
     - a crash of the computer before syncfs loses data
     - with ``db``, close queues the save and syncfs waits for it;
       without ``db``, saves last until the page closes

The Pocket also has limits of its own. It opens files by path, but it has
no directory operations and no listing:

- STAT, REMOVE, RENAME, MKDIR, CHDIR, CHMOD, UTIME, GETLABEL, SETLABEL, and
  GETFREE fail with ENOSYS.
- OPENDIR, READDIR, CLOSEDIR, TELLDIR, SEEKDIR, and REWINDDIR fail with
  ENOSYS.
- An open fails with EACCES for the root of the card,
  ``Assets/rp6502/common``, ``Saves/rp6502/common``, and the directories
  above them. An open of any other directory is sent to the Pocket as the
  open of a file.
- A seek past the end that cannot extend a file fails with EIO, because
  the Pocket has no error for a full card.
