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
the width and the height of the console. After the line editor reads a
line, the program gets the size from :ref:`RIA_ATTR_RLN_WIDTH and
RIA_ATTR_RLN_HEIGHT <api-ria-attributes>`. The monitor of an
:doc:`pico` fits its output to the same size.

One terminal on the console manifold is **in charge**. The line editor
lays out each line for that terminal, takes the size from it, and sends
questions to it alone. It is the first of these that is connected:

#. **A telnet terminal that reports its size.** Most telnet clients,
   such as the telnet of Linux, PuTTY and the telnet of Windows, report
   the size of their window with NAWS. The size comes from NAWS. At the
   start of each line, the line editor asks for the column of the cursor
   with a Cursor Position Report (CPR) sequence. Until the terminal
   first answers the Secondary Device Attributes (DA2) query, the line
   editor also asks that, to learn whether the terminal can change the
   shape of the cursor.
#. **The VGA terminal.** On an :doc:`pico`, the VGA terminal is in
   charge while the VGA module is connected. On the :doc:`emu`, the
   terminal in the window is in charge. On the :doc:`fpga` and the
   :doc:`web`, the VGA terminal is the only terminal. The size comes
   from the console canvas, and the line editor asks the VGA terminal
   for the column of the cursor. The question goes to the VGA terminal
   only, never to the USB port of the VGA module.
#. **A terminal on the UART.** On an :doc:`pico` with no VGA module,
   the UART of the RIA goes to one terminal. On the :doc:`emu` with
   ``--headless``, the terminal the emulator runs in is in charge when
   both ``stdin`` and ``stdout`` are on it. At the start of each line,
   the line editor asks for the column of the cursor, for the type of
   the terminal with DA2, and for the size, by asking for the position
   of the bottom right corner.

Otherwise no terminal is in charge. This is the :doc:`emu` with
``--headless`` and ``stdin`` or ``stdout`` on a pipe or a file. The
line editor asks nothing and does not wrap the line, and the size is
80 columns by 24 rows.

When terminals of different sizes are connected, the line editor lays
out the line for the terminal in charge, and the line can look wrong on
the others. If the word wrap or the paging of a program looks wrong,
check which terminal is in charge.

The line editor shows its mode with the shape of the cursor, a bar to
insert and a block to overwrite. Only a terminal that can change the
shape gets it. The VGA terminal always can. A telnet terminal or a
terminal on the UART can once it answers DA2.

A program that is built for a fixed size can set the size instead. Write
non-zero values to RIA_ATTR_RLN_WIDTH and RIA_ATTR_RLN_HEIGHT. With both
set, the line editor does not ask for the size. It still asks for the
column of the cursor, to place the line. Write 0 to go back to
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
     ``action == 0``. The Escape key arrives once 100 ms pass with no
     other byte from its terminal, because ESC also starts the sequences
     that other keys send. Call ``ria_rln_peek()``
     to get the current input text and cursor position. Respond by
     poking literal characters or ANSI sequences (``CUF``, ``CUB``,
     ``ICH``, ``DCH``) back into the editor.

#. **Read ``RIA_ATTR_RLN_WIDTH`` and ``RIA_ATTR_RLN_HEIGHT``** to obtain
   the dynamic size after the read line completes.

A poke edits as typing does, with two differences. A control byte ends
the input, as :ref:`RLN_POKE <api-rln-poke>` describes. ICH, DCH, and
ECH edit the line only when poked; typed, they are function keys, such
as Shift-F1, and do nothing. Poke ``\r`` to pull the
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

The terminal is a VT102 with most of what xterm and the Linux console
add, such as 256 colors and 24-bit color, the alternate screen, and the
palette sequences. It identifies itself as a VT102. The tables below
list every sequence that it acts on, and `To Do`_ lists features that
might be added.

Text is in the 8-bit code page of :ref:`RIA_ATTR_CODE_PAGE
<api-ria-attributes>`, one byte for each character. The terminal does
not decode UTF-8 and has no C1 controls: bytes 0x80 to 0xFF are always
characters of the code page.

The terminal also keeps a few features from other terminals:

- iCE colors from SyncTERM (mode 33), for ANSI art.
- Fast blink (SGR 6).
- Overline (SGR 53 and 55).
- Underline color (SGR 58 and 59), and the underline styles of kitty
  (SGR 4:n).
- A transparent color (SGR 38;1).
- A faster cursor blink while a wrap is pending.

