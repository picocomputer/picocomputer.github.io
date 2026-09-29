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

``rp6502.js`` and ``rp6502.wasm`` are in the web zip on the `releases
page <https://github.com/picocomputer/rp6502/releases/latest>`__, with a
sample ``index.html`` and program, and they are always replaced as a
pair. In a CMake project, ``rp6502_web()`` builds all four files into a
zip, as described in `Building with CMake`_. ``index.html`` is not tied to
a release: the ``index.html`` described here needs release 0.36 or later,
and it works with the ``rp6502.js`` and ``rp6502.wasm`` of every later
release. Any change to the settings is listed in the release notes.


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
   * - ``border``
     - ``'8px'``
     - Space around the game, in the ``bg`` color, as a CSS length such as
       ``8px`` or ``1em``. It keeps text on the edge of the canvas apart
       from the page around it.
   * - ``filter``
     - ``'sharp'``
     - How pixels are scaled: ``nearest``, ``linear`` or ``sharp``.
       Default ``sharp``, which enlarges by a whole number and then
       smooths.
   * - ``overlay``
     - ``'overlay'``
     - The ``id`` of the template shown while there is no sound. See
       `Click to Play`_.
   * - ``run``
     - ``'always'``
     - When the program starts: ``always``, ``onaudio`` or ``onclick``.
       Default ``always``. See `Click to Play`_.
   * - ``footer``
     - ``'Arrows to move.'``
     - A line of HTML under the game, with links under it. See `Footer`_.
   * - ``github``
     - ``'user/mygame'``
     - The GitHub repository linked under the footer.

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
web site. A site that holds the games of many people shares that set
among them, so there, name the database with your full user name and the
full project name, such as ``rumbledethumps-flappycoo``. A site of your
own, such as a GitHub Pages site, ``<user>.github.io``, holds only your
projects, so there the full project name is enough. With ``db`` blank,
saves last until the page closes.

.. _web-overlay:

Click to Play
-------------

A browser plays no sound on a page until the player clicks the page or
presses a key. While there is no sound, the click-to-play overlay covers
the game with a play button, so that the player knows to click it. The
click turns the sound on and removes the overlay. Where the browser plays
sound at once, there is no overlay.

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

The ``index.html`` in the web zip has a round play button in its overlay
template, with settings at the top of its style:

.. code-block:: css

  .overlay {
    --y: 50%;                              /* height of the button, from the top */
    --size: clamp(56px, 18vmin, 96px);     /* width of the button */
    --shade: rgba(0, 0, 0, .45);           /* over the game */

``--y: 70%`` moves the button lower, over an empty part of a title
screen.

``run`` sets when the program starts:

- ``always``, the default: at once, under the overlay while there is no
  sound.
- ``onaudio``: when there is sound, so the program starts from the
  beginning with sound.
- ``onclick``: at a click on the overlay or a key press, even where the
  browser plays sound at once.

.. _web-footer:

Footer
------

``footer`` is a line under the game, such as the controls. Under it, a
second line links to the GitHub repository in ``github``, to the ROM for
download, and to this site:

.. code-block:: javascript

  footer: 'Arrows to move, Space to fire.',
  github: 'user/mygame',

The footer is HTML, so it can include a link, which opens in a new tab with
``target="_blank"`` instead of in place of the game. The game is scaled
to the space above the footer. Without ``footer``, there is no footer; a
page of your own can put any HTML after the script instead.

License Notices
---------------

With ``?credits`` at the end of its address, such as
``https://example.com/game/?credits``, the page shows the license notices
of the components in ``rp6502.js`` and ``rp6502.wasm``.


.. _web-cmake:

Building with CMake
===================

In a CMake project, ``rp6502_web()`` packages a ROM with the emulator and
a page into a zip, ready to upload. This line builds ``web/game.zip`` in
the build folder from the ROM of the ``game`` target, with the page from
the web zip and the emulator of the latest release:

.. code-block:: cmake

  rp6502_web(game)

The same files are unpacked next to it in ``web/game/``. ``CONFIG`` sets
settings of the page, as JavaScript, with a comma after each one:

.. code-block:: cmake

  rp6502_web(game CONFIG [[
      title: 'My Game',
      footer: 'Arrows to move, Space to fire.',
  ]])

The settings replace the same settings in the page, and the others are
added. ``rom`` is always the ROM of the target, and ``github`` is the
GitHub repository that the git remote of the project names, unless
``CONFIG`` names another. ``PAGE`` gives a page of
your own, and ``OUTPUT`` names the zip, so one ROM can be packaged for
several sites:

.. code-block:: cmake

  rp6502_web(game OUTPUT pages.zip PAGE web/pages.html)
  rp6502_web(game OUTPUT arcade.zip PAGE web/arcade)

A file after ``PAGE`` is stored in the zip as ``index.html``. A folder is
copied into the zip with its subfolders, and an ``index.html`` at its
root is the page. ``EMULATOR`` names the web zip that ``rp6502.js`` and
``rp6502.wasm`` come from, in the forms of :ref:`Fetching BASIC and the
Emulator <sdk-fetch>`:

.. code-block:: cmake

  rp6502_web(game EMULATOR v0.36)

In VS Code, choose "RP6502 (Web)" in the Run and Debug side panel and
press F5. The project is built, and the browser opens a page with a link
to every web player in the build folder.


.. _web-github:

GitHub Pages
============

GitHub Pages publishes web pages from a GitHub repository, so a link in
the README of a game can open a web player for it. The players are named
in the markdown of the repository, and a workflow from
`picocomputer/.github <https://github.com/picocomputer/.github>`__ builds
each one with ``rp6502_web()`` and publishes it on every push to
``main``.

1. On GitHub, open Settings > Pages, and set Source to GitHub Actions.
2. Put this comment above the play link in ``README.md``, or in any other
   markdown file of the repository. GitHub does not show it.

   .. code-block:: text

     <!-- rp6502
     preset: cc65/Release
     publish: game.zip
     -->
     [Play My Game](https://username.github.io/mygame/game/)

3. Add ``.github/workflows/web.yml``:

   .. code-block:: yaml

     name: Web
     on:
       push:
         branches: [main]
       workflow_dispatch:
         inputs:
           source:
             description: Branch, tag or commit to build
           emulator:
             description: Emulator, such as v0.36
     jobs:
       web:
         uses: picocomputer/.github/.github/workflows/web.yml@main
         with:
           source: ${{ inputs.source }}
           emulator: ${{ inputs.emulator }}
         permissions:
           contents: read
           pages: write
           id-token: write

4. Push. Each player is at ``https://<user>.github.io/<repository>/<name>/``,
   where ``<name>`` is the zip without ``.zip``, and
   ``https://<user>.github.io/<repository>/`` lists them.

A repository can have a comment for each of its zips, such as one for
each example in a collection. Each line of a comment is a key and a
value:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Key
     - Description
   * - ``preset``
     - The CMake preset that builds the zip, such as ``cc65/Release``,
       ``llvm-mos/Release`` or ``basic``. Required.
   * - ``publish``
     - The zip that ``rp6502_web()`` makes, such as ``game.zip``. It is
       published at ``game/``. Required.
   * - ``folder``
     - The folder of the CMake project, when it is not the root of the
       repository.
   * - ``frames``
     - The number of frames, 60 a second, that the program runs before
       the screenshot. Default 120.

The workflow also runs each ROM in the emulator and publishes the screen
at ``<name>/screenshot.png``, 640 pixels wide, so that a README can show
a current picture of the program with no image in the repository.
``frames`` sets how long the program runs first, such as until its title
screen. The program gets the same random numbers on every run, so the
same ``frames`` gives the same picture. This comment and link show the
screenshot:

.. code-block:: text

  <!-- rp6502
  preset: llvm-mos/Release
  publish: flappycoo.zip
  -->
  [![Play Flappy Coo](https://rumbledethumps.github.io/flappycoo/flappycoo/screenshot.png)](https://rumbledethumps.github.io/flappycoo/flappycoo/)

"Run workflow" on the Actions tab of the repository runs the workflow by
hand. ``source`` builds another branch, tag or commit of the repository,
and ``emulator`` replaces the ``EMULATOR`` of every ``rp6502_web()``, in
the forms of :ref:`Fetching BASIC and the Emulator <sdk-fetch>`. A commit
of the emulator is for testing: it comes from the CI build of that
commit, which is kept for 90 days, and the build of a pull request is the
pull request merged with ``main``.

The workflow uses the tools committed in ``tools/``. A template, whose
tools should always be the latest, adds ``update-tools: true`` under
``with:`` in its workflow.


.. _web-hosts:

Other Web Servers
=================

Any web server that serves plain files can host a web player: copy the
files of the zip into one folder. ``rp6502.wasm`` is loaded from the
folder of ``rp6502.js``, and the ROM is loaded from a path relative to
``index.html``.

A web player can be shown inside another page with an ``<iframe>``:

.. code-block:: html

  <iframe src="game/index.html" width="640" height="480"
          allow="autoplay; fullscreen; gamepad"></iframe>

The game on the :doc:`home page <index>` of this site is a web player in
an ``<iframe>``.
