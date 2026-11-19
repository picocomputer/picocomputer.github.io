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

A program uses the console through two device names, ``CON:`` and
``TTY:``. A read of ``CON:`` returns cooked input from the `line editor
<Read Line_>`_, a whole line that the user has typed and edited. A read
of ``TTY:`` returns raw input, the bytes of the keys pressed so far, with
no echo and no editing. Both take their input from the console, so a key
that a read of ``TTY:`` returns never reaches the line editor. A write to
``CON:`` adds a carriage return before each newline that lacks one, as a
terminal needs. A write to ``TTY:`` sends its bytes unchanged. ``TTY:``
is what the :ref:`RIA TX and RX registers <ria-uart>` provide, packaged
as stdio.

``stdin``, ``stdout``, and ``stderr`` start as ``CON:0``, ``CON:1``, and
``CON:2``. These three block, as a C program expects. A read returns
when the user presses Enter, and a write returns when every byte is
sent. A write to ``CON:2`` goes to ``stderr``, and a write to the other
two goes to ``stdout``. ``stdout`` and ``stderr`` are the same output
except on a machine that keeps them apart, such as the :doc:`emu`.

``CON:`` without a number does not block. A read returns 0 until the
user presses Enter, and then returns the line. A write sends as many
bytes as it can, returns how many it sent, and goes to ``stdout``. A
program that keeps running while the user types, such as a game, uses
``CON:``. ``TTY:`` does not block either.



Read Line
=========

A read of ``CON:`` starts the line editor. The user types a line, edits
it with backspace and the arrow keys, and presses Enter. The read then
returns the line, ending with a newline. When the buffer of a read is
shorter than the line, the next reads return the rest of it. Every
``CON:`` uses the same line editor, so each line is returned once, to
whichever ``CON:`` reads it first.

.. _term-terminal-size:

Terminal Size
-------------

A program that fits its output to the console, such as MS-BASIC, gets
the width and the height of the terminal from :ref:`RIA_ATTR_RLN_WIDTH
and RIA_ATTR_RLN_HEIGHT <api-ria-attributes>`. The line editor and the
monitor of an :doc:`pico` use the same size. With no VGA module, the
size is 80 columns by 24 rows. A program that is built for a fixed size
can set it instead. Write a width from 2 to 255 to RIA_ATTR_RLN_WIDTH
and a height from 1 to 255 to RIA_ATTR_RLN_HEIGHT, or 0 to both to go
back to the size of the terminal.

The line editor turns insert mode (IRM) off at the start of input. In
`VT52 Mode`_ it edits with characters and backspaces alone, and the
terminal wraps a long line.

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

The terminal is a VT102 with most of what xterm adds: 256 colors and
24-bit color, the alternate screen, the palette sequences, bracketed
paste, left and right margins, and the rectangle sequences of the
VT420. It runs what is written for ``xterm-256color``. It identifies
itself as a VT102. The tables below list every sequence that it acts
on.

Text is in the 8-bit code page of :ref:`RIA_ATTR_CODE_PAGE
<api-ria-attributes>`, one byte for each character. The terminal does
not decode UTF-8 and has no C1 controls: bytes 0x80 to 0xFF are always
characters of the code page.

The terminal also has a few features from other terminals:

- The underline styles of kitty (SGR 4:n): double, curly, dotted, and
  dashed underlines, in a color of their own (SGR 58 and 59).
  See `Setting Reports`_.
- iCE colors from SyncTERM (mode 33), for ANSI art.

The terminal parses escape sequences as xterm does. It ignores a
sequence that it does not know, whole. It ignores APC, PM, and SOS
strings up to the ST that ends them, and DCS strings too, except the
one that asks for a setting (DECRQSS). Inside a sequence, CAN and SUB
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
     - Move the cursor left one column, stopping at column 1 or at
       the left margin.
   * - ^I
     - 0x09
     - HT
     - Tab
     - Move the cursor right to the next tab stop, or to the last
       column or the right margin when there is none.
   * - ^J
     - 0x0A
     - LF
     - Line Feed
     - Move the cursor down one row, and scroll the region at the
       bottom margin. With LNM set, also do a CR.
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
     - Move the cursor to column 1, or to the left margin.
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

