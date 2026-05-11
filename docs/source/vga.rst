==================================
RP6502-VGA
==================================

RP6502 - Video Graphics Array

Introduction
=============

The RP6502 Video Graphics Array is a Raspberry Pi Pico 2 with
RP6502-VGA firmware. Its primary data connection is to a :doc:`ria`
over a 5-wire PIX bus. More than one VGA module can be put on a PIX
bus. Note that all VGA modules share the same 64K of XRAM and only
the first one will generate frame numbers and vsync interrupts.

Video Programming
==================

The VGA system provides virtual video hardware modeled on home
computers and arcades of the 8-bit and early 16-bit era. Adding new
video modes and sprite systems is straightforward. Application
programmers can mix and match these modes freely.

The VGA system is built around a modifed scanvideo library from Pi
Pico Extras. All three planes are enabled with RGB555 color plus
transparency. The mode 4 sprite system is from Pi Pico Playground.
The scanline programming system and all other modes are original
work for the RP6502.

The RP6502 VGA system exposes per-scanline configuration of the
video system to your 6502 application. At the broadest scope we
have three planes. Each plane has two layers, a fill layer and a
sprite layer. Your application can assign different fill and
sprite modes to specific planes and scanlines. There's plenty of
fill rate to exceed the capabilities of any classic 8-bit system,
but if you like to push the limits then you may see a half-blue
screen indicating you went too far.

The built-in 8x8 and 8x16 fonts are available via the special
XRAM pointer $FFFF. Glyphs 0-127 are ASCII; glyphs 128-255 vary
by code page.

Access the built-in color palettes via the special XRAM pointer
$FFFF. 1-bit is black and white. 4-bit and 8-bit modes point to an
ANSI palette of 16 colors, followed by 216 colors (6x6x6), followed
by 24 greys.

16-bit colors are built with the following bit logic. Setting the
alpha bit makes the color opaque; clearing it makes the color
transparent. Despite the name, this is a binary flag, not a
blending factor. The built-in ANSI color palette has the alpha bit
set on all colors except color 0 (black), which is transparent.

.. code-block:: C

  #define COLOR_FROM_RGB8(r,g,b) (((b>>3)<<11)|((g>>3)<<6)|(r>>3))
  #define COLOR_FROM_RGB5(r,g,b) ((b<<11)|(g<<6)|(r))
  #define COLOR_ALPHA_MASK (1u<<5)

Palette information is an array. 8bpp, 4bpp, and 1bpp modes use a
palette. 16 bit per pixel modes don't use indexed color and will
ignore the palette. Palettes must be 16-bit aligned.

.. code-block:: C

  struct {
      uint16_t color;
  } palette[2^bits_per_pixel];


Programming the VGA device is done with `PIX extended registers
<ria.html#pix-extended-registers-xreg>`__ -
XREGS. VGA is PIX device ID 1. Registers are 16 bit values addressed
by $device:$channel:register. e.g. $1:0:0F

.. code-block:: C

    // Select a 320x240 canvas
    result = xreg(1, 0, 0, 1); // or
    result = xreg_vga_canvas(1);
    // Program mode 3 for 4 bit color with
    // its config registers at XRAM $FF00.
    result = xreg(1, 0, 1, 3, 2, 0xFF00); // or
    result = xreg_vga_mode(3, 2, 0xFF00);

Key Registers
-------------

Setting key registers may return a failure (-1) with errno EINVAL.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:0:00
    - CANVAS
    - Select a graphics canvas. This clears $1:0:02-$1:0:FF and all
      scanline programming. The 80 column console canvas is used as
      a failsafe and therefore not scanline programmable.

      * 0 - 80 column console. (4:3 or 5:4)
      * 1 - 320x240 (4:3)
      * 2 - 320x180 (16:9)
      * 3 - 640x480 (4:3)
      * 4 - 640x360 (16:9)

  * - $1:0:01
    - MODE
    - Program a mode into a plane of scanlines.
      $1:0:02-$1:0:FF cleared after programming. Each mode has a
      section of this document for its own registers.

      * 0 - `Console <#mode-0-console>`__
      * 1 - `Character <#mode-1-character>`__
      * 2 - `Tile <#mode-2-tile>`__
      * 3 - `Bitmap <#mode-3-bitmap>`__
      * 4 - `Sprite 16-bit <#mode-4-sprite>`__
      * 5 - `Sprite 1,2,4,8-bit <#mode-5-sprite>`__


