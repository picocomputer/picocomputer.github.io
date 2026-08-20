=================================
RP6502-RIA-W
=================================

RP6502 - RP6502 Interface Adapter W


Introduction
============

The **RP6502 Interface Adapter W** is the :doc:`ria` with a radio — the
same specification and the same firmware, built for a Raspberry Pi Pico
2 W. Everything on the RIA page applies here; this page is only the
wireless part.


Wi-Fi Setup
===========

The radio speaks Wi-Fi 4 (802.11n) and is configured from the monitor.
Set the network name and the password and it connects, remembering both
across reboots. The ``status`` command shows where it got to.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Command
     - Description
   * - ``SET RF (0|1)``
     - Turn all radios on (1, the default) or off (0) without disturbing
       any other setting.
   * - ``SET RFCC (cc|-)``
     - Country code, for best performance — ``US`` or ``GB``, say. Run
       ``help set rfcc`` to list the supported codes, or use ``-`` for
       the worldwide default.
   * - ``SET SSID (ssid|-)``
     - The network name, the Service Set Identifier. Run ``help set
       ssid`` to scan for and list nearby networks. ``-`` clears it.
   * - ``SET PASS (pass|-)``
     - The network password. ``-`` clears it.


Network Time Protocol (NTP)
===========================

The real-time clock synchronizes with internet time servers whenever
Wi-Fi is connected, so it is right without being asked. The ``status``
command reports what NTP is doing.

The clock keeps UTC. For local time, set your time zone with ``SET TZ``
and run ``HELP SET TZ`` for guidance; Daylight Saving adjustments are
automatic if your locale observes them. The :doc:`os` reaches both the
clock and the time zone programmatically.

Once Wi-Fi and the time zone are configured, timekeeping takes care of
itself.


Telnet Console
==============

The console can be exposed over the network, putting the monitor or a
running 6502 in reach of any telnet client. Traffic is unencrypted, so
treat it like any other telnet session.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Command
     - Description
   * - ``SET PORT (port|0)``
     - The TCP port to listen on. The default is ``23``, the standard
       telnet port; ``0`` disables the telnet console.
   * - ``SET KEY (key|-)``
     - The passkey required to connect. ``-`` clears it.

The telnet console starts listening once ``KEY`` is set and ``PORT`` is
non-zero — both, because a console on the open network with no passkey
is not a feature.


Modem Emulation
===============

The RP6502-RIA-W emulates a Hayes modem — the classic AT command set —
for reaching BBSes (bulletin board systems). It places outgoing calls
and answers incoming ones over either raw TCP or telnet. As with the
telnet console the connection is unencrypted, which is at least
period-accurate.

Example AT commands:

- ``ATA`` — Answer incoming call
- ``ATDexample.com:23`` — Dial a BBS by address
- ``ATDS=0`` — Dial phonebook entry (0-3)
- ``+++`` — Escape back to command mode
- ``ATE1`` — Set echo
- ``ATH`` — Hang up
- ``ATO`` — Return to call
- ``ATQ0`` — Set quieting
- ``ATSxxx?`` — Query register number xxx
- ``ATSxxx=yyy`` — Set register number xxx with value yyy
- ``ATV1`` — Set verbosity
- ``ATX0`` — Set progress messaging
- ``ATZ`` — Load profile from flash
- ``AT&F`` — Load factory profile
- ``AT&V`` — View profile, stored profile, phonebook, and network
- ``AT&W`` — Write profile to flash
- ``AT&Z0=example.com:23`` — Save phonebook entry (0-3) to flash
- ``AT\L=23`` and ``AT\L?`` — Listen port for ``ATA`` (0 disables)
- ``AT\N0`` or ``AT\N1`` and ``AT\N?`` — Network mode: 0=raw TCP, 1=telnet
- ``AT\T=ANSI`` and ``AT\T?`` — Terminal type advertised during telnet negotiation
- ``AT+RFCC=US``, ``AT+RFCC?``, and ``AT+RFCC!`` — Access RIA setting RFCC
- ``AT+SSID=your_ssid``, ``AT+SSID?``, and ``AT+SSID!`` — Access RIA setting SSID
- ``AT+PASS=your_pass`` and ``AT+PASS?`` — Access RIA setting PASS

Each ``AT+`` setting uses ``=`` to set, ``?`` to query the current value,
and ``!`` to list (``AT+SSID!`` scans for nearby networks, ``AT+RFCC!``
lists supported country codes). Lists word-wrap to 80 columns.

The modem is available as a set of special device names:

- ``AT:`` is transient — it starts from factory defaults, has no
  phonebook, and ``AT&W`` has nothing to save.
- ``AT0:`` through ``AT9:`` are ten independent profiles, each with its
  own flash-backed settings and four-slot phonebook (``AT&Z0``-``AT&Z3``).

When you open a numbered device, it loads its saved profile. ``AT&W``
writes the profile back, ``ATZ`` reloads it, and ``AT&F`` restores
factory defaults. Up to four modem devices can be open and in use at
once.

The ``AT+`` commands (``+RFCC``, ``+SSID``, ``+PASS``) pass straight
through to the global RIA settings and take effect immediately, no matter
which modem device is open.

The modem needs the radio. Opening any ``AT`` device fails with ``ENODEV``
while the radio is off (``SET RF 0``); enable it with ``SET RF 1``.


Bluetooth
=========

The RP6502-RIA-W supports Bluetooth LE (BLE) keyboards, mice, and
gamepads. Bluetooth Classic (BR/EDR) is not supported. BLE has been
everywhere since Bluetooth 4.0 (June 2010), so compatible devices are
easy to find — though the occasional oddball still turns up.

To add a device, run the monitor command ``set ble 2`` to enter pairing
mode; the LED on the RP6502-RIA-W blinks while it's pairing. Put your
device into its own pairing mode too — check its manual, but it's
probably a button and some more blinking. When the blinking stops, the
device is connected and bonded, so it reconnects automatically from then
on.
