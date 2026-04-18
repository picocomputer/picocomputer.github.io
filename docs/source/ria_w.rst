=================================
RP6502-RIA-W
=================================

RP6502 - RP6502 Interface Adapter W


Introduction
============

The **RP6502 Interface Adapter W** is a Raspberry Pi Pico 2 W running
the RP6502-RIA-W firmware. It provides all the features
of the :doc:`ria` plus wireless services, as described below.


WiFi Setup
==========

The RP6502-RIA-W supports Wi-Fi 4 (802.11n). Configure it through the
console interface.

- **Enable/Disable Radio:**
  Use ``SET RF (0|1)`` to enable (1, default) or disable (0) all radios
  without affecting other settings.

- **Set Country Code:**
  ``SET RFCC (cc|-)`` sets the WiFi country code for optimal performance
  (e.g., ``US``, ``GB``). Use ``help set rfcc`` to list supported codes.
  Use ``-`` to reset to the worldwide default.

- **Set Network Name (SSID):**
  ``SET SSID (ssid|-)`` sets your WiFi network name (Service Set
  Identifier). Use ``-`` to clear.

- **Set Network Password:**
  ``SET PASS (pass|-)`` sets your WiFi password. Use ``-`` to clear.

- **Check WiFi Status:**
  Use the ``status`` command to view current WiFi connection and
  settings.


Network Time Protocol (NTP)
===========================

The real-time clock (RTC) automatically synchronizes with internet
time servers when connected to WiFi. Check NTP status with the
``status`` command.

- **Set Time Zone:**
  To use local time instead of UTC, set your time zone with ``SET TZ``.
  Use ``HELP SET TZ`` for guidance. Daylight saving adjustments are
  automatic if your locale observes them. The :doc:`os` provides
  programmatic access to the clock and time zone.

Once WiFi and time zone are configured, timekeeping is automatic.


Telnet Console
==============

The RP6502-RIA-W can expose its console over the network so you can
reach the monitor or a running 6502 from a remote telnet client.
Connections are unencrypted in transit.

- **Set Listening Port:**
  ``SET PORT (port|0)`` sets the TCP port. The standard telnet port is
  23. Setting ``0`` disables the telnet console.

- **Set Passkey:**
  ``SET KEY (key|-)`` sets the passkey required to connect. Use ``-``
  to clear.

Both ``PORT`` and ``KEY`` must be set to enable the telnet console.


Modem Emulation
===============

The RP6502-RIA-W can emulate a Hayes modem for BBS access. It can
place outgoing calls and answer incoming ones, over either raw TCP or
telnet. Connections are unencrypted in transit.

- **AT Commands:**
  The modem interface supports standard AT commands for dialing,
  answering, and configuration.

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
- ``AT+RF=0`` or ``AT+RF=1`` and ``AT+RF?`` — Access RIA setting RF
- ``AT+RFCC=US`` and ``AT+RFCC?`` — Access RIA setting RFCC
- ``AT+SSID=your_ssid`` and ``AT+SSID?`` — Access RIA setting SSID
- ``AT+PASS=your_pass`` and ``AT+PASS?`` — Access RIA setting PASS

The modem is available as a set of special device names. ``AT:`` is
transient — it starts from factory defaults, has no phonebook, and
``AT&W`` has nothing to save. ``AT0:`` through ``AT9:`` are ten
independent profiles, each with its own flash-backed settings and
four-slot phonebook (``AT&Z0``-``AT&Z3``). On open, the numbered
device loads its saved profile; ``AT&W`` writes it back, ``ATZ``
reloads it, and ``AT&F`` restores factory defaults. Up to four modem
devices can be open and used simultaneously.

``AT+`` commands (``+RF``, ``+RFCC``, ``+SSID``, ``+PASS``) are
pass-throughs to global RIA settings and take effect immediately,
regardless of which modem device is open.


Bluetooth
=========

The RP6502-RIA-W supports Bluetooth LE (BLE) keyboards, mice, and
gamepads. Bluetooth Classic (BR/EDR) is not supported.
BLE has been widely available since Bluetooth 4.0 (June 2010),
so compatible devices are easy to find, though the occasional oddball
exists.

To add a new device, use monitor command ``set ble 2`` to enable
pairing mode. The LED on the RP6502-RIA-W will blink when in pairing
mode. See your device's manual to enable its pairing mode - probably a
button and more blinking. When the blinking stops, the device is
connected and will be remembered (bonded) so it reconnects
automatically in the future.