Mode 0: Console
---------------

The console may be rendered on any canvas plane. ANSI color 0-black
is transparent, which makes it easy to show text over a background
image using planes. The console may be a partial screen, but the
scanlines must be a multiple of the font height. 640 pixel wide
canvases use an 8x16 font for 80 columns. 320 pixel wide canvases
use an 8x8 font for 40 columns. Only one console may be visible,
programming again will remove the previous console.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:0:01
    - MODE
    - 0 - Console
  * - $1:0:02
    - PLANE
    - 0-2 to select which fill plane of scanlines to program.
  * - $1:0:03
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:04
    - END
    - End of scanlines to program. 0 means use canvas height (180-480).


Mode 1: Character
-----------------

Character modes have color information for each position on the
screen. This is the mode you want for showing text in different
colors.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:0:01
    - MODE
    - 1 - Character
  * - $1:0:02
    - OPTIONS
    - | bit 3 - font size 0=8x8, 1=8x16
      | bit 2:0 - 0=1, 1=4r, 2=4, 3=8, or 4=16 bit color
  * - $1:0:03
    - CONFIG
    - Address of config structure in XRAM.
  * - $1:0:04
    - PLANE
    - 0-2 to select which fill plane of scanlines to program.
  * - $1:0:05
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:06
    - END
    - End of scanlines to program. 0 means use canvas height
      (180-480).

Config structure may be updated without reprogramming scanlines.

.. code-block:: C

  typedef struct {
      bool x_wrap;
      bool y_wrap;
      int16_t x_px;
      int16_t y_px;
      int16_t width_chars;
      int16_t height_chars;
      uint16_t data_ptr;
      uint16_t palette_ptr;
      uint16_t font_ptr;
  } vga_mode1_config_t;

Data is encoded based on the color bit depth selected.

.. code-block:: C

  // 2-color, 1-bit
  struct {
      uint8_t glyph_code;
  } data[width_chars * height_chars];

.. code-block:: C

  // 16-color reversed index, 4-bit
  struct {
      uint8_t glyph_code;
      uint8_t fg_bg_index;
  } data[width_chars * height_chars];

.. code-block:: C

  // 16-color, 4-bit
  struct {
      uint8_t glyph_code;
      uint8_t bg_fg_index;
  } data[width_chars * height_chars];

.. code-block:: C

  // 256-color, 8-bit
  struct {
      uint8_t glyph_code;
      uint8_t fg_index;
      uint8_t bg_index;
  } data[width_chars * height_chars];

.. code-block:: C

  // 32768-color, 16-bit (no palette)
  struct {
      uint8_t glyph_code;
      uint8_t attributes; // user defined, ignored by VGA
      uint16_t fg_color;
      uint16_t bg_color;
  } data[width_chars * height_chars];

Fonts are encoded in wide format. The first 256 bytes are the first
row of each of the 256 glyphs.

.. code-block:: C

  struct {
    struct {
        uint8_t col[256];
    } row[height];
  } font;


Mode 2: Tile
------------

Tile modes have color information encoded in the tile bitmap. This is
the mode you want for showing a video game playfield.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:0:01
    - MODE
    - 2 - Tile
  * - $1:0:02
    - OPTIONS
    - | bit 3 - 0=8x8, 1=16x16
      | bit 2:0 - 0=1, 1=2, 2=4, or 3=8 bit color
  * - $1:0:03
    - CONFIG
    - Address of config structure in XRAM.
  * - $1:0:04
    - PLANE
    - 0-2 to select which fill plane of scanlines to program.
  * - $1:0:05
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:06
    - END
    - End of scanlines to program. 0 means use canvas height
      (180-480).

Config structure may be updated without reprogramming scanlines.

