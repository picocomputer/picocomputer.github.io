.. toctree::
   :hidden:

   Hardware <hardware>
   RP6502-RIA <ria>
   RP6502-RIA-W <ria_w>
   RP6502-VGA <vga>
   RP6502-OS <api>

Picocomputer 6502
=================

The **Picocomputer 6502** is a tribute to the processor that launched a computing revolution. Don't let the low parts count and simple construction fool you. The lack of apparent complexity is a by product of the design philosophy: Keep the essence of programming a 6502 and 6522 and rethink everything else.

.. image:: _static/founders.jpg
   :width: 600
   :alt: Picocomputer Photo

Key Features
------------

- **64KB System RAM**
- **64KB Extended RAM**
- **VGA Graphics Output**
- **8-Channel Stereo Sound Generator**
- **Protected Operating System**
- **USB Support** for Keyboard, Mouse, and Gamepads
- **Bluetooth LE** for Keyboard, Mouse, and Gamepads
- **WiFi** for NTP and modem emulation

How To Obtain
-------------

The **Picocomputer 6502** is a single board computer you build yourself. It's been built by hundreds of people. You can also have a single unit manufactured especially for you in China. The whole process has been documented and tested. Everything you need to know is on the hardware page:

- :doc:`Schematic, PCB, and Parts <hardware>`

Resources
---------

For support and community interaction, please use the following channels:

- **GitHub:** https://github.com/picocomputer
- **Forums:** https://github.com/picocomputer/community/discussions
- **Discord:** https://discord.gg/TC6X8kTr6d
- **Wiki:** https://github.com/picocomputer/community/wiki

The entire development process was documented in a series of YouTube videos. The broad strokes are all still in place but remember that these video were made during development.

- **YouTube:** https://youtube.com/playlist?list=PLvCRDUYedILfHDoD57Yj8BAXNmNJLVM2r

Datasheets
----------

The RP6502 chipset consists of three main components:

- :doc:`RP6502-RIA <ria>`: Interface adapter for the 6502, similar to CIA, VIA, and ACIA devices.
- :doc:`RP6502-RIA-W <ria_w>`: Wireless features available when using the recommended "Pico 2 W".
- :doc:`RP6502-VGA <vga>`: Optional video adapter that connects to the RP6502-RIA.

The RP6502-RIA runs a protected operating system which you can use from the 6502.

- :doc:`RP6502-OS <api>`
