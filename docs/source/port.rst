============================
RP6502-PORT
============================

RP6502 - Portability


Introduction
============

A ROM runs unchanged on every Picocomputer: an :doc:`pico`, the
:doc:`emu` on a desktop, in a browser or in RetroArch, and the
:doc:`fpga` on an Analogue Pocket. The 6502, its memory, the video and the
sound are the same on all of them. Gamepads and filesystems vary, because
they come from the hardware and the operating system under each machine.
How a program handles both so that it works the same way everywhere is
covered below, and the filesystem differences that remain are listed in a
table at the end.


.. _port-gamepads:

Gamepads
========

The RIA reports every gamepad in the same layout, described in
:ref:`Gamepads <ria-gamepads>` in the RIA datasheet. The report has a bit
for each of fifteen buttons, in a fixed order: A, B, C, X, Y, Z, L1, R1,
L2, R2, Select, Start, Home, L3 and R3. That order is the DInput layout,
named after a mode of many USB gamepads, and how it came about explains
why the report has C and Z when most gamepads do not.

The Sega Genesis controller of 1989 has three face buttons, A, B and C,
and Sega's six-button pad of 1993 adds a second row, X, Y and Z. The Sega
Saturn pad of 1994 keeps all six and adds L and R shoulder buttons. Many
PC gamepads that followed, such as Microsoft's SideWinder Game Pad of
1996, have the same six face buttons and two shoulder buttons.

Since 2000, Linux has had a name for each button of a generic USB gamepad,
in order: the first button is A, then B, C, X, Y and Z, as on those pads,
then two pairs of shoulder buttons, Select, Start and Mode. Two names
added in 2001 follow Mode, for the stick clicks of Sony's DualShock.
Android has used the same names in the same order since 2011. Many USB
gamepads have two modes: XInput, in which the gamepad works as an Xbox 360
controller, and DInput, named after DirectInput in Windows, in which it
works as a generic USB gamepad. In DInput mode, some gamepads, such as
those from 8BitDo, report their buttons in the Linux order. That is the
order of the RIA report, with Mode as Home and the stick clicks as L3 and
R3.

Nearly every gamepad today has four face buttons, like the A, B, X and Y
of the Xbox 360 controller of 2005. C and Z never became a standard, and
Sega itself left them off its Dreamcast pad in 1998. A four-button gamepad
leaves the C and Z bits empty or reports other buttons there, such as rear
paddles, and even the six-button USB pad made for Sega's Mega Drive Mini
reports its C and Z buttons in other bits. Six-button support takes a
mapping for every model, so it is left out of the RP6502. C and Z stay in
the report because of the DInput history, and for programs that let
players map buttons themselves.

The four face buttons vary only in labeling — XY/AB, YX/BA, or
Square/Triangle/Cross/Circle. Each face button reports in the place of its
letter, wherever it sits on the gamepad, and Cross, Circle, Square and
Triangle report as A, B, X and Y. The labeling rarely matters to a game
until it prints a button's name, or the buttons stand in for directions.
For those, the type bits of the DPAD register give the labeling of gamepad
models with a known layout, such as Xbox, Nintendo and PlayStation pads.
Many gamepads report type 0, unknown, including every gamepad in
RetroArch, the pads on an Analogue Pocket dock and most generic USB
gamepads. For a gamepad of type 0, a game can print which gamepad it was
made for, or have a setting that picks Xbox or Nintendo labels.

Home is the Guide button on an Xbox gamepad and the PS button on a
PlayStation one, and a portable game does not use it. Steam, Windows and
macOS can open a menu when Home is pressed, and nothing in the report
shows when that happens. In RetroArch and on the Pocket, the Home bit is
never set.

A game that uses one stick and one or two buttons works with nearly every
gamepad when it merges the d-pad with the left stick and gives each action
more than one face button. The low four bits of DPAD and of STICKS are up,
down, left and right in the same order, so a bitwise OR merges them. A
game can map both A and X to jump and both B and Y to fire, because each
of those pairs sits side by side on every layout. After
``xreg(0, 0, 2, 0xFF00)``, the RIA writes the report to ``$FF00`` in
extended RAM (XRAM), and this function reads player 1 from there:

.. code-block:: C

   #include <rp6502.h>

   unsigned char dirs, jump, fire;

   void read_player1(void)
   {
       unsigned char dpad, sticks, btn0;
       RIA.addr0 = 0xFF00;
       RIA.step0 = 1;
       dpad = RIA.rw0;
       sticks = RIA.rw0;
       btn0 = RIA.rw0;
       dirs = (dpad | sticks) & 0x0F; /* up 1, down 2, left 4, right 8 */
       jump = btn0 & 0x09;            /* A or X */
       fire = btn0 & 0x12;            /* B or Y */
   }

