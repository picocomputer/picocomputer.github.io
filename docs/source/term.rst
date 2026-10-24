==================================
TERM
==================================

Terminal


Introduction
============

A Picocomputer program reads and writes text through ``stdin``,
``stdout``, and ``stderr``, the standard streams of C. ``printf()``
prints to the console and ``fgets()`` reads a line from it, as in any C
program. The streams are not tied to one screen and one keyboard. On an
:doc:`pico`, a user can work with the same program from a VGA monitor
and a keyboard, from a USB serial terminal, and over telnet, all at
once. The :doc:`emu` can also connect the streams to the ``stdin``,
``stdout``, and ``stderr`` of the computer that runs it.

This page covers three closely related parts. The `console manifold
<Console Manifold_>`_ connects the streams to the terminals. The `line
editor <Read Line_>`_ lets the user edit a line before pressing Enter,
with no editing code in the program, and a program can keep running
while the user types. The `terminal <Terminal_>`_ of the :doc:`vga`
system draws the console, and its escape sequences let a program move
the cursor, color its text, and draw boxes.


.. _term-console-manifold:

Console Manifold
================

A **terminal** is a device that a user types into and reads from. The
**console** is the main terminal, connected to ``stdin``, ``stdout``,
``stderr``, ``CON:``, and ``TTY:``. On an :doc:`pico`, the **monitor**
also runs on the console, for configuration and for loading ROMs.

Several terminals can be attached to the console at once, and the
machine combines them into one console. This is the **console
manifold**. Input from every terminal goes to the console, and the
output of the console goes to every terminal.

Every machine has the VGA terminal with a keyboard. The other terminals
depend on the machine:

- **RP6502-PICO.** A terminal program on another computer connects to
  the USB port of the VGA module as a USB serial terminal. When the RIA
  is a Pi Pico 2 W, a telnet client connects over the network as a
  telnet terminal. :ref:`Console <pico-console>` on the :doc:`pico` page
  describes both.
- **RP6502-EMU.** The emulator connects the console to the ``stdin``,
  ``stdout``, and ``stderr`` of the computer that runs it. Its options
  choose how, and :ref:`In a Toolchain <emu-toolchain>` on the
  :doc:`emu` page describes them. When VS Code runs the emulator,
  ``stdout`` and ``stderr`` appear in the Debug Console of VS Code.
- **RP6502-FPGA** and **RP6502-WEB.** The VGA terminal with a keyboard
  is the only terminal.


Read Line
=========

A **cooked** read returns a complete line. The user has edited freely
with backspace, arrow keys, and optionally command completion and
history; the editor flushes the line when Enter is pressed. A **raw**
read returns bytes as they arrive, keystroke by keystroke, with no echo
and no editing. The line editor of the RIA implements cooked input.

A modern operating system layers canonical input and translated output
over something configurable like termios. A full termios is too heavy
for an 8-bit system, so the two modes worth having arrive as separate
device names instead.

Reading ``stdin`` is cooked and blocks until the user presses Enter.
``stdout`` and ``stderr`` block too, inserting a carriage return before
any newline that lacks one; all of the data is always sent, and a write
blocks until it has fully drained into the output FIFOs. That is what a
C programmer expects, and a poor fit for a multitasking 6502 program.
Two alternate file paths offer non-blocking variants of the same
channels:

* ``CON:`` — non-blocking cooked input. ``read()`` returns 0 while the
  user is still editing and returns the full newline-terminated line
  once the editor flushes. Writes may send less than you asked for.
* ``TTY:`` — non-blocking raw input, with no canonical input and no
  newline translation. ``read()`` returns whatever bytes are queued.
  This is what the :ref:`RIA TX and RX registers <ria-uart>` provide,
  packaged as stdio.

``CON:`` is locked to file descriptor 3 and ``TTY:`` to file descriptor
4, and neither can be closed. A second open returns the same file
descriptor as the first, and a close succeeds as a no-op.

.. _term-terminal-size:

Terminal Size
-------------