CRM (``CSI 3 h``) draws every control except NUL, BS, LF, FF, CR, SO,
SI, and ESC, and draws DEL too, so HT, VT, BEL, CAN, and SUB show as
characters instead of acting. ``CSI 3 l`` turns this off. It applies
only outside escape sequences, so a control inside a sequence still
acts. SGR 0 leaves it on, and RIS turns it off.

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
   * - ESC 6
     - DECBI
     - Back Index
     - Move the cursor left one column. At the left margin, move the
       columns between the margins right one column instead, on every
       line of the scroll region.
   * - ESC 9
     - DECFI
     - Forward Index
     - Move the cursor right one column. At the right margin, move the
       columns between the margins left one column instead.
   * - ESC 7
     - DECSC
     - Save Cursor
     - Save the cursor's position, a pending wrap, SGR, the charset
       slots and which one is active, and origin mode. Autowrap is not
       saved. The primary and alternate screens have separate saves.
       ``CSI s`` is the same, unless mode 69 has made it DECSLRM.
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
   * - ESC P
     - DCS
     - Device Control String
     - Start a string, which runs up to ST. ``ESC P $ q`` asks for a
       setting. See `Setting Reports`_. Any other is ignored.
   * - ESC X, ESC ^, ``ESC _``
     - SOS, PM, APC
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
   * - ESC # 3, ESC # 4
     - DECDHL
     - Double-Height Line
     - Make the cursor's line the top half (3) or the bottom half (4) of
       a double-height line. Write the same text on both rows. Ignored
       while mode 69 is set, as DECDWL is.
   * - ESC # 5
     - DECSWL
     - Single-Width Line
     - Make the cursor's line single size.
   * - ESC # 6
     - DECDWL
     - Double-Width Line
     - Make the cursor's line double width. It holds half as many
       columns.
   * - ESC # 8
     - DECALN
     - Screen Alignment
     - Fill the screen with E. The margins become the whole screen,
       every line becomes single size, and the cursor moves to the top
       left.
   * - ESC =
     - DECKPAM
     - Application Keypad
     - The keypad sends escape sequences. See `Keyboard`_.
   * - ESC >
     - DECKPNM
     - Numeric Keypad
     - The keypad types its characters (default). See `Keyboard`_.
   * - ESC V
     - SPA
     - Start of Guarded Area
     - Protect the characters written after it. See `Protected
       Areas`_.
   * - ESC W
     - EPA
     - End of Guarded Area
     - The characters written after it are not protected.
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
of the next row. Any move of the cursor cancels the pending wrap, and so
do the erase and edit sequences.
With left and right margins set, the wrap is at the right
margin and the next character goes to the left margin. See `Scrolling
and Margins`_.

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
     - Move n columns right, stopping at the last column or at the
       right margin.
   * - CSI n D
     - CUB
     - Cursor Back
     - Move n columns left, stopping at column 1 or at the left
       margin.
   * - CSI n E
     - CNL
     - Cursor Next Line
     - CUD, then CR.
   * - CSI n F
     - CPL
     - Cursor Previous Line
     - CUU, then CR.
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
region, and CUP, HVP, CHA, and HPA count columns from the left margin
and stay inside the right one. DECSC and DECRC (``ESC 7`` and
``ESC 8``) save and restore the cursor.

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
       right, and cells pushed past the right edge, or the right
       margin, are lost.
   * - CSI n P
     - DCH
     - Delete Character
     - Delete n cells at the cursor. The rest of the line moves left,
       and blank cells come in at the right edge, or the right margin.
   * - CSI n X
     - ECH
     - Erase Character
     - Erase n cells from the cursor. The cursor does not move.
   * - CSI n L
     - IL
     - Insert Line
     - Insert n blank lines at the cursor's row. Lines pushed past the
       bottom margin are lost. The cursor moves to column 1, or to the
       left margin. Ignored when the cursor is outside the margins.
   * - CSI n M
     - DL
     - Delete Line
     - Delete n lines at the cursor's row. Blank lines come in at the
       bottom margin. The cursor moves to column 1, or to the left
       margin. Ignored when the cursor is outside the margins.
   * - CSI n b
     - REP
     - Repeat
     - Write the last character again, n times. A control or an escape
       sequence after the character, other than another REP, cancels
       it.

Erase
-----

An erased cell is a space in the current background color, with no
attributes and no protection. Reverse video does not apply, so an erase
under SGR 7 uses the background color, not the foreground color. This is
true of every erase: the sequences below, the blank cells and lines of
the editing and scrolling sequences, and the clear of the alternate
screen.

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
   * - CSI ? n J
     - DECSED
     - Selective Erase in Display
     - As ED 0 to 2, but protected characters stay. See `Protected
       Areas`_. ``CSI ? 3 J`` is ignored.
   * - CSI ? n K
     - DECSEL
     - Selective Erase in Line
     - As EL, but protected characters stay.

