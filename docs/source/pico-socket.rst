============================
Build Without Soldering
============================

This page builds the :doc:`pico` from a board of sockets that a factory
assembles. Prices vary, so you need to get a quote, but expect about $150
in total. To solder the board yourself, see :doc:`pico-solder`.

You don't need to solder, but you will need to plug the eight ICs into
their sockets and flash the two Pi Picos with a USB cable.

Buying an RP6502-PICO
=====================

You'll place two orders: one for the printed circuit boards (PCB) with
assembly, and one for the eight ICs.

Step 1. Watch the Video
=======================

`Here's the video where I build one without soldering.
<https://youtu.be/4CjouKoCMUw>`_


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

PCBWay assembles in quantities as low as one, using the boards from step 2.
The result is a "board of sockets". You install the ICs yourself later. Parts
availability is rarely a constraint; every component has multiple vendors.

Download `the BOM, notes, and photos <_static/rp6502-revb-assembly.zip>`_.

.. warning::

   This BOM is not a shopping list. It tells the factory how to build a board
   of sockets, so it contains no active parts. Upload it to Mouser and you
   will receive, with flawless accuracy, every part except the ones that make
   a computer compute. That order comes later, in `Step 4. More Parts`_.

Request assembly along with your PCB order and send the `BOM, notes, and photos
<_static/rp6502-revb-assembly.zip>`_. There's no centroid file because there
are no surface-mount parts. The default options work fine. Let them source the
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

Mouser prints a Customer# on each parts bag. Map that column to the CSV
reference column and your bags arrive labeled like "C1-C9, C11". If you
forget, no problem — the PCB silkscreen already has the location info.

If something is out of stock, check the :doc:`pico-parts` notes.

Every IC goes in one way, and the silkscreen on the board marks which
way. If you are not sure about one, ask someone before you power on.


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


Active Parts List (ICs Only)
============================

`Active Parts CSV <_static/rp6502-revb-active.csv>`_

.. csv-table::
   :file: _static/rp6502-revb-active.csv
   :header-rows: 1
