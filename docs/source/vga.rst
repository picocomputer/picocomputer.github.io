==================================
VGA
==================================

Video Graphics Array

Introduction
============

The RP6502 Video Graphics Array (VGA) is virtual video hardware modeled
on the home computers and arcades of the 8-bit and early-16-bit era. You
set it up with a few register writes and put your graphics in XRAM, and
from then on it draws every frame by itself while the 6502 runs your
program.

It has the parts that the games of that era were built from. Text in
cells, tile maps, and bitmaps all scroll to the pixel. Sprites come in
1-, 2-, 4-, and 8-bit color with a palette for each sprite, or in 16-bit
color, where they can also rotate and scale. Three planes stack these
from back to front, with transparency, so a status bar can sit over a
scrolling playfield. The picture can also switch to a different mode
partway down the screen, without an interrupt.

The :doc:`pico` has a real analog VGA output with standard VGA timing at
60 Hz, and the VGA system is built around it. That output has 5 bits
each of red, green, and blue, so the picture has 32,768 colors.


Getting Started
===============

This section is for when you are ready to dig in. It starts with the few
ideas that every picture is built from: the canvas, the modes, and the
four steps that put a picture on the canvas. Then it walks you through a
short program, and shows you where this page explains each part of it,
so that you know your way around the video system when you are done.

The VGA system draws your picture on the canvas, a grid of pixels such
as 320x240. The rows of the canvas are scanlines, numbered from 0 at the
top. The VGA system has six rendering modes, and each one draws one kind
of picture:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Mode
     - Draws
   * - :ref:`Mode 0 <vga-mode-0>`
     - The console, with the text that your program prints.
   * - :ref:`Mode 1 <vga-mode-1>`
     - Colored text in cells, for menus and status bars.
   * - :ref:`Mode 2 <vga-mode-2>`
     - A tile map, for the playfield of a game.
   * - :ref:`Mode 3 <vga-mode-3>`
     - A bitmap, in which every pixel can be its own color.
   * - :ref:`Mode 4 <vga-mode-4>`
     - Sprites in 16-bit color, which can rotate and scale.
   * - :ref:`Mode 5 <vga-mode-5>`
     - Sprites in 1-, 2-, 4-, or 8-bit color, each with its own palette.

A mode does not need to cover the whole canvas. You can put a mode on a
range of scanlines, and a different mode on the scanlines below it. One
call to ``xreg()`` programs one mode onto a range of scanlines. More
than one mode can also be on the same scanline, one in front of another.
As the VGA system draws each scanline, it calls the renderer of each
mode programmed on that scanline, and composites what they draw into the
scanline.

Most modes need two things from you in XRAM. The first is the data that
they draw, such as a bitmap. The second is a configuration structure,
which holds where that data is and where to draw it on the canvas. Modes
1 to 3 each take a configuration structure. The sprite modes, 4 and 5,
take a sprite array instead, with one structure for each sprite. Mode 0,
the console, has no configuration structure, so you put nothing in XRAM
for it.

Putting a picture on the canvas takes four steps.

**1. Select a canvas,** for example with
``xreg_vga_canvas(CANVAS_320X240)``. Selecting a canvas gives you a
blank canvas, with no mode programmed on any of its scanlines. It leaves
XRAM as it is.

**2. Load the data** of each mode into XRAM: a bitmap, a tile map and
its tiles, or sprite images, and any palette or font that they use.

**3. Write the configuration structure** of each mode into XRAM, or the
sprite array of a sprite mode.

**4. Program the VGA system with your modes,** using their macros, such
as ``xreg_vga_mode3()``. Each call puts a mode on one of three planes,
over a range of scanlines. From then on, the VGA system draws the modes
on every frame.

Here are the four steps in a program. It is the start of a graphical
text adventure, and it splits the canvas in two: a picture at the top,
and the console under it, where you type. Mode 3 draws the picture, a
bitmap of sky and grass, on scanlines 0 to 159. Mode 0 draws the console
on scanlines 160 to 239. The split takes just two calls.

.. image:: _static/vga/ranges-light.svg
   :class: only-light
   :width: 560
   :alt: A 320 by 240 canvas. Mode 3 draws a bitmap of sky and grass on
         scanlines 0 to 159, and mode 0 draws the console on scanlines 160 to
         239, both on the fill layer of plane 0.

.. image:: _static/vga/ranges-dark.svg
   :class: only-dark
   :width: 560
   :alt: A 320 by 240 canvas. Mode 3 draws a bitmap of sky and grass on
         scanlines 0 to 159, and mode 0 draws the console on scanlines 160 to
         239, both on the fill layer of plane 0.

The program keeps its bitmap and the configuration structure of the
bitmap in XRAM, so its ``xram.h`` has a layout with room for both.
`Video Layout`_ explains this layout. The comment at the top of the file
names the code blocks from `Reference`_ that the file needs:

.. code-block:: C
   :caption: xram.h

   // The xram.h code blocks of Key Registers, Mode 0: Console,
   // and Mode 3: Bitmap go here.

   typedef struct
   {
       uint8_t bitmap[320u * 160];
       mode3_config_t bitmap_config;
   } xram_layout_t;

   #define XRAM_BITMAP offsetof(xram_layout_t, bitmap)
   #define XRAM_BITMAP_CONFIG offsetof(xram_layout_t, bitmap_config)

The program is the same for both compilers, except for how it fills in
the configuration structure:

.. tab:: llvm-mos

   .. code-block:: C
      :caption: main.c

      #include <rp6502.h>
      #include <stdio.h>
      #include "xram.h"

      int main(void)
      {
          static const mode3_config_t config = {
              .width_px = 320,
              .height_px = 160,
              .xram_data_ptr = XRAM_BITMAP,
              .xram_palette_ptr = 0xFFFF,
          };
          char line[40];

          // 1. Select a canvas.
          xreg_vga_canvas(CANVAS_320X240);

          // 2. Load the data: sky, then grass.
          xram0_set(XRAM_BITMAP, 111, 320u * 110);
          xram0_set(XRAM_BITMAP + 320u * 110, 34, 320u * 50);

          // 3. Write the configuration structure.
          xram0_write(XRAM_BITMAP_CONFIG, &config, sizeof(config));

          // 4. Program the modes: the bitmap above, the console below.
          xreg_vga_mode3(MODE3_8BPP, XRAM_BITMAP_CONFIG, 0, 0, 160);
          xreg_vga_mode0(0, 160);

          puts("\fYou are standing in an open field.");
          while (1)
          {
              printf("> ");
              fgets(line, sizeof(line), stdin);
              puts("Nothing happens.");
          }
      }

