Fonts
#####

These charts show every glyph of the VGA's built-in fonts. The VGA
terminal and the character modes draw text with them. Under each glyph
is its code in hex and decimal and the Unicode character it stands for,
which is the character you get when you copy it from the screen. Hold
the pointer over a glyph to see the character's name.

Each font comes in two sizes. The 80-column terminal and 8x16 character
modes use 8x16, and the 40-column terminal and 8x8 character modes use
8x8.

ASCII
=====

The first 128 codes are the same in every code page: ASCII, with
symbols in place of the control codes.

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/ascii-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/ascii-8.html

Code Pages
==========

The other 128 codes, 0x80 to 0xFF, come from the code page that
:ref:`RIA_ATTR_CODE_PAGE <api-ria-attributes>` selects. On the
:doc:`pico`, ``SET CP`` sets it, and on the :doc:`emu`, ``--cp``.

437 United States
-----------------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp437-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp437-8.html

720 Arabic
----------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp720-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp720-8.html

737 Greek
---------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp737-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp737-8.html

771 Cyrillic and Lithuanian
---------------------------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp771-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp771-8.html

775 Baltic
----------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp775-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp775-8.html

850 Western European
--------------------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp850-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp850-8.html

852 Central European
--------------------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp852-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp852-8.html

855 Cyrillic
------------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp855-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp855-8.html

857 Turkish
-----------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp857-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp857-8.html

860 Portuguese
--------------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp860-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp860-8.html

861 Icelandic
-------------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp861-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp861-8.html

862 Hebrew
----------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp862-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp862-8.html

863 Canadian French
-------------------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp863-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp863-8.html

864 Arabic
----------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp864-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp864-8.html

865 Nordic
----------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp865-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp865-8.html

866 Russian
-----------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp866-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp866-8.html

869 Greek
---------

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/cp869-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/cp869-8.html

Italics
=======

The 80-column terminal draws codes below 0x80 in italics with SGR 3. The
8x8 font has no italics.

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/italic-16.html

DEC Special Graphics
====================

The DEC Special Graphics set of the terminal shows lines and corners in
place of codes 0x5F to 0x7E. See :ref:`term-character-sets`.

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/dec-graphics-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/dec-graphics-8.html

DEC Technical
=============

The DEC Technical set of the terminal shows mathematical symbols in place
of codes 0x21 to 0x7E. See :ref:`term-character-sets`.

.. tab:: 8x16

   .. raw:: html
      :file: _static/fonts/dec-technical-16.html

.. tab:: 8x8

   .. raw:: html
      :file: _static/fonts/dec-technical-8.html