A program that fits its output to the console, such as MS-BASIC, needs
the width and the height of the console. At the start of each line that
the line editor reads, it asks the terminals for the size with a Cursor
Position Report (CPR) sequence. After the line editor reads a line, the
program gets the size from :ref:`RIA_ATTR_RLN_WIDTH and
RIA_ATTR_RLN_HEIGHT <api-ria-attributes>`. The monitor of an
:doc:`pico` fits its output to the same size.

The question goes to every terminal on the console manifold, so the size
is right only when one terminal answers. On an :doc:`pico`, the VGA
terminal stops answering while a USB serial or telnet terminal is
connected. When a USB serial terminal and a telnet terminal are both
connected and both answer, the line editor might get the wrong size. If
the word wrap or the paging of a program looks wrong, check which
terminals are connected.

A program that is built for a fixed size can set the size instead. Write
non-zero values to RIA_ATTR_RLN_WIDTH and RIA_ATTR_RLN_HEIGHT. With both
set, the line editor does not ask the terminals. Write 0 to go back to
detection. Both attributes return to 0 when the ROM stops.

.. _term-nonblocking-read-line:

Non-blocking Read Line
----------------------

Between the activating read and the line flush, the application
can inspect and modify the editor's state. That is what makes features
like history recall, tab completion, and multi-field form navigation
possible. The hooks are :ref:`RLN_LASTKEY <api-rln-lastkey>`,
:ref:`RLN_PEEK <api-rln-peek>`, and :ref:`RLN_POKE <api-rln-poke>`.

The basic pattern:

#. **Open the channel.** ``open("CON:", O_RDWR)`` returns a file descriptor.
#. **Set the input cap** (optional). Write ``RIA_ATTR_RLN_LENGTH``.
   Different prompts, or different fields in a form, can use
   different caps. The default is 254.
#. **Pin the terminal size** (optional). Write ``RIA_ATTR_RLN_WIDTH``
   and ``RIA_ATTR_RLN_HEIGHT`` when the layout is built for a fixed
   canvas. See `Terminal Size`_.
#. **Loop on ``read()``** until the line flushes.

   * The first call always returns 0 and activates the editor at the
     current cursor position and SGR state. Position the cursor *before*
     this read.
   * A non-zero return means the line is complete. Pull it whole with a
     buffer at least ``RIA_ATTR_RLN_LENGTH`` + 1 bytes long, or drain it
     in fragments until you see the newline.
   * On the first pass after activation, call ``ria_rln_poke()`` to
     pre-load any text you want to appear in the line. The poked bytes
     are echoed by the editor as if the user had typed them.
   * Optionally check for Ctrl-C via ``RIA_ATTR_SIGINT`` or the RIA SIGINT IRQ.
     To leave cooked input cleanly, poke ``\x03`` to print a visible
     ``^C``, or poke ``\r`` to flush silently. Then wait for
     ``read()`` to return the line.
   * ``ria_rln_lastkey()`` reports the last keystroke and whether the
     editor consumed it as an editing action. When ``action == 0`` the
     editor passed the key through. That is the application's chance
     to handle Tab, function keys, arrow keys for history or form
     navigation, and any other keys it claims. The line editor keeps no
     history while a program reads a line, so Up and Down always have
     ``action == 0``. Call ``ria_rln_peek()``
     to get the current input text and cursor position. Respond by
     poking literal characters or ANSI sequences (``CUF``, ``CUB``,
     ``ICH``, ``DCH``) back into the editor.

#. **Read ``RIA_ATTR_RLN_WIDTH`` and ``RIA_ATTR_RLN_HEIGHT``** to obtain
   the dynamic size after the read line completes.

A poke edits as typing does, except that a control byte ends the input,
as :ref:`RLN_POKE <api-rln-poke>` describes. Poke ``\r`` to pull the
buffer out without the user pressing Enter, for example when Tab should
jump to the next field of a form. The editor
flushes through ``read()`` like any other line, and the application can
move on, entering the next field with a fresh ``read()`` and
``ria_rln_poke()`` to restore its prior contents.


Terminal
========

The :doc:`vga` system includes a color terminal that draws the console.
:ref:`Mode 0 <vga-mode-0>` on the :doc:`vga` page describes where the
terminal goes on the canvas, its 80 or 40 columns, and how a picture on
a plane behind it shows through.