.. tab:: cc65

   .. code-block:: C
      :caption: main.c

      #include <rp6502.h>
      #include <stdio.h>
      #include "xram.h"

      int main(void)
      {
          mode3_config_t config;
          char line[40];

          // 1. Select a canvas.
          xreg_vga_canvas(CANVAS_320X240);

          // 2. Load the data: sky, then grass.
          xram0_set(XRAM_BITMAP, 111, 320u * 110);
          xram0_set(XRAM_BITMAP + 320u * 110, 34, 320u * 50);

          // 3. Write the configuration structure.
          config.x_wrap = false;
          config.y_wrap = false;
          config.x_pos_px = 0;
          config.y_pos_px = 0;
          config.width_px = 320;
          config.height_px = 160;
          config.xram_data_ptr = XRAM_BITMAP;
          config.xram_palette_ptr = 0xFFFF;
          xram0_write(XRAM_BITMAP_CONFIG, &config, sizeof(config));

          // 4. Program the modes: the bitmap above, the console below.
          xreg_vga_mode3(MODE3_8BPP, XRAM_BITMAP_CONFIG, 0, 0, 160);
          xreg_vga_mode0(0, 160);

          puts("\fYou are standing in an open field.");
          while (1)
          {
              printf("> ");
              fgets(line, sizeof(line), stdin);
              puts("Nothing happens.");
          }
      }

That is a lot to take in at once, so this section does not explain it
line by line. Instead, it shows you where to look. Each step leads to a
part of this page, and by the end of step 4, you know how the page is
laid out.

**Step 1** selects the 320x240 canvas. `Key Registers`_ lists every
canvas you can select, and `Canvas`_ explains how a canvas fits the
display.

**Step 2** fills the bitmap with two calls to :c:func:`xram0_set`: 110
rows of color 111, a light blue, and 50 rows of color 34, a green. In
8-bit color, each byte of the bitmap is one pixel, as `Mode 3: Bitmap`_
describes. `Built-in Palette`_ shows colors 111 and 34, and every other
color the program can use without a palette of its own.

**Step 3** writes ``mode3_config_t``, the configuration structure of
mode 3, which `Mode 3: Bitmap`_ declares. `Configuration Structures`_
explains its members, and `Colors and Palettes`_ explains the palette
address $FFFF. The llvm-mos program sets only four members, because C99
designated initializers make every other member 0. cc65 does not have
them, so its program sets each one.

**Step 4** programs the two modes. Their sections, `Mode 3: Bitmap`_ and
`Mode 0: Console`_, give the arguments of each macro. The bitmap is on
scanlines 0 to 159. The console starts at scanline 160, and its call
leaves off END, so it runs to the bottom of the canvas. `Programming a
Mode`_ explains the range of scanlines and the arguments that a call
leaves off. `Planes`_ explains how modes stack, and why both modes can
be on plane 0: they draw on different scanlines. The four steps sent you
into three parts of this page. `Video Layout`_, right after this
section, explains the ideas one at a time: the canvas, the planes,
programming a mode, configuration structures, VSYNC, and colors. Read it
next, in order. `Reference`_ has a section for the key registers and for
each mode, with its registers and its code blocks for ``xram.h`` and
``xram.inc``. Look up a mode there when you use it. `Built-in Palette`_
shows every color that you can use without a palette of your own. The
last part, `Control Channel $F`_, lists the registers that the RIA uses
to control the VGA system.


Video Layout
============

The sections below explain how your picture is put together, one idea at
a time: where the picture goes, how the layers stack, how you program a
mode, how you move things around, when to make changes, and how colors
work.

The video layout is the part of your XRAM layout that the VGA system
draws from: the data of modes 1 to 5, such as images, palettes, and
fonts, and their configuration structures and sprite arrays. In your
project, each of these is a member of ``xram_layout_t`` in ``xram.h``,
with an ``XRAM_`` address, as :ref:`XRAM Memory Map
<sdk-xram-memory-map>` in the :doc:`sdk` describes. The macros and
structures on this page are in its ``xram.h`` code blocks, for you to
copy into your ``xram.h``.

Configuration structures, sprite arrays, and palettes must be at even
XRAM addresses. Neither cc65 nor llvm-mos pads a structure, so in
``xram_layout_t``, a member of odd size moves every member after it by
one byte, and an even address becomes odd. Put a pad byte after that
member, or put it last. :ref:`Symbols in CMake <sdk-symbols-in-cmake>`
in the :doc:`sdk` shows how your build can check the addresses for you.


Canvas
------

You choose the canvas, and the VGA system fits it to the display. The
canvas does not set the resolution of the video output: a 320x240 canvas
and a 640x480 canvas cover the same area, and a pixel on the 320x240
canvas is twice as wide and twice as tall. Any canvas works on any
display.

A scanline is always one row of the canvas, even when the canvas is
doubled or quadrupled to fit the display. The VGA system scales each
scanline to as many video lines, the lines of the signal to the display,
as the display needs. You do not set anything for the scaling.

There are four graphics canvases. 320x240 and 640x480 are 4:3, and
320x180 and 640x360 are 16:9. `Key Registers`_ gives the CANVAS value
of each.

Your ROM starts on the console canvas, which shows only the console. To
draw, select a graphics canvas. A graphics canvas starts blank, without
the console, so anything you print stays hidden until you put mode 0 on
a plane. When your ROM stops, the VGA system goes back to the console
canvas.


Planes
------

The VGA system draws the canvas from three planes, and each plane has
two layers: a fill layer, and a sprite layer over it. In the figure, a
program draws a picture on plane 0, a tile map on plane 1, and a status
bar on plane 2, with sprites on each.

.. image:: _static/vga/planes-light.svg
   :class: only-light
   :width: 762
   :alt: The VGA system draws the canvas from three planes, each with a fill
         layer and a sprite layer. Plane 0 is at the back and plane 2 is at the
         front. The six layers make the canvas, and the status bar of plane 2
         covers part of the sun, a sprite of plane 0.

.. image:: _static/vga/planes-dark.svg
   :class: only-dark
   :width: 762
   :alt: The VGA system draws the canvas from three planes, each with a fill
         layer and a sprite layer. Plane 0 is at the back and plane 2 is at the
         front. The six layers make the canvas, and the status bar of plane 2
         covers part of the sun, a sprite of plane 0.

Plane 0 is at the back and plane 2 is at the front. The sprites of a
plane cover its own fill layer, but the planes in front of it cover its
sprites, wherever those planes have opaque pixels. That is why the
status bar on plane 2 covers part of the sun, a sprite on plane 0.

Modes 0 to 3 draw on a fill layer, and modes 4 and 5 draw on a sprite
layer. You pick the plane with the PLANE argument of the mode. A layer
has at most one mode on each scanline, so text and a bitmap on the same
scanlines need different planes. To show text over a bitmap, put the
text on a plane in front of the bitmap.

