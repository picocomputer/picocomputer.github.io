Schematic, PCB, and Parts
#########################

Schematic
---------

`Picocomputer 6502 <_static/schematic.pdf>`_

I use "Picocomputer 6502" to refer to the reference design. This is buildable on a breadboard. Please use a differentiating name if you change the hardware. For example, "Picocomputer VERA" or "Ulf's Dream Computer". Think about what people asking for help should call the device and go with that.

Tools
-----

Assembly requires a soldering iron, wire cutters, personal protection, and personal responsibility.

Parts List
----------

This is everything for a circuit board. You can send this CSV to mouser.com. If something is out of stock, consult the substitution notes below.

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
