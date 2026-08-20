:orphan:

============================
Documentation Style
============================

RP6502 - Documentation Style

These rules are descriptive. Every one was taken from pages that already
read the way this project should sound — mostly :doc:`emu`, :doc:`fpga`,
:doc:`sdk`, and the MIDI, tablet, and NFC sections of :doc:`ria`. They
are written down so they survive the next edit.


Voice
=====

**1. The machine is the subject, in present tense.**

   "The RIA broadcasts every change to its 64 KB of XRAM."

   Not "XRAM changes are broadcast by the RIA."

**2. The reason rides along in the same sentence — never its own
paragraph.**

   "There is one entry rather than a list plus an alternate, because on
   real hardware reaching the monitor to change layouts interrupts
   whatever you were doing, and this menu is two button presses away."

   Give the reason, not the argument. One subordinate clause, then move
   on. This is the trait most worth protecting.

**3. Close on the consequence for the reader.**

   "…which is all a test runner needs."

   "…so a driver written in any language can work the machine with no
   protocol to implement."

**4. State limits flat, with no apology and no defensiveness.**

   "This is a bug, not a limitation, and is tracked at issue #183."

   "Timers, interrupts, and the status register are not supported."

**5. Dry wit, regularly but in moderation — always attached to a fact.**

   "0xF0000000 is hard to miss on test equipment."

   "…mostly so folks would stop asking about them."

   A line that would work as a joke on its own does not belong. A line
   that makes a fact stick does.

**6. Contrast is a hazard signal, not a sentence shape.** "X rather than
Y" earns its place when Y is something the reader might actually do that
would cost them.

   "The recording drops whole messages rather than backing up" warns
   against expecting backpressure.

   "The call stack is read rather than guessed" says which compiler's
   stack you can trust.

   It is not a default construction and must not become a tic.

**7. No marketing adjectives**, with one exception: the opening paragraph
of the front page may sell. Everywhere else, capability is shown by
number or by mechanism — "over 512 KB/sec", "a 32-bit frame travels in
just 4 PHI2 cycles". Never disparage another project. Say what the RP6502
does, not what anyone else fails at.

**8. Person.** Second for the reader's actions, third for the machine.
First person singular only where the author is personally the subject —
his store, his videos, his bench result. That is :doc:`pico` and nowhere
else. Never "we".

**9. Tell the reader what a thing is before what it does.** A section
that opens straight into a table has skipped a step.


Specification and implementation
================================

The RIA and the VGA are specifications. Fitting entirely on a Raspberry
Pi Pico 2 as part of an :doc:`pico` is a constraint they meet, not what
they are — the same registers answer on the :doc:`fpga` in gates and in
the :doc:`emu` on a host CPU.

Write the specification pages host-neutrally. Where a passage really is
about one implementation — a PIO block, a driver list, a pin — say so in
the passage.

No host is the sentinel. That moved to the tests as the first emulator
was developed, so cross-host disagreements are settled by the test
corpus.


Leave these alone
=================

- **The first person in** :doc:`pico`. It is the author's store, videos,
  and bench result. It gives the page its warmth.
- **The playable game at the top of** :doc:`emu`. Show, then explain.
- **The API entries in** :doc:`os` **and the escape-sequence tables in**
  :doc:`term`. Reference blocks stay terse. No narrative, no wit.
- **The ASCII internals diagram in** :doc:`fpga` and the paragraph that
  reads it back.
- **The gamepad hedges in** :doc:`ria`. "A type is only reported when the
  RIA is certain" is precision, not waffle.
- **The scanvideo and Pi Pico Playground credits in** :doc:`vga`. They
  are correct as history.


Mechanics
=========

Hand-wrap prose at about 76 columns. Tables and code blocks are exempt.

Pages cross-link by raw HTML anchor:

.. code-block:: text

  `Telnet Console <ria_w.html#telnet-console>`__

**Sphinx does not validate these.** Renaming a section silently breaks
every link to it and still builds clean. Before renaming a heading,
search for its anchor:

.. code-block:: text

  grep -rn 'ria_w.html#telnet-console' docs/source/*.rst

After a build, check that every anchor still resolves:

.. code-block:: text

  grep -ohE '[a-z_]+\.html#[a-z0-9-]+' docs/source/*.rst | sort -u | while read L; do
    f="docs/build/html/${L%%#*}"; a="${L#*#}"
    grep -q "id=\"$a\"" "$f" || echo "BROKEN: $L"
  done

Never edit ``docs/build``. It is generated output.
