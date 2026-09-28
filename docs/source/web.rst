============================
RP6502-WEB
============================

RP6502 - Web Player


Introduction
============

A web player is a web page that plays one Picocomputer program. It is the
:doc:`emu` built for a browser, so the program runs the same as on every
other machine, and anyone with a browser can play it without installing
anything.

A web player is four files, served together from one folder:

- ``index.html``, the page, with the settings for the program.
- ``rp6502.js`` and ``rp6502.wasm``, the emulator.
- The ROM, such as ``game.rp6502``.

``rp6502.js`` and ``rp6502.wasm`` are in the itch.io zip on the `releases
page <https://github.com/picocomputer/rp6502/releases/latest>`__, and they
are always replaced as a pair. ``index.html`` is not tied to a release:
the ``index.html`` described here needs release 0.35 or later, and it
works with the ``rp6502.js`` and ``rp6502.wasm`` of every later release.
Any change to the settings is listed in the release notes.


.. _web-page:

The Page
========

This ``index.html`` plays ``game.rp6502``, which is in the same folder.

.. code-block:: html

  <!doctype html>
  <html lang="en">
  <head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  </head>
  <body>
  <script>
    var CONFIG = {
      title: 'My Game',
      rom:   'game.rp6502',
      db:    'username-mygame',
    };
  </script>
  <script src="rp6502.js" onerror="document.body.textContent = 'Could not load rp6502.js'"></script>
  </body>
  </html>

The settings are in ``CONFIG``. The ``rp6502.js`` script goes last in
``<body>``, after everything else on the page, and it builds the page
around the emulator from those settings.

A browser does not run a web player opened as a file, from a ``file://``
address, because the ROM and the WebAssembly load only from a web server.
To try a page on your own computer, start a web server in its folder and
open http://localhost:8000.

.. code-block:: text

  python3 -m http.server 8000

.. list-table::
   :widths: 15 25 60
   :header-rows: 1

   * - Setting
     - Example
     - Description
   * - ``title``
     - ``'My Game'``
     - The name in the browser tab. Default ``Picocomputer 6502``.
   * - ``rom``
     - ``'game.rp6502'``
     - The ROM, as a path from ``index.html``. Required.
   * - ``args``
     - ``['-c1']``
     - The arguments for the program, argv[1] and on.
   * - ``install``
     - ``['game.bas']``
     - Files for the program, as paths from ``index.html``. Each one is
       installed on the null drive, where the program reads it as ``:``
       followed by the file name, in any case. See :ref:`Installed ROMs
       <port-installed-roms>`.
   * - ``db``
     - ``'username-mygame'``
     - The name of the IndexedDB database for saves. See `Saves`_.
   * - ``bg``
     - ``'000000'``
     - The color around the picture when the page and the canvas have
       different shapes, as six hex digits, RRGGBB. Default ``000000``.
   * - ``filter``
     - ``'sharp'``
     - How pixels are scaled: ``nearest``, ``linear`` or ``sharp``.
       Default ``sharp``, which enlarges by a whole number and then
       smooths.
   * - ``overlay``
     - ``'overlay'``
     - The ``id`` of the click-to-play template. See `Click to Play`_.
   * - ``footer``
     - ``'footer'``
     - The ``id`` of the footer template. See `Footer`_.
   * - ``image``
     - ``'play.png'``
     - A picture shown until the game starts. See `Picture`_.

A setting that is left out, or left blank, is off or takes its default.
For example, Microsoft BASIC loads and runs a program named as an
argument, and ``-c1`` keeps the keyboard in capitals:

.. code-block:: javascript

  rom:     'basic.rp6502',
  install: ['game.bas'],
  args:    ['-c1', ':GAME.BAS'],

.. _web-saves:

Saves
-----

A program keeps high scores and saved games in files on the ``SAVE:``
drive, as described in :ref:`Saves <port-save>`. In a browser, those
files are stored in an IndexedDB database, and ``db`` is the name of
that database. A browser holds one set of IndexedDB databases for each
web site. Every game on itch.io is on one site, so there, name the
database with your full user name and the full project name, such as
``rumbledethumps-flappycoo``. A GitHub Pages site, ``<user>.github.io``,
holds only your own projects, so there the full project name is enough.
With ``db`` blank, saves last until the page closes.

.. _web-overlay:

Click to Play
-------------

