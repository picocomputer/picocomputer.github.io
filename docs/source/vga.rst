==================================
RP6502-VGA
==================================

RP6502 - Video Graphics Array

Introduction
=============

The RP6502 Video Graphics Array is a specification for a video system
connected by PIX and programmed with extended registers (XREGs). Its
data connection is to a :doc:`ria` over a 5-wire PIX bus.

More than one VGA device can sit on a PIX bus, but all of them share the
same 64 KB of XRAM, and only the first generates frame numbers and VSYNC
interrupts.

Video Programming
==================

The VGA system provides virtual video hardware modeled on the home
computers and arcades of the 8-bit and early-16-bit era. Applications mix
and match the existing modes freely.

Everything the VGA system draws is on the canvas, a grid of pixels such as
320x240. Scanlines are the rows of the canvas, numbered from 0 at the top.
The canvas does not set the resolution of the video output. It is scaled to
fit the display, so 320x240 and 640x480 canvases cover the same area, and a
pixel on the 320x240 canvas is twice as wide and twice as tall.

Bitmaps, tilemaps and sprites are placed on the canvas at an x and y position
in canvas pixels. A bitmap or tilemap can be a different size than the
canvas. One that is smaller covers part of the canvas, and one that is larger
can be scrolled by changing its position.

The canvas is drawn from three planes, each with two layers, a fill layer
and a sprite layer. Plane 0 is the back and plane 2 is the front, and a
transparent pixel shows the plane behind it. A plane's sprite layer is
drawn over its fill layer. There's enough fill rate to blow past any
classic 8-bit system — but push too hard and you overrun the renderer.

The video system counts rows, not objects. There is no limit on how many
sprites you may have, only a limit on how much work one row of graphics can
take. Doing a whole row at a time is what makes the machine efficient, which
matters because these are often battery powered.

Three fill planes fit on every canvas, at every color depth, on every host.
What differs is how much is left over, and the arithmetic below works out the
tightest case, which is the :doc:`fpga` on a 640 wide canvas.

Video modes are programmed into a plane over a range of scanlines, which
is what the PLANE, BEGIN and END registers do in the mode sections below.
BEGIN is the first scanline and END is one past the last. A mode that
covers the whole canvas may be programmed with both of them 0. Different
ranges of the same plane allow different modes, which is how you might
implement a graphical text adventure with half the screen for text and
the other half for graphics. This happens without interrupts, leaving more
CPU headroom for your game logic.

Putting a picture on the canvas takes four steps. Select a canvas, load
the data into XRAM, write the mode's configuration structure into XRAM,
then program the mode. The configuration structure holds the address of
the data, its size, and its position on the canvas. Each mode has its
own, given in its section below.

You program the VGA device with :ref:`PIX extended registers <ria-xreg>`
(XREGs). VGA is PIX device ID 1. Registers are 16-bit values addressed as
$device:$channel:register — for example, $1:0:0F. ``xaddr`` in the
examples below is the XRAM address of that mode's configuration
structure.

.. code-block:: C

    // Select a 320x240 canvas
    result = xreg(1, 0, 0, 1); // or
    result = xreg_vga_canvas(CANVAS_320X240);
    // Program mode 3 for 4 bit color with
    // its config structure at XRAM $FF00.
    result = xreg(1, 0, 1, 3, 2, 0xFF00); // or
    result = xreg_vga_mode3(MODE3_4BPP, 0xFF00);


.. _vga-key-registers:

Doing the arithmetic
--------------------

The :doc:`fpga` is the slowest, so anything that fits there fits everywhere,
and its budget is simple enough to work out on paper. Its video logic runs at
twice the 25.2 MHz pixel clock, and a row of the raster is 800 pixels wide, so
every row of the raster is 1,600 clocks. A 320 wide canvas is scanned out with
its lines doubled, so each row of graphics gets two of them: **3,200 clocks
for half as many pixels**. That is why 320 is where games have room, and it is
worth choosing for that alone.

Fill and sprites are separate engines, each with the whole line of clocks
to itself and a word of XRAM every clock of its own, so neither takes
anything from the other. Each is measured against the line by itself, and
the last row of the table below is the proof.

Fill lands two pixels a clock, so a plane of paletted pixels costs about half
its width in clocks, and the planes are drawn one after another. Text costs
the same as a bitmap: :ref:`mode 1 <vga-mode-1>` fetches a cell's bytes and
its glyph row in the four clocks its eight pixels take. A palette in XRAM is
reloaded before each fill at two colors a clock, which is 128 clocks for 256
colors and 8 for 16. Built-in palettes load nothing.

Sixteen-bit color loads no palette, but every pixel is a halfword of its own,
so a pair of them is a whole word and the fill takes a word from XRAM every
clock. Its word a clock is exactly that, so it costs the same as a paletted
fill with a built-in palette, wherever the bitmap starts.

A 640 wide canvas has 1,600 clocks for all three planes together. These are
measured, and they include the 25 or so clocks each fill spends starting.

.. list-table::
   :widths: 64 18 18
   :header-rows: 1

   * - Fill across a 640 wide canvas
     - Clocks
     - Of 1,600
   * - One plane, built-in palette or 16-bit color, any depth
     - 345
     - 22%
   * - One plane, 8bpp with a 256-color palette in XRAM
     - 470
     - 29%
   * - Three planes, 16-bit color
     - 1,210
     - 76%
   * - Three planes, 8bpp with palettes in XRAM
     - 1,420
     - 89%
   * - Three planes of 8x8 text, 8bpp with palettes in XRAM
     - 1,425
     - 89%
   * - Three planes, 16-bit color, under sixteen 16x16 sprites
     - 1,210
     - 76%

