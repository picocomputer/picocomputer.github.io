==================================
RP6502-VGA
==================================

RP6502 - Video Graphics Array

Introduction
=============

The RP6502 Video Graphics Array is a Raspberry Pi Pico 2 running
RP6502-VGA firmware. Its primary data connection is to a :doc:`ria`
over a 5-wire PIX bus. You can put more than one VGA module on a PIX
bus, but note that all of them share the same 64 KB of XRAM, and only
the first generates frame numbers and VSYNC interrupts.

Video Programming
==================

The VGA system provides virtual video hardware modeled on the home
computers and arcades of the 8-bit and early-16-bit era. Adding new
video modes and sprite systems is straightforward, and applications can
mix and match the existing ones freely.

Under the hood, it's built around a modified scanvideo library from Pi
Pico Extras. All three planes run RGB555 color plus transparency. The
mode 4 sprite system comes from Pi Pico Playground; the scanline
programming system and every other mode are original work for the
RP6502.

The VGA system exposes per-scanline configuration to your 6502
application. At the broadest level there are three planes, and each
plane has two layers: a fill layer and a sprite layer. Your application
can assign different fill and sprite modes to specific planes and
scanlines. There's enough fill rate to blow past any classic 8-bit
system — but push too hard and you'll see a half-blue screen telling you
that you went too far.

The built-in 8x8 and 8x16 fonts are available through the sentinel XRAM
pointer $FFFF. Glyphs 0-127 are ASCII; glyphs 128-255 vary by code page.

The built-in color palettes are reached the same way, through the
sentinel XRAM pointer $FFFF. 1-bit is black and white. 4-bit and 8-bit
modes start with an ANSI palette of 16 colors, followed by 216 colors
(6x6x6), then 24 grays.

16-bit colors are built with the bit logic below. Setting the alpha bit
makes a color opaque; clearing it makes the color transparent. Despite
the name, alpha here is a binary flag, not a blending factor. The
built-in ANSI palette has the alpha bit set on every color except color
0 (black), which is transparent.

.. code-block:: C

  #define COLOR_FROM_RGB8(r,g,b) (((b>>3)<<11)|((g>>3)<<6)|(r>>3))
  #define COLOR_FROM_RGB5(r,g,b) ((b<<11)|(g<<6)|(r))
  #define COLOR_ALPHA_MASK (1u<<5)

A palette is just an array. The 8bpp, 4bpp, and 1bpp modes use one;
16-bit-per-pixel modes aren't indexed and ignore the palette entirely.
Palettes must be 16-bit aligned.

.. code-block:: C

  struct {
      uint16_t color;
  } palette[2^bits_per_pixel];


You program the VGA device with `PIX extended registers
<ria.html#pix-extended-registers-xreg>`__ (XREGs). VGA is PIX device
ID 1. Registers are 16-bit values addressed as $device:$channel:register
— for example, $1:0:0F.

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

      * 0 - `Console <#mode-0-console>`__
      * 1 - `Character <#mode-1-character>`__
      * 2 - `Tile <#mode-2-tile>`__
      * 3 - `Bitmap <#mode-3-bitmap>`__
      * 4 - `Sprite 16-bit <#mode-4-sprite-16-bit>`__
      * 5 - `Sprite 1,2,4,8-bit <#mode-5-sprite-1-2-4-8-bit>`__


Mode 0: Console
---------------

The console can be rendered on any canvas plane. ANSI color 0 (black)
is transparent, which makes it easy to lay text over a background image
across planes. The console can occupy a partial screen, but its scanline
count must be a multiple of the font height. 640-pixel-wide canvases use
an 8x16 font for 80 columns; 320-pixel-wide canvases use an 8x8 font for
40 columns. Only one console can be visible at a time — programming
another removes the previous one.

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


Mode 1: Character
-----------------

Character modes carry color information for every cell on the screen, so
each character can have its own foreground and background. This is the
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

Fonts are encoded in a wide format: the first 256 bytes hold the first
row of all 256 glyphs, the next 256 bytes the second row, and so on.

.. code-block:: C

  struct {
    struct {
        uint8_t col[256];
    } row[height];
  } font;


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


Mode 3: Bitmap
--------------

Every pixel can be its own color. The 64 KB of XRAM caps how deep a
full-screen image can go: monochrome at 640x480, 16 colors at 320x240,
or 256 colors at 320x180 (16:9).

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

The data is color information packed down to the bit level. 16-bit color
encodes the color directly; 1-, 4-, and 8-bit color encode a palette
index instead.

Bit order traditionally follows the screen, so that left and right bit
shifts move pixels the way you'd expect. The reverse-bits option flips
the bit order of the 1- and 4-bit modes, which makes bit-level
manipulation code slightly smaller and faster.

Data for 16-bit color must be 16-bit aligned.

.. code-block:: C

  struct {
      struct {
          uint8_t cols[(width_px * bit_depth + 7) / 8];
      } rows[height_px];
  } data;


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

Move unused sprites off screen. Non-affine sprites use this config
structure:

.. code-block:: C

  typedef struct {
    int16_t x_pos_px;
    int16_t y_pos_px;
    uint16_t xram_sprite_ptr;
    uint8_t log_size;
    bool has_opacity_metadata;
  } vga_mode4_sprite_t;

Affine sprites apply a 3x3 matrix transform, which makes them slower
than plain sprites. Only the first two rows of the matrix matter —
that's why there are just six transform values — and they're in signed
8.8 fixed-point format.

.. code-block:: C

  typedef struct {
    int16_t transform[6];
    int16_t x_pos_px;
    int16_t y_pos_px;
    uint16_t xram_sprite_ptr;
    uint8_t log_size;
    bool has_opacity_metadata;
  } vga_mode4_asprite_t;


Sprite image data is an array of 16-bit colors.

.. code-block:: C

  struct {
    struct {
        uint16_t color[2^log_size];
    } rows[2^log_size];
  } data;


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

Disable unused sprites by moving them off screen.

.. code-block:: C

  typedef struct {
    int16_t x_pos_px;
    int16_t y_pos_px;
    uint16_t xram_sprite_ptr;
    uint16_t palette_ptr;
  } vga_mode5_sprite_t;

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

Because the PIX bus is unidirectional, the VGA system can't send data
straight back to the RIA. The UART Rx path won't do either — it would
add framing overhead or unusable control characters. But the PIX bus has
plenty of idle bandwidth (it only carries data when the 6502 writes to
XRAM), so all Tx data is routed over PIX, leaving the UART Tx pin free to
serve as a backchannel.

The 6502 programmer never has to think about this; it happens
automatically. This note is mainly for hardware explorers probing the
UART Tx pin.

Values 0x00 to 0x7F send a version string as ASCII, terminated by 0x0D
or 0x0A. Send it immediately after the backchannel-enable message
arrives for it to appear in the boot message.

When bit 0x80 is set, the 0x70 bits give the command type and the 0x0F
bits give a scalar for that command.

0x80 VSYNC - The scalar will increment and be used for the LSB of the
`RIA VSYNC <ria.html#registers>`__ register.

0x90 OP_ACK - Some XREG locations are triggers for remote calls which
may fail or take time to complete. This acknowledges a successful
completion.

0xA0 OP_NAK - This acknowledges a failure.