The report has digital bits for every stick and trigger as well as their
analog values. A game that reads only the digital bits works with every
gamepad, including those without analog sticks or triggers.


.. _port-filesystems:

Filesystems
===========

The rules of FAT, the filesystem of USB drives and memory cards, apply on
every machine to drive names, file names, opens, renames and seeks. A
program that keeps to those rules opens its files the same way on every
machine.

Drives
------

A path can start with a drive name. A drive name always ends in ``:``,
and the path follows the colon directly, as in ``MSC0:/games``. An
:doc:`pico` has a drive for each USB storage volume, ``MSC0:`` to
``MSC9:``, and ``0:`` to ``9:`` are short names for the same drives. On
Windows, the drives are the drive letters, ``A:`` to ``Z:``. Every other
machine has a single root, named ``FS:``, so ``FS:/games`` and ``/games``
are the same folder there. A path with no drive name works on every
machine, and a path that names a drive works only where that drive
exists. A path that names a drive the machine lacks fails with ENODEV.

Some names that end in ``:`` are devices, which a program opens like a
file. ``CON:``, ``TTY:``, ``ROM:`` and ``SAVE:`` exist on every machine,
and a device name that a machine lacks fails with ENODEV.

Names
-----

``/`` and ``\`` both separate folders, and ``..`` at the root of a drive
stays at the root. A path is at most 255 bytes, drive included, and a
longer one fails with EINVAL.

A ``:`` anywhere but at the end of a drive name makes a path invalid. A
``:`` before the first separator names an unknown drive, and the call
fails with ENODEV. A ``:`` after it fails with EINVAL. The characters
that FAT refuses in a name also fail with EINVAL: ``"``, ``*``, ``<``,
``>``, ``?``, ``|``, a control character, and character 127. On Windows,
a file cannot be named ``CON``, ``PRN``, ``AUX``, ``NUL``, ``CONIN$``,
``CONOUT$``, ``COM1`` to ``COM9`` or ``LPT1`` to ``LPT9``, with or
without an extension, and those names fail with EINVAL there.

Text on a Picocomputer uses a code page, a set of 256 characters chosen
with ``RIA_ATTR_CODE_PAGE``. A file put on a drive by another computer can
have a name with a character the code page cannot hold, or one that FAT
refuses, such as ``:``. A listing shows character 127 in place of each
such character, and the file cannot be opened, because character 127 is
refused in a path. On an :doc:`pico`, a name with a character the code
page cannot hold is listed instead by its 8.3 name, a short name that a
FAT drive stores beside each long name: up to eight characters, a dot and
up to three more, such as ``NOTES~1.TXT``. The 8.3 name opens the file.

Case in a name is ignored on some machines and matters on others, so
``Save.dat`` and ``save.dat`` are one file on an :doc:`pico` and two on
Linux. No machine changes the case of a name. A portable program opens a
file with the exact case of its name, as if case always mattered, and
picks a name for a new file as if case never mattered, so a new file
cannot replace one whose name differs only in case.

.. _port-files:

Files and Folders
-----------------

With O_APPEND, the read/write position moves to the end of the file
once, when the file opens. O_EXCL applies only together with O_CREAT. An
open with neither O_RDONLY nor O_WRONLY fails with EINVAL, and an open of
a directory fails with EACCES.

A file can be open on several descriptors at once, and reading it
through all of them is safe. A portable program closes a descriptor that
writes a file before it opens that file again, and it closes a file
before an UNLINK removes it or a RENAME moves or replaces it. Without
those closes, the results differ between machines, and a FAT drive can
be damaged.

A seek past the end of a file opened for writing extends the file with
zeros. On a full drive, that seek fails with ENOSPC and changes nothing.
A seek past the end of a file opened only for reading stops at the end.

STAT of a drive root, such as ``/`` or ``MSC0:/``, returns one fixed
entry: a directory named ``/``, with size 0 and zero dates. STAT of an
empty path or a bare drive name, such as ``MSC0:``, fails with EINVAL. A
RENAME to another drive fails with ENODEV. A file at the new name is
replaced only when the old name is also a file, and any other entry at
the new name fails with EEXIST. An UNLINK of a read-only file fails with
EACCES.

Working Directory
-----------------

A relative path starts from the current directory of the current drive.
Where that is when a machine starts differs: the root of ``MSC0:`` on an
:doc:`pico`, the folder the emulator was started from on a desktop, the
working directory of RetroArch when the core runs there, the root,
``FS:/``, in a browser, and ``FS:/Assets/rp6502/common`` on the Pocket.

