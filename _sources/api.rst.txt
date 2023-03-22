RP6502-API
##########

Rumbledethumps Picocomputer 6502 Application Programming Interface.

.. contents:: Table of Contents
   :local:

1. Introduction
===============

The RIA runs a protected 32-bit kernel that you can call from the 6502.

2. Function Reference
=====================

The $ number in the headings are the API call identification numbers. See the :doc:`ria` documentation about calling the kernel.

$00 zvstack
-----------
.. c:function:: void zvstack();

    Abandon the vstack by resetting the vstack pointer. Not needed for normal operation, but some performance tricks can be achieved with this.

$01 open
--------

.. c:function:: int open(const char *path, int oflag);

   Open a file.

   :param path: Filename
   :param oflag: Flags
   :retval -1: on error.
   :retval >=0: The file handle number.
