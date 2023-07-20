Schematic, PCB, and Parts
#########################

Schematic
---------

`Picocomputer 6502 <_static/2023-06-07-rp6502.pdf>`_ (pdf)

I use "Picocomputer 6502" to refer to the reference design. Please use a differentiating name if you change the hardware. For example, "Picocomputer VERA" or "Ulf's Dream Computer". Think about what people asking for help should call the device and go with that.

Buying a Picocomputer
---------------------

I do not sell hardware at this time and have no immediate plans to do so. Instead, I provide design files that have been tested so that all you need to do is upload them to a factory and use their default options.

There are no affilate links here. To financially support this open source project, consider joining `Patreon <https://www.patreon.com/rumbledethumps>`_ or give a Super Thanks on any of my YouTube Videos.

Even better than money would be pull requests for the many `unfinished features <https://github.com/picocomputer/rp6502/issues>`_ or `this documentation <https://github.com/picocomputer/picocomputer.github.io>`_.

Factory Assembly
----------------

Factory assembly only requires you to plug in the ICs. There is no soldering.

1. Watch `the PCBWay video <http://example.com>`_.
2. Send the `gerbers <_static/gerbers.zip>`_ to a PCB manufacturer that does assembly. The default options will be correct.
3. Request assembly and send the `BOM, notes, and photos <_static/assembly.zip>`_. The default options will be correct.
4. Upload the `active parts list <_static/active.csv>`_ to a `Mouser <https://mouser.com>`_ shopping cart. If something is out of stock, consult the substitution notes below.
5. The latest firmware is on `the forums <https://github.com/orgs/picocomputer/discussions/4>`_.

If the factory has questions you can't answer, post them on the forums. It will most likely be to confirm a part substitution. They may also send you a photo to review before final soldering. There's nothing tricky about the design, so there's no need to overanalyze this.

DIY Assembly
------------

DIY assembly requires through hole soldering. There are no surface mounted devices. IMO, soldering the pins on the Pi Pico is the most difficult part, so you'll be fine if you think you can handle that.

1. Watch `the DIY video <https://youtu.be/bwgLXEQdq20>`_.
2. Send the `gerbers <_static/gerbers.zip>`_ to a PCB manufacturer. The default options will be correct.
3. Upload the `full parts list <_static/parts.csv>`_ to a `Mouser <https://mouser.com>`_ shopping cart. If something is out of stock, consult the substitution notes below.
4. The latest firmware is on `the forums <https://github.com/orgs/picocomputer/discussions/4>`_.

Acrylic Sandwich Case
---------------------

The circuit board is 150 x 100mm (4x6 inches). I regularly see vendors on Amazon and eBay selling 150 x 100 x 3mm acrylic sheets. You'll need to drill 3mm holes for M3 standoffs. The recommended standoff height is >=15.5mm for the top and >=3.5mm for the bottom.

Full Parts List
---------------

`Download CSV <_static/parts.csv>`_

.. csv-table::
   :file: _static/parts.csv
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

Only the Raspberry Pi design of the Pi Pico has been tested. The "H" (header) version may be used, but connecting the three SWD pins will require soldering a debug wire to the circuit board. The SWD connection is only used for kernel development, so it's OK to leave this unconnected.