The six layers stack like the layers of an image editor. Each color has
an alpha bit, which `Colors and Palettes`_ describes. A pixel whose
color has the alpha bit clear is transparent, and the layer behind it
shows through. A layer with no mode on a scanline is transparent on that
scanline. The fill layer of plane 0 has nothing behind it, so it ignores
the alpha bit and draws every pixel in its color. Where no layer draws a
pixel, the canvas is black.

The VGA system has a fixed time to draw each scanline. Fill layers
always fit in that time, so you can fill all three planes at any color
depth on any canvas, on every machine. Sprites can run out of that time.
The limit is not on the number of sprites, but on how many the VGA
system can draw on one scanline. In practice, the 6502 and the 64 KB of
XRAM limit a game first. :ref:`Sprite Limits <port-sprite-limits>` in
:doc:`port` shows how to count sprites, and `Mode 4: Sprite 16-bit`_
describes what happens when they do not fit.


Programming a Mode
------------------

Each mode has a macro that programs it with one call to :ref:`xreg()
<api-xreg>`. The VGA system has a register for the number of the mode
and registers for its arguments, and ``xreg()`` sets them, as `Key
Registers`_ describes. This line from `Getting Started`_ puts an 8-bit
bitmap on plane 0, on scanlines 0 to 159:

.. code-block:: C

  xreg_vga_mode3(MODE3_8BPP, XRAM_BITMAP_CONFIG, 0, 0, 160);

You find the macro in the ``xram.h`` code block of the mode in
`Reference`_, and it takes its arguments in the order of the register
table of the mode. Modes 1 to 3 take these:

- OPTIONS holds the options of the mode, such as its color depth.
  ``MODE3_8BPP`` selects 8-bit color.
- CONFIG is the XRAM address of the configuration structure.
- PLANE is the plane, 0 to 2.
- BEGIN and END set the range of scanlines.

The sprite modes add LENGTH, the number of sprites, after CONFIG, and
their CONFIG is the XRAM address of the sprite array. Mode 0 takes only
PLANE, BEGIN, and END.

BEGIN is the first scanline of the mode, and END is one past the last,
so BEGIN 0 and END 160 are scanlines 0 to 159. An END of 0 means the
height of the canvas, so BEGIN and END both 0 cover the whole canvas,
except for mode 0 on a 16:9 canvas, which `Mode 0: Console`_ describes.
Arguments that you leave off the end of a call are 0, because each call
that sets CANVAS or MODE clears the argument registers. So a call
without PLANE, BEGIN, and END puts its mode on plane 0, over the whole
canvas. A mode draws only on its own scanlines.

To change the picture partway down the canvas, give each part its own
range of scanlines. Different ranges of the same layer can have
different modes. The graphical text adventure of `Getting Started`_ does
this, with its picture on the top 160 scanlines and its console on the
bottom 80. On many computers of the era, a split like this took a
scanline interrupt. The VGA system does not have one, because it changes
modes at each BEGIN and END by itself. That leaves more CPU headroom for
your game logic.

Each range can have its own configuration structure, so each part of the
canvas can scroll on its own. BEGIN and END only set the scanlines that
a mode draws on. They do not move its image. For example, a bitmap at
position 0, 0 on scanlines 100 and down shows its rows from row 100
down, not its top rows.

To change the options of a mode, program the mode again with all of its
arguments. The new mode replaces the old mode of its layer from BEGIN to
END, and the other scanlines keep their modes. Mode 0 is the exception:
only one console can be visible, so programming mode 0 also removes the
console from where it was. No call removes a single mode. To remove one,
or to move a mode to another plane or onto fewer scanlines, select the
canvas again, which leaves no mode on any scanline, and then program
the modes that you still need.

When the VGA system refuses a value, such as a configuration structure
at an odd XRAM address, ``xreg()`` returns -1 and fails with EINVAL.


Configuration Structures
------------------------

A configuration structure holds what a mode draws and where it draws
it. The configuration structures of modes 1 to 3 start with the same
members:

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Member
     - Meaning
   * - ``xram_data_ptr``
     - The XRAM address of the data: the cells of mode 1, the tile map
       of mode 2, or the bitmap of mode 3.
   * - ``xram_palette_ptr``
     - The XRAM address of the palette, as `Colors and Palettes`_
       describes.
   * - ``width_chars``, ``height_chars``, ``width_tiles``,
       ``height_tiles``, ``width_px``, ``height_px``
     - The size of the image: in characters in mode 1, in tiles in mode
       2, and in pixels in mode 3.
   * - ``x_pos_px``, ``y_pos_px``
     - Where the top left pixel of the image goes on the canvas, in
       canvas pixels. They can be negative, so an image can start above
       or to the left of the canvas.
   * - ``x_wrap``, ``y_wrap``
     - When ``x_wrap`` is true, the VGA system repeats the image across
       the canvas, and when ``y_wrap`` is true, down the canvas.

:ref:`Mode 1 <vga-mode-1>` adds ``xram_font_ptr``, and :ref:`mode 2
<vga-mode-2>` adds ``xram_tile_ptr``.

An image does not have to be the size of the canvas. A smaller one
covers part of the canvas, and the layer is transparent around it unless
the image wraps. A larger one shows only the part on the canvas, so
changing its position scrolls it.

In a sprite array, each sprite has its own ``x_pos_px`` and
``y_pos_px``, where its top left pixel goes on the canvas. To move a
sprite, write its new position. This moves sprite ``n`` of a :ref:`mode
5 <vga-mode-5>` sprite array at ``XRAM_SPRITES`` to ``x``, ``y``:

.. code-block:: C

  unsigned addr = XRAM_SPRITES + n * sizeof(mode5_sprite_t);
  xram0_poke16(addr + offsetof(mode5_sprite_t, x_pos_px), x);
  xram0_poke16(addr + offsetof(mode5_sprite_t, y_pos_px), y);

Sprites later in the array cover the sprites before them. To hide a
sprite, move it off the canvas.

Once a mode is programmed, you change the picture by changing XRAM. You
can change a configuration structure, a sprite array, or the data that
they point to at any time, without programming the mode again. That is
how you scroll a map, move sprites, and change images. `VSYNC`_ explains
when to make the changes.


.. _vga-vsync:

VSYNC
-----

The VGA system draws the canvas one scanline at a time, from the top, 60
times a second. A change to XRAM appears on the next scanline that the
VGA system draws, even partway through a frame, so one frame can show
the top of the old image and the bottom of the new one. To change the
whole canvas at once, make your changes between frames. VSYNC, short
for vertical sync, marks the start of that time.

