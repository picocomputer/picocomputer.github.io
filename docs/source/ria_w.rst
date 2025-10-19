=================================
RP6502-RIA-W
=================================

RP6502 - RP6502 Interface Adapter W

Introduction
============

The **RP6502 Interface Adapter W** is a Raspberry Pi Pico 2 W running
the RP6502-RIA-W firmware. The :doc:`ria_w` provides all the features
of the :doc:`ria` plus wireless services, as described below.

WiFi Setup
==========

The RP6502-RIA-W supports Wi-Fi 4 (802.11n). Configuration is performed
via the console interface.

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

The real-time clock (RTC) automatically synchronizes with internet time
servers when connected. Check NTP status with the ``status`` command.

- **Set Time Zone:**
  To use local time instead of UTC, set your time zone with ``SET TZ``.
  Use ``HELP SET TZ`` for guidance. Daylight saving adjustments are
  automatic if your locale observes them.

Once WiFi and time zone are configured, timekeeping is automatic.

Modem Emulation
===============

The :doc:`ria_w` can emulate a Hayes modem for BBS access. Beware that
raw TCP and telnet protocols are plain text in transit.

- **AT Commands:**
  The modem interface supports standard AT commands for dialing,
  answering, and configuration.

Example AT commands:

- ``ATDexample.com:23`` — Dial a BBS
- ``+++`` — Escape back to command mode
- ``ATE1`` — Set echo
- ``ATH`` — Hang up
- ``ATO`` — Return to call
- ``ATQ0`` — Set quieting
- ``ATSxxx?`` — Query register number xxx
- ``ATSxxx=yyy`` — Set register number xxx with value yyy
- ``ATV1`` — Set verbosity
- ``ATX0`` — Set progress messaging
- ``ATZ`` — Load profile from NVRAM
- ``AT&F`` — Load factory profile
- ``AT&V`` — View profile
- ``AT&W`` — Write profile to NVRAM
- ``AT&Z0=example.com:23`` — Save "telephone number" to NVRAM
- ``AT+RF=your_ssid`` and ``AT+RF?`` — Access RIA setting RF
- ``AT+RFCC=your_ssid`` and ``AT+RFCC?`` — Access RIA setting RFCC
- ``AT+SSID=your_ssid`` and ``AT+SSID?`` — Access RIA setting SSID
- ``AT+PASSS=your_ssid`` and ``AT+PASS?`` — Access RIA setting PASS

A full telnet stack has yet to be written so all connections are raw
TCP.

"Telephone Numbers" are saved immediately and are not linked to
profiles.

`Please contribute to this documentation.
<https://github.com/picocomputer/picocomputer.github.io>`_

Bluetooth
=========

The :doc:`ria_w` supports Bluetooth LE (BLE) keyboards, mice, and
gamepads. It does not support the older Bluetooth Classic aka BR/EDR.
The RP6502-RIA-W uses BTStack which can only support one Bluetooth
Classic device at a time so it's not worth the memory. BLE was introduced
in June 2010 with Bluetooth 4.0 so it's not difficult to find devices but
you will find an occasional oddball. Of particular note are Sony DualShock
and DualSense controllers - which you can use on USB instead.

To add a new device, use monitor command ``set ble 2`` to enable pairing
mode. The LED on the RP6502-RIA-W will blink when in pairing mode. See
your device's manual to enable its pairing mode - probably a button and
more blinking. When the blinking stops, the device is connected and will
be remembered (bonded) so it reconnects automatically in the future.