The palette reload is what makes 8bpp the tightest case rather than 16-bit
color: 256 colors are 128 clocks before a single pixel is drawn, and three
planes pay it three times. The last row costs the same as three 16-bit
planes alone: the sprites have their own clocks and their own word of XRAM,
so a stack of them over three 16-bit fills costs the fills nothing.

A 320 wide canvas has half the pixels and twice the budget, so it has four
times the room, and three planes of anything fit there with most of the line
to spare. What limits 16-bit color in practice is not the clock but the
memory: a 640 wide row of it is 1,280 bytes against the 64K of XRAM, so a
16-bit bitmap is a band or a window rather than a whole screen.

Sprites land two pixels a clock like fill, plus a fixed cost for every
sprite in the list. You pay that fixed cost whether or not the sprite lands
on the row, because reading the sprite is how the machine finds out where it
is, but the list is read ahead while the sprites before it draw, so one that
misses the row costs only the two words its descriptor takes. These are
measured, sprite by sprite, and the row's ten clocks of setup are on top.

.. list-table::
   :widths: 40 20 20 20
   :header-rows: 1

   * - One 16 pixel wide sprite on the row
     - Clocks
     - 320 wide
     - 640 wide
   * - :ref:`Mode 5 <vga-mode-5>`, paletted
     - 5 + 8 = 13
     - 245
     - 122
   * - :ref:`Mode 4 <vga-mode-4>`, 16-bit color
     - 5 + 8 = 13
     - 245
     - 122
   * - :ref:`Mode 4 <vga-mode-4>`, affine
     - 11 + 16 = 27
     - 118
     - 59
   * - Any sprite not on the row
     - 2 to 2.5
     - 1,300
     - 640

So a 320 wide canvas holds about 245 sprites of 16x16 on one row, which is
twelve times the width of the row: sprites can be stacked deep everywhere
and still finish. A list longer than about 1,300 runs out of clocks before
drawing anything, however few of them are on screen, so keep the list short
rather than parking unused sprites offscreen. The affine path samples one
texel a clock rather than two, because a rotated row's texels are scattered
across the image and each is a word of its own.

Sprites look their colors up as they go and never load a palette, so a narrow
sprite pays only for the colors it actually uses. A 16-color palette costs
about 45 extra clocks the first time it is used on a row, five for each of
its nine words, and sprites sharing a row share that cache.

The two pixels a clock above assume the cache holds the colors a row of
the sprite uses, and it holds sixteen words of palette, which is 32 colors and
always enough for a 16-color palette. It is emptied at the start of every
row and never watches palette writes, so cycling the palette every frame
costs it nothing: what matters is how many different colors one row of
pixels reaches for. An 8bpp sprite whose row spreads across more than
sixteen words of its palette misses on nearly every pixel, and each miss
holds the sprite until the word arrives, about four and a half clocks a
pixel in all, nine times the usual rate, so plan on a ninth as many of those
on a row.

:doc:`pico` and :doc:`emu` hosts run far beyond all of this. In practice the
friction comes from an 8 MHz CPU and 64K of XRAM long before it comes from
the video system.

Key Registers
-------------

Setting a key register may fail, returning -1 with errno EINVAL.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $1:0:00
     - CANVAS
     - Select a graphics canvas. This clears $1:0:02-$1:0:FF and all
       scanline programming. The console canvas is not programmable.

       * 0 - console (4:3 or 5:4)
       * 1 - 320x240 (4:3)
       * 2 - 320x180 (16:9)
       * 3 - 640x480 (4:3)
       * 4 - 640x360 (16:9)

   * - $1:0:01
     - MODE
     - Program a mode into a plane of scanlines.
       $1:0:02-$1:0:FF cleared after programming. Each mode has a
       section of this document for its own registers.

       * 0 - :ref:`Console <vga-mode-0>`
       * 1 - :ref:`Character <vga-mode-1>`
       * 2 - :ref:`Tile <vga-mode-2>`
       * 3 - :ref:`Bitmap <vga-mode-3>`
       * 4 - :ref:`Sprite 16-bit <vga-mode-4>`
       * 5 - :ref:`Sprite 1,2,4,8-bit <vga-mode-5>`

Select a canvas by setting CANVAS. Set it before programming any modes,
because setting CANVAS clears all scanline programming.

.. code-block:: C

  xreg(1, 0, 0, 1);                // 320x240 canvas
  xreg_vga_canvas(CANVAS_320X240); // macro shortcut

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_canvas(...) xreg(1, 0, 0, __VA_ARGS__)

      #define CANVAS_CONSOLE 0
      #define CANVAS_320X240 1
      #define CANVAS_320X180 2
      #define CANVAS_640X480 3
      #define CANVAS_640X360 4

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_vga_canvas canvas
          xreg 1, 0, 0, canvas
      .endmacro

      CANVAS_CONSOLE = 0
      CANVAS_320X240 = 1
      CANVAS_320X180 = 2
      CANVAS_640X480 = 3
      CANVAS_640X360 = 4

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_vga_canvas canvas
          xreg 1, 0, 0, \canvas
      .endm

      CANVAS_CONSOLE = 0
      CANVAS_320X240 = 1
      CANVAS_320X180 = 2
      CANVAS_640X480 = 3
      CANVAS_640X360 = 4


