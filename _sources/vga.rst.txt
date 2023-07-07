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

This is the current implementation. This is leftovers from validating the PIX bus. The bitmap modes are 4 bpp starting at VRAM 0x0000 with a fixed palette of ANSI colors.

 .. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:00
     - MODE
     - Select a graphics mode.
         * 0 - 80 Column Terminal mode.
         * 1 - 320x240 16 colors (4:3)
         * 2 - 320x180 16 colors (16:9)
   * - $F:FF
     - RESET
     - Always returns to terminal mode.

The following is a new design being worked on. It only exists in the "vga" branch.

The design philosophy for the VGA system is to enable the full power of the Pi Pico while maintaining some 8-bit purity. To that end, it can do affine transforms (mode 7) but is limited to working from 64K of extended memory (XRAM).

The VGA system is built around the scanvideo library from Pi Pico Extras. The color arrangement is identical to their demo board reference design, so sprites and other creations for the Pi Pico have a very good chance of working. This design uses the 16th color bit to render three planes with transparency. The sprite system is from Pi Pico Playground. The RP6502 VGA system exposes per-scanline configuration of these libraries from a 6502 application.

Each scanline has three fill planes. Two sprite layers can be drawn over each fill plane. If you draw too much, the screen will become half-blue. The VGA engine will begin rendering with scanline 0. It first renders fill plane 0 if a fill mode is programmed. Fill planes require modes that fill all pixels, like character and bitmap modes. If no fill plane is programmed, and sprites need to be rendered for this plane, a line of transparent black is automatically rendered (which takes time). Sprites are drawn over their fill plane, in order, over each other using the transparent bit. The process repeats for each fill plane, then repeats for each scanline.

Programming the VGA device should be done with the SDK system calls. These PIX registers are for reference and not yet stable. VGA is PIX device ID 1. VGA PIX extended register addresses store 16 bit values and are specified by $channel:register. e.g. $0:0F

The built-in 8x8 and 8x16 fonts are available by using the special XRAM pointer $FFFF. Glyphs 0-127 are ASCII, glyphs 128-255 vary depending on the code page selected.

The built-in color palettes are accessed by using the special XRAM pointer $FFFF. 1-bit is black and white. 2, 4, and 8-bits point to an ANSI color palette. This is defined as 16 colors, followed by 216 colors (6x6x6), followed by 24 greys.

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:00
    - VSYNC
    - Select which scanline number increments the frame counter and fires the optional IRQ.
  * - $0:01
    - CANVAS
    - Select a graphics canvas. This clears $0:03-$0:FF and all scanline programming. The 80 column console is used as a failsafe and therefore not scanline programmable.
        * 0 - 80 column console. (4:3 or 5:4)
        * 1 - 320x240 (4:3)
        * 2 - 320x180 (16:9)
        * 3 - 640x480 (4:3)
        * 4 - 640x360 (16:9)
  * - $0:02
    - MODE
    - Program a mode into a plane of scanlines. $0:03-$0:FF cleared after programming.
        * 0 - Console, ANSI Terminal
        * 1 - Character 8x8
        * 2 - Character 8x16
        * 3 - Tile 8x8
        * 4 - Tile 16x16
        * 5 - Bitmap
        * 6 - Sprite
        * 7 - Affine Sprite
  * - $0:03
    - PLANE
    - 0-3 to select which fill plane of scanlines to program.
  * - $0:04
    - SLBEGIN
    - First scanline to program. SLBEGIN \<= n \< SLEND
  * - $0:05
    - SLEND
    - End of scanlines to program. 0 means use max y resolution (180-480).


Mode 0: Console
---------------

There are no mode specific registers for the console. Programming the console for a partial screen will align the bottom row on the last scanline. The background is transparent, which makes it easy to show text over a background image using planes.

Mode 1-2: Character 8x8 & 8x16
------------------------------

Character modes have color information for each position on the screen. This is the mode you want for showing text in different colors.