The emulators never change the current drive or directory themselves.
Only CHDIR and CHDRIVE from a program change them, and a ROM starts with
the drive and directory that the ROM before it left. The one exception is
an NFC card on an :doc:`pico`: the ROM it names starts in the folder that
holds the ROM.

A CHDIR into a folder on another drive also makes that drive current.
Each drive keeps the last folder used on it, so a later CHDRIVE back to a
drive returns to that folder. CHDRIVE takes the name of a mounted drive,
colon included, and the name of a drive that is not mounted fails with
ENODEV. On a machine with one drive, a CHDRIVE to it succeeds and changes
nothing. The Pocket has one fixed folder, so CHDIR fails there with
ENOSYS.

:ref:`GETCWD <os-getcwd>` returns an absolute path that starts with its
drive, such as ``MSC0:/games``, ``C:/Users/me`` or ``FS:/home/me``. A
drive is always in its long form, ``MSC0:`` and never ``0:``. Each
folder name in the path appears as it does in a listing, as described in
`Names`_. GETCWD fails with ENOMEM when the path is longer than 255
bytes.

A portable program keeps its saves out of the working directory, because
the working directory can be any folder: the one a shell was in when it
started the emulator, the one a launcher left, or on the Pocket the Assets
folder that also holds the core. Saves go to ``SAVE:`` instead.

.. _port-save:

Saves
-----

A path that starts with ``SAVE:`` names a save, a file in a folder set
aside for saves on each machine. This program keeps a high score in
``SAVE:hopper.hiscore``. It reads the score when it starts, and it writes
a new one when the player beats it.

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
so a save never keeps the end of a longer one.

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
       if (write(fd, &game, sizeof game) != sizeof game)
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

A game with save slots also clears them and shows which are in use. Only
an open works on a ``SAVE:`` path, so a save is cleared by emptying it with
O_TRUNC, and its size is read with ``lseek(fd, 0, SEEK_END)``. An empty
slot then loads as no save, the same as a slot that was never written.

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

A save is opened with :ref:`OPEN <os-open>` and O_RDONLY, O_WRONLY or
O_RDWR, plus any of O_CREAT, O_TRUNC, O_EXCL and O_APPEND. The program
can then read, write, seek within the file, call syncfs and close it.
Every other call on a ``SAVE:`` path, such as STAT, UNLINK or OPENDIR,
fails with ENODEV, or ENOSYS on the Pocket. The file behind a save is an
ordinary file, and on some machines another path to its folder can stat
or unlink it, but the folder differs by machine and only ``SAVE:`` works
on all of them.

A save name is 1 to 32 characters from ``A``–``Z``, ``a``–``z``,
``0``–``9``, ``.``, ``-`` and ``_``. It does not end in ``.``, and it is
not one of the Windows device names, ``CON``, ``PRN``, ``AUX``, ``NUL``,
``COM1`` to ``COM9`` or ``LPT1`` to ``LPT9``, alone or with an extension.
Any other name fails with EINVAL on every machine, so a name that works on
one machine works on all of them. The saves are in one flat folder, so a
name has no folders in it, but ``SAVE:/hopper.slot0`` and
``SAVE:hopper.slot0`` are the same save, so code that joins a folder and a
name with ``/`` works.

Many games can share one save folder, so a save name starts with a short
name for the game. The recommended form is that name, a dot and a suffix,
such as ``SAVE:hopper.hiscore``, ``SAVE:hopper.slot0`` or
``SAVE:hopper.X42``. Case in a save name follows the rule in
`Names`_: open a save with the exact case of its name, and do
not create two saves whose names differ only in case.

The folder for saves is fixed when a ROM starts, so a CHDIR or CHDRIVE by
the program does not move its saves. A missing folder is created the
first time a program creates a save, so a game that never saves leaves
nothing behind. The Pocket cannot create folders, so its save folder is
shipped with the core. The save folder on each machine is:

- On an :doc:`pico`, the working directory when the ROM starts.
- On Linux, the folder given with ``--save-dir``, else
  ``$XDG_DATA_HOME/rp6502/``, which is ``~/.local/share/rp6502/`` by
  default.
- On macOS, the folder given with ``--save-dir``, else
  ``~/Library/Application Support/io.github.picocomputer.rp6502-emu/``.
- On Windows, the folder given with ``--save-dir``, else
  ``Saved Games\rp6502\``.
- In a browser, ``/saves/``.
- In RetroArch, ``rp6502/`` in the RetroArch save folder, or the working
  directory when the ROM starts if RetroArch has no save folder.
- On the Pocket, ``/Saves/rp6502/common/``.

.. _port-durability:

Durability
----------