Colors, Palettes and Fonts
--------------------------

All three planes run RGB555 color plus transparency.

16-bit colors are built with the bit logic below. Setting the alpha bit
makes a color opaque; clearing it makes the color transparent. Despite
the name, alpha here is a binary flag, not a blending factor. The
built-in ANSI palette has the alpha bit set on every color except color
0 (black), which is transparent. Note that ANSI color 16 is also black
but without transparency.

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define COLOR_FROM_RGB8(r, g, b) \
          ((((unsigned)(b) >> 3) << 11) | (((unsigned)(g) >> 3) << 6) | ((unsigned)(r) >> 3))
      #define COLOR_FROM_RGB5(r, g, b) \
          (((unsigned)(b) << 11) | ((unsigned)(g) << 6) | (unsigned)(r))
      #define COLOR_ALPHA_MASK (1u << 5)

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      COLOR_ALPHA_MASK = 1 << 5

      .macro COLOR_FROM_RGB8 r, g, b, alpha
        .ifblank alpha
          .word (((b) >> 3) << 11) | (((g) >> 3) << 6) | ((r) >> 3)
        .else
          .word (((b) >> 3) << 11) | (((g) >> 3) << 6) | ((r) >> 3) | (alpha)
        .endif
      .endmacro

      .macro COLOR_FROM_RGB5 r, g, b, alpha
        .ifblank alpha
          .word ((b) << 11) | ((g) << 6) | (r)
        .else
          .word ((b) << 11) | ((g) << 6) | (r) | (alpha)
        .endif
      .endmacro

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      COLOR_ALPHA_MASK = 1 << 5

      .macro COLOR_FROM_RGB8 r, g, b, alpha=0
          .word ((((\b) >> 3) << 11) | (((\g) >> 3) << 6) | ((\r) >> 3) | (\alpha))
      .endm

      .macro COLOR_FROM_RGB5 r, g, b, alpha=0
          .word (((\b) << 11) | ((\g) << 6) | (\r) | (\alpha))
      .endm

A palette is just an array. The 8bpp, 4bpp, 2bpp, and 1bpp modes use one;
16-bit-per-pixel modes aren't indexed and ignore the palette entirely.
Palettes must be 16-bit aligned.

.. code-block:: C

  uint16_t palette[1 << bits_per_pixel];

The built-in color palettes are reached through the sentinel XRAM pointer
$FFFF. 1-bit is black and white. 4-bit and 8-bit modes start with an ANSI
palette of 16 colors, followed by 216 colors (6x6x6), then 24 grays.


.. _vga-mode-0:

Mode 0: Console
---------------

The console can be rendered on any plane of a graphics canvas. ANSI color 0
(black) is transparent, so text laid over a background image on another plane
shows the image through it. The console can cover part of the canvas, but
its scanline count must be a multiple of the font height. 640-pixel-wide
canvases use an 8x16 font for 80 columns; 320-pixel-wide canvases use an
8x8 font for 40 columns. Only one console can be visible at a time.
Programming another removes the previous one.

See :doc:`term` for the terminal protocol and escape sequences.

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

Program the mode by setting MODE and the registers after it in one call.

.. code-block:: C

  xreg(1, 0, 1, 0, 0); // console on plane 0
  xreg_vga_mode0(0);   // macro shortcut

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_mode0(...) xreg(1, 0, 1, 0, __VA_ARGS__)

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_vga_mode0 plane, begin, end
          xreg 1, 0, 1, 0, plane, begin, end
      .endmacro

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_vga_mode0 values:vararg
          xreg 1, 0, 1, 0, \values
      .endm


.. _vga-mode-1:

Mode 1: Character
-----------------

Character modes carry color information for every cell, so each character
can have its own foreground and background. This is the
mode you want for colorful text — menus, status bars, anything where the
glyphs change color.

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
     - | bit 0:2 - 0=1, 1=4r, 2=4, 3=8, or 4=16 bit color
       | bit 3 - font size 0=8x8, 1=8x16
   * - $1:0:03
     - CONFIG
     - Address of config structure in XRAM. Must be even.
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

Program the mode by setting MODE and the registers after it in one call.

.. code-block:: C

  xreg(1, 0, 1, 1, 3, xaddr, 0);        // 8-bit color on plane 0
  xreg_vga_mode1(MODE1_8BPP, xaddr, 0); // macro shortcut

Config structure may be updated without reprogramming scanlines.

Data is an array of cells, width_chars * height_chars long, encoded based
on the color bit depth selected.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Colors
     - Cell
   * - 2-color, 1-bit
     - glyph_code
   * - 16-color reversed index, 4-bit
     - glyph_code, fg_bg_index
   * - 16-color, 4-bit
     - glyph_code, bg_fg_index
   * - 256-color, 8-bit
     - glyph_code, fg_index, bg_index
   * - 32768-color, 16-bit (no palette)
     - glyph_code, attributes, fg_color, bg_color. The colors are 16-bit, and
       the attributes are user defined and ignored by VGA.

Fonts are encoded in a wide format: the first 256 bytes hold the first
row of all 256 glyphs, the next 256 bytes the second row, and so on.

