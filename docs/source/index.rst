.. toctree::
   :hidden:

   Hardware <hardware>
   RIA <ria>
   VGA <vga>
   API <api>

Picocomputer 6502
=================

.. image:: _static/founders.jpg
  :width: 600
  :alt: Alternative text

The Picocomputer explores retro computing and game development by removing the barrier between genuine 8-bit hardware and modern devices. This is the documentation.

* GitHub: https://github.com/picocomputer
* Forums: https://github.com/picocomputer/community/discussions
* Wiki: https://github.com/picocomputer/community/wiki
* YouTube: https://youtube.com/playlist?list=PLvCRDUYedILfHDoD57Yj8BAXNmNJLVM2r

The RP6502 chipset comes in two parts. The RP6502-RIA is an interface adapter that connects to a 6502 much like CIA, VIA, and ACIA devices. The RP6502-VGA is an optional video chip that connects to the RP6502-RIA. Both of these are simply Raspberry Pi Picos with the RP6502 firmware.

RP6502 Datasheets:

* :doc:`Schematic, PCB, and Parts <hardware>`
* :doc:`RIA Interface Adapter <ria>`
* :doc:`VGA Graphics Processing Unit <vga>`
* :doc:`API for 6502 Programing <api>`