Like the Linux console, the terminal identifies itself as a VT102 and
implements most of the escape sequences of the Linux console, with
additions from ECMA-48, xterm, later DEC terminals, kitty, and SyncTERM.
`To Do`_ lists where it falls short, and the tables below list the
sequences.

Text is in the 8-bit code page of :ref:`RIA_ATTR_CODE_PAGE
<api-ria-attributes>`, one byte for each character. The terminal does
not decode UTF-8.

Some older terminals could not keep up at full speed, so a program sent
padding or waited after a slow operation such as a screen clear, or
paused when the terminal sent XOFF. This terminal keeps up with the
console at full speed, even through a screen clear, so a program needs
no flow control, padding, or delays.

To Do
-----

These sequences of the VT102 and the Linux console are missing or work
differently. Each one is on the to-do list.

VT102:

* FF (``0x0C``) clears the screen and homes the cursor. A VT102 moves
  the cursor down a line, as LF does, and so do the Linux console and
  xterm.
* Insert mode (``CSI 4 h``) and newline mode (``CSI 20 h``), the
  ECMA-48 modes that ``CSI h`` and ``CSI l`` set without a ``?``, are
  missing. A program that expects a VT102 and inserts text with insert
  mode overwrites text instead. ICH (``CSI n @``) inserts characters.