The built-in 8x8 and 8x16 fonts are available through the sentinel
XRAM pointer $FFFF. Glyphs 0-127 are ASCII; glyphs 128-255 vary by code
page.

.. code-block:: C

  struct {
    struct {
        uint8_t col[256];
    } row[height];
  } font;

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_mode1(...) xreg(1, 0, 1, 1, __VA_ARGS__)

      #define MODE1_1BPP 0x00
      #define MODE1_4BPPR 0x01
      #define MODE1_4BPP 0x02
      #define MODE1_8BPP 0x03
      #define MODE1_16BPP 0x04

      #define MODE1_8X8 0x00
      #define MODE1_8X16 0x08

      #define MODE1_FG_BG(fg, bg) ((uint8_t)(((fg) << 4) | (bg)))
      #define MODE1_BG_FG(bg, fg) ((uint8_t)(((bg) << 4) | (fg)))

      typedef struct
      {
          bool x_wrap;
          bool y_wrap;
          int16_t x_pos_px;
          int16_t y_pos_px;
          int16_t width_chars;
          int16_t height_chars;
          uint16_t xram_data_ptr;
          uint16_t xram_palette_ptr;
          uint16_t xram_font_ptr;
      } mode1_config_t;

      typedef struct
      {
          uint8_t glyph_code;
      } mode1_1bpp_data_t;

      typedef struct
      {
          uint8_t glyph_code;
          uint8_t fg_bg_index;
      } mode1_4bppr_data_t;

      typedef struct
      {
          uint8_t glyph_code;
          uint8_t bg_fg_index;
      } mode1_4bpp_data_t;

      typedef struct
      {
          uint8_t glyph_code;
          uint8_t fg_index;
          uint8_t bg_index;
      } mode1_8bpp_data_t;

      typedef struct
      {
          uint8_t glyph_code;
          uint8_t attributes;
          uint16_t fg_color;
          uint16_t bg_color;
      } mode1_16bpp_data_t;

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_vga_mode1 options, config, plane, begin, end
          xreg 1, 0, 1, 1, options, config, plane, begin, end
      .endmacro

      MODE1_1BPP  = $00
      MODE1_4BPPR = $01
      MODE1_4BPP  = $02
      MODE1_8BPP  = $03
      MODE1_16BPP = $04

      MODE1_8X8  = $00
      MODE1_8X16 = $08

      .struct mode1_config_t
          x_wrap           .byte
          y_wrap           .byte
          x_pos_px         .word
          y_pos_px         .word
          width_chars      .word
          height_chars     .word
          xram_data_ptr    .word
          xram_palette_ptr .word
          xram_font_ptr    .word
      .endstruct

      .struct mode1_1bpp_data_t
          glyph_code .byte
      .endstruct

      .struct mode1_4bppr_data_t
          glyph_code  .byte
          fg_bg_index .byte
      .endstruct

      .struct mode1_4bpp_data_t
          glyph_code  .byte
          bg_fg_index .byte
      .endstruct

      .struct mode1_8bpp_data_t
          glyph_code .byte
          fg_index   .byte
          bg_index   .byte
      .endstruct

      .struct mode1_16bpp_data_t
          glyph_code .byte
          attributes .byte
          fg_color   .word
          bg_color   .word
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_vga_mode1 values:vararg
          xreg 1, 0, 1, 1, \values
      .endm

      MODE1_1BPP  = $00
      MODE1_4BPPR = $01
      MODE1_4BPP  = $02
      MODE1_8BPP  = $03
      MODE1_16BPP = $04

      MODE1_8X8  = $00
      MODE1_8X16 = $08

      MODE1_CONFIG_X_WRAP           = 0
      MODE1_CONFIG_Y_WRAP           = 1
      MODE1_CONFIG_X_POS_PX         = 2
      MODE1_CONFIG_Y_POS_PX         = 4
      MODE1_CONFIG_WIDTH_CHARS      = 6
      MODE1_CONFIG_HEIGHT_CHARS     = 8
      MODE1_CONFIG_XRAM_DATA_PTR    = 10
      MODE1_CONFIG_XRAM_PALETTE_PTR = 12
      MODE1_CONFIG_XRAM_FONT_PTR    = 14
      MODE1_CONFIG_SIZE             = 16

      MODE1_1BPP_DATA_GLYPH_CODE = 0
      MODE1_1BPP_DATA_SIZE       = 1

      MODE1_4BPPR_DATA_GLYPH_CODE  = 0
      MODE1_4BPPR_DATA_FG_BG_INDEX = 1
      MODE1_4BPPR_DATA_SIZE        = 2

      MODE1_4BPP_DATA_GLYPH_CODE  = 0
      MODE1_4BPP_DATA_BG_FG_INDEX = 1
      MODE1_4BPP_DATA_SIZE        = 2

      MODE1_8BPP_DATA_GLYPH_CODE = 0
      MODE1_8BPP_DATA_FG_INDEX   = 1
      MODE1_8BPP_DATA_BG_INDEX   = 2
      MODE1_8BPP_DATA_SIZE       = 3

      MODE1_16BPP_DATA_GLYPH_CODE = 0
      MODE1_16BPP_DATA_ATTRIBUTES = 1
      MODE1_16BPP_DATA_FG_COLOR   = 2
      MODE1_16BPP_DATA_BG_COLOR   = 4
      MODE1_16BPP_DATA_SIZE       = 6


