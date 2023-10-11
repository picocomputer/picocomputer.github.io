RP6502-VGA
##########

Rumbledethumps Picocomputer 6502 Video Graphics Array.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The Video Graphics Array is a Raspberry Pi Pico with RP6502-VGA firmware. Its primary connection is to a :doc:`ria` over a 5-wire PIX bus. More than one VGA module can be put on a PIX bus. Note that all VGA modules share the same 64K of XRAM and only one module can generate frame numbers and vsync interrupts.

2. Video Programming
====================

The design philosophy for the VGA system is to enable the full power of the Pi Pico while maintaining some 8-bit purity. 6502 programmers should be solving problems with the same thought processes as was used for classic 8-bit home computers. To that end, the VGA system is limited to working from 64K of extended memory (XRAM).

The VGA system is built around the scanvideo library from Pi Pico Extras. All three planes are enabled with RGB555 color plus transparency. The mode 4 sprite system is from Pi Pico Playground.

The RP6502 VGA system exposes per-scanline configuration of the video system to your 6502 application. We start with three planes. Each plane has two layers, a fill layer and a sprite layer. Your application can assign different fill and sprite modes to specific planes and scanlines. There's plenty of fill rate to exceed the capabilities of any classic 8-bit system, but if you like to push the limits then you may see a half-blue screen indicating you went too far.

The built-in 8x8 and 8x16 fonts are available by using the special XRAM pointer $FFFF. Glyphs 0-127 are ASCII, glyphs 128-255 vary depending on the code page selected.

The built-in color palettes are accessed by using the special XRAM pointer $FFFF. 1-bit is black and white. 4 and 8-bits point to an ANSI color palette of 16 colors, followed by 216 colors (6x6x6), followed by 24 greys.

16-bit colors are built with the following bit logic. Setting the alpha bit will make the color opaque. The built-in ANSI color palette has the alpha bit set on all colors except color 0 black.

.. code-block:: C

  #define COLOR_FROM_RGB8(r,g,b) (((b>>3)<<11)|((g>>3)<<6)|(r>>3))
  #define COLOR_FROM_RGB5(r,g,b) ((b<<11)|(g<<6)|(r))
  #define COLOR_ALPHA_MASK (1u<<5)

Palette information is an array. 8bpp, 4bpp, and 1bpp modes use a palette. 16 bit per pixel modes don't used indexed color and will ignore the palette. Palettes must be 16-bit aligned.

.. code-block:: C

  struct {
      uint16_t color;
  } palette[2^bits_per_pixel];


Programming the VGA device is done with PIX extended registers - XREGS. VGA is PIX device ID 1. Registers are 16 bit values addressed by $device:$channel:register. e.g. $1:0:0F

.. code-block:: C

    // Select a 320x240 canvas
    result = xreg(1, 0, 0, 1);
    // Program mode 3 for 4 bit color with
    // its config registers at XRAM $FF00.
    result = xreg(1, 0, 1, 3, 1, 0xFF00);

Key Registers
-------------

Setting key registers may return a failure (-1) with errno EINVAL. Not all options for all modes are implemented (yet). Check the result of xreg() to detect if a feature is available.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:0:00
    - CANVAS
    - Select a graphics canvas. This clears $1:0:00-$1:0:FF and all scanline programming. The 80 column console canvas is used as a failsafe and therefore not scanline programmable.
        * 0 - 80 column console. (4:3 or 5:4)
        * 1 - 320x240 (4:3)
        * 2 - 320x180 (16:9)
        * 3 - 640x480 (4:3)
        * 4 - 640x360 (16:9)
  * - $1:0:01
    - MODE
    - Program a mode into a plane of scanlines. $1:0:00-$1:0:FF cleared after programming. Each mode has a section of this document for its own registers.
        * 0 - Console
        * 1 - Character
        * 2 - Tile
        * 3 - Bitmap
        * 4 - Sprite
        * 5 - Affine Sprite


