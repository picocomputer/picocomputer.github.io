====================
First Steps with the Picocomputer
====================

Having build or acquired your :doc:`hardware` this page gives a few suggestions
for some initial things for beginners to try.

First Power On
============

Once the hardware is ready, having completed the tests and checks described in
two build videos for the `DIY PCB <https://youtu.be/bwgLXEQdq20>`_ or `the "no soldering" build
<https://youtu.be/4CjouKoCMUw>`_, it should be
possible to plug in the two Picos and power up the board.

The simplest configuration for testing the board is to power it via the
micro USB socket of the RP6502-VGA, with it plugged into a PC.

A terminal programme on the PC can be used to interact with the Picocomputer via
the USB COM/tty serial port.
- For Windows, use something like `PuTTY <https://www.chiark.greenend.org.uk/~sgtatham/putty/>`_.
- For Linux, use something like minicom.

The default baud rate of 115200 should be fine.  Note: On Windows, to find which "COM"
port to use, open Device Manager and view "Ports (COM & LPT)" the board, when powered on,
should appear as "USB Serial Device (COMx)".

If there is nothing shown on the display, press the Picocomputer "REBOOT" button
and you should see something similar to the following::

  Picocomputer 6502
  RIA Version 0.16 W
  VGA Version 0.16
  
  ]

The "]" is the prompt from the RP6502-RIA monitor programme.  At this point, the 6502 CPU
itself is still not running code, this is all interaction with the RP6502-RIA only, athough
if a VGA monitor is plugged into to the board, the same display should be shown there too.

The built-in monitor programme has an extensive help system::

  ]help
  Commands:
  HELP (command|rom)  - This help or expanded help for command or rom.
  HELP ABOUT|SYSTEM   - About includes credits. System for general usage.
  STATUS              - Show status of system and connected devices.
  SET (attr) (value)  - Change or show settings.
  LS (dir|drive)      - List contents of directory.
  CD (dir)            - Change or show current directory.
  (USB)0:             - USB0:-USB7: Change current USB drive.
  LOAD file           - Load ROM file. Start if contains reset vector.
  INFO file           - Show help text, if any, contained in ROM file.
  INSTALL file        - Install ROM file on RIA.
  rom                 - Load and start an installed ROM.
  REMOVE rom          - Remove ROM from RIA.
  REBOOT              - Reboot the RIA. Will load selected boot ROM.
  RESET               - Start 6502 at current reset vector ($FFFC).
  MKDIR dir           - Make a new directory.
  UNLINK file|dir     - Delete a file or empty directory.
  UPLOAD file         - Write file. Binary chunks follow.
  BINARY addr len crc - Write memory. Binary data follows.
  0000 (00 00 ...)    - Read or write memory.
  No installed ROMs.
  ]

Try the following commands::

  ]help system
  ]help set

Now lets actually get the 6502 CPU itself to run some code.

Hello World!
============

If you've watched the videos detailing the design and development of the
Picocomputer, you will have seen the assembler "Hello World" demo.
This recreates that demo for the released system.

First it should be noted that whilst the system talks of ROM, there is no
actual addressable ROM in the hardware - it is all RAM only.  There is almost 64K
of usuable RAM in the system - the very top of the address space is reserved
above FF00 for hardware registers, including the :doc:`ria`.

On power up the RIA's monitor programme can load ROM files into RAM and have
them run.

But it can also modify the memory directly using the "binary" and "direct address"
commands of the monitor so these can be used to place data representing code
directly into the memory.

The video demo used the online 6502 assembler from masswerk found here: `<https://www.masswerk.at/6502/assembler.html>`_.

That can be used again, but there are a couple of differences in the released firmware
compared to the video demo - the address of the serial port has changed, it is now FFE1,
and there is no longer an instruction to shutdown the 6502.

The online assembler can be used to assemble the following code::

  * = $0200
  ldx #0
  loop:
  lda text,x
  sta $ffe1
  inx
  cmp #0
  bne loop
  stop:
  jmp stop

  text:
  .ASCII "Hello, World!"
  .BYTE $0D $0A $00

This does the same as the video demo - it sends each character of the provided string to
the serial port, but then it leaves the processor stuck in an infinite loop.

The assembler can be used to generate the required data bytes - it generates the required
data which can be pasted (as hex) directly into the memory of the 6502 by using the monitor's
direct 'addr data...' commands as follows::

  ]0200 A2 00 BD 10 02 8D E1 FF E8 C9 00 D0 F5 4C 0D 02
  ]0210 48 65 6C 6C 6F 2C 20 57 6F 72 6C 64 21 0D 0A 00

We can check this is correctly stored by entering an address with no data::

  ]0200
  0200  A2 00 BD 10 02 8D E1 FF  E8 C9 00 D0 F5 4C 0D 02  |.............L..|
  ]0210
  0210  48 65 6C 6C 6F 2C 20 57  6F 72 6C 64 21 0D 0A 00  |Hello, World!...|
  ]

In order to allow this to run, we have to set the 6502's reset vector to
the $0200 address (note: we use the "byte swapped" form 00 02) and then
start the CPU using the "reset"::

  ]fffc 00 02
  ]reset
  Hello, World!

At this point the terminal will be stuck, but sending a "break" over the serial
port will return control to the monitor.  Within PuTTY this can be done using
"Special Command" -> "Break" from the terminal menu.

We've now successfully written some data to the RAM and run it on the 6502 itself!

Loading a First ROM
============

The real purpose of the RIA's monitor programme is to store, load, and manage ROMs.
There is a list of community provided ROMs on `the community wiki <https://github.com/picocomputer/community/wiki>`_

For this demonstration, we're going to install and run BASIC.

ROMs can be installed onto the Pico from a USB memory drive.  To do this requires
a micro-USB to USB-A adaptor cable which should be plugged into the micro USB
port of the RP6502-RIA Pico.

- Download the latest EHBASIC ROM release from here: `<https://github.com/picocomputer/ehbasic/releases>`_
- Copy the "basic.rp6502" file to the USB memory drive.
- Plug the USB memory drive into the RP6502-RIA.

The file can be loaded and run directly from the USB memory drive, but
we're going to install it onto the Pico so it will always be available::

  ]ls
   11926 basic.rp6502
  ]install basic.rp6502

Now when the "help" command is run it should show::

  ]help
  Commands:
  (...usual list of commands...)
  1 installed ROM:
  BASIC.
  ]

To run a ROM, simply type in its name::

  ]basic

  52735 Bytes free

  Enhanced BASIC v20240114

  Ready
  10 print "Hello"
  20 goto 10
  list

  10 PRINT "Hello"
  20 GOTO 10

  Ready

Again, to return control to the RIA monitor, either reboot or send a serial break.

Finally, it is possible to get the RIA to run a specific ROM automatically on power up::

  ]set boot basic
  BOOT: BASIC
  ]

Now on power up or reboot it will boot straight into the ROM.  To remove it again requires
"break"ing back out into the monitor and using::

  ]set boot -
  BOOT: (none)
  ]

Next Steps
============

Some places to explore next:

- Try some of the other ROMs from the `community wiki <https://github.com/picocomputer/community/wiki>`_.
- Browse the `discussion area <https://github.com/orgs/picocomputer/discussions>`_ and see what others have been doing.
- Read the `detailed data sheets <https://picocomputer.github.io/#datasheets>`_ for the RIA, RIA-W, VGA and operating system, as linked from the main documentation index page.