The last scanline that the VGA system draws triggers VSYNC: the bottom
of the lowest mode, or the bottom of the canvas when there are no modes.
Part of a scanline later, the RIA's :ref:`VSYNC register
<ria-registers>` increments, and the :ref:`VSYNC interrupt <api-irq>`
fires if you have enabled it.

:c:func:`ria_vsync` does not wait. It returns the value of the VSYNC
register, so to wait for VSYNC, call it in a loop until the value
changes:

.. code-block:: C

  unsigned char frame = ria_vsync();
  while (ria_vsync() == frame)
      ;

Instead of the loop, you can enable the VSYNC interrupt and make your
changes in the interrupt handler.

The time between frames is short. In the emulator, the program of
`Getting Started`_ has about 1.4 ms, roughly 11,000 cycles of a 6502 at
8 MHz, to change the top of the canvas. A change lower on the canvas has
more time. When you need to count cycles, `Frame Timing`_ gives which
scanline comes last, and the time between frames for every canvas and
display.


Colors and Palettes
-------------------

All three planes use RGB555 color: 5 bits each of red, green, and blue,
for 32,768 colors. One more bit of each color, the alpha bit, holds its
transparency. Setting the alpha bit makes a color opaque, and clearing
it makes the color transparent. Despite the name, alpha here is a binary
flag, not a blending factor. The macros below build colors. This is
opaque red:

.. code-block:: C

  uint16_t red = COLOR_FROM_RGB8(255, 0, 0) | COLOR_ALPHA_MASK;

``COLOR_FROM_RGB8`` takes red, green, and blue from 0 to 255, and
``COLOR_FROM_RGB5`` takes them from 0 to 31. In C, they leave the alpha
bit clear, so an opaque color needs ``COLOR_ALPHA_MASK`` too, as in the
example. In assembly, each macro emits a ``.word`` and takes
``COLOR_ALPHA_MASK`` as an optional fourth argument. A color is a 16-bit
value: red is in bits 0-4, the alpha bit is bit 5, green is in bits
6-10, and blue is in bits 11-15.

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

In 1-, 2-, 4-, and 8-bit color, each pixel is an index into a palette.
A palette is just an array of colors:

.. code-block:: C

  uint16_t palette[1 << bits_per_pixel];

In 16-bit color, each pixel is its own color, and the VGA system ignores
the palette.

You do not have to make a palette to get started. A palette address of
$FFFF selects the built-in palette: the 16 ANSI colors, a 6x6x6 color
cube, and 24 grays. `Built-in Palette`_ shows and names every color. In
the built-in palette, color 0 (black) is transparent at every color
depth, and every other color is opaque, so sprites and text that use it
get a transparent background.


Reference
=========

This part is for looking things up. Key Registers and the section of
each mode give the registers and the code blocks for ``xram.h`` and
``xram.inc``. The section of each mode also gives the format of its
data: `Mode 1: Character`_ describes fonts, and `Mode 3: Bitmap`_
describes how pixels pack into bytes. The code blocks of the color
macros are in `Colors and Palettes`_. `Frame Timing`_ gives how much
time a program has to change XRAM between frames. After this part,
`Built-in Palette`_ names every color of the built-in palette, with its
own code blocks, and `Control Channel $F`_ lists the registers that the
RIA uses to control the VGA system.


.. _vga-key-registers:

Key Registers
-------------

Two registers set up the picture. CANVAS selects the canvas, and MODE
programs a mode on it. They're the key registers of channel 0: setting
either one changes the picture, and the VGA system can refuse a value
that it doesn't support. When it refuses one, ``xreg()`` fails with
EINVAL.

The VGA system is PIX device 1, and each of its registers holds 16 bits.
The tables below give each register's address as $device:channel:index,
the first three arguments of :ref:`xreg() <api-xreg>`.

.. list-table::
   :widths: 5 5 90
   :header-rows: 1

   * - Address
     - Name
     - Description
   * - $1:0:00
     - CANVAS
     - Selects a canvas, removes all modes, and clears $1:0:02-$1:0:FF.
       The VGA system refuses any mode on the console canvas.

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

MODE holds only the number of the mode, but a mode needs more values
than that, such as its options and the XRAM address of its
configuration structure. These go in the argument registers after MODE,
$1:0:02-$1:0:FF. The VGA system reads them when the program sets MODE,
so one ``xreg()`` call can set MODE and its arguments together:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 3, 2, 0xFF00);

This sets MODE ($1:0:01) to 3, the :ref:`bitmap mode <vga-mode-3>`. It
also sets $1:0:02 to 2, for 4-bit color, and $1:0:03 to $FF00, the XRAM
address of the configuration structure. The arguments come after MODE
in the call, but the RIA sets them first, so they're ready when the VGA
system reads them. Every value after MODE in a call goes to an argument
register, so one call programs at most one mode. You can also set the
arguments in one call, and then set MODE alone in a later call.

One call can also select the canvas and program the first mode, which is
all the video setup that many programs need:

.. code-block:: C

  xreg(0x1, 0x0, 0x00, 1, 3, 2, 0xFF00);

The RIA sets the key registers, CANVAS and MODE, in order from the
lowest index. So this call selects the 320x240 canvas, then sets 2 and
$FF00, and then programs mode 3. Selecting the canvas clears the
argument registers, but 2 and $FF00 come after that, so mode 3 still
gets them.

A refused value changes nothing on the canvas. After a refused MODE,
every mode stays where it was, and VSYNC still comes at the same
scanline. After a refused CANVAS, the canvas and its modes stay as they
were, and the call stops there, so a MODE later in the same call isn't
set. Either refusal still clears the argument registers.

A refusal doesn't undo what the call set before it. If the VGA system
refuses this call's mode, the 320x240 canvas stays selected with no
modes. The canvas is black, and the console stays hidden until the
program selects the console canvas or programs mode 0, or until the ROM
stops.

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


.. _vga-mode-0:

Mode 0: Console
---------------

Mode 0 draws the console on a plane of a graphics canvas. :doc:`term`
describes the console and its escape sequences.

The console's default background is ANSI color 0 (black), which is
transparent. So console text on a plane in front of a picture shows the
picture around the glyphs.

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

On a canvas 640 pixels wide, the console uses an 8x16 font for 80
columns. On a canvas 320 pixels wide, it uses an 8x8 font for 40
columns. Each row of text is one glyph tall, 8 or 16 scanlines, and the
first row is at BEGIN. The scanlines from BEGIN to END must hold a whole
number of rows, or the VGA system refuses the mode. For example, BEGIN
200 and END 0 on a 320x240 canvas give the console the bottom 40
scanlines, room for 5 rows of 8x8 text.

BEGIN and END both 0 always work, even on the 320x180 and 640x360
canvases, which are 22½ rows tall. There, they put 22 rows of text in
the middle of the canvas.

Only one console can be visible at a time. Programming another removes
the previous one.

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

Mode 1 draws text in cells. A cell is one character on the canvas, and
it holds a glyph code. Character modes carry color information for every
cell, so each character can have its own foreground and background. This
is the mode you want for colorful text — menus, status bars, anything
where the glyphs change color.

Mode 1 isn't a terminal. The console shows what a program writes to
``stdout``, but mode 1 shows cells that the program writes into XRAM, at
any position. There's no cursor, and when the last row is full, the
text doesn't scroll up the way it does on the console.

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

The configuration structure is ``mode1_config_t``. `Configuration
Structures`_ describes the members that it shares with modes 2 and 3.
The one member that it adds is ``xram_font_ptr``, the XRAM address of
the font, as described below. ``MODE1_8X8`` or ``MODE1_8X16`` in
OPTIONS selects the glyph size. Unlike the console, mode 1 can use
either size on any canvas.

The data is an array of cells, ``width_chars`` * ``height_chars`` long,
stored row by row from the top left. Each cell is 8 pixels wide and one
glyph tall, so 40 cells span a canvas 320 pixels wide. The format of a
cell depends on the color depth, and the code blocks below give a type
for each format, such as ``mode1_8bpp_data_t``.

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
       The VGA system ignores the attributes, so a program can use them
       for its own data.

In 1-bit color, a cell holds only a glyph code, and every cell uses
color 1 of the palette for the foreground and color 0 for the
background. In 4-bit color, one byte holds both colors. In
``bg_fg_index``, the background is in the high four bits and the
foreground is in the low four bits. The reversed index swaps the two
halves, so in ``fg_bg_index``, the foreground is in the high four bits.
The bits of each color keep their order. In C, ``MODE1_BG_FG()`` and
``MODE1_FG_BG()`` build these bytes.

With the built-in palette, color 0 is transparent, so a background of
color 0 shows the layer behind it, or black on plane 0. For an opaque
black background, use 8-bit color with a ``bg_index`` of 16,
``ANSI_BLACK_OPAQUE``, or a palette of your own.

Mode 1 draws each character with a glyph from a font. A font holds 256
glyphs, each 8 pixels wide and 8 or 16 pixels tall. A font address of
$FFFF selects the built-in 8x8 or 8x16 font. Its glyphs 0-127 are
ASCII, and glyphs 128-255 vary by code page, which
:ref:`RIA_ATTR_CODE_PAGE <api-ria-attributes>` selects.

A font of your own is in a wide format: the first 256 bytes hold the
first row of every glyph, the next 256 bytes the second row, and so on.
In each byte, bit 7 is the leftmost pixel, and a 1 bit is a pixel in
the foreground color.

.. code-block:: C

  struct {
    struct {
        uint8_t col[256];
    } row[height];
  } font;

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

Mode 2 draws a tile map, a grid of small bitmaps called tiles. Tile
modes bake the color information into each tile's bitmap. This is the
mode you want for a video game playfield, where a small set of tiles is
repeated across a large map.

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
Structures`_ describes the members that it shares with modes 1 and 3. To
scroll the map, change ``x_pos_px`` and ``y_pos_px``. For example, an
``x_pos_px`` of -100 puts pixel column 100 of the map at the left edge
of the canvas.

