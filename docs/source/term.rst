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
editor <Line Editor_>`_ lets the user edit a line before pressing Enter,
with no editing code in the program, and a program can keep running
while the user types. The escape sequences of the `VGA terminal
<Terminal_>`_ let a program move the cursor, color its text, and draw
boxes.


.. _term-console-manifold:

Console Manifold
================

The **console** is the standard streams of a program: ``stdin``,
``stdout``, ``stderr``, ``CON:``, and ``TTY:``. On an :doc:`pico`, the
**monitor** runs on the console too, for configuration and for loading
ROMs.

A **terminal** is a device that a user types into and reads from. The
**console manifold** attaches several terminals to the console at once.
Input from every terminal goes to the console, and the output of the
console goes to every terminal.

The **VGA terminal** is the terminal that :ref:`mode 0 <vga-mode-0>` of
the :doc:`vga` system draws, with a keyboard. The other terminals depend
on the machine:

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
- **RP6502-FPGA** and **RP6502-WEB.** The VGA terminal is the only
  terminal.

A program uses the console through two device names, ``CON:`` and
``TTY:``. A read of ``CON:`` returns cooked input from the `line editor
<Line Editor_>`_, a whole line that the user has typed and edited. A read
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



.. _term-line-editor:

Line Editor
===========

A read of ``CON:`` starts the line editor. The user types a line, edits
it, and presses Enter. The read then returns the line, ending with a
newline. When the buffer of a read is shorter than the line, the next
reads return the rest of it. Every ``CON:`` uses the same line editor, so
each line is returned once, to whichever ``CON:`` reads it first.

The monitor of an :doc:`pico` reads its commands with the line editor
too, so the keys here also work at the monitor prompt.

Keys
----

These keys move the cursor:

.. list-table::
   :widths: 45 55
   :header-rows: 1

   * - Keys
     - Action
   * - Left, Right, Ctrl-B, Ctrl-F
     - Move one character.
   * - Ctrl-Left, Ctrl-Right, Alt-Left, Alt-Right, Alt-B, Alt-F
     - Move one word.
   * - Alt-Ctrl-B, Alt-Ctrl-F
     - Move one argument.
   * - Home, End, Ctrl-A, Ctrl-E
     - Move to the start or the end of the line.

These keys change the line:

.. list-table::
   :widths: 45 55
   :header-rows: 1

   * - Keys
     - Action
   * - Backspace
     - Delete the character before the cursor.
   * - Delete, Ctrl-D
     - Delete the character under the cursor.
   * - Ctrl-W, Alt-Backspace
     - Delete the word before the cursor.
   * - Ctrl-Delete, Alt-D
     - Delete the word after the cursor.
   * - Alt-Ctrl-Backspace
     - Delete the argument before the cursor.
   * - Alt-Ctrl-D
     - Delete the argument after the cursor.
   * - Ctrl-U
     - Delete from the start of the line to the cursor.
   * - Ctrl-K
     - Delete from the cursor to the end of the line.
   * - Ctrl-Y
     - Put back the text that the six rows above deleted last.
   * - Ctrl-T
     - Swap the character before the cursor with the character under it.
       At the end of the line, swap the last two characters.
   * - Insert
     - Switch between insert mode and overwrite mode.
   * - Up, Down, Ctrl-P, Ctrl-N
     - Bring back an earlier line, in the monitor of an :doc:`pico`.
   * - Shift with Left, Right, Home, or End
     - Select text.
   * - Ctrl-Shift-C, Ctrl-Insert
     - Copy the selected text.
   * - Ctrl-Shift-X, Shift-Delete
     - Cut the selected text.
   * - Ctrl-Shift-V, Shift-Insert
     - Paste at the cursor, or in place of the selected text.

Pasted text is typed into the line. Each line end in it is Enter, so a
paste of several lines enters them one after another, and each goes to
the next line that is read. A paste of a single line that ends with a
line end is the exception: the line end is left out, so the line waits
for you to look it over and press Enter.

The clipboard and Ctrl-Y are separate. Copy and cut fill the clipboard,
and only paste reads it. The keys that delete a word, an argument, or
part of the line fill what Ctrl-Y puts back, and never change the
clipboard.

The copy, cut, and paste keys are keys of the keyboard of the VGA
terminal. `Copy and Paste`_ describes its clipboard. On a USB serial
terminal or a telnet terminal, copy and paste with the terminal program
of the computer. What it pastes arrives as typing.

History
-------

The monitor of an :doc:`pico` remembers the lines entered at its prompt.
Up or Ctrl-P brings back the line before, and Down or Ctrl-N the line
after. Edit a line that came back, or press Enter to run it again. The
monitor does not remember an empty line, a line that repeats the one
before it, or a ``SET PASS`` or ``SET KEY`` command that sets a password
or a passkey. The history lasts until the RIA reboots.

A read by a program has no history, and the line editor leaves Up and
Down to the program. `Non-blocking Read Line`_ shows how a program adds
its own. What Ctrl-Y puts back is also kept apart. Each program starts
with nothing to put back, and the monitor keeps its own text while a
program runs.

.. _term-terminal-size:

Terminal Size
-------------

A program that fits its output to the terminal, such as MS-BASIC, gets
the width and the height from :ref:`RIA_ATTR_RLN_WIDTH and
RIA_ATTR_RLN_HEIGHT <api-ria-attributes>`. The line editor and the
monitor of an :doc:`pico` use the same size. It is the size of the VGA
terminal. With no VGA terminal, the size is 80 columns by 24 rows.

A program that is built for a fixed size can set the size instead, and
so can a program whose user types on another terminal, such as a USB
serial terminal or a telnet terminal. Write a width from 2 to 255 to
RIA_ATTR_RLN_WIDTH and a height from 1 to 255 to RIA_ATTR_RLN_HEIGHT,
or 0 to both to go back to the size of the VGA terminal.

.. _term-nonblocking-read-line:

Non-blocking Read Line
----------------------

A program normally stops while the user types a line. ``fgets()`` does
not return until the user presses Enter. A non-blocking read line lets
the program keep running while the user types. Use it when the program
has other work to do, such as a game that asks for a name while the
screen keeps moving.

Open ``CON:`` and call ``read()`` from the main loop of the program.
``read()`` returns 0 while the user is typing. After the user presses
Enter, it returns the line.

.. code-block:: c

   char line[256];
   int n;
   int fd = open("CON:", O_RDWR);

   printf("Name? ");
   do
   {
       /* The other work of the program goes here. */
       n = read(fd, line, sizeof(line));
   } while (n == 0);
   /* line holds n bytes and ends with a newline. */

The user types the line where the cursor is at the first ``read()``. A
line can be up to 254 characters. To change that, write
:ref:`RIA_ATTR_RLN_LENGTH <api-ria-attributes>`.

The program can also watch the keys and change the line while the user
types. Use this to add history, Tab completion, or a form with several
fields. Call these between reads:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Call
     - What it does
   * - :ref:`ria_rln_lastkey() <api-rln-lastkey>`
     - Returns the last key that the user pressed, and whether the line
       editor used it. The program handles the keys that the line editor
       does not use, such as Tab, Escape, Up, Down, the function keys,
       and the keys of the application keypad.
   * - :ref:`ria_rln_peek() <api-rln-peek>`
     - Returns the line so far and where the cursor is in it.
   * - :ref:`ria_rln_poke() <api-rln-poke>`
     - Types text into the line. The text replaces the characters at the
       cursor.

Poke these to change the line:

- To start the line with text already in it, poke the text after the
  first ``read()``.
- To move the cursor, poke CUF or CUB. See `Cursor Movement`_.
- To insert, delete, or erase characters, poke ICH, DCH, or ECH. See
  `Editing`_.
- To end the line as Enter does, poke ``\r``. A form does this when the
  user presses Tab to go to the next field.
- To cancel the line when the user presses Ctrl-C, poke ``\x03``. The
  line shows ``^C`` and ends. :ref:`RIA_ATTR_SIGINT <api-ria-attributes>`
  tells the program that the user pressed Ctrl-C.


Terminal
========

The VGA terminal shows the text of a program on the VGA monitor and
sends the program the keys of the keyboard. A program controls it with
escape sequences. It prints them to move the cursor, color the text,
clear the screen, and more.

The VGA terminal runs software written for ``xterm-256color``. Like
xterm, it identifies itself as a VT420 with xterm's extensions. The
sections below list every sequence that it acts on.

Text is in the 8-bit code page of :ref:`RIA_ATTR_CODE_PAGE
<api-ria-attributes>`, one byte for each character.


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
     - Shown on the terminal. ENQ (0x05) does not send an answerback.
   * - ^G
     - 0x07
     - BEL
     - Bell
     - Ring the bell. To silence it, set :ref:`RIA_ATTR_BEL
       <api-ria-attributes>` to 0.
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
     - Same as LF.
   * - ^M
     - 0x0D
     - CR
     - Carriage Return
     - Move the cursor to column 1, or to the left margin.
   * - ^N
     - 0x0E
     - SO
     - Shift Out
     - LS1: put G1 in GL, the set that characters draw from. See
       `Character Sets`_.
   * - ^O
     - 0x0F
     - SI
     - Shift In
     - LS0: put G0 in GL, the set that characters draw from. See
       `Character Sets`_.
   * - ^P-^W
     - 0x10-0x17
     - —
     - —
     - Shown on the terminal.
   * - ^X
     - 0x18
     - CAN
     - Cancel
     - Cancel an escape sequence. Ignored outside one.
   * - ^Y
     - 0x19
     - EM
     - End of Medium
     - Shown on the terminal.
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
     - Shown on the terminal.
   * - —
     - 0x7F
     - DEL
     - Delete
     - Ignored.

A control code that is shown on the terminal shows as the character of
the code page at that code.

To show the other control codes on the terminal too, set CRM with
``CSI 3 h``. HT, VT, BEL, CAN, SUB, and DEL are then shown instead of
acting. NUL, BS, LF, FF, CR, SO, SI, and ESC still act. ``CSI 3 l``
turns CRM off.

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
       columns between the margins left one column instead, on every
       line of the scroll region.
   * - ESC 7
     - DECSC
     - Save Cursor
     - Save the cursor's position, a pending wrap, SGR, the character
       sets in G0 to G3, which of them is in GL, a pending single
       shift, and origin mode. It does not save autowrap. The primary
       and alternate screens have separate saves. ``CSI s`` is the same,
       unless mode 69 has made it DECSLRM.
   * - ESC 8
     - DECRC
     - Restore Cursor
     - Restore what DECSC saved. With nothing saved, move the cursor
       home with SGR 0, US ASCII in G0 to G3, G0 in GL, no single
       shift, and origin mode off. ``CSI u`` is the same.
   * - ESC Z
     - DECID
     - Identify Terminal
     - Reply as Primary DA does. See `Reports`_.
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
       setting. See `Setting Reports`_. ``ESC P 1 $ t`` restores the
       cursor and ``ESC P 2 $ t`` the tab stops. See `Presentation
       State`_. Any other is ignored.
   * - ESC X, ESC ^, ``ESC _``
     - SOS, PM, APC
     - Strings
     - Start a string, which is ignored up to ST.
   * - ``ESC \``
     - ST
     - String Terminator
     - End an OSC sequence or a string.
   * - ESC (, ESC ), ``ESC *``, ESC +
     - SCS
     - Designate G0, G1, G2, G3
     - Load a character set into G0, G1, G2, or G3. See `Character
       Sets`_.
   * - ESC n, ESC o
     - LS2, LS3
     - Locking Shift Two, Three
     - Put G2 or G3 in GL, the set that characters draw from.
   * - ESC N, ESC O
     - SS2, SS3
     - Single Shift Two, Three
     - Draw the next character from G2 or G3. The character after it
       draws from GL again.
   * - ESC # 3, ESC # 4
     - DECDHL
     - Double-Height Line
     - Make the cursor's line the top half (3) or the bottom half (4) of
       a double-height line. Write the same text on both rows. The line
       shows half as many columns. Ignored while mode 69 is set.
   * - ESC # 5
     - DECSWL
     - Single-Width Line
     - Make the cursor's line single size.
   * - ESC # 6
     - DECDWL
     - Double-Width Line
     - Make the cursor's line double width. It shows half as many
       columns. The characters past the middle are hidden, and they
       show again when the line is made single width. Ignored while
       mode 69 is set.
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
     - Ignored. In VT52 mode, it returns to ANSI mode. See `VT52 Mode`_.

