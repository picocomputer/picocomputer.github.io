============================
RP6502-WEB
============================

RP6502 - Web Player


Introduction
============

With the RP6502-WEB, you can put a playable game on the GitHub page of
your project, upload it to itch.io, or put it on your blog. One click on
the link starts the game in a web browser, with no download and no
emulator to install.

The RP6502-WEB is the machine for the web. It is a Picocomputer hosted in
a web browser, with sound, a keyboard, a mouse, and up to four gamepads.
The browser can keep high scores and saved games between visits, as
described in `Saves`_.

A web player is the game, the emulator and a page, which ``rp6502_web()``
builds into one zip. For :ref:`GitHub Pages <web-github>`, a workflow
builds and publishes the web players of a repository on every push to
``main``, with a screenshot for the README. The same zip can be
uploaded to itch.io, and :ref:`any web server that serves plain files
<web-hosts>` can host its files.


.. _web-files:

The Files
=========

A web player is four files, served together from one folder:

- ``index.html``, the page, with the settings for the program.
- ``rp6502.js`` and ``rp6502.wasm``, the emulator.
- The ROM, such as ``game.rp6502``.

``rp6502.js`` and ``rp6502.wasm`` are in the web zip on the `releases
page <https://github.com/picocomputer/rp6502/releases/latest>`__, with a
sample ``index.html`` and program, and they are always replaced as a
pair. In a CMake project, ``rp6502_web()`` builds all four files into a
zip, as described in `Building with CMake`_.


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
  <title>My Game</title>
  <style>
    html, body { height: 100%; margin: 0; overflow: hidden; background: #000; }
    #game { height: 100%; }
  </style>
  </head>
  <body>
  <div id="game"></div>
  <script src="rp6502.js" onerror="document.body.textContent = 'Could not load rp6502.js'"></script>
  <script>
    rp6502('game', 'game.rp6502', {
      title: 'My Game',
      db:    'username-mygame',
    });
  </script>
  </body>
  </html>

``rp6502(container, rom, options)`` puts a player in the page:

- ``container`` is the element for the player, or the ``id`` of an
  element in the page, such as ``'game'``.
- ``rom`` is the program that runs, as a path from ``index.html``.
- ``options`` holds the settings listed below, and can be left out.

``rp6502.js`` defines ``rp6502()``, so a plain ``<script src>``, with no
``async`` or ``defer``, loads it before the script with the call.

The player is as wide as its container. In a container with no height,
the screen is 4:3 and the footer goes below it. A container given a
height is filled, as ``#game`` fills the window here.

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
   * - ``install``
     - ``'game.bas'``
     - More files for the program, as a path from ``index.html`` or a
       list of paths. Each one is installed on the null drive, where the
       program reads it as ``:`` followed by the file name, in any case.
       See :ref:`Installed ROMs <port-installed-roms>`.
   * - ``title``
     - ``'My Game'``
     - The name in the browser tab while keys go to this player. Without
       it, the tab shows the ``<title>`` of the page.
   * - ``args``
     - ``['-c1']``
     - The arguments for the program, argv[1] and on.
   * - ``db``
     - ``'username-mygame'``
     - The name of the IndexedDB database for saves. Without it, saves
       last until the page closes. See `Saves`_.
   * - ``bgcolor``
     - ``'000000'``
     - The color around the picture when the player and the canvas have
       different shapes, as six hex digits, RRGGBB, with or without
       ``#``. Default ``000000``.
   * - ``border``
     - ``'8px'``
     - Space around the game, in the ``bgcolor`` color, as a CSS length such as
       ``8px`` or ``1em``. It keeps text on the edge of the canvas apart
       from the page around it.
   * - ``filter``
     - ``'sharp'``
     - How pixels are scaled: ``nearest``, ``linear`` or ``sharp``.
       Default ``sharp``, which enlarges by a whole number and then
       smooths.
   * - ``autoplay``
     - ``'muted'``
     - When the program and the sound start: ``on``, ``auto``, ``off`` or
       ``muted``. Default ``on``. See `Click to Play`_.
   * - ``overlay``
     - ``'overlay'``
     - What covers the game while there is no sound: a play button by
       default, nothing with ``false``, or the ``<template>`` with this
       ``id``. See `Click to Play`_.
   * - ``footer``
     - ``'Arrows to move.'``
     - A line of HTML under the game, with links under it. See `Footer`_.
   * - ``github``
     - ``'user/mygame'``
     - The GitHub repository linked under the footer.

A setting that is left out, or left blank, is off or takes its default,
except ``autoplay``, which must not be blank. For example, Microsoft
BASIC loads and runs a program named as an argument, and ``-c1`` keeps
the keyboard in capitals:

.. code-block:: javascript

  rp6502('game', 'basic.rp6502', {
    install: 'game.bas',
    args:    ['-c1', ':GAME.BAS'],
  });

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

A browser usually plays no sound on a page until a click or a key press
there, so a player is silent until a click on it or a key that goes to
it. While a player is silent, an overlay covers the game with a play
button, and the click starts the sound and removes the overlay.

A page cannot scroll when it fits in the window, or when ``html`` or
``body`` has ``overflow: hidden``, as in the page above. On a page that
cannot scroll, keys go to the player while nothing else in the page has
the focus. There, the sound starts when the page loads if the browser
allows sound without a click, and otherwise at the first key. `Autoplay
policy in Chrome <https://developer.chrome.com/blog/autoplay>`__ lists
when Chrome allows sound without a click. On a page that scrolls, the
arrows and Space scroll the page until the player is clicked.

``autoplay`` sets when the program starts, and whether keys and sound
start before a click:

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Value
     - Description
   * - ``on``
     - The default. The program starts when the page loads. Before a
       click, keys and sound start only on a page that cannot scroll.
   * - ``auto``
     - The program starts when the sound starts, so it begins with
       sound. Otherwise the same as ``on``.
   * - ``off``
     - The program starts at the first click on the player.
   * - ``muted``
     - The program starts when the page loads, without sound and under
       the overlay. Keys and sound start at a click on the player.

The play button is styled with these CSS custom properties, set on
``:root`` for every player in the page, or on one container, such as
``#game``:

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Property
     - Description
   * - ``--rp6502-play-x``, ``--rp6502-play-y``
     - The position of the button and the "Click to play" label, from
       the left and from the top. Default ``50%``.
   * - ``--rp6502-button-size``
     - The width of the button. Default ``clamp(56px, 18cqmin, 96px)``,
       where ``1cqmin`` is 1% of the shorter side of the screen.
   * - ``--rp6502-overlay-background``
     - The color over the game. Default ``rgba(0, 0, 0, .45)``.

``--rp6502-play-y: 70%`` moves the button lower, over an empty part of a
title screen:

.. code-block:: css

  #game { --rp6502-play-y: 70%; }

A ``<template>`` in the page can replace the play button. The browser
keeps the HTML in a template without showing it. ``overlay`` names the
template by its ``id``, and the first element in the template is placed
over the game. To add a simple overlay to the page above, put this style
in ``<head>`` and this template in ``<body>``, before the scripts:

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

Then name it with ``overlay``:

.. code-block:: javascript

  rp6502('game', 'game.rp6502', {overlay: 'overlay'});

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
page of your own can put any HTML under the container instead.

License Notices
---------------

With ``?credits`` at the end of its address, such as
``https://example.com/game/?credits``, the page shows the license notices
of the components in ``rp6502.js`` and ``rp6502.wasm``.


.. _web-players:

Players in a Page
=================

A page can hold several players, such as a blog post with a game after
each listing. These lines put two players in a page, with the play
button of the first one lower:

.. code-block:: html

  <style>
    #game1 { --rp6502-play-y: 84%; }
  </style>
  <div id="game1"></div>
  <div id="game2"></div>
  <script src="rp6502.js"></script>
  <script>
    rp6502('game1', 'starhopper.rp6502');
    rp6502('game2', 'adventure.rp6502');
  </script>

A page loads ``rp6502.js`` once, for any number of players. Each call
makes a separate player, with a separate program, screen and sound.
``rp6502()`` returns the player, an object with ``element``, the
container, and ``destroy()``.

Keys, a paste and gamepads go to the player with the focus, and a click
on a player moves the focus to it. On a page that cannot scroll, as
described in `Click to Play`_, keys go to the last player clicked while
nothing in the page has the focus, and to the first player before any
click. Players that run at the same time need different ``db`` names,
because a database is used by one player at a time.

Removing a Player
-----------------

``destroy()`` stops the program, stores the saves, frees the database for
another player, and removes everything the player added to the
container. It returns a Promise that resolves when the saves are stored.
A new player can go in the same container at once. For a new player with
the same ``db``, wait for the Promise first, as in this function, which
changes the program:

.. code-block:: javascript

  let player = rp6502('game', 'one.rp6502', {db: 'me-games'});

  async function change(rom) {
    await player.destroy();
    player = rp6502('game', rom, {db: 'me-games'});
  }

Removing the container from the page does not stop the player, so call
``destroy()`` first.

In a Web Component
------------------

A player works in a shadow root, such as in a web component. Pass the
element itself as ``container``, because an ``id`` is looked up only in
the document. ``overlay`` can name a ``<template>`` in the same shadow
root. The style rules of the page do not apply inside a shadow root, but
the ``--rp6502-*`` properties set on the host element or on ``:root``
do, so ``my-arcade { --rp6502-play-y: 84%; }`` in the page moves the play
button of the element below:

.. code-block:: javascript

  class MyArcade extends HTMLElement {
    #shadow = this.attachShadow({mode: 'closed'});
    #player;

    connectedCallback() {
      const screen = document.createElement('div');
      this.#shadow.replaceChildren(screen);
      this.#player = rp6502(screen, this.getAttribute('rom'));
    }

    disconnectedCallback() {
      this.#player.destroy();
    }
  }
  customElements.define('my-arcade', MyArcade);

.. code-block:: html

  <my-arcade rom="game.rp6502"></my-arcade>

The shadow root is stored in a private field, so the same code works
for a closed root, where ``this.shadowRoot`` is ``null``.


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
options, as JavaScript, with a comma after each one:

.. code-block:: cmake

  rp6502_web(game CONFIG [[
      title: 'My Game',
      footer: 'Arrows to move, Space to fire.',
  ]])

The options in ``CONFIG`` replace the same options of each ``rp6502()``
call in the page, and the others are added. The ``rom`` argument is
always the ROM of the target, and ``github`` is the GitHub repository
that the git remote of the project names, unless ``CONFIG`` names
another. ``PAGE`` gives a page of your own, and ``OUTPUT`` names the zip,
so one ROM can be packaged for several sites:

.. code-block:: cmake

  rp6502_web(game OUTPUT pages.zip PAGE web/pages.html)
  rp6502_web(game OUTPUT arcade.zip PAGE web/arcade)

A file after ``PAGE`` is stored in the zip as ``index.html``. A folder is
copied into the zip with its subfolders, and an ``index.html`` at its
root is the page. A page of your own holds a container, loads
``rp6502.js`` with ``<script src="rp6502.js">``, and calls ``rp6502()``
in a later script, as in `The Page`_.

``EMULATOR`` names the web zip that ``rp6502.js`` and ``rp6502.wasm``
come from, in the forms of :ref:`Fetching BASIC and the Emulator
<sdk-fetch>`:

.. code-block:: cmake

  rp6502_web(game EMULATOR tools/rp6502-web.zip)

In VS Code, choose "RP6502-WEB" in the Run and Debug side panel and
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
             description: Emulator, in the forms EMULATOR takes
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


.. _web-hosts:

Other Web Servers
=================

Any web server that serves plain files can host a web player: copy the
files of the zip into one folder. ``rp6502.wasm`` is loaded from the
folder of ``rp6502.js``, and the ROM is loaded from a path relative to
``index.html``.

On itch.io, the zip is uploaded as it is, to a project of the HTML kind,
and marked to be played in the browser. itch.io serves the games of many
people from one site, so name ``db`` as described in `Saves`_.

A web player can be shown inside another page with an ``<iframe>``:

.. code-block:: html

  <iframe src="game/index.html" width="640" height="480"
          allow="autoplay; fullscreen; gamepad"></iframe>

The game on the :doc:`home page <index>` of this site is a web player in
an ``<iframe>``.
