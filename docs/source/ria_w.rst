RP6502-RIA-W
############

Rumbledethumps Picocomputer 6502 Interface Adapter W

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The **RP6502 Interface Adapter W (RIA W)** is a Raspberry Pi Pico 2 W running the RP6502-RIA-W firmware. The RIA W provides all the features of the :doc:`ria` plus integrated wireless services, as described below.

2. WiFi Setup
=============

The RIA W uses an Infineon CYW43439 chip supporting Wi-Fi 4 (802.11n). Configuration is performed via the console interface.

- **Enable/Disable Radio:**
  Use ``SET RF (0|1)`` to enable (1, default) or disable (0) all radios without affecting other settings.

- **Set Country Code:**
  ``SET RFCC (cc|-)`` sets the WiFi country code for optimal performance (e.g., ``US``, ``GB``). Use ``help set rfcc`` to list supported codes. Use ``-`` to reset to the worldwide default.

- **Set Network Name (SSID):**
  ``SET SSID (ssid|-)`` sets your WiFi network name (Service Set Identifier). Use ``-`` to clear.

- **Set Network Password:**
  ``SET PASS (pass|-)`` sets your WiFi password. Use ``-`` to clear.

- **Check WiFi Status:**
  Use the ``status`` command to view current WiFi connection and settings.

3. Network Time Protocol (NTP)
==============================

The real-time clock (RTC) automatically synchronizes with internet time servers when connected.
Check NTP status with the `status` command.

- **Set Time Zone:**
  To use local time instead of UTC, set your time zone with ``SET TZ``. Use ``help set tz`` for guidance. Daylight saving adjustments are automatic if your locale observes them.

Once WiFi and time zone are configured, timekeeping is automatic—no battery required and no drift to worry about.

4. Modem Emulation
==================

The RIA W can emulate a Hayes modem for BBS access. Beware that raw TCP and telnet protocols are plain text in transit.

- **AT Commands:**
  The modem interface supports standard AT commands for dialing, answering, and configuration.

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

A full telnet stack has yet to be written so all connections are raw TCP.

"Telephone Numbers" are saved immadiately and are not linked to profiles.

`Please contribute to this documentation. <https://github.com/picocomputer/picocomputer.github.io>`_

5. Additional Resources
=======================

- :doc:`RIA Interface Adapter <ria>`
- :doc:`API for 6502 Programming <api>`
- :doc:`Schematic, PCB, and Case Files <hardware>`
