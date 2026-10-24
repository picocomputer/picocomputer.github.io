============================
Parts Substitution
============================

Pi Picos Without Headers
========================

The parts lists of :doc:`pico-solder` and :doc:`pico-socket` both have Pi
Picos with headers, which need no soldering. If you prefer to solder the
headers yourself, these are the part numbers of the Pi Picos without them.

`Pi Picos CSV <_static/rp6502-revb-picos.csv>`_

.. csv-table::
   :file: _static/rp6502-revb-picos.csv
   :header-rows: 1


Substitutions
=============

The WDC W65C02S and W65C22S must not be substituted. Don't try NMOS chips (the
ones without the C in the part number). Some older CMOS designs may work, but
there are no plans to support out-of-production ICs.

Only Raspberry Pi's own Pico 2 has been tested. Both the original and the "H"
(header) versions work great. Pin-compatible alternatives usually work too.

The parts list specifies a Pico 2 W for the RIA. Its radio adds Wi-Fi and
Bluetooth. A Pico 2 without the W runs the RIA without them, flashed with
``rp6502-ria.uf2`` in place of ``rp6502-ria-w.uf2``.

All resistors are 1% tolerance or better, any power rating. Leads must fit
0.8 mm plated holes spaced 10 mm apart. A size of roughly 0.1" x 0.25"
(2.4-2.6 mm x 6-8 mm) is recommended.

0.1 μF ceramic capacitors come in axial packaging (like resistors), but classic
radial (disc) capacitors work just as well if you prefer them. Leads must fit
0.8 mm plated holes spaced 10 mm apart. Any rating of 10 V or higher is fine;
tolerance and temperature coefficient don't matter.

Yes, 47 μF ceramic capacitors are pricey, but you only need two, and they
never leak. Leads must fit 0.8 mm plated holes spaced 5 mm apart. Any rating of
10 V or higher is fine; tolerance and temperature coefficient don't matter.

The CUI audio jack comes in many colors and with optional switches. The
switches go unused, but the board accepts the extra leads.

The REBOOT switch is made by several manufacturers in various lengths, colors,
and actuation forces. Nothing matters except that it's "momentary on".

The VGA jack is made by several manufacturers. This style has been around since
the beginning, so if it looks like it'll fit, it probably will. Newer VGA jacks
are designed to save PCB space or to be oven-soldered; they look different
enough to spot and avoid.

The 74xx ICs must be true CMOS. Use AC or HC, never ACT or HCT. Two of the
three must be AC to reach 8 MHz. You can substitute 74HC00 and 74HC02 for the
AC parts, but then 8 MHz is off the table. I've never seen a DIP 74AC30, but if
you find one, prefer it over the 74HC30.

The RAM IC is 128K because two 32K chips cost more. Speed must be 70 ns or
faster to reach 8 MHz.