Protected Areas
---------------

A form on the screen can protect its labels and leave them in place
while a program erases its fields. A protected character stays when an
erase that respects protection reaches it. DEC terminals and ECMA-48
each have a way to mark characters as protected, and the terminal
combines them as xterm does.

.. list-table::
   :widths: 15 8 25 52
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - CSI n " q
     - DECSCA
     - Select Character Protection Attribute
     - - 1: The characters written after it are protected.
       - 0 or 2: They are not.
   * - ESC V
     - SPA
     - Start of Guarded Area
     - The characters written after it are protected.
   * - ESC W
     - EPA
     - End of Guarded Area
     - The characters written after it are not protected.

After a DECSCA, only DECSED and DECSEL leave protected characters in
place. After an SPA, ED, EL, and ECH leave them too, unless ERM (ANSI
mode 6) is set. The later of the two decides.

Writing a character, ICH, DCH, IL, DL, and scrolling do not respect
protection. A character written over a protected one takes the
protection of the characters being written, and characters that move
keep theirs. An erase that leaves protected characters on a line also
leaves the line's size, where ED and EL make a line single size.

DECSC saves the protection of the characters being written, and DECRC
restores it. SGR 0 does not change it. DECSTR and RIS turn it off, and
until the next DECSCA or SPA no erase leaves a protected character in
place.

Rectangles
----------

These are the rectangle sequences of the VT420, as xterm has them. A
rectangle is given by its top row t, left column l, bottom row b, and
right column r. A side that is left out is the edge of the screen, and a
side past the edge is the edge. A rectangle whose bottom is above its
top, or whose right is left of its left, does nothing. In origin mode
the rows and columns count from the margins, and a rectangle stays
inside them. A double-width line has only its own columns of a
rectangle. The cursor does not move.