.. _term-character-sets:

Character Sets
--------------

A character set changes the characters that the codes from 0x21 to 0x7E
show. With the DEC Special Graphics set, the lowercase letters show
lines and corners, so a program can draw boxes. The DEC Technical set
has mathematical symbols. The sets work in every code page.

The terminal holds four character sets at a time, in **G0**, **G1**,
**G2**, and **G3**. It shows characters from one of the four, which is
called **GL**. To mix regular text with line drawing, load DEC Special
Graphics into G1 once, then switch to G1 with SO and back to G0 with SI.

**Load a set.** The sequence is ESC and two characters. The first
character chooses G0, G1, G2, or G3, and the second chooses the set.
``ESC ( 0`` loads DEC Special Graphics into G0, and ``ESC ) B`` loads US
ASCII into G1.

.. list-table::
   :widths: 22 78
   :header-rows: 1

   * - First character
     - Loads the set into
   * - ``(``
     - G0.
   * - ``)``
     - G1.
   * - ``*``
     - G2.
   * - ``+``
     - G3.

.. list-table::
   :widths: 22 78
   :header-rows: 1

   * - Second character
     - Set loaded
   * - ``B``, ``U``, or ``K``
     - US ASCII (default).
   * - ``A``
     - UK: US ASCII with the pound sign (£) in place of ``#``.
   * - ``0``
     - DEC Special Graphics.
   * - ``>``
     - DEC Technical.