.. code-block:: C

  typedef struct {
      bool x_wrap;
      bool y_wrap;
      int16_t x_px;
      int16_t y_px;
      int16_t width_tiles;
      int16_t height_tiles;
      uint16_t data_ptr;
      uint16_t palette_ptr;
      uint16_t tile_ptr;
  } vga_mode2_config_t;

Data is a matrix of tile ids with 0,0 at the top left.

.. code-block:: C

  struct {
      uint8_t tile_id;
  } data[width_tiles * height_tiles];

Tiles are encoded in "tall" bitmap format.

.. code-block:: C

  // 8x8 tiles
  struct {
      struct {
          uint8_t cols[bpp];
      } rows[8];
  } tile[up_to_256];

  // 16x16 tiles
  struct {
      struct {
          uint8_t cols[2*bpp];
      } rows[16];
  } tile[up_to_256];


Mode 3: Bitmap
--------------

Every pixel can be its own color. 64K XRAM limits the full screen
color depth. Monochrome at 640x480, 16 colors at 320x240, 256 colors
for 320x180 (16:9).

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:0:01
    - MODE
    - 3 - Bitmap
  * - $1:0:02
    - OPTIONS
    - | bit 3 - reverse bit order
      | bit 2:0 - 0=1, 1=2, 2=4, 3=8, or 4=16 bit color
  * - $1:0:03
    - CONFIG
    - Address of config structure in XRAM.
  * - $1:0:04
    - PLANE
    - 0-2 to select which fill plane of scanlines to program.
  * - $1:0:05
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:06
    - END
    - End of scanlines to program. 0 means use canvas height
      (180-480).

Config structure may be updated without reprogramming scanlines.

.. code-block:: C

  typedef struct {
      bool x_wrap;
      bool y_wrap;
      int16_t x_px;
      int16_t y_px;
      int16_t width_px;
      int16_t height_px;
      uint16_t data_ptr;
      uint16_t palette_ptr;
  } vga_mode3_config_t;

Data is the color information packed down to the bit level. 16-bit
color encodes the color directly as data. 1, 4, and 8 bit color
encodes a palette index as data.

Bit order is traditionally done so that left and right bit shift
operations match pixel movement on screen. The reverse bits option
change the bit order of 1 and 4 bit modes so bit-level manipulation
code is slightly faster and smaller.

Data for 16 bit color must be 16 bit aligned.

.. code-block:: C

  struct {
      struct {
          uint8_t cols[(width_px * bit_depth + 7) / 8];
      } rows[height_px];
  } data;


Mode 4: Sprite 16-bit
---------------------

Sprites may be drawn over each fill plane. This is the 16-bit sprite
system from the Pi Pico Playground. Lower bit depths are available in
mode 5. The large memory requirements are offset by its ability to do
affine transforms.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:0:01
    - MODE
    - 4 - Sprite
  * - $1:0:02
    - OPTIONS
    - | bit 0 - affine
  * - $1:0:03
    - CONFIG
    - | Address of config array in XRAM.
  * - $1:0:04
    - LENGTH
    - Length of config array in XRAM.
  * - $1:0:05
    - PLANE
    - 0-2 to select which sprite plane of scanlines to program.
  * - $1:0:06
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:07
    - END
    - End of scanlines to program. 0 means use canvas height
      (180-480).

Unused sprites should be moved off screen. Non-affine sprites use this
config structure.

.. code-block:: C

  typedef struct {
    int16_t x_pos_px;
    int16_t y_pos_px;
    uint16_t xram_sprite_ptr;
    uint8_t log_size;
    bool has_opacity_metadata;
  } vga_mode4_sprite_t;

Affine sprites apply a 3x3 matrix transform. These are slower than
plain sprites. Only the first two rows of the matrix are useful, which
is why there are only six transform values. These are in signed 8.8
fixed point format.

.. code-block:: C

  typedef struct {
    int16_t transform[6];
    int16_t x_pos_px;
    int16_t y_pos_px;
    uint16_t xram_sprite_ptr;
    uint8_t log_size;
    bool has_opacity_metadata;
  } vga_mode4_asprite_t;


