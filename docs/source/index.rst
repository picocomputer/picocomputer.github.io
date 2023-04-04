.. toctree::
   :hidden:

   RIA <ria>
   VGA <vga>
   API <api>

Picocomputer 6502
=================

The Picocomputer explores retro computing and game development by removing the barrier between genuine 8-bit hardware and modern devices. This is the documentation.

The RP6502 chipset comes in two parts. The RP6502-RIA is an interface adapter that connects to a 6502 much like CIA, VIA, and ACIA devices. The RP6502-VGA is an optional video chip that connects to the RP6502-RIA. Both of these are simply Raspberry Pi Picos with the RP6502 firmware.

RP6502 Datasheets:

* :doc:`RIA Interface Adapter <ria>`
* :doc:`VGA Graphics Processing Unit <vga>`
* :doc:`API for 6502 Programing <api>`




* `Reference Design Schematic <_static/schematic.pdf>`_


.. :_how to write mathematics: ../_static/how-to-write-mathematics-halmos.pdf

I use "Picocomputer 6502" to refer to the reference design. It is my hope that derivative projects use a different name. For example, "Picocomputer VERA" or "Ulf's Dream Computer". Think about what people asking for help should call the device and go with that.