**Switch sets.** A locking shift switches to a set until the next
locking shift. A single shift switches to a set for one character.

.. list-table::
   :widths: 17 12 71
   :header-rows: 1

   * - Code
     - Abbr
     - Effect
   * - SI (^O)
     - LS0
     - Switch to G0.
   * - SO (^N)
     - LS1
     - Switch to G1.
   * - ESC n
     - LS2
     - Switch to G2.
   * - ESC o
     - LS3
     - Switch to G3.
   * - ESC N
     - SS2
     - Use G2 for the next character.
   * - ESC O
     - SS3
     - Use G3 for the next character.

All four hold US ASCII at startup, with G0 in GL, so until you load
another set you can ignore this entire feature.

Cursor Movement
---------------

Writing a character in the last column leaves the cursor on that column
with a wrap pending. The next character goes to column 1
of the next row. Any move of the cursor cancels the pending wrap, and so
do the erase and edit sequences.
With left and right margins set, the wrap is at the right
margin and the next character goes to the left margin. See `Scrolling
and Margins`_.

A CSI sequence takes numbers separated by ``;``. A missing number is 0.
Cursor movement treats 0 as 1. Only SGR takes ``:``
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
     - Move n rows up, stopping at the top margin, or at the top row if
       the cursor is above the scroll region.
   * - CSI n B
     - CUD
     - Cursor Down
     - Move n rows down, stopping at the bottom margin, or at the last
       row if the cursor is below the scroll region.
   * - CSI n C
     - CUF
     - Cursor Forward
     - Move n columns right, stopping at the right margin, or at the
       last column if the cursor is right of the right margin.
   * - CSI n D
     - CUB
     - Cursor Back
     - Move n columns left, stopping at the left margin, or at column 1
       if the cursor is left of the left margin.
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
     - Move n columns right. The cursor can pass the right margin and
       stops at the last column. In origin mode, it stops at the right
       margin.
   * - CSI n d
     - VPA
     - Vertical Position Absolute
     - Move to row n. The column does not change.
   * - CSI n e
     - VPR
     - Vertical Position Relative
     - Move n rows down. The cursor can pass the bottom margin and stops
       at the last row. In origin mode, it stops at the bottom margin.
       The column does not change.
   * - CSI n ; m H
     - CUP
     - Cursor Position
     - Move to row n, column m.
   * - CSI n ; m f
     - HVP
     - Horizontal Vertical Position
     - Same as CUP.

Rows and columns count from 1. In origin mode (``CSI ? 6 h``), CUP, HVP,
and VPA count rows from the top margin and stop at the bottom margin,
and CUP, HVP, CHA, and HPA count columns from the left margin and stop
at the right margin. DECSC and DECRC (``ESC 7`` and ``ESC 8``) save and
restore the cursor.

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
     - Write the last character again, n times. REP works only right
       after a character. After anything else, including another REP,
       it does nothing.

Erase
-----

An erased cell is a space in the current background color, with no attributes
and no protection. Reverse video does not apply, so an erase under SGR 7 uses
the background color, not the foreground color. The blank cells and lines that
the editing and scrolling sequences bring in, and the clear of the alternate
screen, are erased cells too.

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
       - 3: Forget the rows that scrolled off the top. The screen is
         not erased.
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

A protected character stays on the screen when a program erases around
it. A program can protect the labels of a form, then erase the fields
without erasing the labels. DECSCA and SPA each protect the characters
written after them.

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

DECSED, DECSEL, and DECSERA leave protected characters in place. ED, EL,
and ECH leave them only after an SPA, and not while ERM (ANSI mode 6) is
set.

Only an erase leaves a protected character in place. Writing a
character, ICH, DCH, IL, DL, and scrolling still change and move
protected characters.

SGR 0 does not turn protection off. DECSTR and RIS do.

Rectangles
----------

A rectangle is given by its top row t, left column l, bottom row b, and
right column r. A side that is left out, or that is past the edge of the
screen, is the edge of the screen. In origin mode the rows and columns
count from the margins, and a rectangle stays inside them. The cursor
does not move.