The data is a tile map: an array of tile IDs, ``width_tiles`` *
``height_tiles`` long, stored row by row from 0,0 at the top left.

.. code-block:: C

  struct {
      uint8_t tile_id;
  } data[width_tiles * height_tiles];

Each tile ID is an index into the tile array at ``xram_tile_ptr``. The
array holds up to 256 tiles, but you only need to store the tiles up to
the highest tile ID that your map uses. A tile ID past the last tile
that you stored draws whatever bytes come after your tiles in XRAM. A
tile whose data would extend past the end of XRAM draws as transparent
black.

An entry of the map holds only a tile ID, so every tile of a map uses
the one palette at ``xram_palette_ptr``.

Tiles are in a "tall" bitmap format, where every row of one tile is
stored, top to bottom, before the next tile begins. A row of a tile is
``width * bits_per_pixel / 8`` bytes long, so an 8x8 tile in 4-bit color
has 8 rows of 4 bytes, 32 bytes in all. In 1-, 2-, and 4-bit color, the
leftmost pixel of a byte is in its most significant bits, as `Mode 3:
Bitmap`_ describes. ``MODE2_TILE`` declares the structure of one tile
from its color depth and tile size, so ``typedef MODE2_TILE(4, 8)
tile_t;`` is an 8x8 tile in 4-bit color.

With trim, the VGA system draws tiles of other sizes, such as 12x12,
from tiles stored at 8x8 or 16x16. X trim drops columns off the right of
each tile, and Y trim drops rows off the bottom. Each tile keeps its
full size in XRAM, and the VGA system doesn't draw the dropped pixels.
A 16x16 tile with X trim 5 and Y trim 6 draws as 11x10, and the tiles of
the map are 11 pixels apart across and 10 pixels apart down. In C,
``MODE2_X_TRIM()`` and ``MODE2_Y_TRIM()`` put the trim in OPTIONS.

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

Mode 3 draws a bitmap. Every pixel can be its own color. The 64 KB of
XRAM caps the color depth of an image that fills the canvas: monochrome
at 640x480, 16 colors at 320x240, or 256 colors at 320x180 (16:9).

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

In 8-bit color, a byte is one pixel. In 1-, 2-, and 4-bit color, a byte
holds 8, 4, or 2 pixels. Bit order traditionally follows the canvas, so
that left and right bit shifts move pixels the way you'd expect: the
leftmost pixel is in the most significant bits. In 4-bit color, the byte
$12 is a pixel of color 1 and then a pixel of color 2. In 1-, 2-, and
4-bit color, ``MODE3_REVERSE_BITS`` (bit 3 of OPTIONS) reverses the
order of the pixels in each byte, so that the leftmost pixel is in the
least significant bits. The bits of each pixel keep their order. The
reversed order makes bit-level manipulation code slightly smaller and
faster.

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

Mode 4 draws sprites in 16-bit color over any fill layer. This is the
same 16-bit sprite system used by Pi Pico Playground and Luke Wren's
RISCBoy. Its appetite for memory is offset by something mode 5 can't do
— affine transforms.

There is no fixed number of sprites. For a game near the limits, see
:ref:`Sprite Limits <port-sprite-limits>`. A sprite off the canvas still
takes time on each scanline. To stop unused sprites from taking time,
program the mode again with a smaller LENGTH. When the sprites of a
scanline do not fit in its time, the result depends on the machine:

- On the :doc:`pico`, the scanline shows part blue and part black
  instead of the picture.
- On the :doc:`fpga`, the sprites that do not fit do not show.
- On the :doc:`emu` and the :doc:`web`, every sprite shows, but the
  host computer slows down. The emulator no longer runs at 60 frames a
  second, and the time of the 6502 falls behind the time of the clock
  on the wall.

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

