Schematic, PCB, and Parts
#########################

Schematic
---------

`Picocomputer 6502 <_static/2023-06-07-rp6502.pdf>`_ (pdf)

I use "Picocomputer 6502" to refer to the reference design. Please use a differentiating name if you change the hardware. For example, "Picocomputer VERA" or "Ulf's Dream Computer". Think about what people asking for help should call the device and go with that.

Buying a Picocomputer
---------------------

You will need to place two orders. First, for the Printed Circuit Board. Second, for the electronic components. Some PCB factories will do the soldering for you, but you'll still need to order the ICs and plug them into sockets.

I have circuit boards in a `Tindie store <https://www.tindie.com/stores/rumbledethumps/>`_ that ships to the United States. International shipping is either too slow or too much when compared to getting boards made locally or in China.

To financially support this open source project, consider joining `Patreon <https://www.patreon.com/rumbledethumps>`_ or give a Super Thanks on any of my YouTube Videos.

Step 1. Watch the Videos
========================

To solder, or not to solder, that is the question. We're living in the future. You can homebrew a 6502 without a soldering iron. Choose your path:

`Here's the video where I build one without soldering. <https://youtu.be/4CjouKoCMUw>`_

`Here's the video where I solder one myself. <https://youtu.be/bwgLXEQdq20>`_

Step 2. Order Printed Circuit Boards
====================================

Download `the gerbers <_static/rp6502-reva-gerbers.zip>`_.

Gerbers are like PDFs for circuit boards. You'll be asked to upload these; simply upload the zip file from above. The PCB manufacturer's website should detect that this is a two-layer 150x100mm board.

PCB manufacturers that welcome hobbyists have optimized their basic services for production in multiples of five. You won't be able to order only one board.

There's a ton of options you can change if you like. The defaults will get you a classic green and white board with lead (Pb) HASL. Consider getting the lead-free HASL upgrade if the other four boards will be kicking around a drawer for the next 20 years.

Step 3. Order Assembly
======================

Skip this step if you want to solder it yourself.

PCBWay has a minimum quantity of one for assembly. They will use the boards you ordered in step 2. What you'll have them make is a "board of sockets" - the ICs will be installed by you later. It should never be constrained on parts availability since there are multiple vendors for every part.

Download `the BOM, notes, and photos <_static/rp6502-reva-assembly.zip>`_.

Request assembly with your PCB order and send the `BOM, notes, and photos <_static/rp6502-reva-assembly.zip>`_. There is no centroid file because there are no surface mount parts. The default options will work. Let them source the parts. Let them make substitutions.

There will be a short delay as they get you a price for the bill-of-materials. Then you can pay and wait. I was estimated four weeks and got it in three.

If they have a question, make sure you both you and your sales rep read the notes you sent them. If you have a question about options on their web site, ask your sales rep before asking on the forums. They help people all day long with projects far more complex than this. Even if you don't understand what you are doing, they can figure it out by looking at the zip files. Really, they do this all day long, and will probably enjoy the easy win.

Step 4. More Parts
==================

Factory assembled boards will need the eight ICs added to them. Upload the `active parts list <_static/rp6502-reva-active.csv>`_ to a `Mouser <https://mouser.com>`_ shopping cart.

If you are soldering it yourself, upload the `full parts list <_static/rp6502-reva-full.csv>`_ to a `Mouser <https://mouser.com>`_ shopping cart.

If something is out of stock, consult the substitution notes below. If it's the Pi Pico or Pi Pico H, do a text search since marketplace vendors often have them.

Step 5. Pi Pico Firmware
=========================

Download the `UF2 files  <https://github.com/picocomputer/rp6502/releases>`_.

To load firmware on a Pi Pico, hold its BOOTSEL button down while plugging it into a computer. The Pi Pico will appear as a storage device. Copy the VGA UF2 file to make a Pico VGA and the RIA UF2 file to make a Pico RIA. It should take less than 15 seconds to copy. The LED turns on when done.

Acrylic Sandwich Case
---------------------

The circuit board is 150 x 100mm (4x6 inches). I regularly see vendors on Amazon and eBay selling 150 x 100 x 3mm acrylic sheets. You'll need to drill 3mm holes for M3 standoffs. The recommended standoff height is >=16mm for the top and >=3.5mm for the bottom.

Full Parts List
---------------

`All Parts CSV <_static/rp6502-reva-full.csv>`_

.. csv-table::
   :file: _static/rp6502-reva-full.csv
   :header-rows: 1


Active Parts List
-----------------

`Active Parts CSV <_static/rp6502-reva-active.csv>`_

.. csv-table::
   :file: _static/rp6502-reva-active.csv
   :header-rows: 1

Pi Picos Parts List
-------------------

Alternative part numbers for the Pi Picos.

.. csv-table::
   :file: _static/rp6502-reva-picos.csv
   :header-rows: 1


Parts Substitution
------------------

All resistors are <= 1% tolerance. Any power rating. Leads must fit 0.8mm plated holes spaced 10mm apart. Recommended size is approximately 0.1" x 0.25" (2.4-2.6mm x 6-8mm).

0.1 μF ceramic capacitors are available in axial packaging (like resistors) but you may use classic radial (disc) capacitors if you prefer. Leads must fit 0.8mm plated holes spaced 10mm apart. Only a voltage of >=10V is required. Tolerance and temperature coefficient do not matter.

Yes, 47 μF ceramic capacitors are expensive, but you only need two and they never leak. Leads must fit 0.8mm plated holes spaced 5mm apart. Only a voltage of \>=10V is required. Tolerance and temperature coefficient do not matter.

The CUI audio jack is available in many colors and with optional switches. The switches are not used, but the circuit board can accept the extra leads.

The REBOOT switch is available from multiple manufacturers in various lengths, colors, and activation forces. Nothing matters except that it's "momentary on".

The VGA jack is available from multiple manufacturers. This style has been around since the beginning, so if it looks like it'll fit then it probably will. Newer VGA jacks are designed to use less PCB space or be oven soldered and will be visibly different enough to avoid.

The 74xx ICs must be true CMOS. Use AC or HC, do not use ACT or HCT. Two out of three must be AC for 8MHz. You may use 74HC00 and 74HC02 instead of AC, but 8MHz will not be achievable. I've never seen a DIP 74AC30, but if you find one then it would be preferred over the 74HC30.

The RAM IC is 128k because 2x32k is more expensive. Speed must be \<=70ns for 8MHz.

The WDC W65C02S and W65C22S must not be substituted. Do not attempt to use NMOS chips (without the C in the number). Some older CMOS designs may work but there are no plans to support out-of-production ICs.

Only the Raspberry Pi design of the Pi Pico has been tested. Both original and "H" (header) versions work great. Pin-compatible alternatives may work, check the forums. The 3-pin SWD connection on the Pi Pico RIA is no longer used internally and may be ignored when looking for alternatives.