.. _vga-mode-2:

Mode 2: Tile
------------

Tile modes bake the color information into each tile's bitmap. This is
the mode you want for a video game playfield, where a small set of tiles
is repeated across a large map.

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
     - | bit 0:2 - 0=1, 1=2, 2=4, or 3=8 bit color
       | bit 3 - 0=8x8, 1=16x16
       | bit 4:7 - X trim, columns dropped off the tile right (0-15)
       | bit 8:11 - Y trim, rows dropped off the tile bottom (0-15)
   * - $1:0:03
     - CONFIG
     - Address of config structure in XRAM. Must be even.
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

Program the mode by setting MODE and the registers after it in one call.

.. code-block:: C

  xreg(1, 0, 1, 2, 2, xaddr, 0);                    // 4-bit color 8x8 tiles on plane 0
  xreg_vga_mode2(MODE2_4BPP | MODE2_8X8, xaddr, 0); // macro shortcut

Config structure may be updated without reprogramming scanlines.

The data is a matrix of tile IDs, with 0,0 at the top left.

.. code-block:: C

  struct {
      uint8_t tile_id;
  } data[width_tiles * height_tiles];

Tiles themselves are encoded in a "tall" bitmap format, where every row of
one tile is stored, top to bottom, before the next tile begins. Each tile ID
is an index into an array of up to 256 tiles. ``MODE2_TILE`` declares the
structure of one tile from its color depth and tile size, so
``typedef MODE2_TILE(4, 8) tile_t;`` is an 8x8 tile in 4-bit color.

Trim values shrink the drawn tile to an arbitrary size up to the base 8x8
or 16x16, dropping X trim columns off the right and Y trim rows off the
bottom. Tiles are still stored at the full base size, so the dropped
cells are unused. A 16x16 tile with X trim 5 and Y trim 6 draws as 11x10.

A full set of 256 tiles is not required. A tile ID whose row would run past
the end of XRAM is not drawn, and its cells are transparent black.

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_mode2(...) xreg(1, 0, 1, 2, __VA_ARGS__)

      #define MODE2_1BPP 0x00
      #define MODE2_2BPP 0x01
      #define MODE2_4BPP 0x02
      #define MODE2_8BPP 0x03

      #define MODE2_8X8 0x00
      #define MODE2_16X16 0x08

      #define MODE2_X_TRIM(cols) ((cols) << 4)
      #define MODE2_Y_TRIM(rows) ((rows) << 8)

      #define MODE2_TILE(bpp, size)                 \
          struct                                    \
          {                                         \
              struct                                \
              {                                     \
                  uint8_t cols[(size) * (bpp) / 8]; \
              } rows[size];                         \
          }

      typedef struct
      {
          bool x_wrap;
          bool y_wrap;
          int16_t x_pos_px;
          int16_t y_pos_px;
          int16_t width_tiles;
          int16_t height_tiles;
          uint16_t xram_data_ptr;
          uint16_t xram_palette_ptr;
          uint16_t xram_tile_ptr;
      } mode2_config_t;

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_vga_mode2 options, config, plane, begin, end
          xreg 1, 0, 1, 2, options, config, plane, begin, end
      .endmacro

      MODE2_1BPP = $00
      MODE2_2BPP = $01
      MODE2_4BPP = $02
      MODE2_8BPP = $03

      MODE2_8X8   = $00
      MODE2_16X16 = $08

      .macro MODE2_TILE name, bpp, size
          .struct name
              rows .struct
                  cols .res (size) * (bpp) / 8
              .endstruct
              .res ((size) - 1) * .sizeof(rows)
          .endstruct
      .endmacro

      .struct mode2_config_t
          x_wrap           .byte
          y_wrap           .byte
          x_pos_px         .word
          y_pos_px         .word
          width_tiles      .word
          height_tiles     .word
          xram_data_ptr    .word
          xram_palette_ptr .word
          xram_tile_ptr    .word
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_vga_mode2 values:vararg
          xreg 1, 0, 1, 2, \values
      .endm

      MODE2_1BPP = $00
      MODE2_2BPP = $01
      MODE2_4BPP = $02
      MODE2_8BPP = $03

      MODE2_8X8   = $00
      MODE2_16X16 = $08

      .macro MODE2_TILE name, bpp, size
          \name\()_ROWS      = 0
          \name\()_ROWS_COLS = 0
          \name\()_ROWS_SIZE = (\size) * (\bpp) / 8
          \name\()_SIZE      = (\size) * \name\()_ROWS_SIZE
      .endm

      MODE2_CONFIG_X_WRAP           = 0
      MODE2_CONFIG_Y_WRAP           = 1
      MODE2_CONFIG_X_POS_PX         = 2
      MODE2_CONFIG_Y_POS_PX         = 4
      MODE2_CONFIG_WIDTH_TILES      = 6
      MODE2_CONFIG_HEIGHT_TILES     = 8
      MODE2_CONFIG_XRAM_DATA_PTR    = 10
      MODE2_CONFIG_XRAM_PALETTE_PTR = 12
      MODE2_CONFIG_XRAM_TILE_PTR    = 14
      MODE2_CONFIG_SIZE             = 16


.. _vga-mode-3:

Mode 3: Bitmap
--------------