The sprite array holds ``mode4_sprite_t``. For affine sprites, set bit
0 of OPTIONS, ``MODE4_AFFINE_BIT``, and the sprite array holds
``mode4_asprite_t`` instead. In both, ``xram_sprite_ptr`` is the XRAM
address of the sprite's image. `Configuration Structures`_ describes how
a program moves sprites and in what order the VGA system draws them.

The image is an array of 16-bit colors. A sprite is a square, and each
side is 2 to the power ``log_size`` pixels: a ``log_size`` of 0 is 1x1,
and 7 is 128x128, the largest. A ``log_size`` above 7 describes a square
too large for XRAM, and the sprite doesn't appear.
``MODE4_IMAGE`` declares the structure of one image from its
``log_size``, so ``typedef MODE4_IMAGE(4) image_t;`` is a 16x16 image.

Opacity metadata lets the VGA system skip the transparent pixels at the
ends of each row, so a sprite with transparent ends can take less time
on each scanline. When ``has_opacity_metadata`` is true, one
little-endian 32-bit value for each row follows the image. Each value
gives the opaque span of its row, in pixels from the left of the image.
Bits 30-16 are the start of the span, and bits 15-0 are its end, one
past its last pixel. The VGA system doesn't draw the pixels outside the
span. ``MODE4_SPAN`` builds one row of opacity metadata.

Bit 31 marks a span as solid. The VGA system draws all of a solid span
without checking the alpha bit of each color. Mark a span solid only
when every color in it is opaque.

An image and its metadata must fit in XRAM together, or the VGA system
draws nothing for the sprite. Affine sprites don't use the metadata,
but when ``has_opacity_metadata`` is true, the metadata still counts
toward that size.

Affine sprites can be rotated and scaled. They apply a 3x3 matrix
transform, which makes them slower than plain sprites. Only the first
two rows of the matrix matter, which is why there are just six
transform values. They're in signed 8.8 fixed-point format, in the
order {a00, a01, b0, a10, a11, b1}. ``MODE4_AFFINE_A00`` to
``MODE4_AFFINE_B1`` are their indexes in ``transform``.

The matrix maps a position within the sprite on the canvas to a position
in the image. The pixel at x, y from the top left of the sprite shows
the pixel of the image at u, v:

.. code-block:: text

  u = a00 * x + a01 * y + b0
  v = a10 * x + a11 * y + b1

The transform {``MODE4_AFFINE_ONE``, 0, 0, 0, ``MODE4_AFFINE_ONE``, 0}
draws the image as it is. The matrix maps the canvas to the image, so
it's the inverse of the change that you see on the canvas. With $0200
(2.0) in a00 and a11, the image appears at half size, not double,
because the VGA system steps through the image two pixels for each pixel
of the canvas.

To rotate the image by an angle t about the center of its square, use
these values. Here size is the width of the square in pixels, and c is
(size - 1) / 2:

.. code-block:: text

  a00 = cos t    a01 = sin t    b0 = c - c * cos t - c * sin t
  a10 = -sin t   a11 = cos t    b1 = c + c * sin t - c * cos t

Multiply each value by ``MODE4_AFFINE_ONE`` to put it in 8.8 format. A
positive t turns the image clockwise. These values fit the 8.8 format
for sprites up to 64x64. An affine sprite draws only inside its own
square, so leave a transparent margin around an image that you rotate,
or its corners are cut off.

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

Mode 5 draws sprites in 1-, 2-, 4-, or 8-bit color. This is a
memory-efficient sprite system that uses palettes to cut the color
depth. The VGA system can draw these sprites over any fill layer,
including an empty one. For example, you might put affine sprites of
mode 4 for explosions and the player on one plane, 16x16 enemy sprites
in 4-bit color on a second, and 8x8 bullets in 1-bit color on the third.
Custom sprites, described below, let one plane mix sprites of different
sizes, color depths, and orientations.

There is no fixed number of sprites. `Mode 4: Sprite 16-bit`_ describes
the limits of sprites, which apply to mode 5 too.

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
       | With 7=custom, the VGA system ignores bits 0:2, and each sprite
         in the sprite array sets its own size and color depth.
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

Each of the first two calls programs 16x16 sprites in 4-bit color on
plane 1, from the sprite array at ``xaddr``. The third call programs
custom sprites on plane 2, from a second sprite array at ``xaddr2``:

.. code-block:: C

  xreg(0x1, 0x0, 0x01, 5, 0x0A, xaddr, length, 1);            // 16x16 4-bit, plane 1
  xreg_vga_mode5(MODE5_4BPP | MODE5_16X16, xaddr, length, 1); // macro shortcut
  xreg_vga_mode5(MODE5_CUSTOM, xaddr2, length2, 2);           // custom sprites, plane 2

The sprite array holds ``mode5_sprite_t``. `Configuration Structures`_
describes how a program moves sprites and in what order the VGA system
draws them. ``xram_sprite_ptr`` is the XRAM address of the sprite's
image, and ``palette_ptr`` is the XRAM address of its palette, so each
sprite can have its own palette. On the :doc:`fpga`, the VGA system
draws sprites fastest when all their palettes are within 1 KB of
contiguous XRAM, as :ref:`Sprite Limits <port-sprite-limits>` explains.

A pixel of a sprite shows only if its color has the alpha bit set. In a
sprite palette, set the alpha bit in each color that shows, for example
with ``COLOR_ALPHA_MASK``, and clear it in the transparent color. With a
``palette_ptr`` of $FFFF, a sprite uses the built-in palette, in which
color 0 is transparent.

The image is in the format of one :ref:`mode 2 <vga-mode-2>` tile. A
16x16 image in 4-bit color is 16 rows of 8 bytes, 128 bytes in all.
``MODE5_IMAGE`` declares the structure of one image from its color depth
and sprite size, so ``typedef MODE5_IMAGE(4, 16) image_t;`` is a 16x16
image in 4-bit color.

With OPTIONS set to custom, the sprite array holds ``mode5_csprite_t``,
and each sprite sets its own size, color depth, and orientation. Only
custom sprites can be flipped or doubled. Their flip and double flags go
in each sprite's ``options`` member. They must not go in the OPTIONS
register, where bits 3:5 select the sprite size: ``MODE5_4BPP |
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


.. _vga-frame-timing:

Frame Timing
------------

This section gives how much time a program has to change XRAM between
frames. When the canvas has no modes, VSYNC comes after the last
scanline of the canvas. Otherwise, it comes after the last scanline of
the lowest mode that the program has put on a plane since it last
selected the canvas. A mode programmed lower on the canvas moves VSYNC
down, but nothing moves it back up until the program selects the canvas
again.