Sprite image data is an array of 16 bit colors.

.. code-block:: C

  struct {
    struct {
        uint16_t color[2^log_size];
    } rows[2^log_size];
  } data;


Mode 5: Sprite 1,2,4,8-bit
--------------------------

This is a memory efficient sprite system using palettes to reduce the bit
depth. Sprites may be drawn over each fill plane. Even if you have a null
fill plane, sprites may be drawn there. That means you can put, for example,
affine sprites for explosions and the player on one plane, 16x16 4bpp enemy
sprites on a second, and 8x8 1bpp bullets on the last.


.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:0:01
    - MODE
    - 5 - Sprite
  * - $1:0:02
    - OPTIONS
    - | bit 5:3 - 0=8x8, 1=16x16, 2=32x32, 3=64x64, 4=128x128, 5=256x256, 6=512x512
      | bit 2:0 - 0=1, 1=2, 2=4, or 3=8 bit color
      | 512x512 only supports 1-bit and 2-bit color.
  * - $1:0:03
    - CONFIG
    - | Address of config array in XRAM.
  * - $1:0:04
    - LENGTH
    - Length of config array in XRAM.
  * - $1:0:05
    - PLANE
    - 0-2 to select which sprite plane of scanlines to program.
  * - $1:0:06
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:07
    - END
    - End of scanlines to program. 0 means use canvas height
      (180-480).

Unused sprites are disabled by moving off screen.

.. code-block:: C

  typedef struct {
    int16_t x_pos_px;
    int16_t y_pos_px;
    uint16_t xram_sprite_ptr;
    uint16_t palette_ptr;
  } vga_mode5_sprite_t;

Sprite image data is the same format as individual mode 2 tiles.

.. code-block:: C

  // 8x8 tiles
  struct {
      struct {
          uint8_t cols[bpp];
      } rows[8];
  } data;

  // 16x16 tiles
  struct {
      struct {
          uint8_t cols[2*bpp];
      } rows[16];
  } data;

  // NxN tiles
  struct {
      struct {
          uint8_t cols[N/8*bpp];
      } rows[N];
  } data;


Terminal
========

The RP6502 VGA system includes a color terminal attached as the
console. It implements the Linux console subset of ECMA-48 / VT102
with xterm-color extensions. The terminal does not require flow
control to keep up with 115200 bps.

Compatibility and Limits
------------------------

