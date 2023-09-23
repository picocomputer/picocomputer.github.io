RP6502-RFC1 Programmable Video Graphics Array
#############################################

Comment in `this forum post <https://github.com/orgs/picocomputer/discussions/38>`_.

The design philosophy for the VGA system is to enable the full power of the Pi Pico while maintaining some 8-bit purity. To that end, it can do affine transforms but is limited to working from 64K of extended memory (XRAM).

The VGA system is built around the scanvideo library from Pi Pico Extras. All three planes are enabled with RGB555 color plus transparency. The sprite system is from Pi Pico Playground.

The RP6502 VGA system exposes per-scanline configuration of the video system from a 6502 application. Each scanline has three fill planes. A sprite layer can be drawn over each fill plane. If you attempt to render too much, the screen will become half-blue. The VGA engine will begin rendering with scanline 0. It first renders fill plane 0 if a fill mode is programmed. Fill planes require modes that fill all pixels, like character and bitmap modes. If no fill plane is programmed, and sprites need to be rendered, a line of transparent black may be automatically rendered (which takes time). Sprites are drawn over their fill plane, in order, over each other using the transparent bit. The process repeats for each fill plane, then repeats for each scanline.

The built-in 8x8 and 8x16 fonts are available by using the special XRAM pointer $FFFF. Glyphs 0-127 are ASCII, glyphs 128-255 vary depending on the code page selected.

The built-in color palettes are accessed by using the special XRAM pointer $FFFF. 1-bit is black and white. 4 and 8-bits point to an ANSI color palette of 16 colors, followed by 216 colors (6x6x6), followed by 24 greys.

16-bit colors are built with the following bit logic. Setting the alpha mask bit will make the color opaque. The built-in ANSI color palette has the alpha bit mask set on all colors except color 0 black.

.. code-block:: C

  #define COLOR_FROM_RGB8(r,g,b) (((b>>3)<<11)|((g>>3)<<6)|(r>>3))
  #define COLOR_FROM_RGB5(r,g,b) ((b<<11)|(g<<6)|(r))
  #define COLOR_ALPHA_MASK (1u<<5)

Palette information is an array.

.. code-block:: C

  struct {
      uint16_t color;
  } palette[2^bits_per_pixel];


Programming the VGA device is done with PIX extended registers - XREGS. VGA is PIX device ID 1. VGA PIX extended registers are 16 bit values specified by $channel:register. e.g. $0:0F

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:00
    - CANVAS
    - Select a graphics canvas. This clears $0:00-$0:FF and all scanline programming. The 80 column console canvas is used as a failsafe and therefore not scanline programmable. Setting this can fail with EINVAL.
        * 0 - 80 column console. (4:3 or 5:4)
        * 1 - 320x240 (4:3)
        * 2 - 320x180 (16:9)
        * 3 - 640x480 (4:3)
        * 4 - 640x360 (16:9)
  * - $0:01
    - MODE
    - Program a mode into a plane of scanlines. $0:00-$0:FF cleared after programming. Setting this can fail with EINVAL.
        * 0 - Console
        * 1 - Character
        * 2 - Tile
        * 3 - Bitmap
        * 4 - Sprite
        * 5 - Affine Sprite


Mode 0: Console
---------------

The console may be rendered on any canvas plane. The background is transparent, which makes it easy to show text over a background image using planes. The console may be a partial screen, but the scanlines must be a multiple of the font height. Only one console may be programmed, doing so again will clear the previous console.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:01
    - MODE
    - 0 - Console
  * - $0:02
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $0:03
    - SLBEGIN
    - First scanline to program. SLBEGIN \<= n \< SLEND
  * - $0:04
    - SLEND
    - End of scanlines to program. 0 means use canvas height (180-480).


Mode 1: Character
-----------------