How much time a program has depends on what it changes and where that
change shows. A change must be in XRAM before the VGA system draws the
first scanline that shows it. For a configuration structure, that is the
first scanline of its mode. For a sprite, it is the top scanline of the
sprite, at its old position or its new one, whichever is higher. After
VSYNC, the VGA system draws nothing until the next frame, so a change at
the top of the canvas has the time from the end of the canvas to its
start in the next frame. A change lower on the canvas also has the time
that the VGA system takes to draw the scanlines above it.

The time depends on the video timing, the format of the signal that goes
to the display. The video timing is separate from the canvas: a 320x240
canvas, for example, can go to the display with 640x480 timing or with
1280x1024 timing. The table gives each video timing:

.. list-table::
   :widths: 20 20 20 20 20
   :header-rows: 1

   * - Timing
     - Lines per frame
     - Visible lines
     - Line time
     - Cycles per line at 8 MHz
   * - 640x480
     - 525
     - 480
     - 31.75 µs
     - 254
   * - 1280x720
     - 750
     - 720
     - 22.22 µs
     - 178
   * - 1280x1024
     - 1066
     - 1024
     - 15.63 µs
     - 125

The :doc:`fpga`, the :doc:`emu`, and the :doc:`web` always use 640x480
timing. On the :doc:`pico`, the display type selects the timing, and
``SET VGA`` in the monitor selects the display type. Display type 0 uses
640x480. Display type 1 uses 1280x720 for the 16:9 canvases and 640x480
for the others. Display type 2 uses 1280x1024.

Each scanline of the canvas takes the same number of video lines. A
320-wide canvas takes 2 lines with 640x480 timing and 4 with the others.
A 640-wide canvas takes 1 line with 640x480 timing and 2 with the
others.

A canvas that does not fill the visible lines leaves blank lines, and
they add to the time between frames. On the RP6502-PICO, the VGA system
centers the canvas, so the blank lines are half above it and half below:
it starts at line 60 for a 16:9 canvas with 640x480 timing, at line 32
for a 4:3 canvas with 1280x1024 timing, and at line 152 for a 16:9
canvas with 1280x1024 timing. On the other machines, the canvas starts
at line 0, and the blank lines all come after it. The total is the same
either way. This table gives the time between the end of the canvas and
the start of the next one, when the modes reach the bottom of the
canvas:

.. list-table::
   :widths: 20 20 20 20 20
   :header-rows: 1

   * - Timing
     - Canvas
     - Lines
     - Time
     - Cycles at 8 MHz
   * - 640x480
     - 4:3
     - 45
     - 1.43 ms
     - 11,400
   * - 640x480
     - 16:9
     - 165
     - 5.24 ms
     - 41,900
   * - 1280x720
     - 16:9
     - 30
     - 0.67 ms
     - 5,300
   * - 1280x1024
     - 4:3
     - 106
     - 1.66 ms
     - 13,300
   * - 1280x1024
     - 16:9
     - 346
     - 5.41 ms
     - 43,300

A 16:9 canvas has more than three times the time of a 4:3 one, except
with 1280x720 timing. There, the canvas fills the display, and the time
is the shortest of all. A program whose modes end higher on the canvas
gets VSYNC sooner, and has the time of the scanlines below its modes
too.

The machines agree to within one scanline, so leave one scanline of
margin. The RP6502-PICO is the reason for the margin. Its VGA system
draws up to 10 scanlines ahead of the display, into a buffer, and it
sends VSYNC when it draws the last scanline, so VSYNC comes early by the
same amount. It draws on two processor cores at once, so when VSYNC
comes, the other core can still be drawing the scanline above. At the
start of a frame, it draws the top 10 scanlines together, from 10 video
lines before the canvas starts, so count a change to any of them as a
change at the top.

For example, take the program of `Getting Started`_ with 640x480 timing. Its
console reaches the bottom of the 320x240 canvas, so VSYNC comes after
video line 479, and the next frame starts 45 lines later. Less one
scanline of margin, which is 2 lines, a change at the top of the canvas
has 43 lines: 1.37 ms, or about 10,900 cycles at 8 MHz. Scanline 100 of
the canvas starts at video line 200, so a change that shows there has
200 lines more, about 7.7 ms in all.


.. _vga-built-in-palette:

Built-in Palette
================

A palette address of $FFFF selects the built-in palette. In 8-bit color,
it has 256 colors:

- Colors 0 to 15 are the 16 ANSI colors: black, red, green, yellow,
  blue, magenta, cyan, and white, and then bright versions of them.
- Colors 16 to 231 are a 6x6x6 color cube. The color with red r, green
  g, and blue b, each from 0 to 5, is ``16 + 36 * r + 6 * g + b``. The
  values 0 to 5 give the levels 0, 95, 135, 175, 215, and 255.
- Colors 232 to 255 are 24 grays, from dark to light. Each has equal
  red, green, and blue: 8 for color 232, and 10 more for each color
  after it, up to 238 for color 255.

2-bit color uses the first 4 of these colors, and 4-bit color uses the
first 16. 1-bit color has a palette of its own: color 0 is black, and
color 1 is white, with red, green, and blue all 229, the same as
color 7. So in 1-, 2-, and 4-bit color, the built-in palette has no
opaque black.

The code blocks below name the colors. ``ANSI_BLACK`` is color 0, and
``ANSI_BLACK_OPAQUE`` is color 16, the black of the cube.
``ANSI_CUBE(r, g, b)`` gives the color of the cube with red r, green g,
and blue b. ``ANSI_GRAY(k)`` gives a gray, with k from 0 for black to 25
for white. ``ANSI_GRAY(0)`` is color 16, ``ANSI_GRAY(1)`` to
``ANSI_GRAY(24)`` are colors 232 to 255, and ``ANSI_GRAY(25)`` is color
231, the white of the cube. In C and ca65, each name gives a constant,
so you can use it anywhere that a number goes, such as in math. In
llvm-mc, the code block gives the formulas of ``ANSI_CUBE`` and
``ANSI_GRAY`` in a comment.

The chart shows the grays in the order of ``ANSI_GRAY``. Color 0 is
black, with a dashed outline because it's transparent.

.. image:: _static/vga/palette-light.svg
   :class: only-light
   :width: 672
   :alt: The built-in palette in 8-bit color, in three groups: the 16 ANSI
         colors in two rows of 8, the 6x6x6 color cube as six blocks of 6 by 6
         with red by block, green by row, and blue by column, and the grays
         from dark to light, from color 16, the black of the cube, through
         colors 232 to 255, to color 231, the white of the cube. Color 0 is
         black and transparent.

.. image:: _static/vga/palette-dark.svg
   :class: only-dark
   :width: 672
   :alt: The built-in palette in 8-bit color, in three groups: the 16 ANSI
         colors in two rows of 8, the 6x6x6 color cube as six blocks of 6 by 6
         with red by block, green by row, and blue by column, and the grays
         from dark to light, from color 16, the black of the cube, through
         colors 232 to 255, to color 231, the white of the cube. Color 0 is
         black and transparent.