Written data is stored in two steps: close passes it on for storage, and
syncfs returns once it is stored. A program that must not lose a save
calls syncfs on it before close. What survives a failure differs by
machine:

- On an :doc:`pico`, close and syncfs write the data to the drive.
  The buffers aren't nearly large enough to survive the time it takes
  to reach for and remove a USB drive.
- On Linux, macOS and Windows, written data survives a crash of the
  emulator, and syncfs keeps it through a crash of the whole computer.
- In a browser, close queues a save to the browser's storage, and syncfs
  waits until the save is stored. Why a game runs in only one window at a
  time is covered in :ref:`Saves and browser storage
  <emu-browser-storage>`.
- In RetroArch, a save is as durable as on the system RetroArch runs on.
- On the Pocket, a successful syncfs does not mean the data is on the
  card, because the Pocket sends no reply once the data is written.
  But like the :doc:`pico`, buffers are too small to be of concern.

.. _port-installed-roms:

Installed ROMs
--------------

The null drive, ``:``, holds ROMs that come from outside the filesystem.
On an :doc:`pico`, the monitor's INSTALL command puts a ROM in flash,
where it stays. On a desktop, ``--install`` puts a ROM there for one run
of the emulator. The emulators also run a ROM from the null drive when no
program could name its path, as when the path is longer than 255 bytes or
has a character that the code page cannot hold or that FAT refuses. A
program runs an installed ROM with EXEC and the name ``:name``, and every
other call on a ``:`` path fails with ENODEV.

argv[0] is the absolute path of the ROM, with its drive, however the ROM
was started: ``MSC0:/games/hopper.rp6502``, ``C:/games/hopper.rp6502`` or
``FS:/home/me/hopper.rp6502``. A short drive name typed before an
absolute path, as in ``0:/games/hopper.rp6502``, stays short. A ROM from
the null drive has ``:name``.

Data Files
----------

Graphics, levels and other data that a program reads are most portable as
named assets inside the ROM, added with ``rp6502_asset()`` as shown in
:ref:`Adding Assets <sdk-assets>`. A program opens one as ``ROM:`` plus
its name on every machine, wherever the ROM is and whatever the working
directory is.

Files beside the ROM are less portable. A program can open them by
replacing the file name at the end of argv[0], but a ROM from the null
drive has no folder, and a browser page holds only the ROM file.


.. _port-compatibility:

Compatibility
=============

Every rule above holds on every machine, apart from the Pocket
exceptions listed in the next paragraph. The rows of the table below
differ, because the machines differ. The Desktop column is the emulator
on Linux, macOS and Windows. RetroArch runs on those systems too, and the
Desktop column holds for it, except that its working directory at start
is the working directory of RetroArch and it has no installed ROMs.

On the Pocket, files are opened by path, but there are no folder
operations and no listing. STAT, UNLINK, RENAME, MKDIR, CHDIR, CHMOD,
UTIME, GETLABEL, SETLABEL and GETFREE fail there with ENOSYS, and so do
OPENDIR, READDIR, CLOSEDIR, TELLDIR, SEEKDIR and REWINDDIR. An open fails
with EACCES for the root of the card, ``Assets/rp6502/common``,
``Saves/rp6502/common`` and the folders above them, and an open of any
other folder is sent to the Pocket as the open of a file. A seek past the
end that cannot extend a file fails with EIO, because the Pocket has no
error for a full card.

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20 20

   * -
     - Pico
     - Desktop
     - Browser
     - Pocket
   * - Drive names
     - ``MSC0:``–``MSC9:``, or ``0:``–``9:``
     - ``FS:``, or ``A:``–``Z:`` on Windows
     - ``FS:``
     - ``FS:``
   * - Working directory at start
     - ``MSC0:/``
     - the folder the emulator was started from
     - ``FS:/``
     - ``FS:/Assets/rp6502/common``
   * - Installed ROMs
     - INSTALL, kept in flash
     - ``--install``, for one run
     - none
     - none
   * - Volume label
     - the FAT label
     - EACCES
     - EACCES
     - ENOSYS
   * - GETFREE
     - the FAT volume
     - the host volume
     - the storage estimate of the browser
     - ENOSYS
   * - Case in names
     - ignored
     - matters on Linux, ignored on macOS and Windows
     - matters
     - ignored
   * - Names outside the code page, in a listing or GETCWD
     - the 8.3 name, which opens the file
     - character 127, and the name cannot be opened
     - character 127, and the name cannot be opened
     - not applicable
   * - Durability limit
     - unplugging a drive before close or syncfs loses data
     - a crash of the computer before syncfs loses data
     - close queues the save, syncfs waits for it
     - the Pocket sends no reply once data is written, so syncfs cannot
       wait for it