Character modes have color information for each position on the screen. This is the mode you want for showing text in different colors.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:01
    - MODE
    - 1 - Character
  * - $0:02
    - STRUCT
    - | Pointer to config structure in XRAM.
      | {
      |   bool x_wrap
      |   bool y_wrap
      |   int16_t x_px
      |   int16_t y_px
      |   int16_t width_chars
      |   int16_t height_chars
      |   uint16_t data_ptr
      |   uint16_t palette_ptr
      |   uint16_t font_ptr
      | }
  * - $0:03
    - ATTRIBUTES
    - | bit 2 - font size 0=8x8, 1=8x16
      | bit 1:0 - 0=1, 1=4, 2=8, or 3=16 bit color
  * - $0:04
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $0:05
    - SLBEGIN
    - First scanline to program. SLBEGIN \<= n \< SLEND
  * - $0:06
    - SLEND
    - End of scanlines to program. 0 means use canvas height (180-480).


Data is encoded based on the color bit depth selected.

.. code-block:: C

  // 2-color, 1-bit
  struct {
      uint8_t glyph_code;
  } data[width_chars * height_chars];

.. code-block:: C

  // 16-color, 4-bit
  struct {
      uint8_t glyph_code;
      uint8_t fg_bg;
  } data[width_chars * height_chars];

.. code-block:: C

  // 256-color, 8-bit
  struct {
      uint8_t glyph_code;
      uint8_t fg_index;
      uint8_t bg_index;
  } data[width_chars * height_chars];

.. code-block:: C

  // 32768-color, 16-bit (no color table)
  struct {
      uint8_t glyph_code;
      uint8_t attributes; // user defined
      uint16_t fg_color;
      uint16_t bg_color;
  } data[width_chars * height_chars];

Fonts are encoded in wide format. The first 256 bytes are the first row of each of the 256 glyphs. This is the fastest layout, but wastes memory when not using the entire character set.

.. code-block:: C

  struct {
    struct {
        uint8_t col[256];
    } row[height];
  } font;


Mode 2: Tile
------------

Tile modes have color information encoded in the tile bitmap. This is the mode you want for showing a video game playfield.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:01
    - MODE
    - 2 - Tile
  * - $0:02
    - STRUCT
    - | Pointer to config structure in XRAM.
      | {
      |   bool x_wrap
      |   bool y_wrap
      |   int16_t x_px
      |   int16_t y_px
      |   int16_t width_tiles
      |   int16_t height_tiles
      |   uint16_t data_ptr
      |   uint16_t palette_ptr
      |   uint16_t tile_ptr
      | }
  * - $0:03
    - ATTRIBUTES
    - | bit 2 - 0=8x8, 1=16x16
      | bit 1:0 - 0=1, 1=4, 2=8, or 3=16 bit color
  * - $0:04
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $0:05
    - SLBEGIN
    - First scanline to program. SLBEGIN \<= n \< SLEND
  * - $0:06
    - SLEND
    - End of scanlines to program. 0 means use canvas height (180-480).

Glyph codes are a 2D array with 0,0 at the top left.

.. code-block:: C

  struct {
      uint8_t glyph_code;
  } data[width_tiles * height_tiles];

Palette information is an array.

.. code-block:: C

  struct {
      uint16_t color;
  } palette[colors_count];

Tile data is encoded in "tall" bitmap format.

.. code-block:: C

  // 1-bit 8x8 tiles
  struct {
      struct {
          uint8_t cols;
      } rows[8];
  } tile[tile_code_count];

  // 1-bit 16x16 tiles
  struct {
      struct {
          uint8_t cols[2];
      } rows[16];
  } tile[tile_code_count];

  // 4-bit 8x8 tiles
  struct {
      struct {
          uint8_t cols[4];
      } rows[8];
  } tile[tile_code_count];

  // 4-bit 16x16 tiles
  struct {
      struct {
          uint8_t cols[8];
      } rows[16];
  } tile[tile_code_count];

  // 8-bit 8x8 tiles
  struct {
      struct {
          uint8_t cols[8];
      } rows[8];
  } tile[tile_code_count];

  // 8-bit 16x16 tiles
  struct {
      struct {
          uint8_t cols[16];
      } rows[16];
  } tile[tile_code_count];

  // 16-bit 8x8 tiles (no color table)
  struct {
      struct {
          uint16_t cols[8];
      } rows[8];
  } tile[tile_code_count];

  // 16-bit 16x16 tiles (no color table)
  struct {
      struct {
          uint16_t cols[16];
      } rows[16];
  } tile[tile_code_count];