* VT (``0x0B``), which moves the cursor down a line, as LF does.
* DECID (``ESC Z``), which asks for the same reply as Primary DA.
* Double-height and double-width lines (``ESC # 3`` to ``ESC # 6``), and
  DECALN (``ESC # 8``), which fills the screen with E.
* Cursor-key mode (``?1``) and the keypad modes (``ESC =`` and
  ``ESC >``), which change what the arrow keys and the keypad send.
* Reverse video for the whole screen (``?5``).
* Keyboard autorepeat (``?8``) and the keyboard LEDs (``CSI q``).

Linux console:

* The null and user mappings (``ESC ( U`` and ``ESC ( K``).
* The palette sequences (``OSC P`` and ``OSC R``).
* Mouse reporting (``?9`` and ``?1000``).
* HPR (``CSI a``) and VPR (``CSI e``), which move the cursor right and
  down relative to its position.
* ED 3 (``CSI 3 J``), which erases the scrollback.
* SGR 10-12, which select the font mapping.
* The private sequences of Linux (``CSI ]``).

kitty:

* SGR 59, which resets the underline color that SGR 58 sets.


C0 Control Codes
----------------

NUL (``0x00``) and BEL (``0x07``) are silently accepted no-ops.

.. list-table::
   :widths: 5 5 5 15 70
   :header-rows: 1

   * - \^
     - C0
     - Abbr
     - Name
     - Effect
   * - ^H
     - 0x08
     - BS
     - Backspace
     - Move cursor left one cell.
   * - ^I
     - 0x09
     - HT
     - Tab
     - Move cursor right to next tab stop (default every 8 columns);
       clamps at right margin.
   * - ^J
     - 0x0A
     - LF
     - Line Feed
     - Move down one row; scroll if at bottom margin.
   * - ^L
     - 0x0C
     - FF
     - Form Feed
     - Clear screen and home cursor.
   * - ^M
     - 0x0D
     - CR
     - Carriage Return
     - Move cursor to column 1.
   * - ^N
     - 0x0E
     - SO
     - Shift Out
     - Switch to the alternate charset slot (G1). See
       `Charset Designation`_.
   * - ^O
     - 0x0F
     - SI
     - Shift In
     - Switch to the primary charset slot (G0). See
       `Charset Designation`_.
   * - ^X
     - 0x18
     - CAN
     - Cancel
     - Abort an in-progress escape sequence (silent).
   * - ^Z
     - 0x1A
     - SUB
     - Substitute
     - Abort an in-progress escape sequence and print ``?`` in its
       place.
   * - ^[
     - 0x1B
     - ESC
     - Escape
     - Start an escape sequence.

Fe Escape Sequences
-------------------

.. list-table::
   :widths: 15 8 25 52
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - ESC c
     - RIS
     - Reset to Initial State
     - Hard reset: SGR, cursor, alt screen, tab stops, colors.
   * - ESC D
     - IND
     - Index
     - Move cursor down one row; scroll at bottom margin.
   * - ESC E
     - NEL
     - Next Line
     - CR + IND.
   * - ESC M
     - RI
     - Reverse Index
     - Move cursor up one row; scroll at top margin.
   * - ESC H
     - HTS
     - Horizontal Tab Set
     - Set a tab stop at the current column.
   * - ESC 7
     - DECSC
     - Save Cursor
     - Save cursor position, SGR, charset state, and origin mode.
   * - ESC 8
     - DECRC
     - Restore Cursor
     - Restore the state saved by DECSC; homes if no save.
   * - ESC \[
     - CSI
     - Control Sequence Inducer
     - Begins a CSI sequence (see CSI subsections below).
   * - ESC ]
     - OSC
     - Operating System Command
     - Begins an OSC sequence. See `OSC Sequences`_.
   * - ESC (
     - —
     - Load primary charset
     - Load a font into the G0 slot. See `Charset Designation`_.
   * - ESC )
     - —
     - Load alternate charset
     - Load a font into the G1 slot. See `Charset Designation`_.
   * - ESC # c
     - —
     - DEC line attribute
     - Recognized; one byte swallowed (DECALN not implemented).
   * - ESC N
     - SS2
     - Single Shift Two
     - Recognized; one byte swallowed. No SS2 commands implemented.
   * - ESC O
     - SS3
     - Single Shift Three
     - Recognized; one byte swallowed. No SS3 commands implemented.

Charset Designation
-------------------

The terminal keeps two character-set slots, named **G0** and
**G1**. You load a font into each slot independently, then switch
which slot is active at any time. This lets you mix regular text
with the DEC line-drawing characters (corners, tees, and lines)
without an escape sequence per character. Load the line-drawing
font into G1 once, then toggle between G0 and G1 as you go.

**Load a font into a slot.** The byte after the sequence selects
which font to load:

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Sequence
     - Font loaded
   * - ESC ( B
     - US ASCII (default) into G0.
   * - ESC ( 0
     - DEC Special Graphics into G0.
   * - ESC ) B
     - US ASCII (default) into G1.
   * - ESC ) 0
     - DEC Special Graphics into G1.

Any other byte after ``ESC (`` or ``ESC )`` is silently consumed.

**Switch the active slot.** Send one byte:

.. list-table::
   :widths: 17 83
   :header-rows: 1

   * - Code
     - Effect
   * - SI (^O)
     - Make G0 the active charset.
   * - SO (^N)
     - Make G1 the active charset.

Both slots are US ASCII at startup, so until you load something
into G1 you can ignore this entire feature.

CSI — Cursor Movement
---------------------

CSI sequences default missing numbers to 0. Some functions,
especially cursor movement, treat 0 as 1 to remain useful without
parameters.

.. list-table::
   :widths: 19 8 25 48
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - CSI n A
     - CUU
     - Cursor Up
     - Move n rows up.
   * - CSI n B
     - CUD
     - Cursor Down
     - Move n rows down.
   * - CSI n C
     - CUF
     - Cursor Forward
     - Move n columns right.
   * - CSI n D
     - CUB
     - Cursor Back
     - Move n columns left.
   * - CSI n E
     - CNL
     - Cursor Next Line
     - Move n rows down, to column 1.
   * - CSI n F
     - CPL
     - Cursor Previous Line
     - Move n rows up, to column 1.
   * - CSI n G
     - CHA
     - Cursor Horizontal Absolute
     - Move to column n (1-indexed).
   * - CSI n \`
     - HPA
     - Horizontal Position Absolute
     - Alias of CHA.
   * - CSI n d
     - VPA
     - Vertical Position Absolute
     - Move to row n (1-indexed); column unchanged.
   * - CSI n ; m H
     - CUP
     - Cursor Position
     - Move to row n, column m (1-indexed).
   * - CSI n ; m f
     - HVP
     - Horizontal Vertical Position
     - Alias of CUP.
   * - CSI s
     - SCP
     - Save Cursor Position
     - SCO-style: save cursor x / y and origin mode.
   * - CSI u
     - RCP
     - Restore Cursor Position
     - Restore the state saved by SCP.

CSI — Editing
-------------

.. list-table::
   :widths: 15 8 25 52
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - CSI n @
     - ICH
     - Insert Character
     - Insert n blank cells; line shifts right.
   * - CSI n P
     - DCH
     - Delete Character
     - Delete n cells; line shifts left.
   * - CSI n X
     - ECH
     - Erase Character
     - Erase n cells in place; cursor unchanged.
   * - CSI n L
     - IL
     - Insert Line
     - Insert n blank lines at cursor row.
   * - CSI n M
     - DL
     - Delete Line
     - Delete n lines at cursor row.

CSI — Erase
-----------

.. list-table::
   :widths: 15 5 20 60
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - CSI n J
     - ED
     - Erase in Display
     - - 0: From cursor to end of screen.
       - 1: From beginning of screen to cursor.
       - 2: Entire screen.
   * - CSI n K
     - EL
     - Erase in Line
     - - 0: From cursor to end of line.
       - 1: From beginning of line to cursor.
       - 2: Entire line.

CSI — Scrolling and Margins
---------------------------

.. list-table::
   :widths: 17 10 25 48
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - CSI n S
     - SU
     - Scroll Up
     - Scroll viewport up n lines.
   * - CSI n T
     - SD
     - Scroll Down
     - Scroll viewport down n lines.
   * - CSI t ; b r
     - DECSTBM
     - Set Top / Bottom Margins
     - Define vertical scroll region (1-indexed); homes the cursor.

CSI — Tabs
----------

Tab stops are also set with ``ESC H`` (HTS) and reset by RIS.

.. list-table::
   :widths: 14 8 20 58
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - CSI n I
     - CHT
     - Cursor Horizontal Tab
     - Advance n tab stops.
   * - CSI n Z
     - CBT
     - Cursor Backward Tab
     - Retreat n tab stops.
   * - CSI n g
     - TBC
     - Tab Clear
     - - 0: Clear stop at current column.
       - 3: Clear all stops.

CSI — Status and Reports
------------------------

.. list-table::
   :widths: 15 8 25 52
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - CSI n c
     - DA
     - Primary Device Attributes
     - Responds with ``ESC[?6c`` (VT102).
   * - CSI > n c
     - —
     - Secondary DA
     - Recognized; no reply.
   * - CSI = n c
     - —
     - Tertiary DA
     - Recognized; no reply.
   * - CSI 5 n
     - DSR
     - Device Status Report
     - Responds with ``ESC[0n`` (terminal OK).
   * - CSI 6 n
     - CPR
     - Cursor Position Report
     - Responds with ``ESC[n;mR``, where n is the row and m is the
       column (1-indexed).
   * - CSI n t
     - —
     - Window manipulation
     - Silently absorbed (no window manager).

CSI — Reset and Cursor Style
----------------------------

.. list-table::
   :widths: 21 9 22 48
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - CSI ! p
     - DECSTR
     - Soft Terminal Reset
     - Reset SGR, cursor, origin mode, autowrap, charset, and
       saved cursor. Preserves OSC colors, tab stops, and screen
       contents.
   * - CSI Ps SP q
     - DECSCUSR
     - Set Cursor Style
     - 0 = host default, 1 / 2 = block, 3 / 4 = underline,
       5 / 6 = bar.

DEC Private Modes
-----------------

Set with ``CSI ?n h``, reset with ``CSI ?n l``. Multiple modes
may be combined in one sequence (semicolon-separated parameters).

Mode 33 is for ANSI art. In the text mode of an IBM PC, one bit of the
attribute byte of each character makes it blink. Some ANSI art was drawn
with blinking turned off in the display adapter, so that bit brightened
the background instead and gave 16 background colors. This is called
iCE color. Mode 33, from SyncTERM, makes SGR 5 and 6 brighten the
background in the same way.

.. list-table::
   :widths: 6 10 22 62
   :header-rows: 1

   * - n
     - Abbr
     - Name
     - Effect
   * - 6
     - DECOM
     - Origin Mode
     - Cursor addressing relative to scroll region; homes the
       cursor on change.
   * - 7
     - DECAWM
     - Autowrap
     - Wrap at right margin.
   * - 12
     - AT&T 610
     - Cursor visibility
     - Set: show cursor. Reset: hide cursor.
   * - 25
     - DECTCEM
     - Cursor visibility
     - Set: show cursor. Reset: hide cursor.
   * - 33
     - —
     - iCE colors
     - Set: SGR 5 / 6 brightens background (iCE colors).
       Reset: SGR 5 / 6 means blink (default).
   * - 47
     - —
     - Legacy alt screen
     - Swap to / from the alt screen buffer.
   * - 1047
     - —
     - Alt screen
     - Swap; clears the alt buffer on exit.
   * - 1049
     - —
     - Alt screen + save
     - Modern app default: saves cursor on entry, swaps, clears on
       entry, restores cursor on exit.

SGR Parameters
--------------

Send multiple parameters separated by ``;``. ``CSI m`` with no
parameters resets all attributes.

.. list-table::
   :widths: 8 22 70
   :header-rows: 1

   * - n
     - Name
     - Effect
   * - 0
     - Reset
     - White (7) foreground, black (0) background, all attributes
       off.
   * - 1
     - Bold
     - Brighter foreground (colors 0-7 → 8-15).
   * - 2
     - Faint
     - Halve foreground channel brightness.
   * - 3
     - Italic
     - Only ASCII 32-127.
   * - 4
     - Underline
     - —
   * - 5
     - Blink (slow)
     - Blinks foreground. With iCE colors mode (``?33h``) set,
       brightens the background instead.
   * - 6
     - Blink (rapid)
     - Same as 5 at double the blink rate.
   * - 7
     - Reverse video
     - Swap foreground and background.
   * - 8
     - Conceal
     - Foreground = background.
   * - 9
     - Strikethrough
     - —
   * - 21
     - Double underline
     - Per Linux console.
   * - 22
     - Normal intensity
     - Cancels both bold (1) and faint (2).
   * - 23
     - Italic off
     - —
   * - 24
     - Underline off
     - Clears both single and double underline.
   * - 25
     - Blink off
     - Clears the blink attribute.
   * - 27
     - Reverse off
     - —
   * - 28
     - Conceal off
     - —
   * - 29
     - Strikethrough off
     - —
   * - 30-37
     - Set foreground color
     - Colors 0-7.
   * - 38
     - Set foreground color
     - - ``;5;n`` — 256-color index n (0-255)
       - ``;2;r;g;b`` — 24-bit RGB color
       - ``;2::r:g:b`` — 24-bit RGB color
       - ``;1`` — transparent
   * - 39
     - Default foreground
     - Color 7 (white).
   * - 40-47
     - Set background color
     - Colors 0-7.
   * - 48
     - Set background color
     - - ``;5;n`` — 256-color index n (0-255)
       - ``;2;r;g;b`` — 24-bit RGB color
       - ``;2::r:g:b`` — 24-bit RGB color
       - ``:2:r:g:b`` — 24-bit RGB color
       - ``;1`` — transparent
   * - 49
     - Default background
     - Color 0 (transparent black).
   * - 53
     - Overline
     - —
   * - 55
     - Overline off
     - —
   * - 58
     - Underline color
     - Same format as 38.
   * - 90-97
     - Bright foreground
     - Colors 8-15.
   * - 100-107
     - Bright background
     - Colors 8-15.

OSC Sequences
-------------

Operating System Command sequences set dynamic terminal colors.
The color argument must be ``#rrggbb``; other xterm color formats
(X11 names, ``rgb:``) are not accepted. Each sequence is
terminated by BEL (``0x07``) or ST (``ESC \``).

.. list-table::
   :widths: 33 67
   :header-rows: 1

   * - Code
     - Effect
   * - OSC 10 ; #rrggbb ST
     - Set default foreground color.
   * - OSC 11 ; #rrggbb ST
     - Set default background color.
   * - OSC 12 ; #rrggbb ST
     - Set cursor color.
   * - OSC 110 ST
     - Reset default foreground color.
   * - OSC 111 ST
     - Reset default background color.
   * - OSC 112 ST
     - Reset cursor color.
