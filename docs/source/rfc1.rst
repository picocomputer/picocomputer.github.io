RP6502-RFC-1
############

Comment in `this forum post <https://github.com/orgs/picocomputer/discussions/38>`_.

VGA Graphics
============

The design philosophy for the VGA system is to enable the full power of the Pi Pico while maintaining some 8-bit purity. To that end, it can do affine transforms but is limited to working from 64K of extended memory (XRAM).

The VGA system is built around the scanvideo library from Pi Pico Extras. The color arrangement is identical to their demo board reference design, so sprites and other creations for the Pi Pico have a very good chance of working. This design uses the 16th color bit to render three planes with transparency. The sprite system is from Pi Pico Playground. The RP6502 VGA system exposes per-scanline configuration of these libraries from a 6502 application.

Each scanline has three fill planes. Two sprite layers can be drawn over each fill plane. If you draw too much, the screen will become half-blue. The VGA engine will begin rendering with scanline 0. It first renders fill plane 0 if a fill mode is programmed. Fill planes require modes that fill all pixels, like character and bitmap modes. If no fill plane is programmed, and sprites need to be rendered for this plane, a line of transparent black is automatically rendered (which takes time). Sprites are drawn over their fill plane, in order, over each other using the transparent bit. The process repeats for each fill plane, then repeats for each scanline.

Programming the VGA device should be done with the SDK system calls. These PIX registers are for reference and not yet stable. VGA is PIX device ID 1. VGA PIX extended register addresses store 16 bit values and are specified by $channel:register. e.g. $0:0F

The built-in 8x8 and 8x16 fonts are available by using the special XRAM pointer $FFFF. Glyphs 0-127 are ASCII, glyphs 128-255 vary depending on the code page selected.

The built-in color palettes are accessed by using the special XRAM pointer $FFFF. 1-bit is black and white. 4, and 8-bits point to an ANSI color palette. This is defined as 16 colors, followed by 216 colors (6x6x6), followed by 24 greys.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:00
    - CANVAS
    - Select a graphics canvas. This clears $0:02-$0:FF and all scanline programming. The 80 column console canvas is used as a failsafe and therefore not scanline programmable.
        * 0 - 80 column console. (4:3 or 5:4)
        * 1 - 320x240 (4:3)
        * 2 - 320x180 (16:9)
        * 3 - 640x480 (4:3)
        * 4 - 640x360 (16:9)
  * - $0:01
    - MODE
    - Program a mode into a plane of scanlines. $0:02-$0:FF cleared after programming.
        * 0 - Console
        * 1 - Character
        * 2 - Tile
        * 3 - Bitmap
        * 4 - Sprite
        * 5 - Affine Sprite
  * - $0:02
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $0:03
    - SLBEGIN
    - First scanline to program. SLBEGIN \<= n \< SLEND
  * - $0:04
    - SLEND
    - End of scanlines to program. 0 means use max y resolution (180-480).


Mode 0: Console
---------------

There are no additional registers for the console. Programming the console for a partial screen will align the bottom row on the last scanline. The background is transparent, which makes it easy to show text over a background image using planes.

Mode 1: Character
-----------------

Character modes have color information for each position on the screen. This is the mode you want for showing text in different colors.



.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:06
    - ATTRIBUTES
    - | bit 4 - 0=8x8, 1=8x16
      | bit 3 - wrapy
      | bit 2 - wrapx
      | bit 1:0 - 0=1, 1=4, 2=8, or 3=16 bit color
  * - $0:07
    - STRUCT
    - | Pointer to config structure in XRAM.
      | {
      |   int16_t xpos_px
      |   int16_t ypos_px
      |   int16_t width_chars
      |   int16_t height_chars
      |   uint16_t xram_data_ptr
      |   uint16_t xram_color_ptr
      |   uint16_t xram_font_ptr
      | }

Fonts are encoded in wide format. The first 256 bytes are the first row of each of the 256 glyphs. This is the fastest layout, but wastes memory when not using the entire character set.

.. code-block:: C

  struct {
      uint8_t col_bits[256];
  } *font_row[height];

Data and color information is encoded based on the color bit depth selected.

.. code-block:: C

  // 2-color, 1-bit
  struct {
      uint8_t glyph_code;
  } *data[width_chars * height_chars];

  struct {
      uint16_t color;
  } *color[2];

.. code-block:: C

  // 16-color, 4-bit
  struct {
      uint8_t glyph_code;
      uint8_t fg_bg;
  } *data_ptr[width_chars * height_chars];

  struct {
      uint16_t color;
  } *color[16];

.. code-block:: C

  // 256-color, 8-bit
  struct {
      uint8_t glyph_code;
      uint8_t fg_index;
      uint8_t bg_index;
  } *data_ptr[width_chars * height_chars];

  struct {
      uint16_t color;
  } *color[256];

.. code-block:: C

  // 32768-color, 16-bit (no color table)
  struct {
      uint8_t glyph_code;
      uint8_t attributes; // user defined
      uint16_t fg_color;
      uint16_t bg_color;
  } *data_ptr[width_chars * height_chars];


Mode 2: Tile
------------