Mode 3: Bitmap
--------------

Every pixel can be its own color. 64K XRAM has limits. Monochrome for 640x480, 256 color for 320x180, and 16 colors on 320x240.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:01
    - MODE
    - 3 - Bitmap
  * - $0:02
    - STRUCT
    - | Pointer to config structure in XRAM.
      | {
      |   bool x_wrap
      |   bool y_wrap
      |   int16_t x_px
      |   int16_t y_px
      |   int16_t width_px
      |   int16_t height_px
      |   uint16_t data_ptr
      |   uint16_t palette_ptr
      | }
  * - $0:03
    - ATTRIBUTES
    - | bit 2 - reverse bits
      | bit 1:0 - 0=1, 1=4, 2=8, or 3=16 bit color
  * - $0:04
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $0:05
    - SLBEGIN
    - First scanline to program. SLBEGIN \<= n \< SLEND
  * - $0:06
    - SLEND
    - End of scanlines to program. 0 means use canvas height (180-480).

Palette information is an array.

.. code-block:: C

  struct {
      uint16_t color;
  } palette[colors_count];

Data is the color information packed down to the bit level. 16-bit color encodes the color directly as data. 1, 4, and 8 bit color encodes a palette index as data.

Bit order is traditionally done so that left and right bit shift operations match pixel movement on screen. The reverse bits option change the bit order of 1 and 4 bit modes so bit-level manipulation code is slightly faster and smaller.

.. code-block:: C

  struct {
    struct {
        uint8_t cols[(width_px * bit_depth + 7) / 8];
    } rows[height_px];
  } data;


Mode 4: Sprite
--------------

Sprites may be drawn over each fill plane.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:01
    - MODE
    - 4 - Sprite
  * - $0:02
    - STRUCT
    - | Pointer to config structure array in XRAM.
      | {
      |   int16_t x_px
      |   int16_t y_px
      |   int16_t sprite_ptr
      |   uint8_t log_size;
      |   bool has_opacity_metadata;
      | }
  * - $0:03
    - LENGTH
    - Length of sprite structure array in XRAM.
  * - $0:04
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $0:05
    - SLBEGIN
    - First scanline to program. SLBEGIN \<= n \< SLEND
  * - $0:06
    - SLEND
    - End of scanlines to program. 0 means use canvas height (180-480).

Sprite image data is an array of 16 bit colors.

.. code-block:: C

  struct {
    struct {
        uint16_t pixels[2^log_size];
    } rows[2^log_size];
  } sprite;

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
  * - $0:01
    - MODE
    - 5 - Affine Sprite
  * - $0:02
    - STRUCT
    - | Pointer to config structure array in XRAM.
      | {
      |   int16_t transform[6];
      |   int16_t x_px
      |   int16_t y_px
      |   int16_t xram_img_ptr
      |   uint8_t log_size;
      |   bool has_opacity_metadata;
      | }
  * - $0:03
    - LENGTH
    - Length of sprite structure array in XRAM.
  * - $0:04
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $0:05
    - SLBEGIN
    - First scanline to program. SLBEGIN \<= n \< SLEND
  * - $0:06
    - SLEND
    - End of scanlines to program. 0 means use canvas height (180-480).


Control Channel $F
------------------

These registers are managed by the RIA. Do not distribute applications that set these.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $F:00
    - DISPLAY
    - This sets the aspect ratio of your display. This also resets CANVAS o the console.
       * 0 - VGA (4:3) 640x480
       * 1 - HD (16:9) 640x480 and 1280x720
       * 2 - SXGA (5:4) 1280x1024
  * - $F:01
    - CODEPAGE
    - Set code page for built-in font.
  * - $F:02
    - UART
    - Set baud rate. Reserved, not implemented.
  * - $F:03
    - UART_TX
    - Alternate path for UART Tx when using backchannel.
  * - $F:04
    - BACKCHAN
    - Control using UART Tx as backchannel.
       * 0 - Disable
       * 1 - Enable
       * 2 - Request acknowledgment
