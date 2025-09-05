.. toctree::
   :hidden:

   Hardware <hardware>
   RIA <ria>
   RIA W <ria_w>
   VGA <vga>
   API <api>

Picocomputer 6502
=================

The **Picocomputer 6502** is a platform for exploring retro computing and game development, bridging the gap between authentic 8-bit hardware and modern devices.

.. image:: _static/founders.jpg
   :width: 600
   :alt: Picocomputer Photo

Key Features
------------

- **64KB System RAM**
- **64KB Extended RAM**
- **VGA Graphics Output**
- **8-Channel Stereo Sound Generator**
- **USB Support** for Keyboard, Mouse, and Gamepads
- **Bluetooth LE** for Keyboard, Mouse, and Gamepads
- **WiFi** for NTP and modem emulation
- **100% Through-Hole Construction**

Resources
---------

For support and community interaction, please use the following channels:

- **GitHub:** https://github.com/picocomputer
- **Forums:** https://github.com/picocomputer/community/discussions
- **Discord:** https://discord.gg/TC6X8kTr6d
- **Wiki:** https://github.com/picocomputer/community/wiki
- **YouTube:** https://youtube.com/playlist?list=PLvCRDUYedILfHDoD57Yj8BAXNmNJLVM2r

Datasheets & Documentation
--------------------------

The RP6502 chipset consists of three main components:

- :doc:`RP6502-RIA<ria>`: An interface adapter for the 6502, similar to CIA, VIA, and ACIA devices.
- :doc:`RP6502-RIA-W<ria_w>`: An alternative RIA with wireless radio technology.
- :doc:`RP6502-VGA<vga>`: An optional video chip that connects to the RP6502-RIA.

All components are based on Raspberry Pi Pico 2 boards running RP6502 firmware.

Further documentation:

- :doc:`Schematic, PCB, and Parts <hardware>`
- :doc:`RIA Interface Adapter <ria>`
- :doc:`RIA W Interface Adapter <ria_w>`
- :doc:`VGA Graphics Processing Unit <vga>`
- :doc:`API for 6502 Programming <api>`