Tile modes have color information encoded in the tile bitmap. This is the mode you want for showing a video game playfield.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:06
     - ATTRIBUTES
     - | bit 4 - 0=8x8, 1=16x16
       | bit 3 - wrapy
       | bit 2 - wrapx
       | bit 1:0 - 0=1, 1=4, 2=8, or 3=16 bit color
   * - $0:07
     - STRUCT
     - | Pointer to config structure in XRAM.
       | {
       |   int16_t xpos_px
       |   int16_t ypos_px
       |   int16_t width_tiles
       |   int16_t height_tiles
       |   uint16_t xram_data_ptr
       |   uint16_t xram_color_ptr
       |   uint16_t xram_tile_ptr
       | }

Tile codes are WCHAR, for more than 256, as memory permits.

.. code-block:: C

  // 2-color, 1-bit
  struct {
      uint16_t glyph_code;
  } *data[width_tiles * height_tiles];

Color information is an array.

.. code-block:: C

  struct {
      uint16_t color;
  } *color[colors_count];

Tile data is encoded in "tall" bitmap format.

.. code-block:: C

  // 1-bit 8x8 tiles
  struct {
      struct {
          uint8_t cols_0_7;
      } line[8];
  } *data_ptr[tile_code_count];

  // 1-bit 16x16 tiles
  struct {
      struct {
          uint8_t cols_0_7;
          uint8_t cols_8_15;
      } line[16];
  } *data_ptr[tile_code_count];

  // 4-bit 8x8 tiles
  struct {
      struct {
          uint8_t cols[4];
      } line[8];
  } *data_ptr[tile_code_count];

  // 4-bit 16x16 tiles
  struct {
      struct {
          uint8_t cols[8];
      } line[16];
  } *data_ptr[tile_code_count];

  // 8-bit 8x8 tiles
  struct {
      struct {
          uint8_t cols[8];
      } line[8];
  } *data_ptr[tile_code_count];

  // 8-bit 16x16 tiles
  struct {
      struct {
          uint8_t cols[16];
      } line[16];
  } *data_ptr[tile_code_count];

  // 16-bit 8x8 tiles
  struct {
      struct {
          uint16_t cols[8];
      } line[8];
  } *data_ptr[tile_code_count];

  // 16-bit 16x16 tiles
  struct {
      struct {
          uint16_t cols[16];
      } line[16];
  } *data_ptr[tile_code_count];


Mode 3: Bitmap
--------------

Every pixel can be its own color. 64K XRAM has limits. Monochrome for 640x480, 256 color for 320x180, and 16 colors on 320x240.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:06
     - ATTRIBUTES
     - | bit 3 - wrapy
       | bit 2 - wrapx
       | bit 1:0 - 0=1, 1=4, 2=8, or 3=16 bit color
   * - $0:07
     - STRUCT
     - | Pointer to config structure in XRAM.
       | {
       |   int16_t xpos_px
       |   int16_t ypos_px
       |   int16_t width_px
       |   int16_t height_px
       |   uint16_t xram_data_ptr
       |   uint16_t xram_color_ptr
       | }

Color information is an array.

.. code-block:: C

  struct {
      uint16_t color;
  } *color[colors_count];

Data is the color information packed down to the bit level. 16-bit color encodes the color directly, less uses the color table.

.. code-block:: C

  struct {
      uint8_t data[(width_px * bit_depth + 7) / 8];
  } *rows[height_px];



Mode 4: Sprite
--------------

Sprites have two layers drawn over each plane. This allows for both plain sprites and affine sprites to be drawn on each plane.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:06
     - LAYER
     - 0-1 Two sprite layers per plane.
   * - $0:07
     - LENGTH
     - Length of sprite structure array in XRAM.
   * - $0:08
     - STRUCT
     - | Pointer to config structure array in XRAM.
       | {
       |   int16_t xpos_px
       |   int16_t ypos_px
       |   int16_t xram_img_ptr
       |   uint8_t log_size;
       |   bool has_opacity_metadata;
       | }

Sprite image data is an array of 16 bit colors.

.. code-block:: C

  struct {
      uint16_t pixels[2^log_size];
  } *rows[2^log_size];

TODO: Opacity metadata can be used to speed up rendering. See source for format.

Mode 5: Affine Sprite
---------------------

Affine sprites apply a 3x3 matrix transform. These are slower than plain sprites. Only the first two rows of the matrix is useful, which is why there's only six transform values. These are in signed 8.8 fixed point format.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:06
     - LAYER
     - 0-1 Two sprite layers per plane.
   * - $0:07
     - LENGTH
     - Length of sprite structure array in XRAM.
   * - $0:08
     - STRUCT
     - | Pointer to config structure array in XRAM.
       | {
       |   int16_t transform[6];
       |   int16_t xpos_px
       |   int16_t ypos_px
       |   int16_t xram_img_ptr
       |   uint8_t log_size;
       |   bool has_opacity_metadata;
       | }


Control Channel $F
------------------

These registers are managed by the RIA.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $F:00
     - DISPLAY
     - This sets the aspect ratio of your display. Use CANVAS to select the resolution the 6502 works with.
        * 0 - VGA (4:3) 640x480
        * 1 - HD (16:9) 640x480 and 1280x720
        * 2 - SXGA (5:4) 1280x1024
   * - $F:01
     - CODEPAGE
     - Set code page for built-in font.
   * - $F:02
     - UART
     - Set baud rate.
   * - $F:03
     - UART_TX
     - Alternate path for UART Tx when using backchannel.
   * - $F:04
     - BACKCHAN
     - Control using UART Tx as backchannel.
        * 0 - Disable
        * 1 - Enable
        * 2 - Request acknowledgment