.. list-table::
   :widths: 30 10 60
   :header-rows: 1

   * - Code
     - Abbr
     - Effect
   * - CSI c ; t ; l ; b ; r $ x
     - DECFRA
     - Fill the rectangle with the character whose code is c, as if it
       were written in the current colors and attributes. A c that is
       left out or 0 is a space. A control code (1-31 or 127) or a code
       above 255 does nothing.
   * - CSI t ; l ; b ; r $ z
     - DECERA
     - Erase the rectangle, protected characters too.
   * - CSI t ; l ; b ; r $ {
     - DECSERA
     - Erase the rectangle, but protected characters stay, as with
       DECSED. See `Protected Areas`_.
   * - CSI t ; l ; b ; r ; 1 ; t2 ; l2 ; 1 $ v
     - DECCRA
     - Copy the rectangle so that its top left is at row t2, column
       l2, with its colors and attributes. The copy can lie over the
       rectangle. What would land past the edge is lost. The two 1s
       are page numbers, which are ignored: there is one page.
   * - CSI t ; l ; b ; r ; n ... $ r
     - DECCARA
     - Change the attributes of the characters already there. Each n
       is 1, 4, 5, or 7 to set bold, underline, blink, or reverse; 22,
       24, 25, or 27 to clear one; or 0 to clear all four.
   * - CSI t ; l ; b ; r ; n ... $ t
     - DECRARA
     - Reverse attributes of the characters already there: each n is
       1, 4, 5, or 7, or 0 for all four. What was on goes off, and what
       was off goes on.
   * - CSI n * x
     - DECSACE
     - Choose what DECCARA and DECRARA change. 2: the rectangle. 0 or
       1 (default): the stream of characters from the top left of the
       rectangle to its bottom right, which on the rows between those
       two is the whole row. The stream runs to the edges of the
       screen, also outside the left and right margins in origin mode.

DECCARA and DECRARA leave a character as SGR would have written it.
Bold is the brighter color of SGR 1, and taking bold off leaves a color
that was bright without it, such as one from SGR 90-97. A 24-bit color
has no brighter color and does not change. An underline that they set
is a single one in the foreground color. In iCE colors mode 5 does
nothing: it does not set or reverse blink, and it does not brighten the
background as SGR 5 does. 25 and 0 still clear blink from a character
that has it.

Scrolling and Margins
---------------------

The scroll region runs from the top margin to the bottom margin, and is
the whole screen by default. LF, IND, and NEL scroll it up at the bottom
margin, and RI scrolls it down at the top margin. The primary and
alternate screens share it.

Mode 69 (DECLRMM) allows left and right margins, which DECSLRM sets.
They work as in xterm. A cursor between them stays between them, except
with CBT:

- A character written on the right margin wraps to the left margin of
  the next row.
- CR, BS, and CUB stop at the left margin, and CUF, HT, and CHT stop at
  the right one.
- CBT stops at the left margin only in origin mode. Otherwise it goes
  on to column 1, outside the margins.
- Scrolling moves only the columns between the margins. This includes
  LF, IND, NEL, and RI at the top or the bottom margin, SU, SD, SL, SR,
  IL, and DL. The columns either side stay where they are.
- ICH, DCH, and insert mode move the characters up to the right margin.

A program can still move the cursor outside the margins with CUP. From
there a move away from the margins stops at the edge of the screen, as
with no margins. A move toward them, or text written left of them, goes
in and stops or wraps at the far margin. CR goes to the left margin
from right of it, and to column 1 from left of it unless origin mode is
set.

With the cursor left or right of the margins, LF, IND, NEL, and RI at
the top or bottom margin do not scroll, ICH and DCH do nothing, and
insert mode writes over the character at the cursor. SL, SR, IL, and DL
do nothing there, or with the cursor above or below the scroll region.
SU and SD scroll wherever the cursor is.

While mode 69 is set every line is single size, and ``CSI s`` sets the
margins and no longer saves the cursor. Resetting mode 69 makes the
left and right margins the whole width again. When a program stops,
the system resets mode 69.

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
   * - CSI n SP @
     - SL
     - Scroll Left
     - Move every line of the region n columns left. Blank cells come
       in at the right. The cursor does not move. Ignored when the
       cursor is outside the margins.
   * - CSI n SP A
     - SR
     - Scroll Right
     - Move every line of the region n columns right. Blank cells come
       in at the left. The cursor does not move. Ignored when the
       cursor is outside the margins.
   * - CSI n ' }
     - DECIC
     - Insert Column
     - Insert n blank columns at the cursor's column, on every line of
       the region. The columns up to the right margin move right.
       Ignored when the cursor is outside the margins.
   * - CSI n ' ~
     - DECDC
     - Delete Column
     - Delete n columns at the cursor's column, on every line of the
       region. Blank columns come in at the right margin. Ignored when
       the cursor is outside the margins.
   * - CSI t ; b r
     - DECSTBM
     - Set Top and Bottom Margins
     - Set the scroll region to rows t to b. The defaults are the top
       and the bottom rows. The cursor moves home, which in origin mode
       is the top and left margins. A region of less than two rows is
       ignored.
   * - CSI l ; r s
     - DECSLRM
     - Set Left and Right Margins
     - With mode 69 set, set the margins to columns l to r. The
       defaults are the first and the last columns. The cursor moves
       home, which in origin mode is the top and left margins. Margins
       of less than two columns are ignored. With mode 69 reset,
       ``CSI s`` with no numbers saves the cursor, and with numbers it
       is ignored.

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
     - Move forward n tab stops, stopping at the last column or at the
       right margin.
   * - CSI n Z
     - CBT
     - Cursor Backward Tab
     - Move back n tab stops, stopping at column 1, or at the left
       margin in origin mode.
   * - CSI n g
     - TBC
     - Tab Clear
     - - 0: Clear the stop at the cursor's column.
       - 3: Clear all stops.

.. _term-reports:

Reports
-------

The terminal sends its replies to the console as input. The 40-column
and 80-column terminals both follow the output, and only the one on the
canvas replies. Set :ref:`RIA_ATTR_TERM_QUIET <api-ria-attributes>` to 1
to turn the replies off.

Replies wait until the program reads them. Up to 256 bytes can wait,
and a reply that does not fit is dropped whole, so a program that asks
many questions should read the replies before it asks more. This covers
the replies of `Mode Reports`_ and `Setting Reports`_ and the color
questions of `OSC Sequences`_ too, and RIA_ATTR_TERM_QUIET turns those
off as well.

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
   * - CSI > q, CSI > 0 q
     - XTVERSION
     - Terminal name and version
     - ``ESC P > | RP6502(version) ESC \``
   * - CSI 5 n
     - DSR
     - Device Status Report
     - ``ESC [ 0 n``, terminal OK.
   * - CSI 6 n
     - CPR
     - Cursor Position Report
     - ``ESC [ n ; m R``, where n is the row and m is the column. In
       origin mode, the row counts from the top margin and the column
       from the left margin.
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
     - ``ESC [ 1 t``, not minimized. Only the desktop :doc:`emu`
       replies ``ESC [ 2 t``, while its window is minimized.
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
     - Set: draw controls. Reset (default): controls act. See `C0
       Control Codes`_.
   * - 4
     - IRM
     - Insert
     - Set: a character inserts at the cursor, and the rest of the line
       moves right. Cells pushed past the right edge are lost. Reset
       (default): a character replaces the cell at the cursor.
   * - 6
     - ERM
     - Erasure
     - Set: ED, EL, and ECH erase protected characters too. Reset
       (default): after an SPA, they leave them. See `Protected
       Areas`_.
   * - 12
     - SRM
     - Send/Receive
     - Ignored. There is no local echo.
   * - 20
     - LNM
     - Line Feed/New Line
     - Set: LF, VT, and FF also do a CR, and the Enter key sends CR and
       LF. Reset (default): they only move the
       cursor down, and Enter sends CR.

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
   * - 1
     - DECCKM
     - Cursor Keys
     - Set: the arrow keys, Home, and End send ``ESC O`` and a letter.
       Reset (default): they send ``ESC [`` and a letter. See
       `Keyboard`_.
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
   * - 5
     - DECSCNM
     - Reverse Screen
     - Set: the whole screen is in reverse video, with the foreground
       and the background of every cell swapped. Reset (default): the
       screen is normal.
   * - 6
     - DECOM
     - Origin Mode
     - Set: CUP, HVP, and VPA count rows from the top margin and stay
       inside the scroll region, and CUP, HVP, CHA, and HPA count
       columns from the left margin and stay inside the right one. CPR
       reports the same way. Reset (default): they count from the top
       row and column 1. Both move the cursor home, which is the top
       and left margins when set. DECSC saves this mode.
   * - 7
     - DECAWM
     - Autowrap
     - Set (default): a character after the last column goes to the
       next row. Reset: the cursor stays on the last column, and the
       next character replaces the one there. Autowrap is on by
       default, as in xterm and Linux.
   * - 8
     - DECARM
     - Autorepeat
     - Set (default): a key that is held down repeats. Reset: a key
       types once, however long it is held.
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
   * - 66
     - DECNKM
     - Keypad
     - Set: application keypad, as ``ESC =``. Reset (default): numeric
       keypad, as ``ESC >``. See `Keyboard`_.
   * - 69
     - DECLRMM
     - Left and Right Margins
     - Set: ``CSI l ; r s`` sets left and right margins, and every line
       is single size. Reset (default): the margins are the whole
       width, and ``CSI s`` saves the cursor. See `Scrolling and
       Margins`_.
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
   * - 2004
     - —
     - Bracketed paste
     - Set: text pasted into the :doc:`emu` or the :doc:`web` arrives
       between ``ESC [ 200 ~`` and ``ESC [ 201 ~``, so a program can
       tell it from typing, and any ESC in the text is left out. Reset
       (default): a paste arrives as if typed.

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
   * - 3 (CRM), 4 (IRM), 6 (ERM), 20 (LNM)
     - 1 or 2.
   * - 12 (SRM)
     - 3, permanently set: there is no local echo.
   * - ?2 (DECANM)
     - 1, ANSI mode. In VT52 mode, the request is not a sequence the
       terminal takes.
   * - ?3 (DECCOLM), ?4 (DECSCLM)
     - 4, permanently reset: 80 columns and no smooth scroll.
   * - ?1, ?5, ?6, ?7, ?8, ?25, ?33, ?66, ?69, ?2004
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

Setting Reports
---------------

``ESC P $ q`` and the end of a sequence, then ST (DECRQSS), asks what
that sequence's setting is now. The reply is ``ESC P 1 $ r``, the
setting written as the sequence that would set it, and ST. For any
other sequence the reply is ``ESC P 0 $ r ESC \``.

.. list-table::
   :widths: 22 18 60
   :header-rows: 1

   * - Ask with
     - Setting
     - Reply after ``ESC P 1 $ r``
   * - ``ESC P $ q m ESC \``
     - SGR
     - 0, then every attribute and color that is set, and ``m``. See
       below.
   * - ``ESC P $ q r ESC \``
     - DECSTBM
     - ``t ; b r``, the top and bottom margins.
   * - ``ESC P $ q s ESC \``
     - DECSLRM
     - ``l ; r s``, the left and right margins.
   * - ``ESC P $ q SP q ESC \``
     - DECSCUSR
     - ``n SP q``, the cursor style, 1 to 6.
   * - ``ESC P $ q " q ESC \``
     - DECSCA
     - ``1 " q`` while DECSCA 1 protects the characters written,
       otherwise ``0 " q``, also when SPA protects them.
   * - ``ESC P $ q * x ESC \``
     - DECSACE
     - ``2 * x`` for the rectangle, otherwise ``0 * x``.

The SGR reply lists what `SGR Parameters`_ would set, separated by
``;``: 1, 2, 3, the underline (4, or ``4:n`` for another style), 5 or
6, 7, 8, 9, 53, then the foreground, the background, and the underline
color. A foreground or background in palette entries 0-15 is 30-37,
90-97, 40-47, or 100-107, however it was set. Any other palette color,
and every palette underline color, is the ``38:5:n`` form. A 24-bit
color is ``38:2::r:g:b`` with the numbers that set it. A default color
is not listed.

This is how a program finds what the terminal can draw without knowing
its name. Neovim sets a curly underline with ``CSI 4:3 m``, asks for
SGR, and uses the underline styles and the underline color when the
reply is ``ESC P 1 $ r 0 ; 4:3 m ESC \``. It finds 24-bit color the
same way.

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
cursor. RIS puts the style back to 0, and DECSTR leaves it alone. The
line editor changes the shape to show its mode, as `Terminal Size`_
describes.

VT52 Mode
---------

``CSI ? 2 l`` puts the terminal in VT52 mode, as on a VT102. In VT52
mode the terminal takes only the escape sequences below, and ``ESC <``
returns it to ANSI mode. Characters and controls work as in ANSI mode,
except that insert mode (IRM) is off until the return to ANSI mode. The
keys send the codes of a VT52, as `Keyboard`_ describes.
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
   * - ESC =
     - Application keypad, as in ANSI mode.
   * - ESC >
     - Numeric keypad, as in ANSI mode.

Any other escape sequence is ignored in VT52 mode.

Keyboard
--------

The keys send what they send in xterm, except on the keypad. A key
with a character types it. Alt sends ESC before the character. Ctrl
turns it into a control code:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Ctrl with
     - Sends
   * - ``@``, A to Z, ``[``, ``\``, ``]``, ``^``, ``_``
     - 0x00 to 0x1F. Ctrl-C is 0x03.
   * - The backquote, a to z, ``{``, ``|``, ``}``, ``~``
     - 0x00 to 0x1E, as the row above.
   * - Space, 2
     - 0x00, NUL.
   * - 3 to 7
     - 0x1B to 0x1F.
   * - 8, ``?``
     - 0x7F, DEL.
   * - ``/``
     - 0x1F.
   * - Any other character
     - The character.

These keys send a control code:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Key
     - Sends
   * - Enter
     - CR. With LNM set, CR and LF.
   * - Tab
     - HT. Shift-Tab sends ``ESC [ Z``.
   * - Escape
     - ESC.
   * - Backspace
     - DEL, 0x7F. Ctrl-Backspace sends BS, 0x08.

Alt sends ESC before these too.

The cursor keys and the function keys send escape sequences:

.. list-table::
   :widths: 30 35 35
   :header-rows: 1

   * - Key
     - Sends
     - With a modifier
   * - Up, Down, Right, Left
     - ``ESC [ A``, ``ESC [ B``, ``ESC [ C``, ``ESC [ D``
     - ``ESC [ 1 ; m A`` to ``ESC [ 1 ; m D``
   * - Home, End
     - ``ESC [ H``, ``ESC [ F``
     - ``ESC [ 1 ; m H``, ``ESC [ 1 ; m F``
   * - F1 to F4
     - ``ESC O P``, ``ESC O Q``, ``ESC O R``, ``ESC O S``
     - ``ESC [ 1 ; m P`` to ``ESC [ 1 ; m S``
   * - Insert, Delete
     - ``ESC [ 2 ~``, ``ESC [ 3 ~``
     - ``ESC [ 2 ; m ~``, ``ESC [ 3 ; m ~``
   * - Page Up, Page Down
     - ``ESC [ 5 ~``, ``ESC [ 6 ~``
     - ``ESC [ 5 ; m ~``, ``ESC [ 6 ; m ~``
   * - F5 to F8
     - ``ESC [ n ~``, where n is 15, 17, 18, 19
     - ``ESC [ n ; m ~``
   * - F9 to F12
     - ``ESC [ n ~``, where n is 20, 21, 23, 24
     - ``ESC [ n ; m ~``

A modifier is Shift, Alt, or Ctrl held with the key. In the sequence, m
is 1, plus 1 for Shift, 2 for Alt, and 4 for Ctrl. GUI-Space switches to
the next keyboard layout.

Three modes change these keys:

- **Cursor key mode** (``CSI ? 1 h``). The arrow keys, Home, and End
  send ``ESC O`` and their letter, such as ``ESC O A``.
- **Autorepeat off** (``CSI ? 8 l``). A key that is held down types
  once.
- **VT52 mode.** The arrow keys, Home, End, and F1 to F4 send ESC and
  their letter, such as ``ESC A`` and ``ESC P``.

The keypad follows NumLock, and Shift with NumLock on acts as NumLock
off. A program sets the application keypad with ``ESC =`` and leaves it
with ``ESC >``.

.. list-table::
   :widths: 16 22 28 34
   :header-rows: 1

   * - Key
     - NumLock on
     - NumLock off
     - NumLock off, application keypad
   * - 0
     - 0
     - Insert
     - ``ESC O p``
   * - 1
     - 1
     - End
     - ``ESC O q``
   * - 2
     - 2
     - Down
     - ``ESC O r``
   * - 3
     - 3
     - Page Down
     - ``ESC O s``
   * - 4
     - 4
     - Left
     - ``ESC O t``
   * - 5
     - 5
     - Begin, ``ESC [ E``
     - ``ESC O u``
   * - 6
     - 6
     - Right
     - ``ESC O v``
   * - 7
     - 7
     - Home
     - ``ESC O w``
   * - 8
     - 8
     - Up
     - ``ESC O x``
   * - 9
     - 9
     - Page Up
     - ``ESC O y``
   * - Period
     - ``.``
     - Delete
     - ``ESC O n``
   * - Plus
     - ``+``
     - ``+``
     - ``ESC O k``
   * - Comma
     - ``,``
     - ``,``
     - ``ESC O l``
   * - Minus
     - ``-``
     - ``-``
     - ``ESC O m``
   * - Multiply
     - ``*``
     - ``*``
     - ``ESC O j``
   * - Divide
     - ``/``
     - ``/``
     - ``ESC O o``
   * - Equals
     - ``=``
     - ``=``
     - ``ESC O X``
   * - Enter
     - Enter
     - Enter
     - ``ESC O M``

The application keypad sends what xterm's does. A VT100 has a comma key
where a PC keypad has its plus key: plus sends xterm's ``ESC O k``, and a
keypad with a comma key sends the VT100's ``ESC O l``. F1 to F4 are the
VT100's PF1 to PF4. In VT52
mode, the application keypad sends ``ESC ?`` and the letter, such as
``ESC ? p``.

On an :doc:`pico` with NumLock on, hold Alt and type the number of a
character of the code page on the keypad to type that character.

Modified Keys
-------------

Most keys with a character send one byte, so some keys cannot be told
apart: Tab and Ctrl-I, Enter and Ctrl-M, Ctrl-A and Ctrl-Shift-A. A
program that wants to tell them apart sets xterm's modifyOtherKeys, and
those keys then send a sequence of their own:

``ESC [ 27 ; m ; code ~``

Here m is the modifier number of `Keyboard`_, and code is the code of
the character the key types, in the code page: 97 for ``a``, 65 for
``A``, 13 for Enter, 9 for Tab, 27 for Escape, and 127 for Backspace.
Editors such as Vim, Neovim, and Emacs set it when they start.

.. list-table::
   :widths: 28 72
   :header-rows: 1

   * - Code
     - Effect
   * - CSI > 4 ; n m
     - Set modifyOtherKeys to level n, 0 to 3. See below.
   * - CSI > 4 m
     - Level 0. ``CSI > 4 n`` and ``CSI > m`` do the same.
   * - CSI ? 4 m
     - Report the level, as ``ESC [ > 4 ; n m``.
   * - CSI > 4 ; 1 f
     - Set formatOtherKeys: the sequence is the shorter
       ``ESC [ code ; m u``.
   * - CSI > 4 ; 0 f
     - Back to ``ESC [ 27 ; m ; code ~``. ``CSI > 4 f`` and ``CSI > f``
       do the same.
   * - CSI ? 4 g
     - Report formatOtherKeys, as ``ESC [ > 4 ; n f``.

The levels are xterm's:

- **Level 0** (default). Keys send what `Keyboard`_ describes.
- **Level 1.** Only a key that has no byte of its own sends the
  sequence: Ctrl-Shift with a letter, Ctrl with a character that Ctrl
  makes no control code of (such as Ctrl-1 or Ctrl-comma), and Enter or
  Tab with Shift or Ctrl. Shift-Tab still sends ``ESC [ Z``. Alt still
  sends ESC first.
- **Level 2.** Every key with a modifier sends the sequence. That
  includes Shift with a letter, so Shift-A sends ``ESC [ 27 ; 2 ; 65 ~``,
  and Alt, which no longer sends ESC first. A character that only Shift
  makes, such as ``!``, is typed as it is, but Shift-Space sends the
  sequence. Ctrl-Backspace still sends BS.
- **Level 3.** Every key sends the sequence, modified or not, with m
  as 1 for no modifier.

The cursor keys, the function keys, the editing keys, and the keypad
send what they always do at every level. VT52 mode has no modified keys.

SGR Parameters
--------------

Send multiple parameters separated by ``;``. ``CSI m`` with no
parameters is the same as SGR 0. Parameters not listed are ignored.

The default foreground and background colors are separate from the
256-color palette. They start as the white of palette entry 7 and the
black of entry 0, but SGR 39 and 49 select them, OSC 10 and 11 change
them, and OSC 4 does not. Palette entry 0 and the default background
are transparent, so a plane behind the console shows through.

A change to a palette entry or to a default color also changes the text
already on the screen that was written in it, and an underline in that
palette entry. Text that SGR 1 made bright follows its bright entry,
8-15. A 24-bit color does not change.

.. list-table::
   :widths: 8 22 70
   :header-rows: 1

   * - n
     - Name
     - Effect
   * - 0
     - Reset
     - The default colors, and all attributes off.
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
       none, ``4:1`` single, ``4:2`` double, ``4:3`` curly, ``4:4``
       dotted, and ``4:5`` dashed. SGR 58 gives it a color of its own.
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
     - Per ECMA-48 and xterm.
   * - 22
     - Normal intensity
     - Cancels both bold (1) and faint (2).
   * - 23
     - Italic off
     - —
   * - 24
     - Underline off
     - Clears an underline of any style.
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
to 4 hex digits per channel. Color names are not accepted, and an item
longer than 20 bytes is ignored.

A ``?`` in place of a color asks what the color is. The reply is the
OSC that sets that one color, with the color as ``rgb:rrrr/gggg/bbbb``,
ended the way the question was ended, with BEL or ST. So
``OSC 10 ; ? ; ? ST`` replies ``OSC 10 ; rgb:... ST`` and
``OSC 11 ; rgb:... ST``. The terminal shows 5 bits of each
channel, so the reply has the color to those 5 bits. One OSC can ask
for up to 6 colors.

.. list-table::
   :widths: 33 67
   :header-rows: 1

   * - Code
     - Effect
   * - OSC 4 ; n ; color ST
     - Set palette entry n, 0-255. More pairs of n and a color can
       follow, as in ``OSC 4 ; 1 ; #f00 ; 2 ; #0f0 ST``.
       ``OSC 4 ; n ; ? ST`` replies ``OSC 4 ; n ; rgb:.../.../... ST``.
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
     - Set the cursor color. ``OSC 10 ; ? ST``, ``OSC 11 ; ? ST``, and
       ``OSC 12 ; ? ST`` reply with each color.
   * - OSC 110 ST
     - Reset the default foreground color.
   * - OSC 111 ST
     - Reset the default background color.
   * - OSC 112 ST
     - Reset the cursor color.


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
     - Reset everything.
   * - CSI 2 ; 1 y
     - DECTST
     - Invoke Confidence Test
     - The power-up test, which is the same as RIS. Other tests are
       ignored.
   * - CSI ! p
     - DECSTR
     - Soft Terminal Reset
     - Reset the modes on the DEC list.

**RIS** clears both screens and puts every mode and setting of the
terminal back to its default.

**DECSTR** is the soft reset that a program sends. It turns insert
mode, origin mode, and cursor key mode off, sets the numeric keypad,
turns autowrap on, shows the cursor, puts US ASCII in G0 and G1 with G0
active, and resets SGR, character protection, the scroll region, the
left and right margins with mode 69, and both saved cursors. It ends a
pending wrap but does not move the cursor. It leaves the cursor style,
iCE colors, the reverse screen, autorepeat, LNM, CRM, DECSACE, the
palette, the default colors, the tab stops, the line sizes, and the
screen as they are.

**A change of the code page**, through :ref:`RIA_ATTR_CODE_PAGE
<api-ria-attributes>` or the CODE_PAGE register of the VGA system, does
a RIS of the VGA terminal. When a program that changed the code page
stops, the system puts the code page back, with the same RIS.