.. tab:: C

   .. code-block:: C
      :caption: xram.h (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      #define ANSI_BLACK           0 // #000000, transparent
      #define ANSI_RED             1 // #CD0000
      #define ANSI_GREEN           2 // #00CD00
      #define ANSI_YELLOW          3 // #CDCD00
      #define ANSI_BLUE            4 // #0000EE
      #define ANSI_MAGENTA         5 // #CD00CD
      #define ANSI_CYAN            6 // #00CDCD
      #define ANSI_WHITE           7 // #E5E5E5
      #define ANSI_BRIGHT_BLACK    8 // #7F7F7F
      #define ANSI_BRIGHT_RED      9 // #FF0000
      #define ANSI_BRIGHT_GREEN   10 // #00FF00
      #define ANSI_BRIGHT_YELLOW  11 // #FFFF00
      #define ANSI_BRIGHT_BLUE    12 // #5C5CFF
      #define ANSI_BRIGHT_MAGENTA 13 // #FF00FF
      #define ANSI_BRIGHT_CYAN    14 // #00FFFF
      #define ANSI_BRIGHT_WHITE   15 // #FFFFFF
      #define ANSI_BLACK_OPAQUE   16 // #000000

      // r, g, and b are 0 to 5, for the levels 0, 95, 135, 175, 215, and 255.
      #define ANSI_CUBE(r, g, b) (16 + (r) * 36 + (g) * 6 + (b))

      // k is 0 to 25: black, then #080808 to #EEEEEE in steps of #0A0A0A,
      // then white.
      #define ANSI_GRAY(k) ((k) ? 231 + (k) % 25 : 16)

.. tab:: ca65

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)

      ANSI_BLACK          = 0  ; #000000, transparent
      ANSI_RED            = 1  ; #CD0000
      ANSI_GREEN          = 2  ; #00CD00
      ANSI_YELLOW         = 3  ; #CDCD00
      ANSI_BLUE           = 4  ; #0000EE
      ANSI_MAGENTA        = 5  ; #CD00CD
      ANSI_CYAN           = 6  ; #00CDCD
      ANSI_WHITE          = 7  ; #E5E5E5
      ANSI_BRIGHT_BLACK   = 8  ; #7F7F7F
      ANSI_BRIGHT_RED     = 9  ; #FF0000
      ANSI_BRIGHT_GREEN   = 10 ; #00FF00
      ANSI_BRIGHT_YELLOW  = 11 ; #FFFF00
      ANSI_BRIGHT_BLUE    = 12 ; #5C5CFF
      ANSI_BRIGHT_MAGENTA = 13 ; #FF00FF
      ANSI_BRIGHT_CYAN    = 14 ; #00FFFF
      ANSI_BRIGHT_WHITE   = 15 ; #FFFFFF
      ANSI_BLACK_OPAQUE   = 16 ; #000000

      ; r, g, and b are 0 to 5, for the levels 0, 95, 135, 175, 215, and 255.
      .define ANSI_CUBE(r, g, b) (16 + (r) * 36 + (g) * 6 + (b))

      ; k is 0 to 25: black, then #080808 to #EEEEEE in steps of #0A0A0A,
      ; then white.
      .define ANSI_GRAY(k) (231 + (k) .mod 25 - ((k) = 0) * 215)

.. tab:: llvm-mc

   .. code-block:: ca65
      :caption: xram.inc (see :ref:`XRAM Memory Map <sdk-xram-memory-map>`)
      :force:

      ANSI_BLACK          = 0  ; #000000, transparent
      ANSI_RED            = 1  ; #CD0000
      ANSI_GREEN          = 2  ; #00CD00
      ANSI_YELLOW         = 3  ; #CDCD00
      ANSI_BLUE           = 4  ; #0000EE
      ANSI_MAGENTA        = 5  ; #CD00CD
      ANSI_CYAN           = 6  ; #00CDCD
      ANSI_WHITE          = 7  ; #E5E5E5
      ANSI_BRIGHT_BLACK   = 8  ; #7F7F7F
      ANSI_BRIGHT_RED     = 9  ; #FF0000
      ANSI_BRIGHT_GREEN   = 10 ; #00FF00
      ANSI_BRIGHT_YELLOW  = 11 ; #FFFF00
      ANSI_BRIGHT_BLUE    = 12 ; #5C5CFF
      ANSI_BRIGHT_MAGENTA = 13 ; #FF00FF
      ANSI_BRIGHT_CYAN    = 14 ; #00FFFF
      ANSI_BRIGHT_WHITE   = 15 ; #FFFFFF
      ANSI_BLACK_OPAQUE   = 16 ; #000000

      ; llvm-mc has no macro that works inside an expression, so this file
      ; can't define ANSI_CUBE and ANSI_GRAY. These are their formulas.
      ; ANSI_CUBE(r, g, b) is 16 + 36 * r + 6 * g + b, with r, g, and b
      ; from 0 to 5 for the levels 0, 95, 135, 175, 215, and 255.
      ; ANSI_GRAY(k) is 16 for k = 0, 231 + k for k = 1 to 24, and 231 for
      ; k = 25: black, then #080808 to #EEEEEE in steps of #0A0A0A, then
      ; white.


.. _vga-control-channel:

Control Channel $F
==================

The RIA uses the registers of channel $F to control the VGA system. A
program can't set them, and an ``xreg()`` call that sets one fails with
EACCES. On an RP6502-PICO, the call fails only while the VGA module, the
Pico 2 that runs the VGA firmware, is connected.

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
     - Sets the code page of the built-in fonts. It holds the same value
       as :ref:`RIA_ATTR_CODE_PAGE <api-ria-attributes>`.
   * - $1:F:02
     - SUPPRESS_TERM_REPLY
     - Suppresses replies from the VGA system's terminal. The telnet
       server sets it.
   * - $1:F:03
     - UART_TX
     - Carries UART Tx data over the PIX bus while the :ref:`backchannel
       <pico-backchannel>` uses the UART Tx pin.
   * - $1:F:04
     - BACKCHAN
     - Controls the use of UART Tx as the backchannel.

       * 0 - Disable
       * 1 - Enable
       * 2 - Request
   * - $1:F:06
     - REBOOT_OR_LOCKUP
     - The RIA sets it after it writes the flash of the VGA module. 0
       reboots the VGA module. Any other value locks it up, so that the
       error message of a failed flash write stays on the screen.
   * - $1:F:07
     - FLASH_PROGRAM
     - Writes XRAM $0000-$00FF to flash page N of the VGA module, where N
       is the value and each page is 256 bytes. The VGA module erases the
       sector of the page first, unless the page already reads as erased.
