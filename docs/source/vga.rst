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
and match the existing modes freely, and a new mode is one more scanline
engine alongside the ones already here.

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

Every mode is programmed into one plane over a range of scanlines, which
is what the PLANE, BEGIN and END registers do in the mode sections below.
BEGIN is the first scanline and END is one past the last, so a mode that
covers the whole canvas is programmed with both of them 0. Different
ranges of the same plane take different modes, which is how a status bar
of characters sits above a bitmap.

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
    result = xreg_vga_canvas(1);
    // Program mode 3 for 4 bit color with
    // its config structure at XRAM $FF00.
    result = xreg(1, 0, 1, 3, 2, 0xFF00); // or
    result = xreg_vga_mode3(2, 0xFF00);


.. _vga-key-registers:

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

       * 0 - :ref:`Console <vga-mode-0>`
       * 1 - :ref:`Character <vga-mode-1>`
       * 2 - :ref:`Tile <vga-mode-2>`
       * 3 - :ref:`Bitmap <vga-mode-3>`
       * 4 - :ref:`Sprite 16-bit <vga-mode-4>`
       * 5 - :ref:`Sprite 1,2,4,8-bit <vga-mode-5>`

Select a canvas by setting CANVAS. Set it before programming any modes,
because setting CANVAS clears all scanline programming.

.. code-block:: C

  xreg(1, 0, 0, 1);   // 320x240 canvas
  xreg_vga_canvas(1); // macro shortcut

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_canvas(...) xreg(1, 0, 0, __VA_ARGS__)

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc

      .macro xreg_vga_canvas canvas
          xreg 1, 0, 0, canvas
      .endmacro

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc
      :force:

      .macro xreg_vga_canvas canvas
          xreg 1, 0, 0, \canvas
      .endm


Colors, Palettes and Fonts
--------------------------

All three planes run RGB555 color plus transparency.

16-bit colors are built with the bit logic below. Setting the alpha bit
makes a color opaque; clearing it makes the color transparent. Despite
the name, alpha here is a binary flag, not a blending factor. The
built-in ANSI palette has the alpha bit set on every color except color
0 (black), which is transparent.

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
Palettes must be 16-bit aligned; an odd one falls back to the built-in
table.

.. code-block:: C

  uint16_t palette[1 << bits_per_pixel];

The built-in color palettes are reached through the sentinel XRAM pointer
$FFFF. 1-bit is black and white. 4-bit and 8-bit modes start with an ANSI
palette of 16 colors, followed by 216 colors (6x6x6), then 24 grays.

The built-in 8x8 and 8x16 fonts are available through the same sentinel
XRAM pointer $FFFF. Glyphs 0-127 are ASCII; glyphs 128-255 vary by code
page.


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

  xreg(1, 0, 1, 1, 3, xaddr, 0); // 8-bit color on plane 0
  xreg_vga_mode1(3, xaddr, 0);   // macro shortcut

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
the mode you want for a video-game playfield, where a small set of tiles
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

  xreg(1, 0, 1, 2, 2, xaddr, 0); // 4-bit color 8x8 tiles on plane 0
  xreg_vga_mode2(2, xaddr, 0);   // macro shortcut

Config structure may be updated without reprogramming scanlines.

The data is a matrix of tile IDs, with 0,0 at the top left.

.. code-block:: C

  struct {
      uint8_t tile_id;
  } data[width_tiles * height_tiles];

Tiles themselves are encoded in a "tall" bitmap format.

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

Trim values shrink the drawn tile to an arbitrary size up to the base 8x8
or 16x16, dropping X trim columns off the right and Y trim rows off the
bottom. Tiles are still stored at the full base size, so the dropped
cells are unused. A 16x16 tile with X trim 5 and Y trim 6 draws as 11x10.

.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_mode2(...) xreg(1, 0, 1, 2, __VA_ARGS__)

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

  xreg(1, 0, 1, 3, 2, xaddr, 0); // 4-bit color on plane 0
  xreg_vga_mode3(2, xaddr, 0);   // macro shortcut

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

Sprites can be drawn over any fill plane. This is the 16-bit sprite
system from the Pi Pico Playground; for lower bit depths, see mode 5.
Its appetite for memory is offset by something the others can't do —
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
describes a square too large for XRAM and draws nothing.

.. code-block:: C

  struct {
    struct {
        uint16_t color[1 << log_size];
    } rows[1 << log_size];
  } data;

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
fill plane. So you might put affine sprites for explosions and the
player on one plane, 16x16 4bpp enemy sprites on a second, and 8x8 1bpp
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

  xreg(1, 0, 1, 5, 0x0A, xaddr, length, 1); // 16x16 4-bit sprites on plane 1
  xreg_vga_mode5(0x0A, xaddr, length, 1);   // macro shortcut

Disable unused sprites by moving them off the canvas.

Sprite image data uses the same format as individual mode 2 tiles.

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


.. tab:: C

   .. code-block:: C
      :caption: xram.h

      #define xreg_vga_mode5(...) xreg(1, 0, 1, 5, __VA_ARGS__)

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

The 6502 programmer never has to think about any of this. What follows is
the return path for machines where the RIA and the VGA are separate chips
joined by a serial wire.

Because the PIX bus is unidirectional, the VGA system can't send data
straight back to the RIA. The UART Rx path won't do either — it would
add framing overhead or unusable control characters. But the PIX bus has
plenty of idle bandwidth (it only carries data when the 6502 writes to
XRAM), so all Tx data is routed over PIX, leaving the UART Tx pin free to
serve as a backchannel.

Values 0x00 to 0x7F send a version string as ASCII, terminated by 0x0D
or 0x0A. Send it immediately after the backchannel-enable message
arrives for it to appear in the boot message.

When bit 0x80 is set, the 0x70 bits give the command type and the 0x0F
bits give a scalar for that command.

0x80 VSYNC - The scalar will increment and be used for the LSB of the
:ref:`RIA VSYNC <ria-registers>` register.

0x90 OP_ACK - Some XREG locations are triggers for remote calls which
may fail or take time to complete. This acknowledges a successful
completion.

0xA0 OP_NAK - This acknowledges a failure.


Two Implementations
===================

Everything on this page exists twice. There is a software renderer in C
and there is Register Transfer Logic (RTL) in System Verilog. Neither one
is a simplification of the other. They have the same registers, the same
config structures at the same offsets, and they produce the same pixels.

The C is the RP6502-VGA firmware, which is designed to fit entirely on a
Raspberry Pi Pico 2 as part of an :doc:`pico`, and the :doc:`emu`
compiles the same files, so that module and every software host draw
with one renderer. The RTL is in the :doc:`fpga`, where each mode is a
scanline engine in fabric.

The C renderer is built around a modified scanvideo library from Pi Pico
Extras. The mode 4 sprite system comes from Pi Pico Playground, and the
scanline programming system and every other mode are original work for
the RP6502.

The two are tested against each other. A generator writes a corpus of
small ROMs covering every mode. Every fixture boots on both machines,
settles, and the two framebuffers are compared word for word.
