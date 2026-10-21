==================================
VGA
==================================

Video Graphics Array

Introduction
============

The RP6502 Video Graphics Array (VGA) gives a 6502 program three planes
of graphics in 32,768 colors plus transparency. Each plane has a fill
layer of text, tiles, or a bitmap, with a sprite layer drawn over it. A
program can scroll a tile map under a text status bar, rotate and scale
sprites in 16-bit color, and switch a plane to a different mode partway
down the canvas without an interrupt. A program writes images and
settings into XRAM, and the VGA redraws the canvas from them every frame
with no further work from the 6502.

The VGA is a specification for a video system that connects to the
:doc:`ria` by PIX. A program controls the VGA with extended registers
(XREGs). On the :doc:`pico`, the VGA is the VGA module, a second Pico 2
that connects to the RIA by a 5-wire :ref:`PIX bus <pico-pix>`. A PIX
bus can connect more than one VGA. All of them share the same 64 KB of
XRAM. Only the first one increments the VSYNC register of the RIA, and
the RIA requests the VSYNC interrupt when it does.


Video Programming
=================

The VGA provides virtual video hardware modeled on the home computers
and arcades of the 8-bit and early-16-bit era. A program can mix and
match the modes freely, on different planes and on different ranges of
scanlines. Mode 0 draws the console. Mode 1 draws text that the program
writes into XRAM. Mode 2 draws tiles, mode 3 draws a bitmap, and modes 4
and 5 draw sprites.

A program puts an image on the canvas in four steps:

#. Select a canvas, the grid of pixels that the VGA draws. Selecting a
   canvas removes all modes, so it is the first step. It does not change
   XRAM.
#. Load the data of the image into XRAM.
#. Write the configuration structure of the mode into XRAM. It holds the
   XRAM address of the data and the position of the image on the
   canvas. A sprite mode uses a sprite array instead, with one structure
   for each sprite. Mode 0 uses neither.
#. Program the mode with ``xreg()``. The call also selects the plane and
   the scanlines of the mode.

This program fills a 320x240 canvas with blue. It uses mode 3, the
bitmap mode, in 4-bit color. The program is in C. An assembly program
uses the ``xram.inc`` code blocks of this page instead, and writes XRAM
through the :ref:`XRAM portals <ria-xram-portals>` of the RIA. To run
the program in your project:

#. Copy the ``xram.h`` code blocks of `Key Registers`_ and :ref:`Mode 3
   <vga-mode-3>` into ``xram.h``, above ``xram_layout_t``.
#. Replace the layout of the template and its ``XRAM_`` definitions
   with this layout. ``XRAM_BITMAP`` and ``XRAM_BITMAP_CONFIG`` are XRAM
   addresses from the layout, as :ref:`XRAM Memory Map
   <sdk-xram-memory-map>` in the :doc:`sdk` describes.

   .. code-block:: C

     typedef struct
     {
         uint8_t bitmap[38400u];
         mode3_config_t bitmap_config;
     } xram_layout_t;

     #define XRAM_BITMAP offsetof(xram_layout_t, bitmap)
     #define XRAM_BITMAP_CONFIG offsetof(xram_layout_t, bitmap_config)

#. Replace ``main.c`` with the program:

   .. code-block:: C

     #include <rp6502.h>
     #include <stdio.h>
     #include "xram.h"

     int main(void)
     {
         mode3_config_t config;

         xreg_vga_canvas(CANVAS_320X240);

         xram0_set(XRAM_BITMAP, 0x44, 38400u); // 320x240 pixels, two per byte

         config.x_wrap = false;
         config.y_wrap = false;
         config.x_pos_px = 0;
         config.y_pos_px = 0;
         config.width_px = 320;
         config.height_px = 240;
         config.xram_data_ptr = XRAM_BITMAP;
         config.xram_palette_ptr = 0xFFFF;
         xram0_write(XRAM_BITMAP_CONFIG, &config, sizeof(config));

         if (xreg_vga_mode3(MODE3_4BPP, XRAM_BITMAP_CONFIG) < 0)
         {
             xreg_vga_canvas(CANVAS_CONSOLE);
             puts("Mode 3 failed.");
             return 1;
         }

         while (1)
             ;
     }

``xreg_vga_canvas()`` selects the 320x240 canvas. ``xram0_set()`` fills
the bitmap with $44. In 4-bit color, each byte holds two pixels, so $44
is two pixels of color 4, which is blue in the built-in palette.

In place of ``xram0_set()``, a program usually gets its image from an
:ref:`asset <sdk-assets>`, which the RIA loads into XRAM before the
program starts. For this layout, ``rp6502_asset(hello XRAM(XRAM_BITMAP)
img/picture.bin)`` in ``CMakeLists.txt`` loads a file of 38,400 bytes in
the format of :ref:`Mode 3 <vga-mode-3>`. A program can also read the
image from a file with :c:func:`read_xram`.

The configuration structure gives the bitmap a position of 0, 0, the top
left of the canvas, and a palette address of $FFFF, which selects the
built-in palette. Last, ``xreg_vga_mode3()`` programs mode 3 in 4-bit
color, with the configuration structure at ``XRAM_BITMAP_CONFIG``. The
table of mode 3 also lists PLANE, BEGIN, and END, which select the plane
and the scanlines of the mode. Selecting a canvas clears them to 0, so
the call leaves them out, and mode 3 is on plane 0, over the whole
canvas.

When the VGA refuses a value, ``xreg()`` returns -1. A graphics canvas
with no mode 0 does not show the console, so the program selects the
console canvas before it reports the error. When a ROM stops, the VGA
returns to the console canvas, so the program ends in a loop that keeps
the ROM running.

``xreg_vga_canvas()`` and ``xreg_vga_mode3()`` are macros for
:ref:`xreg() <api-xreg>`, with the VGA as PIX device 1. Each register of
the VGA holds a 16-bit value. The tables of this page give the address
of each register as $device:channel:index, the first three arguments of
``xreg()``. The arguments of a mode macro are the registers in the table
of its mode, in order, from the register after MODE. `Key Registers`_
shows the same calls without the macros.


Canvas
------

Everything that the VGA draws is on the canvas, a grid of pixels such as
320x240. Scanlines are the rows of the canvas, numbered from 0 at the
top. The canvas does not set the resolution of the video output. The VGA
scales the canvas to fit the display, so 320x240 and 640x480 canvases
cover the same area, and a pixel on the 320x240 canvas is twice as wide
and twice as tall. Every canvas works on every display.

Canvas 0 is the console canvas. It shows only the console, and the VGA
refuses any mode on it. The other four canvases are the graphics
canvases, and a program selects one of them to draw. A graphics canvas
starts with no modes, so it shows no console until the program programs
mode 0. `Key Registers`_ lists the canvases.

A program places the text of mode 1, bitmaps, tile maps, and sprites on
the canvas at an x and y position in canvas pixels. A bitmap or a tile
map can be a different size than the canvas. One that is smaller covers
part of the canvas, and a program scrolls one that is larger by changing
its position.


Planes
------

The VGA draws the canvas from three planes. Each plane has two layers, a
fill layer and a sprite layer, and the VGA draws the sprite layer over
the fill layer. Modes 0 to 3 draw a fill layer, and modes 4 and 5 draw a
sprite layer. Plane 0 is at the back and plane 2 is at the front.

A pixel is transparent when the alpha bit of its color is clear, as
`Colors, Palettes, and Fonts`_ describes. A transparent pixel shows the
layer behind it. The fill layer of plane 0 is the exception: nothing is
behind it, so it shows the color of each of its pixels, even a
transparent one. Where no layer draws a pixel, the canvas is black.

There is no limit on the number of sprites, only on how many the VGA can
draw in the time of one scanline. Fill layers never run out of time: a
program can fill all three planes at any color depth on any canvas, on
every machine. :ref:`Sprite Limits <port-sprite-limits>` in :doc:`port`
shows how to count sprites against the time of one scanline.


Scanlines
---------

Programming a mode puts it on one plane, over a range of scanlines. The
PLANE register of each mode selects the plane, and the BEGIN and END
registers select the scanlines. BEGIN is the first scanline, and END is
one past the last. An END of 0 means the height of the canvas, so a mode
with BEGIN and END both 0 covers the whole canvas. Mode 0 on a 16:9
canvas is the exception, as `Mode 0: Console`_ describes.

Different ranges of the same plane can have different modes. That is how
you might implement a graphical text adventure, with half the screen for
text and the other half for graphics. The change of mode happens without
interrupts, which leaves more CPU headroom for your game logic. The VGA
has no scanline interrupt, so a change partway down the canvas is a
range of scanlines of its own.

Each range can have its own configuration structure, so each range can
scroll on its own. On a 320x240 canvas, these calls put a tile map on
scanlines 0 to 199 of plane 0, and a status bar of text below it, on
scanlines 200 to 239:

.. code-block:: C

  xreg_vga_mode2(MODE2_4BPP | MODE2_8X8, XRAM_MAP_CONFIG, 0, 0, 200);
  xreg_vga_mode1(MODE1_8BPP, XRAM_BAR_CONFIG, 0, 200);

In each call, the numbers after the configuration structure are PLANE,
BEGIN, and END. The second call leaves out END, so END is 0, the height
of the canvas. A position counts from the top left of the canvas, so the
configuration structure of the status bar has a ``y_pos_px`` of 200. A
program scrolls the map with the position in the configuration
structure at ``XRAM_MAP_CONFIG``, and the status bar does not move.

On each scanline, each layer of a plane has at most one mode.
Programming a mode replaces the old mode of that layer from BEGIN to
END, and the other scanlines keep their modes. Mode 0 is the exception,
as `Mode 0: Console`_ describes.


Configuration Structures
------------------------

Modes 1 to 3 draw from a configuration structure in XRAM. Modes 4 and 5
draw from a sprite array, an array in XRAM with one structure for each
sprite. A program may change these structures, and the data that they
point to, at any time without programming the mode again.

A change takes effect from the next scanline that the VGA draws, even
partway through a frame, so one frame can show the top of the old image
and the bottom of the new one. To change the whole canvas at once, a
program waits for the :ref:`VSYNC register <ria-registers>` of the RIA
to change, and then makes its changes. :c:func:`ria_vsync` returns the
register without waiting, so a program reads it until the value
changes:

.. code-block:: C

  unsigned char frame = ria_vsync();
  while (ria_vsync() == frame)
      ;

A program can also make its changes after the :ref:`VSYNC interrupt
<api-irq>`.

The VGA reads the registers of a mode, such as OPTIONS and LENGTH, only
when the program sets MODE. To change one of them, a program sets MODE
again, with all its arguments.

The configuration structures of modes 1 to 3 start with the same
members:

- When ``x_wrap`` is true, the VGA repeats the image across the canvas,
  and when ``y_wrap`` is true, down the canvas. Without wrap, the layer
  outside the image is transparent.
- ``x_pos_px`` and ``y_pos_px`` are the position of the top left pixel
  of the image, counted from the top left of the canvas, not from BEGIN.
  They may be negative.
- ``width_chars`` and ``height_chars``, ``width_tiles`` and
  ``height_tiles``, or ``width_px`` and ``height_px`` are the size of the
  image, in characters, tiles, or pixels.
- ``xram_data_ptr`` is the XRAM address of the data: the cells of mode
  1, the tile map of mode 2, or the bitmap of mode 3.
- ``xram_palette_ptr`` is the XRAM address of the palette, as `Colors,
  Palettes, and Fonts`_ describes.

Mode 1 adds ``xram_font_ptr``, and mode 2 adds ``xram_tile_ptr``. The
section of each mode describes them.

Each sprite in a sprite array has its own ``x_pos_px`` and ``y_pos_px``,
the position on the canvas of its top left pixel. A program moves a
sprite by writing its position. This code moves sprite ``n`` of a mode 5
sprite array at ``XRAM_SPRITES`` to ``x``, ``y``:

.. code-block:: C

  unsigned addr = XRAM_SPRITES + n * sizeof(mode5_sprite_t);
  xram0_poke16(addr + offsetof(mode5_sprite_t, x_pos_px), x);
  xram0_poke16(addr + offsetof(mode5_sprite_t, y_pos_px), y);

The VGA draws each sprite over the sprites before it in the array. To
hide a sprite, a program moves it off the canvas. A hidden sprite still
takes time on each scanline, as :ref:`Sprite Limits <port-sprite-limits>`
shows.

Configuration structures, sprite arrays, and palettes must be at even
XRAM addresses. Neither compiler pads a layout, so a member of odd size
moves every member after it by one byte, unless the layout adds a pad
byte. :ref:`Symbols in CMake <sdk-symbols-in-cmake>` in the :doc:`sdk`
shows how the build checks the addresses.


.. _vga-key-registers:

Key Registers
-------------

CANVAS and MODE are the key registers of channel 0: setting one of them
changes the picture. The VGA can refuse a value that it does not
support, and then ``xreg()`` fails with EINVAL.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $1:0:00
     - CANVAS
     - Selects a canvas, removes all modes, and clears $1:0:02-$1:0:FF.
       The VGA refuses any mode on the console canvas.

       * 0 - console (4:3 or 5:4)
       * 1 - 320x240 (4:3)
       * 2 - 320x180 (16:9)
       * 3 - 640x480 (4:3)
       * 4 - 640x360 (16:9)

   * - $1:0:01
     - MODE
     - Programs a mode on a plane, over a range of scanlines, and then
       clears $1:0:02-$1:0:FF. The section of each mode lists its
       registers.

       * 0 - :ref:`Console <vga-mode-0>`
       * 1 - :ref:`Character <vga-mode-1>`
       * 2 - :ref:`Tile <vga-mode-2>`
       * 3 - :ref:`Bitmap <vga-mode-3>`
       * 4 - :ref:`Sprite 16-bit <vga-mode-4>`
       * 5 - :ref:`Sprite 1,2,4,8-bit <vga-mode-5>`

Each of these calls selects the 320x240 canvas:

.. code-block:: C

  xreg(0x1, 0x0, 0x00, 1);         // 320x240 canvas
  xreg_vga_canvas(CANVAS_320X240); // macro shortcut

A mode needs more values than MODE holds, such as its options and the
XRAM address of its configuration structure. These values go in the
argument registers after MODE, $1:0:02-$1:0:FF, and the VGA reads them
when the program sets MODE. One ``xreg()`` call sets MODE and its
arguments together:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 3, 2, 0xFF00);

This call sets MODE ($1:0:01) to 3, the :ref:`bitmap mode <vga-mode-3>`.
It also sets $1:0:02 to 2, which selects 4-bit color, and $1:0:03 to
$FF00, the XRAM address of the configuration structure of the mode. MODE
gets its arguments even though they come after it in the call, because
the RIA sets the argument registers before MODE. Every value after MODE
in a call goes to an argument register, so one call programs at most
one mode. An earlier call can also set the arguments, and a later call
then sets MODE alone.

Setting CANVAS or MODE clears the argument registers, so an argument
that no call has set since then is 0. The call above leaves out PLANE,
BEGIN, and END, so it programs mode 3 on plane 0 over the whole canvas.

One call can also select the canvas and program the first mode, which is
all the video setup that many programs need:

.. code-block:: C

  xreg(0x1, 0x0, 0x00, 1, 3, 2, 0xFF00);

The RIA sets the key registers in order, from the lowest index, so this
call selects the 320x240 canvas first, and then programs mode 3. CANVAS
clears the argument registers before the RIA sets the arguments of
MODE, so mode 3 gets the arguments 2 and $FF00.

When the VGA refuses a value, the registers that the call set before the
refusal keep their new values. If the VGA refuses the mode of this call,
the 320x240 canvas stays selected with no modes. The canvas is black,
and the console is not visible. To show an error message, a program
first selects the console canvas or programs mode 0, as the program in
`Video Programming`_ does.

.. tab:: C

   .. code-block:: C
      :caption: xram.h (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      #define xreg_vga_canvas(...) xreg(0x1, 0x0, 0x00, __VA_ARGS__)

      #define CANVAS_CONSOLE 0
      #define CANVAS_320X240 1
      #define CANVAS_320X180 2
      #define CANVAS_640X480 3
      #define CANVAS_640X360 4

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      .macro xreg_vga_canvas canvas
          xreg $1, $0, $00, canvas
      .endmacro

      CANVAS_CONSOLE = 0
      CANVAS_320X240 = 1
      CANVAS_320X180 = 2
      CANVAS_640X480 = 3
      CANVAS_640X360 = 4

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)
      :force:

      .macro xreg_vga_canvas canvas
          xreg $1, $0, $00, \canvas
      .endm

      CANVAS_CONSOLE = 0
      CANVAS_320X240 = 1
      CANVAS_320X180 = 2
      CANVAS_640X480 = 3
      CANVAS_640X360 = 4


Colors, Palettes, and Fonts
---------------------------

All three planes use RGB555 color plus transparency. A color is a 16-bit
value: red is in bits 0-4, the alpha bit is bit 5, green is in bits
6-10, and blue is in bits 11-15. The macros below build colors.
``COLOR_FROM_RGB8`` takes red, green, and blue from 0 to 255, and
``COLOR_FROM_RGB5`` takes them from 0 to 31.

Setting the alpha bit makes a color opaque, and clearing it makes the
color transparent. Despite the name, alpha here is a binary flag, not a
blending factor. `Planes`_ describes what a transparent pixel shows.

In C, ``COLOR_FROM_RGB8`` and ``COLOR_FROM_RGB5`` leave the alpha bit
clear, so an opaque color needs ``COLOR_ALPHA_MASK``.
``COLOR_FROM_RGB8(255, 0, 0) | COLOR_ALPHA_MASK`` is opaque red. In
assembly, each macro emits a ``.word``, and takes ``COLOR_ALPHA_MASK``
as an optional fourth argument. ``COLOR_FROM_RGB8 255, 0, 0,
COLOR_ALPHA_MASK`` is opaque red.

.. tab:: C

   .. code-block:: C
      :caption: xram.h (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      #define COLOR_FROM_RGB8(r, g, b) \
          ((((unsigned)(b) >> 3) << 11) | (((unsigned)(g) >> 3) << 6) | ((unsigned)(r) >> 3))
      #define COLOR_FROM_RGB5(r, g, b) \
          (((unsigned)(b) << 11) | ((unsigned)(g) << 6) | (unsigned)(r))
      #define COLOR_ALPHA_MASK (1u << 5)

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

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
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)
      :force:

      COLOR_ALPHA_MASK = 1 << 5

      .macro COLOR_FROM_RGB8 r, g, b, alpha=0
          .word ((((\b) >> 3) << 11) | (((\g) >> 3) << 6) | ((\r) >> 3) | (\alpha))
      .endm

      .macro COLOR_FROM_RGB5 r, g, b, alpha=0
          .word (((\b) << 11) | ((\g) << 6) | (\r) | (\alpha))
      .endm

In 1-, 2-, 4-, and 8-bit color, each pixel, or each color of a mode 1
cell, is a palette index, and a palette is the array of colors that the
indexes select. In 16-bit color, each pixel is its own color, and the
VGA ignores the palette.

.. code-block:: C

  uint16_t palette[1 << bits_per_pixel];

A palette address of $FFFF selects the built-in palette. In 1-bit color,
the built-in palette is black and white. In 8-bit color, it is the 16
ANSI colors, then 216 colors (6x6x6), and then 24 grays. 2-bit and 4-bit
color use the first 4 and the first 16 of these colors. Colors 0 to 7
are black, red, green, yellow, blue, magenta, cyan, and white, and
colors 8 to 15 are bright versions of them.

At every color depth, color 0 (black) of the built-in palette is
transparent, and every other color is opaque. Color 16 is also black,
and it is opaque. Only 8-bit color has color 16, so with the built-in
palette, 1-, 2-, and 4-bit color have no opaque black.

In a bitmap, a tile, or a mode 5 sprite in 1-, 2-, or 4-bit color, each
byte holds 8, 4, or 2 pixels. The leftmost pixel is in the most
significant bits, unless mode 3 reverses the order. In 4-bit color, the
byte $12 is a pixel of color 1 and then a pixel of color 2.

A font holds 256 glyphs, each 8 pixels wide and 8 or 16 pixels tall, in
a wide format: the first 256 bytes hold the first row of all 256 glyphs,
the next 256 bytes the second row, and so on. In each byte, bit 7 is the
leftmost pixel, and a 1 bit is a pixel in the foreground color.

.. code-block:: C

  struct {
    struct {
        uint8_t col[256];
    } row[height];
  } font;

A font address of $FFFF selects the built-in 8x8 or 8x16 font. Glyphs
0-127 are ASCII, and glyphs 128-255 vary by code page, which
:ref:`RIA_ATTR_CODE_PAGE <api-ria-attributes>` selects.


.. _vga-mode-0:

Mode 0: Console
---------------

Mode 0 draws the console on a plane of a graphics canvas. :doc:`term`
describes the console and its escape sequences.

The default background of console text is ANSI color 0 (black), which is
transparent. Console text on a plane in front of an image shows the
image around the glyphs.

On a canvas 640 pixels wide, the console uses an 8x16 font for 80
columns. On a canvas 320 pixels wide, it uses an 8x8 font for 40
columns. Each row of text is one font tall, and the first row is at
BEGIN. To put the console on part of the canvas, make END minus BEGIN a
whole number of rows. The VGA refuses any other range, except BEGIN and
END both 0. The 320x180 and 640x360 canvases are 22½ rows tall, so on
them, BEGIN and END both 0 put 22 rows of text in the middle of the
canvas.

Only one console can be visible at a time. Programming another removes
the previous one.

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
     - The plane, 0-2.
   * - $1:0:03
     - BEGIN
     - The first scanline.
   * - $1:0:04
     - END
     - One past the last scanline, or 0 for the height of the canvas.

Each of these calls programs the console on plane 0:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 0, 0); // console on plane 0
  xreg_vga_mode0(0);          // macro shortcut

.. tab:: C

   .. code-block:: C
      :caption: xram.h (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      #define xreg_vga_mode0(...) xreg(0x1, 0x0, 0x01, 0, __VA_ARGS__)

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      .macro xreg_vga_mode0 plane, begin, end
          xreg $1, $0, $01, 0, plane, begin, end
      .endmacro

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)
      :force:

      .macro xreg_vga_mode0 values:vararg
          xreg $1, $0, $01, 0, \values
      .endm


.. _vga-mode-1:

Mode 1: Character
-----------------

Character modes carry color information for every cell, so each
character can have its own foreground and background. This is the mode
you want for colorful text — menus, status bars, anything where the
glyphs change color. Unlike the console, which shows what a program
writes to ``stdout``, mode 1 draws cells that the program writes into
XRAM. A cell is one character on the canvas: a glyph code and its
colors. Mode 1 has no cursor. Its text does not move up when the last
row is full, as the text of the console does.

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
     - | bit 0:2 - 0=1, 1=4 reversed, 2=4, 3=8, or 4=16 bit color
       | bit 3 - font size 0=8x8, 1=8x16
   * - $1:0:03
     - CONFIG
     - The XRAM address of the configuration structure. Must be even.
   * - $1:0:04
     - PLANE
     - The plane, 0-2.
   * - $1:0:05
     - BEGIN
     - The first scanline.
   * - $1:0:06
     - END
     - One past the last scanline, or 0 for the height of the canvas.

Each of these calls programs mode 1 in 8-bit color on plane 0, with the
configuration structure at ``xaddr``:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 1, 3, xaddr, 0); // 8-bit color on plane 0
  xreg_vga_mode1(MODE1_8BPP, xaddr, 0); // macro shortcut

The configuration structure is ``mode1_config_t``, and `Configuration
Structures`_ describes the members that it shares with modes 2 and 3.
``xram_font_ptr`` is the XRAM address of the font, or $FFFF for the
built-in font. `Colors, Palettes, and Fonts`_ describes fonts. Bit 3 of
OPTIONS selects 8x8 or 8x16 glyphs, on any canvas. With the built-in
font, the glyph code of a character is its ASCII code.

The data is an array of cells, ``width_chars`` * ``height_chars`` long,
stored row by row from the top left. Each row of cells is one font
tall, and each cell is 8 pixels wide, so 40 cells fill a row of a canvas
320 pixels wide. Each cell is a glyph code and its colors, in the format
of the color depth. The code blocks below give a type for each format,
such as ``mode1_8bpp_data_t``.

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
     - glyph_code, attributes, fg_color, bg_color. The colors are 16-bit.
       The VGA ignores the attributes, so a program can use them for its
       own data.

In 1-bit color, a cell holds only a glyph code, and every cell uses
color 1 of the palette for the foreground and color 0 for the
background. In 4-bit color, the high four bits of ``bg_fg_index`` are
the background and the low four bits are the foreground. The reversed
index swaps the two colors in the byte, not the order of its bits, so
the high four bits of ``fg_bg_index`` are the foreground.
``MODE1_BG_FG()`` and ``MODE1_FG_BG()`` build these bytes.

With the built-in palette, color 0 is transparent, so a background of
color 0 shows the layer behind it, or black on plane 0. For an opaque
black background, use 8-bit color with a ``bg_index`` of 16, or a
palette of your own.

This program puts a status bar of 3 rows of 40 cells, bright white on
blue, on the bottom 24 scanlines of a 320x240 canvas, and writes
``SCORE`` at its left end. To run it, copy the ``xram.h`` code blocks of
`Key Registers`_ and this section into ``xram.h``, and use this layout:

.. code-block:: C

  typedef struct
  {
      mode1_8bpp_data_t bar[3 * 40];
      mode1_config_t bar_config;
  } xram_layout_t;

  #define XRAM_BAR offsetof(xram_layout_t, bar)
  #define XRAM_BAR_CONFIG offsetof(xram_layout_t, bar_config)

.. code-block:: C

  #include <rp6502.h>
  #include "xram.h"

  int main(void)
  {
      static const char text[] = "SCORE";
      mode1_config_t config;
      mode1_8bpp_data_t cell;
      unsigned i;

      xreg_vga_canvas(CANVAS_320X240);

      config.x_wrap = false;
      config.y_wrap = false;
      config.x_pos_px = 0;
      config.y_pos_px = 216;
      config.width_chars = 40;
      config.height_chars = 3;
      config.xram_data_ptr = XRAM_BAR;
      config.xram_palette_ptr = 0xFFFF;
      config.xram_font_ptr = 0xFFFF;
      xram0_write(XRAM_BAR_CONFIG, &config, sizeof(config));

      cell.fg_index = 15; // bright white
      cell.bg_index = 4;  // blue
      for (i = 0; i < 3 * 40; i++)
      {
          cell.glyph_code = i < sizeof(text) - 1 ? text[i] : ' ';
          xram0_write(XRAM_BAR + i * sizeof(cell), &cell, sizeof(cell));
      }

      xreg_vga_mode1(MODE1_8BPP, XRAM_BAR_CONFIG, 0, 216);

      while (1)
          ;
  }

To put the bar over the bitmap of the program in `Video Programming`_,
program it on plane 1, or on plane 0 after mode 3, where it then
replaces mode 3 on scanlines 216 to 239.

.. tab:: C

   .. code-block:: C
      :caption: xram.h (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      #define xreg_vga_mode1(...) xreg(0x1, 0x0, 0x01, 1, __VA_ARGS__)

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
      } mode1_config_t; /* layout */

      typedef struct
      {
          uint8_t glyph_code;
      } mode1_1bpp_data_t; /* layout */

      typedef struct
      {
          uint8_t glyph_code;
          uint8_t fg_bg_index;
      } mode1_4bppr_data_t; /* layout */

      typedef struct
      {
          uint8_t glyph_code;
          uint8_t bg_fg_index;
      } mode1_4bpp_data_t; /* layout */

      typedef struct
      {
          uint8_t glyph_code;
          uint8_t fg_index;
          uint8_t bg_index;
      } mode1_8bpp_data_t; /* layout */

      typedef struct
      {
          uint8_t glyph_code;
          uint8_t attributes;
          uint16_t fg_color;
          uint16_t bg_color;
      } mode1_16bpp_data_t; /* layout */

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      .macro xreg_vga_mode1 options, config, plane, begin, end
          xreg $1, $0, $01, 1, options, config, plane, begin, end
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
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)
      :force:

      .macro xreg_vga_mode1 values:vararg
          xreg $1, $0, $01, 1, \values
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
     - The XRAM address of the configuration structure. Must be even.
   * - $1:0:04
     - PLANE
     - The plane, 0-2.
   * - $1:0:05
     - BEGIN
     - The first scanline.
   * - $1:0:06
     - END
     - One past the last scanline, or 0 for the height of the canvas.

Each of these calls programs mode 2 with 8x8 tiles in 4-bit color on
plane 0, with the configuration structure at ``xaddr``:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 2, 2, xaddr, 0);             // 4-bit color 8x8 tiles on plane 0
  xreg_vga_mode2(MODE2_4BPP | MODE2_8X8, xaddr, 0); // macro shortcut

The configuration structure is ``mode2_config_t``, and `Configuration
Structures`_ describes the members that it shares with modes 1 and 3.
``x_pos_px`` and ``y_pos_px`` are the position of the top left of the
map on the canvas, so a program scrolls the map by writing them. To show
the map from its pixel column 100 at the left edge of the canvas, a
program sets ``x_pos_px`` to -100.

The data is a tile map: an array of tile IDs, ``width_tiles`` *
``height_tiles`` long, stored row by row from 0,0 at the top left.

.. code-block:: C

  struct {
      uint8_t tile_id;
  } data[width_tiles * height_tiles];

Each tile ID is an index into the tile array at ``xram_tile_ptr``, which
holds up to 256 tiles. The tile array can hold fewer than 256 tiles. It
needs the tiles up to the highest tile ID that the map uses. For a tile
ID past the end of the array, the VGA draws the bytes that follow the
array in XRAM as the tile. For a tile whose data would extend past the
end of XRAM, it draws transparent black.

An entry of the map holds only a tile ID, so all the tiles of one map
use the palette at ``xram_palette_ptr``. In 4-bit color, the palette is
16 colors, as `Colors, Palettes, and Fonts`_ describes.

Tiles are in a "tall" bitmap format, where every row of one tile is
stored, top to bottom, before the next tile begins. A row of a tile is
``width * bits_per_pixel / 8`` bytes long, so an 8x8 tile in 4-bit color
has 8 rows of 4 bytes, 32 bytes in all. `Colors, Palettes, and Fonts`_
gives the order of the pixels in a byte. ``MODE2_TILE`` declares the
structure of one tile from its color depth and tile size, so ``typedef
MODE2_TILE(4, 8) tile_t;`` is an 8x8 tile in 4-bit color.

With trim, the VGA draws tiles of other sizes, such as 12x12, from tiles
stored at 8x8 or 16x16. X trim drops columns off the right of each tile,
and Y trim drops rows off the bottom. In C, ``MODE2_X_TRIM()`` and
``MODE2_Y_TRIM()`` put them in OPTIONS. Each tile keeps its full base
size in XRAM, and the VGA does not draw the dropped pixels. A 16x16 tile
with X trim 5 and Y trim 6 draws as 11x10, and the VGA places the tiles
of the map 11 pixels apart across and 10 pixels apart down.

.. tab:: C

   .. code-block:: C
      :caption: xram.h (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      #define xreg_vga_mode2(...) xreg(0x1, 0x0, 0x01, 2, __VA_ARGS__)

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
      } mode2_config_t; /* layout */

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      .macro xreg_vga_mode2 options, config, plane, begin, end
          xreg $1, $0, $01, 2, options, config, plane, begin, end
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
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)
      :force:

      .macro xreg_vga_mode2 values:vararg
          xreg $1, $0, $01, 2, \values
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
     - The XRAM address of the configuration structure. Must be even.
   * - $1:0:04
     - PLANE
     - The plane, 0-2.
   * - $1:0:05
     - BEGIN
     - The first scanline.
   * - $1:0:06
     - END
     - One past the last scanline, or 0 for the height of the canvas.

Each of these calls programs mode 3 in 4-bit color on plane 0, with the
configuration structure at ``xaddr``:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 3, 2, xaddr, 0); // 4-bit color on plane 0
  xreg_vga_mode3(MODE3_4BPP, xaddr, 0); // macro shortcut

The configuration structure is ``mode3_config_t``, and `Configuration
Structures`_ describes its members. The data is a bitmap of
``height_px`` rows, from the top down, and each row starts on a byte
boundary. In 16-bit color, each pixel is a 16-bit color, low byte first.

.. code-block:: C

  struct {
      struct {
          uint8_t cols[(width_px * bits_per_pixel + 7) / 8];
      } rows[height_px];
  } data;

Bit order traditionally follows the canvas, so that left and right bit
shifts move pixels the way you'd expect. In 1-, 2-, and 4-bit color,
bit 3 of OPTIONS reverses the order of the pixels in each byte, so that
the leftmost pixel is in the least significant bits. The bits of each
pixel keep their order. The reversed order makes bit-level manipulation
code slightly smaller and faster.

.. tab:: C

   .. code-block:: C
      :caption: xram.h (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      #define xreg_vga_mode3(...) xreg(0x1, 0x0, 0x01, 3, __VA_ARGS__)

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
      } mode3_config_t; /* layout */

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      .macro xreg_vga_mode3 options, config, plane, begin, end
          xreg $1, $0, $01, 3, options, config, plane, begin, end
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
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)
      :force:

      .macro xreg_vga_mode3 values:vararg
          xreg $1, $0, $01, 3, \values
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

The VGA can draw sprites over any fill layer. This is the same 16-bit
sprite system used by Pi Pico Playground and Luke Wren's RISCBoy. Its
appetite for memory is offset by something mode 5 can't do — affine
transforms.

There is no fixed number of sprites. For a game near the limits, see
:ref:`Sprite Limits <port-sprite-limits>`.

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
     - The XRAM address of the sprite array. Must be even.
   * - $1:0:04
     - LENGTH
     - The number of sprites in the sprite array.
   * - $1:0:05
     - PLANE
     - The plane, 0-2.
   * - $1:0:06
     - BEGIN
     - The first scanline.
   * - $1:0:07
     - END
     - One past the last scanline, or 0 for the height of the canvas.

Each of these calls programs ``length`` sprites on plane 1, from the
sprite array at ``xaddr``:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 4, 0, xaddr, length, 1); // sprites on plane 1
  xreg_vga_mode4(0, xaddr, length, 1);          // macro shortcut

When bit 0 of OPTIONS, ``MODE4_AFFINE_BIT``, is clear, the sprite array
holds ``mode4_sprite_t``. When it is set, the sprite array holds
``mode4_asprite_t``, for affine sprites. `Configuration Structures`_
describes how a program moves sprites and in what order the VGA draws
them. ``xram_sprite_ptr`` is the XRAM address of the image of the
sprite.

The image is an array of 16-bit colors. A sprite is a square of
2^log_size pixels a side, from 1x1 up to 128x128. A ``log_size`` above 7
describes a square too large for XRAM, and the VGA draws nothing for it.
``MODE4_IMAGE`` declares the structure of one image from its
``log_size``, so ``typedef MODE4_IMAGE(4) image_t;`` is a 16x16 image.

Opacity metadata lets the VGA skip the transparent pixels at the ends of
each row, so a sprite with transparent ends can take less of the time
of a scanline. When ``has_opacity_metadata`` is true, one little-endian
32-bit value for each row follows the image. Each value gives the
opaque span of its row, in pixels from the left of the image. Bits 15-0
are the end of the span (exclusive), and bits 30-16 are its start. The
VGA does not draw the pixels outside the span. ``MODE4_SPAN`` builds
one row of opacity metadata.

When bit 31 is set, the span is solid. The VGA draws all of a solid span
without checking the alpha bit of each color. Mark a span solid only
when every color in it is opaque.

An image, with its metadata, must fit in XRAM, or the VGA draws nothing
for the sprite. Affine sprites do not use the metadata, but when
``has_opacity_metadata`` is true, its bytes still count toward the size
of the sprite.

Affine sprites apply a 3x3 matrix transform, which makes them slower
than plain sprites. Only the first two rows of the matrix matter, which
is why there are just six transform values. They are in signed 8.8
fixed-point format, in the order {a00, a01, b0, a10, a11, b1}, and
``MODE4_AFFINE_A00`` to ``MODE4_AFFINE_B1`` are their indexes in
``transform``. The matrix maps a position within the sprite on the
canvas to a position in the image. The pixel at x, y from the top left
of the sprite shows the pixel of the image at u, v:

.. code-block:: text

  u = a00 * x + a01 * y + b0
  v = a10 * x + a11 * y + b1

With the transform {``MODE4_AFFINE_ONE``, 0, 0, 0, ``MODE4_AFFINE_ONE``,
0}, the VGA draws the image as it is. The matrix maps the canvas to the
image, so it holds the inverse of the change that appears on the canvas.
With $0200 (2.0) in a00 and a11, the VGA steps through the image two
pixels for each pixel of the canvas, so the image appears at half size.

These values rotate the image by an angle t about the center of its
square. In them, size is the width of the square in pixels, and c is
(size - 1) / 2:

.. code-block:: text

  a00 = cos t    a01 = sin t    b0 = c - c * cos t - c * sin t
  a10 = -sin t   a11 = cos t    b1 = c + c * sin t - c * cos t

Multiply each value by ``MODE4_AFFINE_ONE`` to put it in 8.8 format. A
positive t turns the image clockwise. These values fit the 8.8 format
for sprites up to 64x64. The VGA draws an affine sprite only inside its
own square, so an image that a program rotates needs a transparent
margin around it.

.. tab:: C

   .. code-block:: C
      :caption: xram.h (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      #define xreg_vga_mode4(...) xreg(0x1, 0x0, 0x01, 4, __VA_ARGS__)

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
      } mode4_sprite_t; /* layout */

      typedef struct
      {
          int16_t transform[6];
          int16_t x_pos_px;
          int16_t y_pos_px;
          uint16_t xram_sprite_ptr;
          uint8_t log_size;
          bool has_opacity_metadata;
      } mode4_asprite_t; /* layout */

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      .macro xreg_vga_mode4 options, config, length, plane, begin, end
          xreg $1, $0, $01, 4, options, config, length, plane, begin, end
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
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)
      :force:

      .macro xreg_vga_mode4 values:vararg
          xreg $1, $0, $01, 4, \values
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
color depth. The VGA can draw these sprites over any fill layer,
including an empty one. For example, you might put affine sprites of
mode 4 for explosions and the player on one plane, 16x16 enemy sprites
in 4-bit color on a second, and 8x8 bullets in 1-bit color on the third.
Custom sprites, described below, let one plane mix sprites of different
sizes, color depths, and orientations.

There is no fixed number of sprites. For a game near the limits, see
:ref:`Sprite Limits <port-sprite-limits>`.

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
       | bit 3:5 - 0=8x8, 1=16x16, 2=32x32, 3=64x64, 4=128x128,
         5=256x256, 6=512x512, 7=custom
       | 512x512 only supports 1-bit and 2-bit color.
       | With 7=custom, the VGA ignores bits 0:2, and each sprite in the
         sprite array sets its own size and color depth.
   * - $1:0:03
     - CONFIG
     - The XRAM address of the sprite array. Must be even.
   * - $1:0:04
     - LENGTH
     - The number of sprites in the sprite array.
   * - $1:0:05
     - PLANE
     - The plane, 0-2.
   * - $1:0:06
     - BEGIN
     - The first scanline.
   * - $1:0:07
     - END
     - One past the last scanline, or 0 for the height of the canvas.

These calls program 16x16 sprites in 4-bit color on plane 1, from the
sprite array at ``xaddr``, and custom sprites on plane 2, from a second
sprite array at ``xaddr2``:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 5, 0x0A, xaddr, length, 1);            // 16x16 4-bit, plane 1
  xreg_vga_mode5(MODE5_4BPP | MODE5_16X16, xaddr, length, 1); // macro shortcut
  xreg_vga_mode5(MODE5_CUSTOM, xaddr2, length2, 2);           // custom sprites, plane 2

The sprite array holds ``mode5_sprite_t``. `Configuration Structures`_
describes how a program moves sprites and in what order the VGA draws
them. ``xram_sprite_ptr`` is the XRAM address of the image of the
sprite, and ``palette_ptr`` is the XRAM address of its palette, so each
sprite can have its own palette. On the :doc:`fpga`, the VGA draws
sprites fastest when all their palettes fit in one 1 KB block of XRAM,
as :ref:`Sprite Limits <port-sprite-limits>` explains.

The VGA draws a pixel of a sprite only where its color has the alpha bit
set. A sprite palette needs the alpha bit in each color that shows, and
a clear alpha bit in its transparent color. With a ``palette_ptr`` of
$FFFF, a sprite uses the built-in palette, in which color 0 is
transparent.

The image is in the format of one :ref:`mode 2 <vga-mode-2>` tile. A
16x16 image in 4-bit color is 16 rows of 8 bytes, 128 bytes in all.
``MODE5_IMAGE`` declares the structure of one image from its color depth
and sprite size, so ``typedef MODE5_IMAGE(4, 16) image_t;`` is a 16x16
image in 4-bit color.

With OPTIONS set to custom, the sprite array holds ``mode5_csprite_t``,
and each sprite sets its own size, color depth, and orientation. The VGA
flips and doubles only custom sprites. Their flags go in the member
``options`` of each sprite. They must not go in the OPTIONS register,
where bits 3:5 select the size of the sprites. ``MODE5_4BPP |
MODE5_16X16 | MODE5_HFLIP`` in OPTIONS selects 64x64 sprites, not
flipped ones.

- ``width_height`` holds the width and height, each 4 to 64 pixels in
  steps of 4. ``MODE5_SIZE(width, height)`` builds it.
- Bits 0:2 of ``options`` hold the color depth, with the same values as
  bits 0:2 of OPTIONS. Bit 3 is reserved and must be 0.
- ``MODE5_HFLIP`` and ``MODE5_VFLIP`` in ``options`` flip the image left
  to right and top to bottom.
- ``MODE5_HDOUBLE`` and ``MODE5_VDOUBLE`` in ``options`` draw each pixel
  twice across or down, so a doubled 16x16 image covers 32x32 canvas
  pixels.

``MODE5_CUSTOM_IMAGE`` declares one image from its color depth, width,
and height, so ``typedef MODE5_CUSTOM_IMAGE(4, 24, 16) image_t;`` is a
24x16 image in 4-bit color. Each row of the image starts on a byte
boundary.

.. tab:: C

   .. code-block:: C
      :caption: xram.h (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      #define xreg_vga_mode5(...) xreg(0x1, 0x0, 0x01, 5, __VA_ARGS__)

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
      #define MODE5_CUSTOM 0x38

      #define MODE5_HFLIP 0x10
      #define MODE5_VFLIP 0x20
      #define MODE5_HDOUBLE 0x40
      #define MODE5_VDOUBLE 0x80

      #define MODE5_IMAGE(bpp, size)                \
          struct                                    \
          {                                         \
              struct                                \
              {                                     \
                  uint8_t cols[(size) * (bpp) / 8]; \
              } rows[size];                         \
          }

      #define MODE5_SIZE(width, height) \
          ((((height) / 4 - 1) << 4) | ((width) / 4 - 1))

      #define MODE5_CUSTOM_IMAGE(bpp, width, height)       \
          struct                                           \
          {                                                \
              struct                                       \
              {                                            \
                  uint8_t cols[((width) * (bpp) + 7) / 8]; \
              } rows[height];                              \
          }

      typedef struct
      {
          int16_t x_pos_px;
          int16_t y_pos_px;
          uint16_t xram_sprite_ptr;
          uint16_t palette_ptr;
      } mode5_sprite_t; /* layout */

      typedef struct
      {
          int16_t x_pos_px;
          int16_t y_pos_px;
          uint16_t xram_sprite_ptr;
          uint16_t palette_ptr;
          uint8_t width_height;
          uint8_t options;
      } mode5_csprite_t; /* layout */

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      .macro xreg_vga_mode5 options, config, length, plane, begin, end
          xreg $1, $0, $01, 5, options, config, length, plane, begin, end
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
      MODE5_CUSTOM  = $38

      MODE5_HFLIP   = $10
      MODE5_VFLIP   = $20
      MODE5_HDOUBLE = $40
      MODE5_VDOUBLE = $80

      .macro MODE5_IMAGE name, bpp, size
          .struct name
              rows .struct
                  cols .res (size) * (bpp) / 8
              .endstruct
              .res ((size) - 1) * .sizeof(rows)
          .endstruct
      .endmacro

      .macro MODE5_SIZE width, height
          .byte (((height) / 4 - 1) << 4) | ((width) / 4 - 1)
      .endmacro

      .macro MODE5_CUSTOM_IMAGE name, bpp, width, height
          .struct name
              rows .struct
                  cols .res ((width) * (bpp) + 7) / 8
              .endstruct
              .res ((height) - 1) * .sizeof(rows)
          .endstruct
      .endmacro

      .struct mode5_sprite_t
          x_pos_px        .word
          y_pos_px        .word
          xram_sprite_ptr .word
          palette_ptr     .word
      .endstruct

      .struct mode5_csprite_t
          x_pos_px        .word
          y_pos_px        .word
          xram_sprite_ptr .word
          palette_ptr     .word
          width_height    .byte
          options         .byte
      .endstruct

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)
      :force:

      .macro xreg_vga_mode5 values:vararg
          xreg $1, $0, $01, 5, \values
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
      MODE5_CUSTOM  = $38

      MODE5_HFLIP   = $10
      MODE5_VFLIP   = $20
      MODE5_HDOUBLE = $40
      MODE5_VDOUBLE = $80

      .macro MODE5_IMAGE name, bpp, size
          \name\()_ROWS      = 0
          \name\()_ROWS_COLS = 0
          \name\()_ROWS_SIZE = (\size) * (\bpp) / 8
          \name\()_SIZE      = (\size) * \name\()_ROWS_SIZE
      .endm

      .macro MODE5_SIZE width, height
          .byte ((((\height) / 4 - 1) << 4) | ((\width) / 4 - 1))
      .endm

      .macro MODE5_CUSTOM_IMAGE name, bpp, width, height
          \name\()_ROWS      = 0
          \name\()_ROWS_COLS = 0
          \name\()_ROWS_SIZE = ((\width) * (\bpp) + 7) / 8
          \name\()_SIZE      = (\height) * \name\()_ROWS_SIZE
      .endm

      MODE5_SPRITE_X_POS_PX        = 0
      MODE5_SPRITE_Y_POS_PX        = 2
      MODE5_SPRITE_XRAM_SPRITE_PTR = 4
      MODE5_SPRITE_PALETTE_PTR     = 6
      MODE5_SPRITE_SIZE            = 8

      MODE5_CSPRITE_X_POS_PX        = 0
      MODE5_CSPRITE_Y_POS_PX        = 2
      MODE5_CSPRITE_XRAM_SPRITE_PTR = 4
      MODE5_CSPRITE_PALETTE_PTR     = 6
      MODE5_CSPRITE_WIDTH_HEIGHT    = 8
      MODE5_CSPRITE_OPTIONS         = 9
      MODE5_CSPRITE_SIZE            = 10



.. _vga-control-channel:

Control Channel $F
==================

The RIA uses the registers of channel $F to control the VGA. When a
program sets one of them, ``xreg()`` fails with EACCES. On an
RP6502-PICO, the call fails only while the VGA module is connected.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $1:F:00
     - DISPLAY
     - Sets the aspect ratio of the display, and resets CANVAS to the
       console canvas.

       * 0 - VGA (4:3) 640x480
       * 1 - HD (16:9) 640x480 and 1280x720
       * 2 - SXGA (5:4) 1280x1024

   * - $1:F:01
     - CODE_PAGE
     - Sets the code page of the built-in fonts. Matches
       :ref:`RIA_ATTR_CODE_PAGE <api-ria-attributes>`.
   * - $1:F:02
     - SUPPRESS_TERM_REPLY
     - Suppresses the replies of the terminal of the VGA. The telnet
       server sets it.
   * - $1:F:03
     - UART_TX
     - Carries UART Tx data over PIX while the :ref:`backchannel
       <pico-backchannel>` uses the UART Tx pin.
   * - $1:F:04
     - BACKCHAN
     - Controls the use of UART Tx as the backchannel.

       * 0 - Disable
       * 1 - Enable
       * 2 - Request
   * - $1:F:06
     - REBOOT_OR_LOCKUP
     - The RIA sets it after it writes the flash of the VGA. 0 reboots
       the VGA, and any other value locks up the VGA to leave the error
       message visible.
   * - $1:F:07
     - FLASH_PROGRAM
     - Writes XRAM $0000-$00FF to flash page N of the VGA, where N is the
       value and each page is 256 bytes. The VGA erases the sector of the
       page first, unless the page already reads as erased.