Every pixel can be its own color. The 64 KB of XRAM caps the color depth
of an image that fills the canvas: monochrome at 640x480, 16 colors at
320x240, or 256 colors at 320x180 (16:9).

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
     - | bit 0:2 - 0=1, 1=2, 2=4, 3=8, or 4=16 bit color
       | bit 3 - reverse bit order
   * - $1:0:03
     - CONFIG
     - Address of config structure in XRAM. Must be even.
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

Program the mode by setting MODE and the registers after it in one call.

.. code-block:: C

  xreg(1, 0, 1, 3, 2, xaddr, 0);        // 4-bit color on plane 0
  xreg_vga_mode3(MODE3_4BPP, xaddr, 0); // macro shortcut

Config structure may be updated without reprogramming scanlines.

The data is color information packed down to the bit level. 16-bit color
encodes the color directly; 1-, 2-, 4-, and 8-bit color encode a palette
index instead.

Bit order traditionally follows the canvas, so that left and right bit
shifts move pixels the way you'd expect. The reverse-bits option flips
the bit order of the 1-, 2- and 4-bit modes, which makes bit-level
manipulation code slightly smaller and faster.


.. code-block:: C

  struct {
      struct {
          uint8_t cols[(width_px * bit_depth + 7) / 8];
      } rows[height_px];
  } data;

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_mode3(...) xreg(1, 0, 1, 3, __VA_ARGS__)

      #define MODE3_1BPP 0x00
      #define MODE3_2BPP 0x01
      #define MODE3_4BPP 0x02
      #define MODE3_8BPP 0x03
      #define MODE3_16BPP 0x04

      #define MODE3_REVERSE_BITS 0x08

      typedef struct
      {
          bool x_wrap;
          bool y_wrap;
          int16_t x_pos_px;
          int16_t y_pos_px;
          int16_t width_px;
          int16_t height_px;
          uint16_t xram_data_ptr;
          uint16_t xram_palette_ptr;
      } mode3_config_t;

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_vga_mode3 options, config, plane, begin, end
          xreg 1, 0, 1, 3, options, config, plane, begin, end
      .endmacro

      MODE3_1BPP  = $00
      MODE3_2BPP  = $01
      MODE3_4BPP  = $02
      MODE3_8BPP  = $03
      MODE3_16BPP = $04

      MODE3_REVERSE_BITS = $08

      .struct mode3_config_t
          x_wrap           .byte
          y_wrap           .byte
          x_pos_px         .word
          y_pos_px         .word
          width_px         .word
          height_px        .word
          xram_data_ptr    .word
          xram_palette_ptr .word
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_vga_mode3 values:vararg
          xreg 1, 0, 1, 3, \values
      .endm

      MODE3_1BPP  = $00
      MODE3_2BPP  = $01
      MODE3_4BPP  = $02
      MODE3_8BPP  = $03
      MODE3_16BPP = $04

      MODE3_REVERSE_BITS = $08

      MODE3_CONFIG_X_WRAP           = 0
      MODE3_CONFIG_Y_WRAP           = 1
      MODE3_CONFIG_X_POS_PX         = 2
      MODE3_CONFIG_Y_POS_PX         = 4
      MODE3_CONFIG_WIDTH_PX         = 6
      MODE3_CONFIG_HEIGHT_PX        = 8
      MODE3_CONFIG_XRAM_DATA_PTR    = 10
      MODE3_CONFIG_XRAM_PALETTE_PTR = 12
      MODE3_CONFIG_SIZE             = 14


.. _vga-mode-4:

Mode 4: Sprite 16-bit
---------------------

Sprites can be drawn over any fill plane. This is the same 16-bit
sprite system used by Pi Pico Playground and Luke Wren's RISCBoy.
Its appetite for memory is offset by something mode 5 can't do —
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
     - | Address of config array in XRAM. Must be even.
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

Program the mode by setting MODE and the registers after it in one call.

.. code-block:: C

  xreg(1, 0, 1, 4, 0, xaddr, length, 1); // sprites on plane 1
  xreg_vga_mode4(0, xaddr, length, 1);   // macro shortcut

Move unused sprites off the canvas.

Affine sprites apply a 3x3 matrix transform, which makes them slower
than plain sprites. Only the first two rows of the matrix matter, which is
why there are just six transform values. They're in signed 8.8 fixed-point
format, in the order {a00, a01, b0, a10, a11, b1}. The matrix maps a
position within the sprite on the canvas to a position in the image.

Sprite image data is an array of 16-bit colors. A sprite is a square of
2^log_size pixels a side, from 1x1 up to 128x128; a log_size above 7
describes a square too large for XRAM and draws nothing. ``MODE4_IMAGE``
declares the structure of one image from its log_size, so
``typedef MODE4_IMAGE(4) image_t;`` is a 16x16 image.

When ``has_opacity_metadata`` is set, the image is followed by one
little-endian 32-bit value per row. Bits 15-0 are the end of the row's
opaque span (exclusive) and bits 30-16 are its start. Bit 31 marks the span
as solid, which draws it without checking each color's alpha bit.
Affine sprites do not use the metadata, but its bytes still count toward
the size of the sprite.

