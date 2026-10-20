============================
Build With Soldering
============================

RP6502-PICO

The RP6502-PICO is the standalone machine, a 6502 computer you build
yourself for under $100 in the US. The machine is one circuit board with
a WDC 65C02, a WDC 65C22, a RAM chip, three logic chips and two Raspberry
Pi Pico 2 boards. This page builds it from a bare circuit board that you
solder yourself. To have a factory solder the board, see
:doc:`pico-socket`.

You don't need to understand the electronics. Every part is currently in
production, and the Raspberry Pi Pico 2 is slated to stay that way until
at least `January 2040
<https://www.raspberrypi.com/products/raspberry-pi-pico-2/>`_. The design
was already updated once, from the Pico 1 to the Pico 2. The project does
not depend on any one of these parts staying in production, because the
:doc:`fpga`, the machine in fabric, uses none of them.

.. image:: _static/ria-w-sandwich.jpg
   :width: 600
   :align: center
   :alt: RP6502-PICO Photo

Schematic
=========

`RP6502-PICO <_static/2026-01-26-rp6502.pdf>`_ (pdf)


Buying an RP6502-PICO
=====================

You'll place two orders: one for the printed circuit board (PCB), and one for
the electronic components.

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

Most VGA-to-HDMI cables can draw power straight from the RP6502-PICO; a few
need external power. None of them add lag, which matters on a machine built for
games. All VGA output uses HDMI-compatible timings, so these cables are an
ideal solution.

The boot message no longer says COLOR, so don't expect your device to match
older YouTube videos exactly.


Step 1. Watch the Video
=======================

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


Step 3. Order the Parts
=======================

Upload the `full parts list <_static/rp6502-revb-full.csv>`_ to a `Mouser
<https://mouser.com>`_ shopping cart.

Mouser prints a Customer# on each parts bag. Map that column to the CSV
reference column and your bags arrive labeled like "C1-C9, C11". If you
forget, no problem — the PCB silkscreen already has the location info.

If something is out of stock, check the :doc:`pico-parts` notes.


Step 4. Solder the Board
========================

Solder the board as the video in Step 1 shows.


Step 5. Pi Pico Firmware
========================

Download the `pico zip
<https://github.com/picocomputer/rp6502/releases/latest>`_ and unpack the UF2 files
inside it.

Every RP6502-PICO needs both Picos flashed with two different files. The VGA
file is the same for everyone. The RIA file depends on which Pi Pico you have.
The Pi Pico 2 W goes in U2, the RIA socket, and takes the "-w" file.

To flash a Pi Pico, hold its BOOTSEL button while plugging it into a computer.
The Pico 2 mounts as a storage device. Copy the RIA or VGA UF2 file to it. The
copy takes under 30 seconds, and the LED turns on when it's done.

Formally, a Pi Pico flashed with the RIA firmware is an RP6502-RIA, a Pi
Pico 2 W flashed with the RIA-W firmware is an RP6502-RIA-W, and a Pi Pico
flashed with the VGA firmware is an RP6502-VGA.

It is not possible to "brick" a Pi Pico from a failed flash. You can always
recover with the BOOTSEL method. Once you have a machine running, later
upgrades don't need BOOTSEL. See :ref:`Firmware Updates
<pico-firmware-updates>`.


Step 6. First Boot
==================

Plug the eight ICs into their sockets. Connect a VGA monitor, or an HDMI
display with a VGA-to-HDMI cable, and plug a USB keyboard into the RIA.
Apply 5V power to the VGA module, enough for all your devices plus one watt
for the RP6502-PICO itself. A fresh RIA boots into the RP6502 monitor.
Continue with :doc:`pico`.


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
