==================================
RP6502-TERM
==================================

Manifold Console
================

In the RP6502 vocabulary, a **terminal** is any device a user types into
and reads from. The **console** is the main terminal — the one connected
to ``stdin``, ``stdout``, ``stderr``, ``CON:``, and ``TTY:``. The
**monitor** is the system program that runs on the console to assist
with configuration and ROM loading.

The console is not tied to a single physical device. Multiple terminals
can be attached at once and fanned in to one console; this is the
**console manifold**. There are three ways to attach a terminal:

* **VGA and USB keyboard.** In the standard configuration with a
  :doc:`vga` module, the console is accessed with a VGA monitor and a
  USB keyboard plugged into the RIA module.
* **USB CDC ACM.** Connect the USB port on the VGA module to a computer
  and access the console over the USB CDC ACM serial port that appears.
  No driver is needed.
* **Telnet.** The :doc:`ria_w` exposes the console over the network. See
  `Telnet Console <ria_w.html#telnet-console>`__ for setup.

Any terminal attached to the console manifold can be used for software
development and scripting. This is powerful and convenient, but has
limits when software requests the terminal respond with information.

Size and Feature Detection
--------------------------

The monitor, and some ROMs like MS-BASIC, send ANSI commands that
terminals respond to. This is used for screen size and feature
detection. At the start of every cooked stdin read, the active terminal
is queried for this information using the Cursor Position Report (CPR)
sequence.

The built-in VGA terminal stops responding to these queries if a telnet
or USB terminal is connected, so the external terminal wins. **If both
USB and telnet terminals are connected at the same time and both reply,
the system may get confused.** If pagination or word-wrap seem wrong,
check what terminals are attached to the console manifold.

The monitor word-wraps and column-fits its output — listings, help
text, status responses, settings, the timezone selector — to the
detected width. ROMs that use cooked stdin and read the size get the
same information.

Locking the Size
----------------

A ROM can pin a fixed terminal size by writing non-zero values to
`RIA_ATTR_RLN_WIDTH and RIA_ATTR_RLN_HEIGHT <os.html#ria-attributes>`__.
With both axes pinned, the auto-detect handshake is skipped entirely.
Writing 0 returns the channel to auto-detect, and both attributes revert
to 0 when the ROM stops.


Read Line
=========

A **cooked** read returns a complete line. The user has edited freely
with backspace, arrow keys, and optionally command completion and history;
the editor flushes the line
when Enter is pressed. A **raw** read returns bytes as they arrive,
keystroke by keystroke, with no echo and no editing. The OS implements
cooked input with the line editor in ``rln.c``.

Reading ``stdin`` is cooked but blocks until the user presses Enter.
Two alternate file paths offer non-blocking variants of the same channels:

* ``CON:`` — non-blocking cooked input. ``read()`` returns 0 while the
  user is still editing and returns the full newline-terminated line
  once the editor flushes.
* ``TTY:`` — non-blocking raw input. ``read()`` returns whatever bytes
  are queued, with no editing applied.

Non-blocking Read Line
----------------------

A non-blocking cooked read is more than just a prompt that doesn't
stall. Between the activating read and the line flush, the application
can inspect and modify the editor's state. That is what makes features
like history recall, tab completion, and multi-field form navigation
possible. The hooks are `RLN_LASTKEY <os.html#rln-lastkey>`__,
`RLN_PEEK <os.html#rln-peek>`__, and `RLN_POKE <os.html#rln-poke>`__.

The basic pattern:

#. **Open the channel.** ``open("CON:", 0)`` returns a file descriptor.
#. **Set the input cap** (optional): write ``RIA_ATTR_RLN_LENGTH``.
   Different prompts — or different fields in a form — can use
   different caps. The default is 254.
#. **Pin the terminal size** (optional): write ``RIA_ATTR_RLN_WIDTH``
   and ``RIA_ATTR_RLN_HEIGHT`` when the layout is built for a fixed
   canvas. See `Locking the Size`_.
