=================================
RP6502-RIA-W
=================================

RP6502 - RP6502 Interface Adapter W


Introduction
============

The **RP6502 Interface Adapter W** is a Raspberry Pi Pico 2 W running
RP6502-RIA-W firmware. It does everything the :doc:`ria` does, plus the
wireless services described below.


Wi-Fi Setup
===========

The RP6502-RIA-W supports Wi-Fi 4 (802.11n). Configure it from the
monitor.

- **Enable or disable the radio.**
  ``SET RF (0|1)`` turns all radios on (1, the default) or off (0)
  without touching your other settings.

- **Set the country code.**
  ``SET RFCC (cc|-)`` sets the Wi-Fi country code for best performance
  (for example ``US`` or ``GB``). Run ``help set rfcc`` to list supported
  codes, or use ``-`` to reset to the worldwide default.

- **Set the network name (SSID).**
  ``SET SSID (ssid|-)`` sets your Wi-Fi network name, the Service Set
  Identifier. Use ``-`` to clear it.

- **Set the network password.**
  ``SET PASS (pass|-)`` sets your Wi-Fi password. Use ``-`` to clear it.

- **Check status.**
  The ``status`` command shows your current Wi-Fi connection and
  settings.


Network Time Protocol (NTP)
===========================

The real-time clock (RTC) synchronizes with internet time servers
automatically whenever Wi-Fi is connected. Check NTP status with the
``status`` command.

- **Set the time zone.**
  To use local time instead of UTC, set your time zone with ``SET TZ``;
  run ``HELP SET TZ`` for guidance. Daylight Saving Time adjustments are
  automatic if your locale observes them. The :doc:`os` offers
  programmatic access to the clock and time zone.

Once Wi-Fi and the time zone are configured, timekeeping takes care of
itself.


Telnet Console
==============

The RP6502-RIA-W can expose its console over the network, so you can
reach the monitor or a running 6502 from a remote telnet client. Traffic
is unencrypted, so treat it like any other telnet session.

- **Set the listening port.**
  ``SET PORT (port|0)`` sets the TCP port. The default is ``23``, the
  standard telnet port; setting ``0`` disables the telnet console.

- **Set the passkey.**
  ``SET KEY (key|-)`` sets the passkey required to connect. Use ``-``
  to clear it.

The telnet console starts listening once ``KEY`` is set and ``PORT``
is non-zero.


Modem Emulation
===============

The RP6502-RIA-W can emulate a Hayes modem — the classic AT command
set — for reaching BBSes (bulletin board systems). It places outgoing
calls and answers incoming ones over either raw TCP or telnet. As with
the telnet console, the connection is unencrypted.

- **AT commands.**
  The modem speaks the standard AT command set for dialing, answering,
  and configuration.

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

The modem is available as a set of special device names:

- ``AT:`` is transient — it starts from factory defaults, has no
  phonebook, and ``AT&W`` has nothing to save.
- ``AT0:`` through ``AT9:`` are ten independent profiles, each with its
  own flash-backed settings and four-slot phonebook (``AT&Z0``-``AT&Z3``).

When you open a numbered device, it loads its saved profile. ``AT&W``
writes the profile back, ``ATZ`` reloads it, and ``AT&F`` restores
factory defaults. Up to four modem devices can be open and in use at
once.

The ``AT+`` commands (``+RF``, ``+RFCC``, ``+SSID``, ``+PASS``) pass
straight through to the global RIA settings and take effect immediately,
no matter which modem device is open.


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
