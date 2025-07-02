RP6502-RIA-W
############

Rumbledethumps Picocomputer 6502 Interface Adapter W.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The RP6502 Interface Adapter W (RIA W) is a Raspberry Pi Pico 2 W with RP6502-RIA-W firmware. The RIA W provides everythiung the :doc:`ria` does along with the wireless services described in this document.

2. WiFi Setup
=============

The WiFi hardware is an Infineon CYW43439 supporting Wi-Fi 4 (802.11n). Configuration is done from the console.

`SET RF (0|1)` is used to disable all radios without clearing any other settings. It defaults to 1 (enabled).

`SET RFCC (cc|-)` can be used to improve WiFi performance. `help set rfcc` will show the supported country codes. Clearing with "-" will use the Worldwide default.

`SET SSID (ssid|-)` sets the name of your WiFi network, also called the Service Set Identifier.

`SET PASS (pass|-)` sets the password for your WiFi network, if you have one.

You can check WiFi status with the `status` command.

3. Network Time Protocol
========================

The real time clock will automatically update its time whenever connected to the internet.You can check NTP status with the `status` command.

If you prefer local time instead of UTC, set the TZ. Always remember `help set tz` is there for you. Once set, it will adjust for daylight savings time if your locale uses it.

Once your Wifi and time zone are set, you can forget about time. Drift isn't a problem and there's no battery to replace.

4. Modem
========

lorem ipsum

3.1. AT Commands
----------------

dolar sit amet