#. **Loop on ``read()``** until the line flushes.

   * The first call always returns 0 and activates the editor at the
     current cursor position and SGR state. Position the cursor *before*
     this read.
   * A non-zero return means the line is complete. Pull it whole with a
     buffer at least ``RIA_ATTR_RLN_LENGTH`` bytes long, or drain it in
     fragments until you see the newline.
   * On the first pass after activation, call ``ria_rln_poke()`` to
     pre-load any text you want to appear in the line. The poked bytes
     are echoed by the editor as if the user had typed them.
   * Check for Ctrl-C via ``RIA_ATTR_SIGINT`` or the RIA SIGINT IRQ.
     To leave cooked input cleanly, poke ``\x03`` to print a visible
     ``^C`` and flush, or poke ``\r`` to flush silently.
   * ``ria_rln_lastkey()`` reports the last keystroke and whether the
     editor consumed it as an editing action. When ``action == 0`` the
     editor passed the key through — that is the application's chance
     to handle Tab, function keys, arrow keys for history or form
     navigation, and any other keys it wants to claim. Respond by
     poking literal characters or ANSI sequences (``CUF``, ``CUB``,
     ``ICH``, ``DCH``) back into the editor as if the user had typed
     them.

Anything you can do by typing, you can do by poking. To pull the buffer
out without the user pressing Enter — for example, when Tab should jump
to the next field of a form — poke ``\r``. The editor flushes through
``read()`` like any other line, and the application can move on,
re-entering the next field with a fresh ``ria_rln_poke()`` to restore
its prior contents.


Terminal
========

The RP6502 :doc:`vga` module includes a color terminal that attaches to
the console manifold. It implements the Linux console subset of
ECMA-48 / VT102 with xterm-color extensions. The terminal does not
require flow control to keep up with 115200 bps.

Compatibility and Limits
------------------------

* Self-identifies as VT102 in response to Primary DA
  (``CSI c`` → ``ESC[?6c``).
* Implements the subset documented in ``man 4 console_codes``
  (Linux console).
* xterm extensions supported: 256-color and truecolor SGR
  (38 / 48 / 58 sub-args); dynamic colors via OSC 10 / 11 / 12;
  alternate screen buffer (``?47`` / ``?1047`` / ``?1049``).
* 8-bit codepage encoding only — no UTF-8 decode.

Behavior Notes
--------------

**Blink and iCE colors.** SGR 5 / 6 (blink) sets the blink
attribute and the renderer pulses the cell foreground at a fixed
rate. The legacy ANSI.SYS / IBM-VGA behavior — where SGR 5 / 6
brightens the background instead of blinking — is preserved as
opt-in via ``CSI ?33h`` (iCE colors). This is the standard
ANSI-art compatibility mode; off by default. Toggle off with
``CSI ?33l``.

**Alternate screen buffer.** ``?47`` swaps only. ``?1047`` swaps
and clears the alt buffer on exit. ``?1049`` is the modern app
default — saves the cursor on entry, swaps, clears on entry, and
restores the cursor on exit.

**DEC Special Graphics.** A built-in line-drawing font (boxes,
dashes, arrows) for borders and ASCII-art frames without UTF-8.
See `Charset Designation`_.

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
with the DEC line-drawing characters (boxes, dashes, arrows)
without an escape sequence per character — load the line-drawing
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

CSI sequences default missing numbers to 0. Some functions
(cursor movement) treat 0 as 1 to remain useful without parameters.

CSI — Cursor Movement
---------------------

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
    - Set: SGR 5 / 6 brightens background (IBM-VGA quirk).
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
    - Accepted; no italic font, never rendered.
  * - 4
    - Underline
    - —
  * - 5
    - Blink (slow)
    - Blinks foreground. With iCE colors mode (``?33h``) set
      instead, brightens the background — the IBM-VGA / ANSI.SYS
      quirk.
  * - 6
    - Blink (rapid)
    - Aliased to 5 (one phase rate).
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
    - No-op (3 is also no-op).
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
    - Sub-args parsed (same form as 38) and discarded — not
      rendered.
  * - 90-97
    - Bright foreground
    - Colors 8-15.
  * - 100-107
    - Bright background
    - Colors 8-15.

OSC Sequences
-------------

Operating System Command sequences set dynamic terminal colors.
The color argument must be ``#rrggbb``; other xterm spellings
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