Non-affine sprites use ``mode4_sprite_t`` and affine sprites use
``mode4_asprite_t``. ``MODE4_SPAN`` builds one row of opacity metadata.

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_mode4(...) xreg(1, 0, 1, 4, __VA_ARGS__)

      #define MODE4_AFFINE_BIT 0x01

      #define MODE4_AFFINE_A00 0
      #define MODE4_AFFINE_A01 1
      #define MODE4_AFFINE_B0 2
      #define MODE4_AFFINE_A10 3
      #define MODE4_AFFINE_A11 4
      #define MODE4_AFFINE_B1 5
      #define MODE4_AFFINE_ONE 0x0100

      #define MODE4_SPAN(start, end, solid)            \
          (((solid) ? 0x80000000ul : 0ul) |            \
           ((unsigned long)(start) << 16) | (unsigned)(end))

      #define MODE4_IMAGE(log_size)                \
          struct                                   \
          {                                        \
              struct                               \
              {                                    \
                  uint16_t color[1 << (log_size)]; \
              } rows[1 << (log_size)];             \
          }

      typedef struct
      {
          int16_t x_pos_px;
          int16_t y_pos_px;
          uint16_t xram_sprite_ptr;
          uint8_t log_size;
          bool has_opacity_metadata;
      } mode4_sprite_t;

      typedef struct
      {
          int16_t transform[6];
          int16_t x_pos_px;
          int16_t y_pos_px;
          uint16_t xram_sprite_ptr;
          uint8_t log_size;
          bool has_opacity_metadata;
      } mode4_asprite_t;

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_vga_mode4 options, config, length, plane, begin, end
          xreg 1, 0, 1, 4, options, config, length, plane, begin, end
      .endmacro

      MODE4_AFFINE_BIT = $01

      MODE4_AFFINE_A00 = 0
      MODE4_AFFINE_A01 = 1
      MODE4_AFFINE_B0  = 2
      MODE4_AFFINE_A10 = 3
      MODE4_AFFINE_A11 = 4
      MODE4_AFFINE_B1  = 5
      MODE4_AFFINE_ONE = $0100

      .macro MODE4_SPAN start, end, solid
          .dword ((solid) << 31) | ((start) << 16) | (end)
      .endmacro

      .macro MODE4_IMAGE name, log_size
          .struct name
              rows .struct
                  color .word 1 << (log_size)
              .endstruct
              .if log_size
                  .res ((1 << (log_size)) - 1) * .sizeof(rows)
              .endif
          .endstruct
      .endmacro

      .struct mode4_sprite_t
          x_pos_px             .word
          y_pos_px             .word
          xram_sprite_ptr      .word
          log_size             .byte
          has_opacity_metadata .byte
      .endstruct

      .struct mode4_asprite_t
          transform            .word 6
          x_pos_px             .word
          y_pos_px             .word
          xram_sprite_ptr      .word
          log_size             .byte
          has_opacity_metadata .byte
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_vga_mode4 values:vararg
          xreg 1, 0, 1, 4, \values
      .endm

      MODE4_AFFINE_BIT = $01

      MODE4_AFFINE_A00 = 0
      MODE4_AFFINE_A01 = 1
      MODE4_AFFINE_B0  = 2
      MODE4_AFFINE_A10 = 3
      MODE4_AFFINE_A11 = 4
      MODE4_AFFINE_B1  = 5
      MODE4_AFFINE_ONE = $0100

      .macro MODE4_SPAN start, end, solid
          .4byte (((\solid) << 31) | ((\start) << 16) | (\end))
      .endm

      .macro MODE4_IMAGE name, log_size
          \name\()_ROWS       = 0
          \name\()_ROWS_COLOR = 0
          \name\()_ROWS_SIZE  = 2 << (\log_size)
          \name\()_SIZE       = (1 << (\log_size)) * \name\()_ROWS_SIZE
      .endm

      MODE4_SPRITE_X_POS_PX             = 0
      MODE4_SPRITE_Y_POS_PX             = 2
      MODE4_SPRITE_XRAM_SPRITE_PTR      = 4
      MODE4_SPRITE_LOG_SIZE             = 6
      MODE4_SPRITE_HAS_OPACITY_METADATA = 7
      MODE4_SPRITE_SIZE                 = 8

      MODE4_ASPRITE_TRANSFORM            = 0
      MODE4_ASPRITE_X_POS_PX             = 12
      MODE4_ASPRITE_Y_POS_PX             = 14
      MODE4_ASPRITE_XRAM_SPRITE_PTR      = 16
      MODE4_ASPRITE_LOG_SIZE             = 18
      MODE4_ASPRITE_HAS_OPACITY_METADATA = 19
      MODE4_ASPRITE_SIZE                 = 20


.. _vga-mode-5:

Mode 5: Sprite 1,2,4,8-bit
--------------------------

This is a memory-efficient sprite system that uses palettes to cut the
bit depth. Sprites can be drawn over any fill plane, including a null
fill plane. For example, you might put affine sprites for explosions and
the player on one plane, 16x16 4bpp enemy sprites on a second, and 8x8 1bpp
bullets on the third.

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
     - | bit 0:2 - 0=1, 1=2, 2=4, or 3=8 bit color
       | bit 3:5 - 0=8x8, 1=16x16, 2=32x32, 3=64x64, 4=128x128, 5=256x256, 6=512x512
       | 512x512 only supports 1-bit and 2-bit color.
   * - $1:0:03
     - CONFIG
     - | Address of config array in XRAM. Must be even.
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

Program the mode by setting MODE and the registers after it in one call.