The terminal parses escape sequences as xterm does. It ignores a
sequence that it does not know, whole, and ignores DCS, APC, PM, and SOS
strings up to the ST that ends them. Inside a sequence, CAN and SUB
cancel the sequence, and ESC starts a new one. BS, HT, LF, VT, FF, CR,
SO, SI, and BEL act without ending the sequence, NUL and DEL are
ignored, and any other control or a byte from 0x80 to 0xFF ends it.

Some older terminals could not keep up at full speed, so a program sent
padding or waited after a slow operation such as a screen clear, or
paused when the terminal sent XOFF. This terminal keeps up with the
console at full speed, even through a screen clear, so a program needs
no flow control, padding, or delays.

C0 Control Codes
----------------

.. list-table::
   :widths: 9 9 5 15 62
   :header-rows: 1

   * - \^
     - C0
     - Abbr
     - Name
     - Effect
   * - ^@
     - 0x00
     - NUL
     - Null
     - Ignored.
   * - ^A-^F
     - 0x01-0x06
     - —
     - —
     - Drawn. ENQ (0x05) sends no answerback.
   * - ^G
     - 0x07
     - BEL
     - Bell
     - Ignored.
   * - ^H
     - 0x08
     - BS
     - Backspace
     - Move the cursor left one column, stopping at column 1.
   * - ^I
     - 0x09
     - HT
     - Tab
     - Move the cursor right to the next tab stop, or to the last
       column when there is none.
   * - ^J
     - 0x0A
     - LF
     - Line Feed
     - Move the cursor down one row, and scroll the region at the
       bottom margin. With LNM set, also move to column 1.
   * - ^K
     - 0x0B
     - VT
     - Vertical Tab
     - Same as LF.
   * - ^L
     - 0x0C
     - FF
     - Form Feed
     - Same as LF. It does not clear the screen.
   * - ^M
     - 0x0D
     - CR
     - Carriage Return
     - Move the cursor to column 1.
   * - ^N
     - 0x0E
     - SO
     - Shift Out
     - Make G1 the active charset slot. See `Charset Designation`_.
   * - ^O
     - 0x0F
     - SI
     - Shift In
     - Make G0 the active charset slot. See `Charset Designation`_.
   * - ^P-^W
     - 0x10-0x17
     - —
     - —
     - Drawn.
   * - ^X
     - 0x18
     - CAN
     - Cancel
     - Cancel an escape sequence. Ignored outside one.
   * - ^Y
     - 0x19
     - EM
     - End of Medium
     - Drawn.
   * - ^Z
     - 0x1A
     - SUB
     - Substitute
     - Cancel an escape sequence. Ignored outside one.
   * - ^[
     - 0x1B
     - ESC
     - Escape
     - Start an escape sequence.
   * - ``^\``-``^_``
     - 0x1C-0x1F
     - —
     - —
     - Drawn.
   * - —
     - 0x7F
     - DEL
     - Delete
     - Ignored.

The controls marked "Drawn" are the ones that the Linux console does
not act on. As on Linux, the terminal draws them as the characters of
the code page at those codes.

SGR 11 and CRM (``CSI 3 h``) draw every control except NUL, BS, LF, FF,
CR, SO, SI, and ESC, and draw DEL too, so HT, VT, BEL, CAN, and SUB show
as characters instead of acting. SGR 10 and ``CSI 3 l`` turn this off.
It applies only outside escape sequences, so a control inside a
sequence still acts. SGR 0 leaves it on, and RIS turns it off.

Fe Escape Sequences
-------------------

.. list-table::
   :widths: 20 12 22 46
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - ESC c
     - RIS
     - Reset to Initial State
     - Reset the terminal. See `Resets`_.
   * - ESC D
     - IND
     - Index
     - Move the cursor down one row, and scroll the region at the
       bottom margin.
   * - ESC E
     - NEL
     - Next Line
     - CR and IND.
   * - ESC H
     - HTS
     - Horizontal Tab Set
     - Set a tab stop at the cursor's column.
   * - ESC M
     - RI
     - Reverse Index
     - Move the cursor up one row, and scroll the region down at the
       top margin.
   * - ESC 7
     - DECSC
     - Save Cursor
     - Save the cursor's position, a pending wrap, SGR, the charset
       slots and which one is active, and origin mode. Autowrap is not
       saved. The primary and alternate screens have separate saves.
       ``CSI s`` is the same.
   * - ESC 8
     - DECRC
     - Restore Cursor
     - Restore what DECSC saved. With nothing saved, move the cursor
       home with SGR 0, US ASCII in G0 and G1, G0 active, and origin
       mode off. ``CSI u`` is the same.
   * - ESC Z
     - DECID
     - Identify Terminal
     - Reply as Primary DA does, ``ESC [ ? 6 c``.
   * - ESC [
     - CSI
     - Control Sequence Introducer
     - Start a control sequence.
   * - ESC ]
     - OSC
     - Operating System Command
     - Start an OSC sequence. See `OSC Sequences`_.
   * - ESC P, ESC X, ESC ^, ``ESC _``
     - DCS, SOS, PM, APC
     - Strings
     - Start a string, which is ignored up to ST.
   * - ``ESC \``
     - ST
     - String Terminator
     - End an OSC sequence or a string.
   * - ESC (, ESC )
     - —
     - Designate G0, G1
     - Load a charset into G0 or G1. See `Charset Designation`_.
   * - ESC N, ESC O
     - SS2, SS3
     - Single Shift Two, Three
     - Ignored. The next byte prints as itself.
   * - ESC # 3 to ESC # 6
     - DECDHL, DECSWL, DECDWL
     - Line size
     - Ignored. Every line is single size. See `To Do`_.
   * - ESC # 8
     - DECALN
     - Screen Alignment
     - Ignored. The screen is not filled with E. See `To Do`_.
   * - ESC =, ESC >
     - DECKPAM, DECKPNM
     - Keypad modes
     - Ignored. See `To Do`_.
   * - ESC <
     - —
     - ANSI mode
     - Ignored in ANSI mode. Leaves `VT52 Mode`_.
   * - ESC %, ESC SP, ``ESC *``, ESC +
     - —
     - Other
     - Ignored, with their final byte: the UTF-8 selection, the 7-bit and
       8-bit control selection, and the G2 and G3 charsets.

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
   :widths: 22 78
   :header-rows: 1

   * - Sequence
     - Font loaded
   * - ESC ( B
     - US ASCII (default) into G0.
   * - ESC ( A
     - UK into G0: US ASCII with the pound sign (£) in place of ``#``.
   * - ESC ( 0
     - DEC Special Graphics into G0.
   * - ESC ( U, ESC ( K
     - US ASCII into G0. These are the null and the user mappings of
       the Linux console.
   * - ESC ) B
     - US ASCII (default) into G1.
   * - ESC ) A
     - UK into G1.
   * - ESC ) 0
     - DEC Special Graphics into G1.
   * - ESC ) U, ESC ) K
     - US ASCII into G1.

DEC Special Graphics replaces the characters from 0x5F to 0x7E with
line-drawing characters and symbols. It and the pound sign of UK work
in every code page.

Any other byte after ``ESC (`` or ``ESC )`` leaves the slot as it was.
The national charsets of the VT220, such as German and French, are not
supported, and neither are the alternate ROM charsets of the VT100
(``ESC ( 1`` and ``ESC ( 2``). On a VT220, ``ESC ( K`` selects German,
but here it is the user mapping of Linux.

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

Cursor Movement
---------------

Writing a character in the last column leaves the cursor on that column
with a wrap pending, as on a VT102. The next character goes to column 1
of the next row. Any move of the cursor cancels the pending wrap, and
so do the erase and edit sequences. While a wrap is pending, the cursor
shows as a block, and a blinking cursor blinks twice as fast.

A CSI sequence takes up to 16 parameters separated by ``;``, and
ignores any after the 16th. A missing number is 0, and a number above
65535 counts as 65535. Some functions, especially cursor movement,
treat 0 as 1 to remain useful without parameters. Only SGR takes ``:``
between numbers, and any other sequence with a ``:`` is ignored.

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
     - Move n rows up, stopping at the top margin, or at the top row
       from above the scroll region.
   * - CSI n B
     - CUD
     - Cursor Down
     - Move n rows down, stopping at the bottom margin, or at the last
       row from below the scroll region.
   * - CSI n C
     - CUF
     - Cursor Forward
     - Move n columns right, stopping at the last column.
   * - CSI n D
     - CUB
     - Cursor Back
     - Move n columns left, stopping at column 1.
   * - CSI n E
     - CNL
     - Cursor Next Line
     - CUD, then move to column 1.
   * - CSI n F
     - CPL
     - Cursor Previous Line
     - CUU, then move to column 1.
   * - CSI n G
     - CHA
     - Cursor Horizontal Absolute
     - Move to column n.
   * - CSI n \`
     - HPA
     - Horizontal Position Absolute
     - Same as CHA.
   * - CSI n a
     - HPR
     - Horizontal Position Relative
     - Same as CUF.
   * - CSI n d
     - VPA
     - Vertical Position Absolute
     - Move to row n. The column does not change.
   * - CSI n e
     - VPR
     - Vertical Position Relative
     - Same as CUD.
   * - CSI n ; m H
     - CUP
     - Cursor Position
     - Move to row n, column m.
   * - CSI n ; m f
     - HVP
     - Horizontal Vertical Position
     - Same as CUP.

Rows and columns count from 1. In origin mode (``CSI ? 6 h``), CUP, HVP,
and VPA count rows from the top margin and stay inside the scroll
region. DECSC and DECRC (``ESC 7`` and ``ESC 8``) save and restore the
cursor.

Editing
-------

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
     - Insert n blank cells at the cursor. The rest of the line moves
       right, and cells pushed past the right edge are lost.
   * - CSI n P
     - DCH
     - Delete Character
     - Delete n cells at the cursor. The rest of the line moves left,
       and blank cells come in at the right.
   * - CSI n X
     - ECH
     - Erase Character
     - Erase n cells from the cursor. The cursor does not move.
   * - CSI n L
     - IL
     - Insert Line
     - Insert n blank lines at the cursor's row. Lines pushed past the
       bottom margin are lost. The cursor moves to column 1. Ignored
       when the cursor is outside the scroll region.
   * - CSI n M
     - DL
     - Delete Line
     - Delete n lines at the cursor's row. Blank lines come in at the
       bottom margin. The cursor moves to column 1. Ignored when the
       cursor is outside the scroll region.
   * - CSI n b
     - REP
     - Repeat
     - Write the last character again, n times. A control or an escape
       sequence after the character, other than another REP, cancels
       it.

Erase
-----

An erased cell is a space in the current background color, with no
attributes. Reverse video does not apply, so an erase under SGR 7 uses
the background color, not the foreground color. This is true of every
erase: the sequences below, the blank cells and lines of the editing
and scrolling sequences, and the clear of the alternate screen.

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
     - - 0: From the cursor to the end of the screen.
       - 1: From the start of the screen to the cursor.
       - 2: The whole screen. The cursor does not move.
       - 3: Forget the rows that scrolled off the top. While the
         console is shorter than the tallest it can be, the terminal
         keeps these rows, and a taller console shows them again. The
         screen is not erased.
   * - CSI n K
     - EL
     - Erase in Line
     - - 0: From the cursor to the end of the line.
       - 1: From the start of the line to the cursor.
       - 2: The whole line.

Scrolling and Margins
---------------------

The scroll region runs from the top margin to the bottom margin, and is
the whole screen by default. LF, IND, and NEL scroll it up at the bottom
margin, and RI scrolls it down at the top margin. The primary and
alternate screens share it.

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
     - Scroll the region up n lines. Blank lines come in at the bottom.
       The cursor does not move.
   * - CSI n T
     - SD
     - Scroll Down
     - Scroll the region down n lines. Blank lines come in at the top.
       The cursor does not move.
   * - CSI t ; b r
     - DECSTBM
     - Set Top and Bottom Margins
     - Set the scroll region to rows t to b. The defaults are the top
       and the bottom rows. The cursor moves home, to the top margin in
       origin mode. A region of less than two rows is ignored.

Tabs
----

Tab stops start every 8 columns. HTS (``ESC H``) sets a stop, and RIS
puts them back to every 8 columns.

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
     - Move forward n tab stops, stopping at the last column.
   * - CSI n Z
     - CBT
     - Cursor Backward Tab
     - Move back n tab stops, stopping at column 1.
   * - CSI n g
     - TBC
     - Tab Clear
     - - 0: Clear the stop at the cursor's column.
       - 3: Clear all stops.

Reports
-------

The terminal sends its replies to the console as input. The 40-column
and 80-column terminals both follow the output, and only the one on the
canvas replies. While a telnet terminal that reports its size is in
charge (see `Terminal Size`_), the RIA suppresses the replies.

.. list-table::
   :widths: 18 13 22 47
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Reply
   * - CSI c, CSI 0 c
     - DA
     - Primary Device Attributes
     - ``ESC [ ? 6 c``, a VT102.
   * - CSI > c, CSI > 0 c
     - DA2
     - Secondary Device Attributes
     - ``ESC [ > 0 ; 1 ; 0 c``: a VT100 (type 0), firmware version 1,
       and ROM 0.
   * - CSI = c, CSI = 0 c
     - DA3
     - Tertiary Device Attributes
     - ``ESC P ! | 00000000 ESC \``, a unit ID of zeros.
   * - ESC Z
     - DECID
     - Identify Terminal
     - The same as DA.
   * - CSI 5 n
     - DSR
     - Device Status Report
     - ``ESC [ 0 n``, terminal OK.
   * - CSI 6 n
     - CPR
     - Cursor Position Report
     - ``ESC [ n ; m R``, where n is the row and m is the column. In
       origin mode, the row counts from the top margin.
   * - CSI x, CSI 0 x
     - DECREQTPARM
     - Request Terminal Parameters
     - ``ESC [ 2 ; 1 ; 1 ; 112 ; 112 ; 1 ; 0 x``: no parity, 8 bits,
       19200 baud to send and to receive, clock multiplier 1, and no
       flags.
   * - CSI 1 x
     - DECREQTPARM
     - Request Terminal Parameters
     - The same, starting with 3 in place of 2.
   * - CSI 11 t
     - —
     - Window state
     - ``ESC [ 1 t``, not minimized.
   * - CSI 14 t
     - —
     - Text area in pixels
     - ``ESC [ 4 ; h ; w t``, the height and the width.
   * - CSI 16 t
     - —
     - Character cell in pixels
     - ``ESC [ 6 ; h ; w t``: 8 by 8 on the 40-column terminal, and 16
       high by 8 wide on the 80-column terminal.
   * - CSI 18 t
     - —
     - Text area in characters
     - ``ESC [ 8 ; rows ; cols t``.
   * - CSI 19 t
     - —
     - Screen in characters
     - ``ESC [ 9 ; rows ; cols t``, the same size as 18.

Other parameters of these sequences get no reply, and neither do the
other window sequences of xterm, which move, resize, and name a window.

ANSI Modes
----------

Set with ``CSI n h`` and reset with ``CSI n l``. Multiple modes may be
combined in one sequence (semicolon-separated parameters). Modes not
listed are ignored.

.. list-table::
   :widths: 6 8 24 62
   :header-rows: 1

   * - n
     - Abbr
     - Name
     - Effect
   * - 2
     - KAM
     - Keyboard Action
     - Ignored. The keyboard is never locked.
   * - 3
     - CRM
     - Control Representation
     - Set: draw controls, as SGR 11 does. Reset (default): controls
       act. See `C0 Control Codes`_.
   * - 4
     - IRM
     - Insert
     - Set: a character inserts at the cursor, and the rest of the line
       moves right. Cells pushed past the right edge are lost. Reset
       (default): a character replaces the cell at the cursor.
   * - 12
     - SRM
     - Send/Receive
     - Ignored. There is no local echo.
   * - 20
     - LNM
     - Line Feed/New Line
     - Set: LF, VT, and FF also move the cursor to column 1. Reset
       (default): they only move it down. The Return key is not
       affected.

DEC Private Modes
-----------------

Set with ``CSI ? n h``, reset with ``CSI ? n l``. Multiple modes
may be combined in one sequence (semicolon-separated parameters). Modes
not listed are ignored.

Mode 33 is for ANSI art. In the text mode of an IBM PC, one bit of the
attribute byte of each character makes it blink. Some ANSI art was drawn
with blinking turned off in the display adapter, so that bit brightened
the background instead and gave 16 background colors. This is called
iCE color. Mode 33, from SyncTERM, makes SGR 5 and 6 brighten the
background in the same way.

.. list-table::
   :widths: 7 10 22 61
   :header-rows: 1

   * - n
     - Abbr
     - Name
     - Effect
   * - 2
     - DECANM
     - ANSI/VT52 Mode
     - Reset: enter `VT52 Mode`_, with US ASCII in G0 and G1 and G0
       active. Set: no effect.
   * - 3
     - DECCOLM
     - 132 Columns
     - Ignored. The width does not change, and the screen is not
       cleared.
   * - 6
     - DECOM
     - Origin Mode
     - Set: CUP, HVP, VPA, and CPR count rows from the top margin,
       inside the scroll region. Reset (default): they count from the
       top row. Both move the cursor home. DECSC saves this mode.
   * - 7
     - DECAWM
     - Autowrap
     - Set (default): a character after the last column goes to the
       next row. Reset: the cursor stays on the last column, and the
       next character replaces the one there. Autowrap is on by
       default, as in xterm and Linux.
   * - 12
     - —
     - Cursor blink
     - Set: the cursor blinks. Reset: the cursor is steady. This
       switches the DECSCUSR style between the blinking and the steady
       style of the same shape. See `Cursor Style`_.
   * - 25
     - DECTCEM
     - Cursor visibility
     - Set (default): show the cursor. Reset: hide the cursor.
   * - 33
     - —
     - iCE colors
     - Set: SGR 5 and 6 brighten the background (iCE colors).
       Reset (default): SGR 5 and 6 blink.
   * - 47
     - —
     - Alternate screen
     - Set: switch to the alternate screen. Reset: switch back to the
       primary screen. The cursor and SGR carry over both ways.
   * - 1047
     - —
     - Alternate screen
     - The same as 47, except that leaving clears the alternate screen
       first.
   * - 1048
     - —
     - Save cursor
     - Set: save the cursor, as DECSC does. Reset: restore it, as DECRC
       does.
   * - 1049
     - —
     - Alternate screen and save cursor
     - Set: save the cursor, switch to the alternate screen, and clear
       it. Reset: switch back to the primary screen and restore the
       cursor, which it does on the primary screen too, as in xterm. Most
       full-screen programs use this mode.

Mode Reports
------------

``CSI ? n $ p`` (DECRQM) asks for the state of DEC private mode n, and
``CSI n $ p`` asks for ANSI mode n. The reply is ``ESC [ ? n ; s $ y``
or ``ESC [ n ; s $ y``, where s is 0 for a mode that is not reported, 1
for set, 2 for reset, 3 for permanently set, and 4 for permanently
reset.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Mode
     - Reply s
   * - 2 (KAM)
     - 4, permanently reset.
   * - 3 (CRM), 4 (IRM), 20 (LNM)
     - 1 or 2.
   * - 12 (SRM)
     - 3, permanently set: there is no local echo.
   * - ?2 (DECANM)
     - 1, ANSI mode. In VT52 mode, the request is not a sequence the
       terminal takes.
   * - ?3 (DECCOLM), ?4 (DECSCLM)
     - 4, permanently reset: 80 columns and no smooth scroll.
   * - ?6, ?7, ?25, ?33
     - 1 or 2.
   * - ?12
     - 2 for a steady cursor style, 1 for a blinking one.
   * - ?47, ?1047, ?1049
     - 1 while the alternate screen shows, 2 otherwise.
   * - ?1048
     - 1 when DECSC saved a cursor on the current screen since the last
       reset, 2 otherwise.
   * - Any other mode
     - 0.

Cursor Style
------------

``CSI Ps SP q`` (DECSCUSR) sets the shape of the cursor and whether it
blinks. The space before the ``q`` is part of the sequence.

.. list-table::
   :widths: 10 90
   :header-rows: 1

   * - Ps
     - Style
   * - 0
     - The default: a blinking block.
   * - 1
     - Blinking block.
   * - 2
     - Steady block.
   * - 3
     - Blinking underline.
   * - 4
     - Steady underline.
   * - 5
     - Blinking bar.
   * - 6
     - Steady bar.

Values above 6 are ignored. Mode 12 switches between the blinking and
the steady style of the same shape, and OSC 12 sets the color of the
cursor. While a wrap is pending, the cursor shows as a block on the last
column. RIS puts the style back to 0, and DECSTR leaves it alone. The
line editor changes the shape to show its mode, as `Terminal Size`_
describes.

VT52 Mode
---------

``CSI ? 2 l`` puts the terminal in VT52 mode, as on a VT102. In VT52
mode the terminal takes only the escape sequences below, and ``ESC <``
returns it to ANSI mode. Characters and controls work as in ANSI mode.
RIS is not a VT52 sequence, so the resets of the system start with
``ESC <``, which ends VT52 mode and does nothing in ANSI mode.

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Code
     - Effect
   * - ESC A
     - Move the cursor up one row, as CUU does.
   * - ESC B
     - Move the cursor down one row, as CUD does.
   * - ESC C
     - Move the cursor right one column.
   * - ESC D
     - Move the cursor left one column.
   * - ESC F
     - Enter graphics mode: DEC Special Graphics into G0, and G0 active.
   * - ESC G
     - Leave graphics mode: US ASCII into G0, and G0 active.
   * - ESC H
     - Move the cursor to the top left.
   * - ESC I
     - Reverse line feed, as RI does.
   * - ESC J
     - Erase from the cursor to the end of the screen.
   * - ESC K
     - Erase from the cursor to the end of the line.
   * - ESC Y r c
     - Move the cursor to row r and column c. Both are a byte of 32
       (0x20) plus the row or the column, counting from 0. A row off the
       screen leaves the row as it is, and a column past the last moves
       to the last column.
   * - ESC Z
     - Identify: reply ``ESC / Z``, a VT100 in VT52 mode.
   * - ESC <
     - Return to ANSI mode.

Any other escape sequence is ignored in VT52 mode, including the keypad
modes, ``ESC =`` and ``ESC >``.

SGR Parameters
--------------

Send multiple parameters separated by ``;``. ``CSI m`` with no
parameters is the same as SGR 0. Parameters not listed are ignored.

The default foreground and background colors are separate from the
256-color palette. They start as the white of palette entry 7 and the
black of entry 0, but SGR 39 and 49 select them, OSC 10 and 11 change
them, and OSC 4 does not. Palette entry 0 and the default background
are transparent, so a plane behind the console shows through. A change
to the palette or to the default colors applies to text written
afterwards. Text already on the screen keeps its colors.

.. list-table::
   :widths: 8 22 70
   :header-rows: 1

   * - n
     - Name
     - Effect
   * - 0
     - Reset
     - The default colors, and all attributes off. SGR 11 stays on.
   * - 1
     - Bold
     - Brighter foreground: palette colors 0-7 become 8-15, and the
       default foreground becomes color 15.
   * - 2
     - Faint
     - Halve the brightness of the foreground.
   * - 3
     - Italic
     - Only characters below 0x80, on the 80-column terminal.
   * - 4
     - Underline
     - A single underline. ``4:n`` (kitty) selects a style: ``4:0``
       none, ``4:1`` single, ``4:2`` double, and ``4:3`` to ``4:5``
       (curly, dotted, and dashed) draw as single.
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
   * - 10
     - Primary font
     - Controls act (SCO, Linux). Turns off SGR 11.
   * - 11
     - First alternate font
     - Draw controls as characters (SCO, Linux). See
       `C0 Control Codes`_.
   * - 21
     - Double underline
     - Per ECMA-48 and xterm.
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
     - Clears slow and rapid blink.
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
     - Palette colors 0-7.
   * - 38
     - Set foreground color
     - A color in one of the forms below.
   * - 39
     - Default foreground
     - The default foreground color.
   * - 40-47
     - Set background color
     - Palette colors 0-7.
   * - 48
     - Set background color
     - A color in one of the forms below.
   * - 49
     - Default background
     - The default background color.
   * - 53
     - Overline
     - —
   * - 55
     - Overline off
     - —
   * - 58
     - Underline color
     - A color in one of the forms below.
   * - 59
     - Default underline color
     - The underline takes the foreground color again.
   * - 90-97
     - Bright foreground
     - Palette colors 8-15. SGR 22 leaves them bright.
   * - 100-107
     - Bright background
     - Palette colors 8-15.

SGR 38, 48, and 58 take a color in these forms, shown here for 38:

- ``38;5;n`` or ``38:5:n``: palette entry n, 0-255. A larger n does
  nothing.
- ``38;2;r;g;b``, ``38:2:r:g:b``, or ``38:2::r:g:b``: a 24-bit color.
  The empty field of the last form is the color space, which is
  ignored. A channel above 255 does nothing.
- ``38;1`` or ``38:1``: the color as it is, made transparent, so a plane
  behind the console shows through.

An unknown or incomplete form is taken whole, so its numbers do not act
as SGR parameters of their own.

OSC Sequences
-------------

An OSC sequence starts with ``ESC ]`` and ends with BEL (``0x07``) or
ST (``ESC \``). It holds a command number and items, separated by
``;``. Inside it, controls other than BEL, CAN, SUB, and ESC are
ignored, and CAN and SUB cancel it.

A color is an X11 color spec, as xterm takes it: ``#rgb``,
``#rrggbb``, ``#rrrgggbbb``, ``#rrrrggggbbbb``, or ``rgb:r/g/b`` with 1
to 4 hex digits per channel. Color names and ``?`` queries are not
accepted, and an item longer than 20 bytes is ignored.

.. list-table::
   :widths: 33 67
   :header-rows: 1

   * - Code
     - Effect
   * - OSC 4 ; n ; color ST
     - Set palette entry n, 0-255. More pairs of n and a color can
       follow, as in ``OSC 4 ; 1 ; #f00 ; 2 ; #0f0 ST``.
   * - OSC 104 ST
     - Reset the palette.
   * - OSC 104 ; n ST
     - Reset palette entry n. More entries can follow, separated by
       ``;``.
   * - OSC 10 ; color ST
     - Set the default foreground color. As in xterm, a second and a
       third item set the default background color and the cursor
       color.
   * - OSC 11 ; color ST
     - Set the default background color. A second item sets the cursor
       color.
   * - OSC 12 ; color ST
     - Set the cursor color.
   * - OSC 110 ST
     - Reset the default foreground color.
   * - OSC 111 ST
     - Reset the default background color.
   * - OSC 112 ST
     - Reset the cursor color.
   * - ESC ] P nrrggbb
     - Linux: set palette entry n, a hex digit from 0 to f, to the hex
       color rrggbb. There is no terminator. A byte that is not a hex
       digit ends the sequence and is dropped.
   * - ESC ] R
     - Linux: reset palette entries 0-15. There is no terminator.

Other OSC commands, such as window titles, are ignored. A color change
applies at once to the current colors and the saved cursors, so text
written afterwards uses it. Text already on the screen keeps its colors.

Resets
------

.. list-table::
   :widths: 18 10 25 47
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - ESC c
     - RIS
     - Reset to Initial State
     - Reset everything except the size and the code page.
   * - CSI 2 ; 1 y
     - DECTST
     - Invoke Confidence Test
     - The power-up test, which is the same as RIS. Other tests are
       ignored.
   * - CSI ! p
     - DECSTR
     - Soft Terminal Reset
     - Reset the modes on the DEC list.

**RIS** leaves the terminal in one known state, whatever came before.
It clears both screens, forgets the rows above the screen (see ED 3),
shows the primary screen, and moves the cursor home. It resets every
mode and setting: SGR, the charsets, insert mode, LNM, SGR 11 and CRM,
VT52 mode, iCE colors, autowrap (on), origin mode, the visibility (on)
and the style (0) of the cursor, the scroll region, the tab stops, both
saved cursors, the palette, the default colors, and the cursor color.
The cursor and the blinking text start to blink again together. Only
the size and the code page stay.

**DECSTR** is the soft reset that a program sends. It turns insert mode
and origin mode off, turns autowrap on, shows the cursor, puts US ASCII
in G0 and G1 with G0 active, and resets SGR, the scroll region, and both
saved cursors. It ends a pending wrap but does not move the cursor. It
leaves the cursor style, iCE colors, LNM, SGR 11, the palette, the
default colors, the tab stops, and the screen as they are.

**When a program stops**, the console sends a soft reset to every
terminal that is attached to it. It holds only what any VT100-class
terminal takes: CAN, ``ESC <``, ``CSI ? 47 l``, ``CSI 0 m``, ``ESC ( B``, SI,
``CSI 4 l``, ``CSI ? 7 h``, and ``CSI ? 25 h``, then CR and LF when the
cursor is not at the start of a line. The terminals that take cursor
shapes also get ``CSI 0 SP q``. The VGA terminal gets the rest of the
reset out of band, through the DISPLAY register of the VGA system on an
:doc:`pico`, and directly on the other machines. This reset does
everything that RIS does, iCE colors and the palette included, except
clear the screen. The cursor stays where it is, and the primary screen
replaces the alternate screen. Text written afterwards starts from the
clean state. On an :doc:`pico`, a program that writes the DISPLAY
register gets the same reset.

**When an RP6502-PICO starts**, the monitor sends CAN, ``ESC <``, and
RIS to the VGA terminal alone, which clears it, and then the soft reset
to every terminal. Every other terminal, such as one on the UART, keeps what it
shows.

**A change of the code page**, through :ref:`RIA_ATTR_CODE_PAGE
<api-ria-attributes>` or the CODE_PAGE register of the VGA system, does
a RIS of the VGA terminal. When a program that changed the code page
stops, the system puts the code page back, with the same RIS.

To Do
-----

These features of xterm, DEC terminals, and the Linux console are not in
the terminal. It is not yet decided whether they will be added.

* Scrolling left and right with SL and SR (``CSI n SP @`` and
  ``CSI n SP A``), from ECMA-48 and xterm. The terminal ignores them.
* Double-height and double-width lines (``ESC # 3`` to ``ESC # 6``).
  Every line is single size.
* DECALN (``ESC # 8``), which fills the screen with E.
* Cursor-key mode (``?1``), the keypad modes (``ESC =`` and ``ESC >``),
  and the keyboard half of LNM, where Return sends CR and LF. These
  change what the keys send, and the keys do not pass through the
  terminal.
* Reverse video for the whole screen (``?5``).
* Keyboard autorepeat (``?8``) and the keyboard LEDs (``CSI q``).
* Mouse reporting (``?9`` and ``?1000`` to ``?1006``). DECRQM reports
  these modes as unknown.
* Recoloring text already on the screen when the palette or the default
  colors change (``OSC 4``, ``OSC 104``, ``OSC 10``, ``OSC 11``, the
  Linux palette sequences). xterm and the Linux console recolor it. Here
  the new colors apply to text written afterwards.
* Protected areas and selective erase: DECSCA marks characters that
  DECSED and DECSEL leave alone, and ECMA-48's SPA, EPA and ERM do the
  same, for the form screens of VT220 and later terminals and xterm. The
  terminal accepts these sequences and ignores them.