.. list-table::
   :widths: 30 10 60
   :header-rows: 1

   * - Code
     - Abbr
     - Effect
   * - CSI c ; t ; l ; b ; r $ x
     - DECFRA
     - Fill the rectangle with the character of code c, in the current
       colors and attributes. With c left out or 0, the character is a
       space.
   * - CSI t ; l ; b ; r $ z
     - DECERA
     - Erase the rectangle, protected characters too. Each cell becomes
       a space in the current background color, with no attributes and
       no protection.
   * - CSI t ; l ; b ; r $ {
     - DECSERA
     - Make the characters of the rectangle spaces. Each cell keeps its
       colors and attributes. Protected characters stay, as with
       DECSED. See `Protected Areas`_.
   * - CSI t ; l ; b ; r ; 1 ; t2 ; l2 ; 1 $ v
     - DECCRA
     - Copy the rectangle so that its top left is at row t2, column l2,
       with its colors and attributes. The copy can overlap the
       original. What would land past the edge is lost. The two 1s are
       page numbers and are ignored.
   * - CSI t ; l ; b ; r ; n ... $ r
     - DECCARA
     - Change the attributes of the characters already there. Each n
       is 1, 4, 5, or 7 to set bold, underline, blink, or reverse; 22,
       24, 25, or 27 to clear one; or 0 to clear all four.
   * - CSI t ; l ; b ; r ; n ... $ t
     - DECRARA
     - Turn each attribute of the characters already there on if it is
       off, and off if it is on. Each n is 1, 4, 5, or 7, or 0 for all
       four.
   * - CSI n * x
     - DECSACE
     - Choose what DECCARA and DECRARA change. 2: the rectangle. 0 or 1
       (default): every character from the top left corner to the
       bottom right corner in reading order. The rows between the first
       and the last change across the whole width of the screen.

An underline that DECCARA or DECRARA sets is a single underline in the
foreground color. With iCE colors (mode 33) set, 5 changes blink only.
It does not brighten the background as SGR 5 does.

Scrolling and Margins
---------------------

The scroll region is the whole screen until DECSTBM sets a top and a
bottom margin. Then only the rows from the top margin to the bottom
margin scroll. The primary and alternate screens share one scroll
region.

``CSI ? 4 h`` (DECSCLM) turns on smooth scroll. A new line moves into
the scroll region one scanline at a time, about four lines a second, and
the output of the program waits while it does. To let the last lines
finish moving before a program exits, call ``syncfs()`` on ``stdout``.

``CSI ? 69 h`` (DECLRMM) allows left and right margins, and DECSLRM sets
them. Text then wraps at the right margin to the left margin of the next
row, and scrolling moves only the columns between the margins. While
mode 69 is set, every line is single size. Resetting mode 69 makes the
left and right margins the whole width again.

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
       The cursor does not move. ``CSI 0 T`` and ``CSI T`` with more
       than one number do not scroll. They answer highlight tracking.
       See `Mouse Reports`_.
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
puts them back to every 8 columns. ``CSI 2 $ w`` reports the columns of
the stops, and ``ESC P 2 $ t`` sets them all at once. See `Presentation
State`_.

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

The terminal sends its replies to the console as input. These are the
replies in the table below, the replies of `Mode Reports`_, `Setting
Reports`_, and `Presentation State`_, and the color replies of `OSC
Sequences`_. Set :ref:`RIA_ATTR_TERM_QUIET
<api-ria-attributes>` to 1 to turn the replies off.

Replies wait in a 256-byte queue. A reply that does not fit is lost.

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
     - ``ESC [ ? 64 ; 6 ; 21 ; 22 ; 28 ; 29 c``: a VT420 (64) with
       selective erase (6), horizontal scrolling and left and right
       margins (21), ANSI color (22), rectangular editing (28), and the
       DEC locator (29).
   * - CSI > c, CSI > 0 c
     - DA2
     - Secondary Device Attributes
     - ``ESC [ > 41 ; 10 ; 0 c``: a VT420 (41) with firmware version 1.0
       (10).
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
   * - CSI ? 5 n
     - DSR
     - Device Status Report
     - ``ESC [ ? 0 n``, terminal OK.
   * - CSI ? 6 n
     - DECXCPR
     - Extended Cursor Position Report
     - ``ESC [ ? n ; m ; 1 R``, where n is the row, m is the column,
       and 1 is the page. In origin mode, the row counts from the top
       margin and the column from the left margin.
   * - CSI ? 15 n
     - DSR
     - Printer Status
     - ``ESC [ ? 13 n``, no printer.
   * - CSI ? 25 n
     - DSR
     - User-Defined Key Status
     - ``ESC [ ? 20 n``, user-defined keys unlocked.
   * - CSI ? 26 n
     - DSR
     - Keyboard Status
     - ``ESC [ ? 27 ; 1 ; 0 ; 0 n``: a North American keyboard (1),
       ready (0), and an LK201 (0).
   * - CSI ? 55 n
     - DSR
     - Locator Status
     - ``ESC [ ? 50 n``, the locator is ready. See `DEC Locator`_.
   * - CSI ? 56 n
     - DSR
     - Locator Type
     - ``ESC [ ? 57 ; 1 n``, the locator is a mouse.
   * - CSI ? 62 n
     - DECMSR
     - Macro Space Report
     - ``ESC [ 0000 * {``, no space for macros.
   * - CSI ? 63 ; id n
     - DECCKSR
     - Memory Checksum Report
     - ``ESC P id ! ~ 0000 ESC \``, the checksum of no macros. A missing
       id is 0.
   * - CSI ? 75 n
     - DSR
     - Data Integrity Report
     - ``ESC [ ? 70 n``, no errors.
   * - CSI ? 85 n
     - DSR
     - Multiple Session Status
     - ``ESC [ ? 83 n``, sessions not configured.
   * - CSI 1 $ w
     - DECRQPSR
     - Request Presentation State
     - DECCIR, ``ESC P 1 $ u``, the cursor and its settings, and
       ``ESC \``. See `Presentation State`_.
   * - CSI 2 $ w
     - DECRQPSR
     - Request Presentation State
     - DECTABSR, ``ESC P 2 $ u``, the columns of the tab stops, and
       ``ESC \``. See `Presentation State`_.
   * - CSI x, CSI 0 x, CSI 1 x
     - DECREQTPARM
     - Request Terminal Parameters
     - ``ESC [ n ; 1 ; 1 ; s ; s ; 1 ; 0 x``. The first number
       tells which request the reply answers: 2 for ``CSI x`` and
       ``CSI 0 x``, and 3 for ``CSI 1 x``. The other numbers are the
       serial settings of a VT100, in this order: no parity (1), 8 bits
       (1), the speed to send (s), the speed to receive (s), a clock
       multiplier of 1 (1), and no flags (0). Both speeds are the
       speed of the console; `Speed`_ gives the number for each.
   * - CSI 11 t
     - —
     - Window state
     - ``ESC [ 1 t``, not minimized. The desktop :doc:`emu` replies
       ``ESC [ 2 t`` while its window is minimized.
   * - CSI 13 t
     - —
     - Window position in pixels
     - Always ``ESC [ 3 ; 1 ; 1 t``, an x of 1 and a y of 1.
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

ANSI Modes
----------

Set with ``CSI n h`` and reset with ``CSI n l``. One sequence can set or
reset several modes, with their numbers separated by semicolons.

.. list-table::
   :widths: 6 8 24 62
   :header-rows: 1

   * - n
     - Abbr
     - Name
     - Effect
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
     - Set: ED, EL, and ECH erase protected characters too. Reset (default):
       they leave the characters that SPA protected. See `Protected Areas`_.
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

Set with ``CSI ? n h``, reset with ``CSI ? n l``. One sequence can set
or reset several modes, with their numbers separated by semicolons.

ANSI art made with iCE colors uses blink to mean a bright background. To
show it, set ``CSI ? 33 ; 35 h``. Mode 33 gives blinking text a bright
background, and mode 35 stops the blinking.

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
     - Reset: enter `VT52 Mode`_. To leave VT52 mode, send ``ESC <``.
   * - 3
     - DECCOLM
     - 132 Columns
     - The terminal has no 132-column width, so this mode does not
       change the width. By default it does nothing. With Allow 80 to
       132 set, setting or resetting it clears the screen and moves the
       cursor to the top left.
   * - 4
     - DECSCLM
     - Smooth Scroll
     - Set: new lines scroll in smoothly. Reset (default): they jump
       into place. See `Scrolling and Margins`_.
   * - 5
     - DECSCNM
     - Reverse Screen
     - Set: the whole screen is in reverse video, with the foreground
       and the background of every cell swapped. Reset (default): the
       screen is normal.
   * - 6
     - DECOM
     - Origin Mode
     - Set: rows and columns count from the top margin and the left
       margin, and the cursor cannot be moved outside the margins.
       Reset (default): rows and columns count from the top left of the
       screen. Setting or resetting the mode moves the cursor home.
   * - 7
     - DECAWM
     - Autowrap
     - Set (default): a character after the last column goes to the
       next row. Reset: the cursor stays on the last column, and the
       next character replaces the one there.
   * - 8
     - DECARM
     - Autorepeat
     - Set (default): a key that is held down repeats. Reset: a key
       types once, however long it is held.
   * - 9
     - —
     - Mouse presses
     - Set: the terminal reports each press of the left, middle, or
       right button. See `Mouse Reports`_.
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
     - Set: text written with SGR 5 or 6 gets a bright background.
       Reset (default): it does not.
   * - 35
     - —
     - Blink off
     - Set: no text blinks, including text already on the screen. Reset
       (default): text written with SGR 5 or 6 blinks.
   * - 40
     - —
     - Allow 80 to 132
     - Set: the 132 Columns mode clears the screen. Reset (default):
       the 132 Columns mode does nothing. RIS and DECSTR leave this mode
       as it
       is.
   * - 47
     - —
     - Alternate screen
     - Set: switch to the alternate screen. Reset: switch back to the primary
       screen. The cursor position and the text attributes stay the same when
       the screen switches.
   * - 66
     - DECNKM
     - Keypad
     - Set: application keypad, as ``ESC =``. Reset (default): numeric
       keypad, as ``ESC >``. See `Keyboard`_.
   * - 67
     - DECBKM
     - Backarrow Key
     - Set: Backspace sends BS (0x08), and Ctrl-Backspace sends DEL
       (0x7F). Reset (default): Backspace sends DEL, and Ctrl-Backspace
       sends BS. See `Keyboard`_.
   * - 69
     - DECLRMM
     - Left and Right Margins
     - Set: ``CSI l ; r s`` sets the left and right margins, and every
       double-size line becomes single size. Reset (default): the margins are
       the whole width, and ``CSI s`` saves the cursor. See `Scrolling and
       Margins`_.
   * - 1000
     - —
     - Mouse buttons
     - Set: the terminal reports each press and release of a mouse
       button, and each turn of the wheel. See `Mouse Reports`_.
   * - 1001
     - —
     - Mouse highlight
     - Set: as 1000, and a press of the left button waits for the
       program to say what to highlight. See `Mouse Reports`_.
   * - 1002
     - —
     - Mouse drags
     - Set: as 1000, and the terminal also reports the mouse moving
       while a button is down. See `Mouse Reports`_.
   * - 1003
     - —
     - Mouse motion
     - Set: as 1000, and the terminal also reports every move of the
       mouse. See `Mouse Reports`_.
   * - 1004
     - —
     - Focus events
     - Set: on the :doc:`emu` and the :doc:`web`, the terminal reports
       the window gaining and losing the focus. See `Mouse Reports`_.
   * - 1005
     - —
     - UTF-8 mouse reports
     - Set: mouse reports give positions in UTF-8. See `Mouse Reports`_.
   * - 1006
     - —
     - SGR mouse reports
     - Set: mouse reports give positions in decimal. See
       `Mouse Reports`_.
   * - 1007
     - —
     - Alternate scroll
     - Set: on the alternate screen, the mouse wheel sends the up and
       down arrow keys. See `Mouse Reports`_.
   * - 1015
     - —
     - urxvt mouse reports
     - Set: mouse reports give positions in decimal, in the form of
       urxvt. See `Mouse Reports`_.
   * - 1016
     - —
     - SGR pixel mouse reports
     - Set: as 1006, with positions in pixels. See `Mouse Reports`_.
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
       cursor. Most
       full-screen programs use this mode.
   * - 2004
     - —
     - Bracketed paste
     - Set: pasted text arrives between ``ESC [ 200 ~`` and
       ``ESC [ 201 ~``, so a program can tell it from typing. Reset
       (default): a paste arrives as if typed. See `Copy and Paste`_.

Mode Reports
------------

``CSI ? n $ p`` (DECRQM) asks for the state of DEC private mode n, and
``CSI n $ p`` asks for ANSI mode n. The reply is ``ESC [ ? n ; s $ y``
or ``ESC [ n ; s $ y``, where s is 0 for an unknown mode, 1
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
     - 3, permanently set.
   * - ?2 (DECANM)
     - 1, ANSI mode. In VT52 mode, there is no reply.
   * - ?3 (DECCOLM)
     - 4, permanently reset, on the 80-column terminal, and 0 on the
       40-column terminal.
   * - ?1, ?4, ?5, ?6, ?7, ?8, ?9, ?25, ?33, ?35, ?40, ?66, ?67, ?69,
       ?1000, ?1001, ?1002, ?1003, ?1005, ?1006, ?1007, ?1015, ?1016,
       ?2004
     - 1 or 2.
   * - ?1004
     - 1 or 2 on the :doc:`emu` and the :doc:`web`. 4, permanently
       reset, on the other machines.
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

``ESC P $ q``, the last characters of a sequence, and ST (DECRQSS) ask
for the current setting of that sequence. The reply is ``ESC P 1 $ r``, the
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
   * - ``ESC P $ q " p ESC \``
     - DECSCL
     - ``n ; 1 " p``, where n is the conformance level, 62 to 64, and
       1 means 7-bit controls. The level is 64 unless DECSCL sets
       another. At level 61, a VT100, the reply is ``61 " p``.
   * - ``ESC P $ q t ESC \``
     - DECSLPP
     - ``n t``, where n is the number of rows.
   * - ``ESC P $ q $ | ESC \``
     - DECSCPP
     - ``n $ |``, where n is the number of columns.
   * - ``ESC P $ q * | ESC \``
     - DECSNLS
     - ``n * |``, where n is the number of rows.
   * - ``ESC P $ q * r ESC \``
     - DECSCS
     - ``; n * r``, where n is the speed, 0 to 11. See `Speed`_.

The SGR reply lists what `SGR Parameters`_ would set, separated by ``;``: 1, 2,
3, the underline (4, or ``4:n`` for another style), 5 or 6, 7, 8, 9, 53, then
the foreground, the background, and the underline color. A foreground or
background in palette entries 0-15 is 30-37, 90-97, 40-47, or 100-107, however
it was set. Any other palette color is ``38:5:n`` for the foreground and
``48:5:n`` for the background. A palette underline color is ``58:5:n``. A
24-bit color is ``38:2::r:g:b``, ``48:2::r:g:b``, or ``58:2::r:g:b``, with the
numbers that set it. A default color is not listed.

This is how a program finds what the terminal can draw without knowing
its name. Neovim sets a curly underline with ``CSI 4:3 m``, asks for
SGR, and uses the underline styles and the underline color when the
reply is ``ESC P 1 $ r 0 ; 4:3 m ESC \``. It finds 24-bit color the
same way.

Presentation State
------------------

A program that moves the cursor or changes its settings can put them back
when it is done. Before the change, the program asks the terminal for the
cursor and its settings and keeps the reply. After the change, the program
sends the reply back, and the cursor and its settings are as they were before.
This is like save cursor (``ESC 7``) and restore cursor (``ESC 8``), except
that the program keeps the saved copy, so it can keep more than one. The tab
stops are saved and put back the same way.

**The cursor.** To save the cursor, the program sends ``CSI 1 $ w``
(DECRQPSR) and reads the reply. The reply is ``ESC P 1 $ u``, ten fields
separated by ``;``, and ``ESC \``. On a terminal that was just reset, the
reply is ``ESC P 1 $ u 1 ; 1 ; 1 ; @ ; @ ; @ ; 0 ; 2 ; @ ; BBBB ESC \``.

To put the cursor back, the program sends the reply with ``t`` in place of
``u`` (DECRSPS). The cursor returns to the row and column in the reply, and
each setting returns to the value in its field. If a field is missing or
holds a value that is not possible, such as a row past the bottom of the
screen, nothing changes.

The reply has these fields:

.. list-table::
   :widths: 6 20 74
   :header-rows: 1

   * - n
     - Field
     - Value
   * - 1
     - Row
     - The cursor's row, counted from the top row, also in origin mode.
   * - 2
     - Column
     - The cursor's column, counted from column 1, also in origin mode.
   * - 3
     - Page
     - 1.
   * - 4
     - Rendition
     - One character: ``@`` (0x40), plus 8 for reverse video, 4 for
       blink, 2 for an underline of any style, and 1 for bold.
   * - 5
     - Protection
     - One character: ``@``, plus 1 while DECSCA 1 protects the
       characters written. See `Protected Areas`_.
   * - 6
     - Flags
     - One character: ``@``, plus 8 for a pending wrap, 4 for a pending
       SS3, 2 for a pending SS2, and 1 for origin mode.
   * - 7
     - GL
     - The number of the set in GL, 0 to 3.
   * - 8
     - GR
     - 2.
   * - 9
     - Sizes
     - ``@``: the sets in G0 to G3 are all of 94 characters.
   * - 10
     - Sets
     - The final bytes of the sets in G0, G1, G2, and G3, with nothing
       between them, as `Character Sets`_ lists them.

**The tab stops.** ``CSI 2 $ w`` replies with DECTABSR:
``ESC P 2 $ u``, the column of each tab stop with ``/`` between them,
and ``ESC \``. With the stops every 8 columns on a screen 80 columns
wide, the reply is ``ESC P 2 $ u 9/17/25/33/41/49/57/65/73 ESC \``.
With no stops, nothing comes between ``u`` and ``ESC \``.

``ESC P 2 $ t``, columns with ``/`` between them, and ``ESC \`` clears
every tab stop and sets one at each column given. A column past the
last column of the screen sets no stop. When the string holds a byte
other than a digit or ``/``, the stops stay as they were.

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

``CSI ? 12 l`` makes the cursor steady and ``CSI ? 12 h`` makes it
blink, with the same shape.

A block cursor shows its cell with the colors reversed. OSC 12 gives the
cursor a color of its own, which fills the block, and OSC 112 takes it
away. See `OSC Sequences`_.

When the window of the :doc:`emu` or the :doc:`web` loses the focus, a
block cursor becomes an outline of the cell, and the cursor stops
blinking until the window has the focus again.

VT52 Mode
---------

``CSI ? 2 l`` puts the terminal in VT52 mode, as on a VT102. In VT52
mode the terminal takes only the escape sequences below, and ``ESC <``
returns it to ANSI mode. Characters and controls work as in ANSI mode,
except that insert mode (IRM) is off until the return to ANSI mode. The
keys send the codes of a VT52, as `Keyboard`_ describes.


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
     - Enter graphics mode: DEC Special Graphics into G0, and G0 in GL.
   * - ESC G
     - Leave graphics mode: US ASCII into G0, and G0 in GL.
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



Keyboard
--------

The keys send what they send in xterm. A key
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
     - DEL, 0x7F. Ctrl-Backspace sends BS, 0x08. With DECBKM
       (``CSI ? 67 h``) set, Backspace sends BS and Ctrl-Backspace
       sends DEL.

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

A modifier is Shift, Alt, or Ctrl held with the key. In the sequence, m is 1,
plus 1 for Shift, 2 for Alt, and 4 for Ctrl. The copy and paste keys of `Copy
and Paste`_ send nothing to the program. The cut keys are ordinary keys to
a program that reads the keyboard itself: Shift-Delete sends its sequence
from this table, and Ctrl-Shift-X sends what Ctrl-X sends.

Three modes change these keys:

- **Cursor key mode** (``CSI ? 1 h``). The arrow keys, Home, and End
  send ``ESC O`` and their letter, such as ``ESC O A``.
- **Autorepeat off** (``CSI ? 8 l``). A key that is held down types
  once.
- **VT52 mode.** The arrow keys, Home, End, and F1 to F4 send ESC and
  their letter, such as ``ESC A`` and ``ESC P``.

The keypad follows NumLock, and Shift with NumLock on acts as NumLock
off. A program sets the application keypad with ``ESC =`` and leaves it
with ``ESC >``. The `line editor <Line Editor_>`_ leaves the keys of the
application keypad to the program, Enter included, so they type nothing
in a line.

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

F1 to F4 are the VT100's PF1 to PF4. In VT52 mode, the application
keypad sends ``ESC ?`` and the letter, such as ``ESC ? p``.

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
``A``, 13 for Enter, 9 for Tab, 27 for Escape, and 127 for Backspace,
or 8 with DECBKM set.

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
     - Set formatOtherKeys. The keys send ``ESC [ code ; m u`` in place
       of the longer sequence.
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
- **Level 2.** Every key with a modifier sends the sequence. Shift with a
  letter counts, so Shift-A sends ``ESC [ 27 ; 2 ; 65 ~``. Alt is part of the
  sequence, and no ESC comes first. A character that only Shift makes, such as
  ``!``, is typed as it is, but Shift-Space sends the sequence. Ctrl-Backspace
  still sends one byte: BS, or DEL with DECBKM set.
- **Level 3.** Every key sends the sequence, modified or not, with m
  as 1 for no modifier.

The cursor keys, the function keys, the editing keys, and the keypad
send what they always do at every level. VT52 mode has no modified keys.

The `line editor <Line Editor_>`_ reads each sequence as the key it
stands for, so its keys work the same at every level.

.. _term-copy-paste:

Copy and Paste
--------------

The mouse selects text on the VGA terminal. Drag with the left button to
select characters, double-click to select a word, or triple-click to
select a line. The middle button pastes the selected text. These keys
copy and paste with the clipboard:

.. list-table::
   :widths: 45 55
   :header-rows: 1

   * - Keys
     - Action
   * - Ctrl-Shift-C, Ctrl-Insert
     - Copy the selected text.
   * - Ctrl-Shift-X, Shift-Delete
     - Cut the selected text of the `line editor <Line Editor_>`_.
   * - Ctrl-Shift-V, Shift-Insert
     - Paste.

On the desktop :doc:`emu` and the :doc:`web`, the clipboard is the
clipboard of the computer, and Cmd-C, Cmd-X, and Cmd-V also work on a
Mac. While a program reads the mouse, hold Shift to select text.

Mouse Reports
-------------

A program can read the mouse of the VGA terminal as xterm reports it.
The reports arrive as typed input. Set one of these modes to choose what
is reported:

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Mode
     - Reports
   * - 9
     - Each press of the left, middle, or right button.
   * - 1000
     - Each press and release of a button, and each turn of the wheel.
   * - 1001
     - As 1000, with highlight tracking, described below.
   * - 1002
     - As 1000, and each move of the mouse while a button is down.
   * - 1003
     - As 1000, and each move of the mouse.

Setting one of these modes turns the others off, and resetting it turns
the reports off.

A report gives a button and a position, with column 1 and row 1 at the top
left. It is ``ESC [ M`` and three bytes: the button plus 32, the column plus
32, and the row plus 32. Set one of these modes for a report in another form:

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Mode
     - Report
   * - 1005
     - The same, but a button of 96 or more, such as the back and
       forward buttons, is two bytes of UTF-8.
   * - 1006
     - ``ESC [ <`` button ``;`` column ``;`` row, then ``M`` for a press
       or a move, or ``m`` for a release.
   * - 1015
     - ``ESC [`` button plus 32 ``;`` column ``;`` row ``M``.
   * - 1016
     - The same as 1006, with the position in pixels, from 1.

The button is 0 for the left, 1 for the middle, and 2 for the right, 64
and 65 for the wheel turned up and down, 66 and 67 for the wheel tilted
left and right, and 128 and 129 for the back and forward buttons. A
release is button 3, except with modes 1006 and 1016, which end a
release with ``m``. A move adds 32 to the button. Alt adds 8, and Ctrl
adds 16, except in mode 9. A click with Shift is never reported, because
Shift selects text.

**Highlight tracking.** With mode 1001, a program chooses what a drag
with the left button highlights. After the terminal reports the press,
it waits for the program to answer with this sequence:

``ESC [ 1 ; column ; row ; first ; last T``

The highlight then starts at that column and row and follows the
pointer, from row ``first`` up to, but not including, row ``last``. An
answer of ``ESC [ 0 T`` makes the press an ordinary one.

When the button comes up, the terminal reports the highlight, with each
position in the form that the modes above choose:

- ``ESC [ t``, the column, and the row where the highlight ends, when it
  starts where the answer put it and ends at the pointer.
- Otherwise ``ESC [ T`` and the column and row of the start of the
  highlight, of its end, and of the pointer.

**Focus.** With mode 1004 set, the terminal sends ``ESC [ I`` when the
window of the :doc:`emu` or the :doc:`web` gains the focus, and
``ESC [ O`` when it loses it.

**Wheel scrolling.** With mode 1007 set and no mouse mode, the wheel
sends the up and down arrow keys while the alternate screen shows, five
for each notch. A pager or another full-screen program then scrolls with
the wheel.

DEC Locator
-----------

A program can also read the mouse of the VGA terminal as the locator of
a DEC terminal, as in xterm. The reports arrive as typed input. Turning
the locator on turns the mouse modes of `Mouse Reports`_ off, and setting
one of those modes turns the locator off.

.. list-table::
   :widths: 22 10 25 43
   :header-rows: 1

   * - Code
     - Abbr
     - Name
     - Effect
   * - CSI Ps ; Pu ' z
     - DECELR
     - Enable Locator Reports
     - Ps 1 turns the locator on, Ps 2 turns it on for one report, and Ps 0
       turns it and the mouse modes off. Pu 1 gives positions in pixels, and
       any other Pu in characters.
   * - CSI Ps ; ... ' {
     - DECSLE
     - Select Locator Events
     - Each Ps chooses: 1 reports a button going down, 2 does not, 3
       reports a button coming up, 4 does not, and 0 reports neither.
       The locator starts with neither.
   * - CSI ' |
     - DECRQLP
     - Request Locator Position
     - Report where the locator is now.
   * - CSI Pt ; Pl ; Pb ; Pr ' w
     - DECEFR
     - Enable Filter Rectangle
     - Report once when the locator leaves the rectangle from row Pt to
       row Pb and from column Pl to column Pr, in the units of DECELR.
       An edge that is left out or 0 is where the locator is now.

A report is ``ESC [ event ; buttons ; row ; column & w``. The row and
the column count from 1 at the top left. The buttons are the ones held
after the event, added together: 1 for the right, 2 for the middle, 4
for the left, and 8 for the back button.

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Event
     - Meaning
   * - 0
     - The locator is not over the VGA terminal. The report is
       ``ESC [ 0 & w`` alone.
   * - 1
     - The answer to DECRQLP.
   * - 2, 3
     - The left button went down, or came up.
   * - 4, 5
     - The middle button went down, or came up.
   * - 6, 7
     - The right button went down, or came up.
   * - 8, 9
     - The back button went down, or came up.
   * - 10
     - The locator left the filter rectangle.

SGR Parameters
--------------

Send multiple parameters separated by ``;``. ``CSI m`` with no
parameters is the same as SGR 0.

The default foreground and background colors are separate from the 256-color
palette. They start as the white of palette entry 7 and the black of entry 0.
SGR 39 and 49 select them, and OSC 10 and 11 change them. Palette entry 0 and
the default background start transparent, so a plane behind the terminal shows
through. A color that OSC 4 or OSC 11 sets is opaque.

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
     - Characters below 0x80 show in italics on the 80-column
       terminal.
   * - 4
     - Underline
     - A single underline. ``4:n`` (kitty) selects a style: ``4:0``
       none, ``4:1`` single, ``4:2`` double, ``4:3`` curly, ``4:4``
       dotted, and ``4:5`` dashed. SGR 58 gives it a color of its own.
   * - 5
     - Blink (slow)
     - Blinks foreground. With iCE colors (mode 33) set, also brightens
       the background. With mode 35 set, it does not blink.
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
     - —
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

- ``38;5;n`` or ``38:5:n``: palette entry n, 0-255.
- ``38;2;r;g;b``, ``38:2:r:g:b``, or ``38:2::r:g:b``: a 24-bit color.


OSC Sequences
-------------

An OSC sequence starts with ``ESC ]`` and ends with BEL (``0x07``) or
ST (``ESC \``). It holds a command number and items, separated by
``;``.

A color is an X11 color spec: ``#rgb``, ``#rrggbb``, ``#rrrgggbbb``,
``#rrrrggggbbbb``, or ``rgb:r/g/b`` with 1 to 4 hex digits per channel.


A ``?`` in place of a color asks what the color is. The reply is the
OSC that sets that one color, with the color as ``rgb:rrrr/gggg/bbbb``,
ended the way the question was ended, with BEL or ST. So
``OSC 10 ; ? ; ? ST`` replies ``OSC 10 ; rgb:... ST`` and
``OSC 11 ; rgb:... ST``. The terminal keeps 16-bit color, 5 bits for
each of red, green and blue, so it drops the low 3 bits of each 8-bit
channel it is given, and the reply gives back the 5 bits it kept. One OSC
can ask for up to 6 colors.

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
   * - OSC 17 ; color ST
     - Set the background color of the selection.
   * - OSC 19 ; color ST
     - Set the text color of the selection.
   * - OSC 110 ST
     - Reset the default foreground color.
   * - OSC 111 ST
     - Reset the default background color.
   * - OSC 112 ST
     - Reset the cursor color.
   * - OSC 117 ST
     - Reset the background color of the selection.
   * - OSC 119 ST
     - Reset the text color of the selection.



Speed
-----

Some ANSI art and animation was made to play as it arrived over a modem.
``CSI 0 ; Ps * r`` (DECSCS) slows the output of the console to the speed
of a modem, so that it plays as it was made to. Ps is the speed:

.. list-table::
   :widths: 15 55 30
   :header-rows: 1

   * - Ps
     - Speed in bits per second
     - DECREQTPARM
   * - 0 or empty
     - Full speed, the default.
     - 128
   * - 1
     - 300
     - 48
   * - 2
     - 600
     - 56
   * - 3
     - 1200
     - 64
   * - 4
     - 2400
     - 88
   * - 5
     - 4800
     - 104
   * - 6
     - 9600
     - 112
   * - 7
     - 19200
     - 120
   * - 8
     - 38400
     - 128
   * - 9
     - 57600
     - 128
   * - 10
     - 76800
     - 128
   * - 11
     - 115200, the same as full speed.
     - 128

At 300 bits per second, the console shows 30 characters a second. The
new speed starts with the character after the sequence.

The DECREQTPARM column is the number the reply to ``CSI x`` gives for the
speed, as a VT100 numbers speeds. The VT100 has no number above 38400, so
the reply gives 128 for the faster speeds and for full speed.

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
     - The same as RIS.
   * - CSI ! p
     - DECSTR
     - Soft Terminal Reset
     - Soft reset. See below.
   * - CSI Pl ; Pc " p
     - DECSCL
     - Select Conformance Level
     - Set the conformance level to Pl, and do a DECSTR.

**RIS** clears both screens and puts every mode and setting of the
terminal back to its default, except mode 40, which it leaves as it is.
The conformance level goes back to 64.

**DECSTR** turns insert mode,
origin mode, and cursor key mode off, sets the numeric keypad, turns
autowrap on, shows the cursor, puts US ASCII in G0 to G3 with G0 in GL,
and resets SGR, character protection, the scroll region, the left and
right margins and mode 69, and the saved cursor of each screen. The
cursor does not move.

**DECSCL** sets the conformance level: 61 for a VT100, 62 for a VT220,
63 for a VT320, or 64 for a VT420. Then it does a DECSTR. The terminal
acts as a VT420 at every level. The level changes only what DECRQSS
reports for ``" p``. The terminal always sends 7-bit controls.

**A change of the code page** through :ref:`RIA_ATTR_CODE_PAGE
<api-ria-attributes>` does a RIS of the VGA terminal. When a program that
changed the code page stops, the system puts the code page back, with
the same RIS.

**When a program stops**, the system resets the VGA terminal as RIS
does, but leaves the text on the screen and the cursor where it is.