* Self-identifies as VT102 in response to Primary DA
  (``CSI c`` → ``ESC[?6c``).
* Implements the subset documented in ``man 4 console_codes``
  (Linux console).
* xterm extensions supported: 256-color and truecolor SGR
  (38 / 48 / 58 sub-args); dynamic colors via OSC 10 / 11 / 12;
  alternate screen buffer (``?47`` / ``?1047`` / ``?1049``);
  bracketed paste (``?2004``).
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

**REP** (``CSI n b``). Repeats the last printed character n times.
Most C0 controls (BS, HT, LF, FF, CR, SO, SI) break the REP chain;
NUL, BEL, and ESC do not.

**Cursor style** (DECSCUSR). Accepted and stored, but the
software block-invert cursor does not yet render the chosen shape.

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
  :widths: 12 8 25 55
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
  * - ESC ( c
    - —
    - Load primary charset
    - Load a font into the G0 slot. See `Charset Designation`_.
  * - ESC ) c
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
  :widths: 12 12 76
  :header-rows: 1

  * - Sequence
    - Byte
    - Font loaded
  * - ``ESC ( c``
    - ``B``
    - US ASCII (default) into G0.
  * - ``ESC ( c``
    - ``0``
    - DEC Special Graphics into G0.
  * - ``ESC ) c``
    - ``B``
    - US ASCII (default) into G1.
  * - ``ESC ) c``
    - ``0``
    - DEC Special Graphics into G1.

Any other byte after ``ESC (`` or ``ESC )`` is silently consumed.

**Switch the active slot.** Send one byte:

.. list-table::
  :widths: 12 88
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
  :widths: 15 8 25 52
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
  :widths: 12 8 25 55
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
  * - CSI n b
    - REP
    - Repeat
    - Repeat the last printed character n times.

CSI — Erase
-----------

.. list-table::
  :widths: 10 5 20 65
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
      - 3: xterm erase-scrollback — no-op (no scrollback buffer).
  * - CSI n K
    - EL
    - Erase in Line
    - - 0: From cursor to end of line.
      - 1: From beginning of line to cursor.
      - 2: Entire line.

CSI — Scrolling and Margins
---------------------------

.. list-table::
  :widths: 15 10 25 50
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
  :widths: 10 8 20 62
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
  :widths: 12 8 25 55
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
  :widths: 14 8 22 56
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
      5 / 6 = bar. Stored; the software cursor does not yet render
      the chosen shape.

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
  * - 1
    - DECCKM
    - Application Cursor Keys
    - Stored; read by the input layer.
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
  * - 2004
    - —
    - Bracketed paste
    - Stored; read by the input layer.

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
  :widths: 25 75
  :header-rows: 1

  * - Code
    - Effect
  * - OSC 10 ; #rrggbb ST
    - Set default foreground color.
  * - OSC 11 ; #rrggbb ST
    - Set default background color.
  * - OSC 12 ; #rrggbb ST
    - Set cursor color. Painted behind the glyph at the cursor
      position; the glyph keeps its own color.
  * - OSC 110 ST
    - Reset default foreground color.
  * - OSC 111 ST
    - Reset default background color.
  * - OSC 112 ST
    - Reset cursor color.

Pre-Launch Soft Reset
---------------------

The OS ensures this sequence is sent before launching a ROM. Screen
contents are preserved but all out state is reset.

.. code-block::

  \30\33[?1049l\33[!p\33[3g\33]110\7\33]111\7\33]112\7

Control Channel $F
==================

The RIA manages these registers. 6502 applications will be denied
access to sending these if a VGA module is connected.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:F:00
    - DISPLAY
    - This sets the aspect ratio of your display. This also resets
      CANVAS to the console.

      * 0 - VGA (4:3) 640x480
      * 1 - HD (16:9) 640x480 and 1280x720
      * 2 - SXGA (5:4) 1280x1024

  * - $1:F:01
    - CODE_PAGE
    - Set code page for built-in font. Matches
      `RIA_ATTR_CODE_PAGE <os.html#ria-attributes>`__.
  * - $1:F:02
    - SUPPRESS_TERM_REPLY
    - Used by the telnet server to suppress term responses.
  * - $1:F:03
    - UART_TX
    - Alternate path for UART Tx when using backchannel.
  * - $1:F:04
    - BACKCHAN
    - Control using UART Tx as backchannel.

      * 0 - Disable
      * 1 - Enable
      * 2 - Request
  * - $1:F:05
    - FLASH_SECTOR
    - Flash the contents of XRAM[0..4095] to the specified sector.
  * - $1:F:06
    - REBOOT_OR_LOCKUP
    - Called after flashing. Non-0 locks up to leave error message visible.


Backchannel
===========

Because the PIX bus is unidirectional, the VGA system cannot send
data back to the RIA directly. The UART Rx path is unsuitable because
it would introduce framing overhead or unusable control characters.
The PIX bus has significant idle bandwidth - it only carries data
when the 6502 writes to XRAM - so all Tx data is routed over PIX
leaving the UART Tx pin available as a backchannel.

The 6502 programmer need not worry about this; it happens
automatically. This note is primarily for hardware explorers probing
the UART Tx pin.

Values 0x00 to 0x7F are used to send a version string as ASCII
terminated with a 0x0D or 0x0A. This must be sent immediately after
the backchannel enable message is received for it to be displayed as
part of the boot message.

When bit 0x80 is set, the 0x70 bits indicate the command type, and the
0x0F bits are a scalar for the command.

0x80 VSYNC - The scalar will increment and be used for the LSB of the
`RIA VSYNC <ria.html#registers>`__ register.

0x90 OP_ACK - Some XREG locations are triggers for remote calls which
may fail or take time to complete. This acknowledges a successful
completion.

0xA0 OP_NAK - This acknowledges a failure.