A browser plays no sound on a page until the player clicks the page or
presses a key, and a page shown inside another page, in an
``<iframe>``, gets no key presses until it is clicked. The click-to-play
overlay covers the game with a play button, so that the player knows to
click it. The game runs silently under the overlay, and the click, or any
key press, removes the overlay and turns the sound on.

The overlay is a ``<template>`` in ``index.html``. The browser keeps the
HTML in a template without showing it. ``overlay`` names the template by
its ``id``, and the one element in the template is placed over the game.
Everything about the overlay, from the words to the colors, is in
``index.html``. To add a simple overlay to the page above, put this
style in ``<head>`` and this template in ``<body>``, before the scripts:

.. code-block:: html

  <style>
    .overlay {
      position: absolute; inset: 0; cursor: pointer;
      display: grid; place-items: center;
      background: rgba(0, 0, 0, .5); color: #fff;
      font: 20px system-ui, sans-serif;
    }
  </style>

  <template id="overlay">
    <div class="overlay">&#9654; Click to play</div>
  </template>

Then turn it on in ``CONFIG``:

.. code-block:: javascript

  overlay: 'overlay',

The ``index.html`` in the itch.io zip has a round play button in its
overlay template, with settings at the top of its style:

.. code-block:: css

  .overlay {
    --y: 50%;                              /* height of the button, from the top */
    --size: clamp(56px, 18vmin, 96px);     /* width of the button */
    --shade: rgba(0, 0, 0, .45);           /* over the game */

``--y: 70%`` moves the button lower, over an empty part of a title
screen. The overlay is off in that file, because itch.io shows a launch
button before the game, and that click turns the sound on.

.. _web-footer:

Footer
------

A footer is a line or two under the game, such as the controls and the
credits. Like the overlay, it is a template, named by ``footer``, and its
one element is placed under the game. The game is scaled to the space
above it. This style and template add a footer, in the same places as
those of the overlay:

.. code-block:: html

  <style>
    .footer {
      padding: 8px; border-top: 1px solid #303335; text-align: center;
      color: #9ca0a5; font: 13px system-ui, sans-serif;
    }
    .footer p { margin: 0; }
  </style>

  <template id="footer">
    <div class="footer">
      <p>Arrows to move, Space to fire.</p>
      <p>By Your Name</p>
    </div>
  </template>

.. code-block:: javascript

  footer: 'footer',

Give a link in the footer ``target="_blank"``, so that it opens in a new
tab instead of in place of the game.

.. _web-picture:

Picture
-------

``image`` names a picture shown in place of the game until it starts.
With the overlay, the game starts at the click, so the picture is under
the play button until then, and the emulator is already loaded when the
player clicks. Without the overlay, the game starts at once, and the
picture shows only while the emulator loads.

A screenshot of the title screen works well. This command runs the ROM
for 120 frames and writes the screen to ``play.png``:

.. code-block:: text

  rp6502-emu game.rp6502 --screenshot play.png

The picture is scaled to fit, keeping its shape, and its pixels stay
square when it is enlarged.

License Notices
---------------

With ``?credits`` at the end of its address, such as
``https://example.com/game/?credits``, the page shows the license notices
of the components in ``rp6502.js`` and ``rp6502.wasm``.


.. _web-itch:

itch.io
=======

itch.io publishes browser games for free, and it is the quickest way to
share a program.

1. Download ``rp6502-<version>-itch.io.zip`` from the `releases page
   <https://github.com/picocomputer/rp6502/releases/latest>`__ and unpack
   it. The folder holds ``index.html``, ``rp6502.js``, ``rp6502.wasm``,
   the sample program ``adventure.rp6502`` and a ``README.txt``.
2. Put your ROM in the folder and delete ``adventure.rp6502``.
3. In ``index.html``, set ``title``, ``rom`` and ``db`` in ``CONFIG``.
   Leave ``overlay`` blank.
4. Zip the contents of the folder, so that ``index.html`` is at the root
   of the zip, not in a subfolder.
5. On itch.io, create a project, set the kind of project to HTML, upload
   the zip, and tick "This file will be played in the browser".
6. In the embed options, set the size manually to 640x480 or 640x360,
   and leave scrollbars and SharedArrayBuffer support off. A program with
   a 320-pixel-wide canvas is enlarged to fit.

Please tag your project **RP6502**, so that it is listed with the other
Picocomputer software at https://itch.io/games/tag-rp6502.

To update the emulator, replace ``rp6502.js`` and ``rp6502.wasm`` with the
ones from a newer itch.io zip, keep ``index.html``, and upload a new zip.


.. _web-github:

GitHub Pages
============

GitHub Pages publishes web pages from a GitHub repository, so a link in
the README of a game can open a web player for it. The players are named
in the markdown of the repository, and a workflow from
`picocomputer/.github <https://github.com/picocomputer/.github>`__ builds
each one and publishes it on every push to ``main``, with ``rp6502.js``
and ``rp6502.wasm`` from the latest release. The repository needs no
``index.html``.

1. On GitHub, open Settings > Pages, and set Source to GitHub Actions.
2. Put this comment above the play link in ``README.md``, or in any other
   markdown file of the repository. GitHub does not show it.

   .. code-block:: text

     <!-- rp6502
     preset: cc65/Release
     target: game
     -->
     [Play My Game](https://username.github.io/mygame/game/)

3. Add ``.github/workflows/web.yml``:

   .. code-block:: yaml

     name: Web
     on:
       push:
         branches: [main]
       workflow_dispatch:
     jobs:
       web:
         uses: picocomputer/.github/.github/workflows/web.yml@main
         permissions:
           contents: read
           pages: write
           id-token: write

4. Push. Each player is at ``https://<user>.github.io/<repository>/<target>/``,
   and ``https://<user>.github.io/<repository>/`` lists them.

A repository can have a comment for each of its ROMs, such as one for
each example in a collection. Each line of a comment is a key and a
value:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Key
     - Description
   * - ``preset``
     - The CMake preset that builds the ROM, such as ``cc65/Release``,
       ``llvm-mos/Release`` or ``basic``. Required.
   * - ``target``
     - The CMake target. The ROM is ``<target>.rp6502``, and the player is
       published at ``<target>/``. Required.
   * - ``folder``
     - The folder of the CMake project, when it is not the root of the
       repository.
   * - ``title``, ``args``, ``install``, ``image``, ``db``, ``bg``,
       ``filter``
     - The settings of `The Page`_. A list is separated by spaces, and a
       path is relative to ``folder``.
   * - ``overlay``
     - ``no`` turns off the click-to-play overlay, for a program without
       sound. The default is ``yes``, because a browser plays no sound
       until the player clicks the page or presses a key.
   * - ``frames``
     - The number of frames, 60 a second, that the program runs before
       the screenshot. Default 120.
   * - ``footer``
     - A line of plain text under the game, such as the controls. Repeat
       it for more lines. A last line links to the repository.

The workflow also runs each ROM in the emulator and publishes the screen
at ``<target>/screenshot.png``, 640 pixels wide, so that a README can show
a current picture of the program with no image in the repository.
``frames`` sets how long the program runs first, such as until its title
screen. The program gets the same random numbers on every run, so the
same ``frames`` gives the same picture.

This comment makes a player with saves and a footer, and its link shows
the screenshot:

.. code-block:: text

  <!-- rp6502
  preset: llvm-mos/Release
  target: flappycoo
  title: Flappy Coo
  db: flappycoo
  footer: Space or click to flap, P to pause.
  -->
  [![Play Flappy Coo](https://rumbledethumps.github.io/flappycoo/flappycoo/screenshot.png)](https://rumbledethumps.github.io/flappycoo/flappycoo/)

The workflow uses the tools committed in ``tools/``, including
``tools/basic.rp6502`` for a BASIC project. A template, whose tools
should always be the latest, adds ``update-tools: true`` under ``with:``
in its workflow. ``rp6502: v0.35`` under ``with:`` keeps the players on
that release.


.. _web-hosts:

Other Web Servers
=================

Any web server that serves plain files can host a web player: copy the
four files into one folder. ``rp6502.wasm`` is loaded from the folder of
``rp6502.js``, and the ROM and the picture are loaded from paths
relative to ``index.html``.

A web player can be shown inside another page with an ``<iframe>``:

.. code-block:: html

  <iframe src="game/index.html" width="640" height="480"
          allow="autoplay; fullscreen; gamepad"></iframe>

Turn the overlay on for a player in an ``<iframe>``, because the frame
gets no key presses until it is clicked. The game on the :doc:`home page
<index>` of this site is a web player in an ``<iframe>``.