Mode 0: Console
---------------

The console may be rendered on any canvas plane. The background is transparent, which makes it easy to show text over a background image using planes. The console may be a partial screen, but the scanlines must be a multiple of the font height. 640 pixel wide canvases use an 8x16 font for 80 columns. 320 pixel wide canvases use an 8x8 font for 40 columns. Only one console may be visible, programming again will remove the previous console.

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
    - 0-3 to select which fill plane of scanlines to program.
  * - $1:0:03
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:04
    - END
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
  * - $1:0:01
    - MODE
    - 1 - Character
  * - $1:0:02
    - OPTIONS
    - | bit 2 - font size 0=8x8, 1=8x16
      | bit 1:0 - 0=1, 1=4, 2=8, or 3=16 bit color
  * - $1:0:03
    - CONFIG
    - Address of config structure in XRAM.
  * - $1:0:04
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $1:0:05
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:06
    - END
    - End of scanlines to program. 0 means use canvas height (180-480).

Config structure may be updated without reprogramming scanlines.

.. code-block:: C

  struct {
      bool x_wrap;
      bool y_wrap;
      int16_t x_px;
      int16_t y_px;
      int16_t width_chars;
      int16_t height_chars;
      uint16_t data_ptr;
      uint16_t palette_ptr;
      uint16_t font_ptr;
  } config;

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

  // 32768-color, 16-bit (no palette)
  struct {
      uint8_t glyph_code;
      uint8_t attributes; // user defined, ignored by VGA
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
  * - $1:0:01
    - MODE
    - 2 - Tile
  * - $1:0:02
    - OPTIONS
    - | bit 2 - 0=8x8, 1=16x16
      | bit 1:0 - 0=1, 1=4, 2=8, or 3=16 bit color
  * - $1:0:03
    - CONFIG
    - Address of config structure in XRAM.
  * - $1:0:04
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $1:0:05
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:06
    - END
    - End of scanlines to program. 0 means use canvas height (180-480).

Config structure may be updated without reprogramming scanlines.

.. code-block:: C

  struct {
      bool x_wrap;
      bool y_wrap;
      int16_t x_px;
      int16_t y_px;
      int16_t width_tiles;
      int16_t height_tiles;
      uint16_t data_ptr;
      uint16_t palette_ptr;
      uint16_t tile_ptr;
  } config;

Data is a matrix of glyph codes with 0,0 at the top left.

.. code-block:: C

  struct {
      uint8_t glyph_code;
  } data[width_tiles * height_tiles];

Tile data is encoded in "tall" bitmap format.

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

  // 16-bit 8x8 tiles (no palette)
  struct {
      struct {
          uint16_t cols[8];
      } rows[8];
  } tile[up_to_256];

  // 16-bit 16x16 tiles (no palette)
  struct {
      struct {
          uint16_t cols[16];
      } rows[16];
  } tile[up_to_256];


Mode 3: Bitmap
--------------

Every pixel can be its own color. 64K XRAM limits the full screen color depth. Monochrome at 640x480, 16 colors at 320x240, 256 colors for 320x180 (16:9).

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
    - | bit 2 - reverse bits
      | bit 1:0 - 0=1, 1=4, 2=8, or 3=16 bit color
  * - $1:0:03
    - CONFIG
    - Address of config structure in XRAM.
  * - $1:0:04
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $1:0:05
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:06
    - END
    - End of scanlines to program. 0 means use canvas height (180-480).

Config structure may be updated without reprogramming scanlines.

.. code-block:: C

  struct {
      bool x_wrap;
      bool y_wrap;
      int16_t x_px;
      int16_t y_px;
      int16_t width_px;
      int16_t height_px;
      uint16_t data_ptr;
      uint16_t palette_ptr;
  } config;

Data is the color information packed down to the bit level. 16-bit color encodes the color directly as data. 1, 4, and 8 bit color encodes a palette index as data.

Bit order is traditionally done so that left and right bit shift operations match pixel movement on screen. The reverse bits option change the bit order of 1 and 4 bit modes so bit-level manipulation code is slightly faster and smaller.

Data for 16 bit color must be 16 bit aligned.

.. code-block:: C

  struct {
      struct {
          uint8_t cols[(width_px * bit_depth + 7) / 8];
      } rows[height_px];
  } data;


Mode 4: Sprite
--------------

Sprites may be drawn over each fill plane. This is the 16-bit sprite system from the Pi Pico Playground. Lower bit depths are planned for a different mode.

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
    - | bit 1 - affine
  * - $1:0:03
    - CONFIG
    - | Address of config array in XRAM.
  * - $1:0:04
    - LENGTH
    - Length of config array array in XRAM.
  * - $1:0:05
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $1:0:06
    - BEGIN
    - First scanline to program. BEGIN \<= n \< END
  * - $1:0:07
    - END
    - End of scanlines to program. 0 means use canvas height (180-480).

Unused sprites should be moved off screen. Non-affine sprites use this config structure.

.. code-block:: C

  struct {
      int16_t x_px;
      int16_t y_px;
      int16_t sprite_ptr;
      uint8_t log_size;
      bool has_opacity_metadata;
  } config[LENGTH];

Affine sprites apply a 3x3 matrix transform. These are slower than plain sprites. Only the first two rows of the matrix is useful, which is why there's only six transform values. These are in signed 8.8 fixed point format.

.. code-block:: C

  struct {
       int16_t transform[6];
       int16_t x_px
       int16_t y_px
       int16_t sprite_ptr
       uint8_t log_size;
       bool has_opacity_metadata;
  } config[LENGTH];


Sprite image data is an array of 16 bit colors.

.. code-block:: C

  struct {
    struct {
        uint16_t pixels[2^log_size];
    } rows[2^log_size];
  } sprite;


Control Channel $F
------------------

These registers are managed by the RIA. Do not distribute applications that set these.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $1:F:00
    - DISPLAY
    - This sets the aspect ratio of your display. This also resets CANVAS to the console.
       * 0 - VGA (4:3) 640x480
       * 1 - HD (16:9) 640x480 and 1280x720
       * 2 - SXGA (5:4) 1280x1024
  * - $1:F:01
    - CODEPAGE
    - Set code page for built-in font.
  * - $1:F:02
    - UART
    - Set baud rate. Reserved, not implemented.
  * - $1:F:03
    - UART_TX
    - Alternate path for UART Tx when using backchannel.
  * - $1:F:04
    - BACKCHAN
    - Control using UART Tx as backchannel.
       * 0 - Disable
       * 1 - Enable
       * 2 - Request acknowledgment


3. Backchannel
==============

Because the PIX bus is unidirectional, it can't be used for sending data from the VGA system back to the RIA. Using the UART Rx path is undesirable since there would be framing overhead or unusable control characters. Since there is a lot of unused bandwidth on the PIX bus, which is only used when the 6502 is writing to XRAM, it can be used for the UART Tx path allowing the UART Tx pin to switch directions.

This is not interesting to the 6502 programmer as it happens automatically. RIA Kernel developers can extend its usefulness. The backchannel is simply a UART implemented in PIO so it sends 8-bit values.

Values 0x00 to 0x7F are used to send a version string as ASCII terminated with a 0x0D or 0x0A. This must be sent immediately after the backchannel enable message is received for it to be displayed as part of the boot message. It may be updated any time after that and inspected with the STATUS CLI command, but currently there is no reason to do so.

When bit 0x80 is set, the 0x70 bits indicate the command type, and the 0x0F bits are a scalar for the command.

0x80 VSYNC - The scalar will increment and be used for the LSB of the RIA_VSYNC register.

0x90 OP_ACK - Some XREG locations are triggers for remote calls which may fail or take time to complete. This acknowledges a successful completion.

0xA0 OP_NAK - This acknowledges a failure.
