========
Hardware
========

The Picocomputer 6502 is a homebrew computer you build yourself. You don't
need to understand the electronics, and you don't even need to solder — but
you will need to plug the eight ICs into their sockets.

Every part is currently in production, and the Raspberry Pi Pico 2 is slated
to stay that way until at least `January 2040
<https://www.raspberrypi.com/products/raspberry-pi-pico-2/>`_.
The design has already survived the Pico 1 to Pico 2 transition, and its
manufacturing lifetime should stretch into the coming era of democratized
hobbyist ASICs.

Schematic
=========

`Picocomputer 6502 <_static/2026-01-26-rp6502.pdf>`_ (pdf)


Buying a Picocomputer
=====================

You'll place two orders: one for the printed circuit board (PCB), and one for
the electronic components. Some PCB factories will do the soldering for you,
but you'll still order the ICs separately and plug them into their sockets
yourself.

I keep circuit boards in a `Ko-fi store
<https://ko-fi.com/rumbledethumps>`_, but it ships only within the
United States. For everyone else, international shipping is either too slow or
too expensive to beat having boards made locally or in China.

US import tariffs aren't a concern here. Orders from my store and from Mouser
ship within the USA, so there's no surprise bill from the courier.

Step 0. Read This
=================

Rev. A and Rev. B boards are identical except for the debug connectors under
the RIA. They do nothing even when connected, so they were removed — mostly so
folks would stop asking about them.

Most VGA-to-HDMI cables can draw power straight from the Picocomputer; a few
need external power. None of them add lag, which matters on a machine built for
games. All VGA output uses HDMI-compatible timings, so these cables are an
ideal solution.

The boot message no longer says COLOR, so don't expect your device to match
older YouTube videos exactly.


Step 1. Watch the Videos
========================

To solder, or not to solder — that is the question. We're living in the
future: you can homebrew a 6502 without ever touching a soldering iron. Choose
your path.

`Here's the video where I build one without soldering.
<https://youtu.be/4CjouKoCMUw>`_

`Here's the video where I solder one myself.
<https://youtu.be/bwgLXEQdq20>`_


Step 2. Order Printed Circuit Boards
====================================

Order from the project page at `PCBWay
<https://www.pcbway.com/project/shareproject/Picocomputer_6502_RP6502_Rev_B_1f41cb0b.html>`_
or download `the gerbers <_static/rp6502-revb-gerbers.zip>`_ to have the boards
made anywhere you prefer.

Gerbers are like PDFs for circuit boards. When asked to upload them, just hand
over the zip file linked above. The manufacturer's website should detect a
two-layer 150 x 100 mm board.

PCB shops that cater to hobbyists optimize their basic service for batches of
five, so you can't order just one board.

There are plenty of options to tweak if you want to. The defaults get you a
classic green-and-white board with leaded (Pb) HASL. Consider the lead-free
HASL upgrade if the other four boards are going to live in a drawer for the
next 20 years.


Step 3. Order Assembly
======================

Skip this step if you want to solder it yourself.

PCBWay assembles in quantities as low as one, using the boards from step 2.
The result is a "board of sockets" — you install the ICs yourself later. Parts
availability is rarely a constraint; every component has multiple vendors.

Download `the BOM, notes, and photos <_static/rp6502-revb-assembly.zip>`_.

Request assembly along with your PCB order and send the `BOM, notes, and photos
<_static/rp6502-revb-assembly.zip>`_. There's no centroid file because there
are no surface-mount parts. The default options work fine — let them source the
parts and make substitutions.

Expect a short delay while they quote the bill of materials, then pay and wait.
They quoted four weeks; mine arrived in three.

If they have a question, make sure both you and your sales rep have read the
notes you sent. If you have a question about options on their website, ask your
sales rep before heading to the forums. They help people all day with projects
far more complex than this, and they can figure out your build from the zip
files even if you can't. They do this all day long and will probably enjoy the
easy win.


Step 4. More Parts
==================

Factory-assembled boards still need you to install the eight ICs. Upload the
`active parts list <_static/rp6502-revb-active.csv>`_ to a `Mouser
<https://mouser.com>`_ shopping cart.

If you're soldering the whole thing yourself, upload the `full parts list
<_static/rp6502-revb-full.csv>`_ to a Mouser_ cart instead.

Mouser prints a Customer# on each parts bag. Map that column to the CSV
reference column and your bags arrive labeled like "C1-C9, C11". If you
forget, no problem — the PCB silkscreen already has the location info.

If something is out of stock, check the `Parts Substitution`_ notes below.


Step 5. Pi Pico Firmware
========================

Download the `UF2 files
<https://github.com/picocomputer/rp6502/releases>`_.

To flash a Pico 2, hold its BOOTSEL button while plugging it into a computer.
The Pico 2 mounts as a storage device. Copy the RIA-W UF2 file to make a
:doc:`ria_w`, or the VGA UF2 file to make a :doc:`vga`. The copy takes under 30
seconds, and the LED turns on when it's done.


Acrylic Sandwich Case
=====================

The circuit board is 150 x 100 mm (4 x 6 inches). Vendors on Amazon and eBay
regularly sell 150 x 100 x 3 mm acrylic sheets to match. Drill 3 mm holes for
M3 standoffs, and use standoffs of at least 16 mm on top and 3.5 mm on the
bottom.


Full Parts List (All Components)
================================

`All Parts CSV <_static/rp6502-revb-full.csv>`_

.. csv-table::
   :file: _static/rp6502-revb-full.csv
   :header-rows: 1


Active Parts List (ICs Only)
============================

`Active Parts CSV <_static/rp6502-revb-active.csv>`_

.. csv-table::
   :file: _static/rp6502-revb-active.csv
   :header-rows: 1


Pi Picos Parts List
===================

Alternative part numbers for the Pi Picos.

.. csv-table::
   :file: _static/rp6502-revb-picos.csv
   :header-rows: 1


Parts Substitution
==================

All resistors are 1% tolerance or better, any power rating. Leads must fit
0.8 mm plated holes spaced 10 mm apart. A size of roughly 0.1" x 0.25"
(2.4-2.6 mm x 6-8 mm) is recommended.

0.1 μF ceramic capacitors come in axial packaging (like resistors), but classic
radial (disc) capacitors work just as well if you prefer them. Leads must fit
0.8 mm plated holes spaced 10 mm apart. Any rating of 10 V or higher is fine;
tolerance and temperature coefficient don't matter.

Yes, 47 μF ceramic capacitors are pricey — but you only need two, and they
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

The WDC W65C02S and W65C22S must not be substituted. Don't try NMOS chips (the
ones without the C in the part number). Some older CMOS designs may work, but
there are no plans to support out-of-production ICs.

Only Raspberry Pi's own Pico 2 has been tested. Both the original and the "H"
(header) versions work great. Pin-compatible alternatives usually work too.