Fonts are encoded in wide format. The first 256 bytes are the first row of 256 glyphs. This is the fastest layout, but wastes memory when not using the entire character set.

TODO: c, c(fb), cfb, (cc)(ff)(bb)

.. list-table::
  :widths: 5 5 90
  :header-rows: 1

  * - Address
    - Name
    - Description
  * - $0:06
    - COLORS
    - 2^(n+1) = 2, 4, 8, or 16 bit color
  * - $0:07
    - WRAP
    - | bit 7 - wrapx
      | bit 6 - wrapy
  * - $0:08
    - STRUCT
    - | Pointer to config structure in XRAM.
      | {
      |   int16_t xpos_px
      |   int16_t ypos_px
      |   int16_t width_chars
      |   int16_t height_chars
      |   uint16_t data_xram_ptr
      |   uint16_t color_table_xram_ptr
      |   uint16_t font_xram_ptr
      | }


Mode 3-4: Tile 8x8 & 16x16
--------------------------

Tile modes have color information encoded with the tiles. This is the mode you want for showing a video game playfield.

Tiles are encoded in tall format. The first bytes are the entire first glyph. The 16x16 mode also supports WCHAR for more than 256 characters, as memory permits.

TODO: b, ff, (ff), (ffff)

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:06
     - COLORS
     - 2^(n+1) = 2, 4, 8, or 16 bit color
   * - $0:07
     - WRAP
     - | bit 7 - wrapx
       | bit 6 - wrapy
   * - $0:08
     - STRUCT
     - | Pointer to config structure in XRAM.
       | {
       |   int16_t xpos_px
       |   int16_t ypos_px
       |   int16_t width_px
       |   int16_t height_px
       |   uint16_t data_xram_ptr
       |   uint16_t color_table_xram_ptr
       |   uint16_t tile_xram_ptr
       | }


Mode 5: Bitmap
--------------

Every pixel can be its own color. 64K XRAM has limits. Monochrome for 640x480, 256 color for 320x180, and 16 colors on 320x240.

TODO b, ff, (ff), (ffff)

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:06
     - COLORS
     - 2^(n+1) = 2, 4, 8, or 16 bit color
   * - $0:07
     - WRAP
     - | bit 7 - wrapx
       | bit 6 - wrapy
   * - $0:08
     - STRUCT
     - | Pointer to config structure in XRAM.
       | {
       |   int16_t xpos_px
       |   int16_t ypos_px
       |   int16_t width_px
       |   int16_t height_px
       |   uint16_t data_xram_ptr
       |   uint16_t color_table_xram_ptr
       | }


Mode 6: Sprite
--------------

Sprite images are log-sized (1x1, 2x2, 4x4, 8x8, etc.) arrays of 16-colors pixel data.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $0:06
     - LAYER
     - 0-1 Two sprite layers plane.
   * - $0:07
     - LENGTH
     - Length of sprite structure array in XRAM.
   * - $0:08
     - STRUCT
     - | Pointer to config structure array in XRAM.
       | {
       |   int16_t xpos_px
       |   int16_t ypos_px
       |   int16_t img_xram_ptr
       |   uint8_t log_size;
       |   bool has_opacity_metadata;
       | }

Mode 7: Affine Sprite
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
     - 0-1 Two sprite layers plane.
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
       |   int16_t img_xram_ptr
       |   uint8_t log_size;
       |   bool has_opacity_metadata;
       | }


Control Channel $F
------------------

These registers are managed by the RIA. Display and code page are settings. The backchannel is an internal resource.

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
     - Select code page for built-in font.
   * - $F:02
     - STDOUT
     - Alternate path for UART Tx when using backchannel.
   * - $F:03
     - BACKCHANREQ
     - Request UART Tx switch over to backchannel.
   * - $F:04
     - BACKCHANACK
     - Acknowledge UART Tx switch over to backchannel.