.. code-block:: C

  xreg(1, 0, 1, 5, 0x0A, xaddr, length, 1);                   // 16x16 4-bit, plane 1
  xreg_vga_mode5(MODE5_4BPP | MODE5_16X16, xaddr, length, 1); // macro shortcut

Disable unused sprites by moving them off the canvas.

Sprite image data uses the same format as individual mode 2 tiles.
``MODE5_IMAGE`` declares the structure of one image from its color depth and
sprite size, so ``typedef MODE5_IMAGE(4, 16) image_t;`` is a 16x16 image in
4-bit color.

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_mode5(...) xreg(1, 0, 1, 5, __VA_ARGS__)

      #define MODE5_1BPP 0x00
      #define MODE5_2BPP 0x01
      #define MODE5_4BPP 0x02
      #define MODE5_8BPP 0x03

      #define MODE5_8X8 0x00
      #define MODE5_16X16 0x08
      #define MODE5_32X32 0x10
      #define MODE5_64X64 0x18
      #define MODE5_128X128 0x20
      #define MODE5_256X256 0x28
      #define MODE5_512X512 0x30

      #define MODE5_IMAGE(bpp, size)                \
          struct                                    \
          {                                         \
              struct                                \
              {                                     \
                  uint8_t cols[(size) * (bpp) / 8]; \
              } rows[size];                         \
          }

      typedef struct
      {
          int16_t x_pos_px;
          int16_t y_pos_px;
          uint16_t xram_sprite_ptr;
          uint16_t palette_ptr;
      } mode5_sprite_t;

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_vga_mode5 options, config, length, plane, begin, end
          xreg 1, 0, 1, 5, options, config, length, plane, begin, end
      .endmacro

      MODE5_1BPP = $00
      MODE5_2BPP = $01
      MODE5_4BPP = $02
      MODE5_8BPP = $03

      MODE5_8X8     = $00
      MODE5_16X16   = $08
      MODE5_32X32   = $10
      MODE5_64X64   = $18
      MODE5_128X128 = $20
      MODE5_256X256 = $28
      MODE5_512X512 = $30

      .macro MODE5_IMAGE name, bpp, size
          .struct name
              rows .struct
                  cols .res (size) * (bpp) / 8
              .endstruct
              .res ((size) - 1) * .sizeof(rows)
          .endstruct
      .endmacro

      .struct mode5_sprite_t
          x_pos_px        .word
          y_pos_px        .word
          xram_sprite_ptr .word
          palette_ptr     .word
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_vga_mode5 values:vararg
          xreg 1, 0, 1, 5, \values
      .endm

      MODE5_1BPP = $00
      MODE5_2BPP = $01
      MODE5_4BPP = $02
      MODE5_8BPP = $03

      MODE5_8X8     = $00
      MODE5_16X16   = $08
      MODE5_32X32   = $10
      MODE5_64X64   = $18
      MODE5_128X128 = $20
      MODE5_256X256 = $28
      MODE5_512X512 = $30

      .macro MODE5_IMAGE name, bpp, size
          \name\()_ROWS      = 0
          \name\()_ROWS_COLS = 0
          \name\()_ROWS_SIZE = (\size) * (\bpp) / 8
          \name\()_SIZE      = (\size) * \name\()_ROWS_SIZE
      .endm

      MODE5_SPRITE_X_POS_PX        = 0
      MODE5_SPRITE_Y_POS_PX        = 2
      MODE5_SPRITE_XRAM_SPRITE_PTR = 4
      MODE5_SPRITE_PALETTE_PTR     = 6
      MODE5_SPRITE_SIZE            = 8


Control Channel $F
==================

The RIA manages these registers. If a VGA module is connected, 6502
applications are denied access to them.

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
       :ref:`RIA_ATTR_CODE_PAGE <os-ria-attributes>`.
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
   * - $1:F:06
     - REBOOT_OR_LOCKUP
     - Called after flashing. Non-0 locks up to leave error message visible.
   * - $1:F:07
     - FLASH_PROGRAM
     - Program XRAM[0..255] into the 256 byte page at this index. The page's
       sector is erased first when the page does not already read as erased.


Backchannel
===========

The :doc:`pico` hardware is constrained by GPIO pins, which is why two
are needed for a Picocomputer. This is a hack to recover a single pin.
The 6502 programmer never has to think about any of this.

Because the PIX bus is unidirectional, the VGA system can't send data
straight back to the RIA. The UART Rx path won't do either — it would
add framing overhead or unusable control characters. But the PIX bus has
plenty of idle bandwidth (it only carries data when the 6502 writes to
XRAM), so all Tx data is routed over PIX, leaving the UART Tx pin free to
reverse directions and serve as the backchannel.

Values 0x00 to 0x7F send a version string as ASCII, terminated by 0x0D
or 0x0A. Sent immediately after the backchannel-enable message
arrives for it to appear in the boot message.

When bit 0x80 is set, the 0x70 bits give the command type and the 0x0F
bits give a scalar for that command.

0x80 VSYNC - The scalar will increment and be used for the LSB of the
:ref:`RIA VSYNC <ria-registers>` register.

0x90 OP_ACK - Some XREG locations are triggers for remote calls which
may fail or take time to complete. This acknowledges a successful
completion.

0xA0 OP_NAK - This acknowledges a failure.

Because waiting for an entire character to decode over UART is lost time
for VSYNC, a predictive algorithm suspends ACK/NAK around the expected
window for a VSYNC so it can be edge triggered on the first bit.
