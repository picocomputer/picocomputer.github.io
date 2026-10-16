# Picocomputer Manual

The manual is the Sphinx reStructuredText in `source/`. Write it for
engineers and programmers, in the style of a data sheet, in plain language.
The rules below are the writing rules of ASD-STE100 Simplified Technical
English, without its restricted dictionary.

## Write for the reader

The reader is a programmer who works through the manual in order. Write
each passage for what that reader is trying to do at that point, not for
how the system is arranged inside.

**Start from the reader's goal.** "To write in assembly, replace
`src/main.c` in `CMakeLists.txt` with `src/main-cc65.s`." Tell the reader
what to do, then what happens.

**Name who does the action**, above all when the reader could take it as
their own job. "The launch configuration uploads the ROM to a USB drive
plugged into the RP6502-PICO" tells the reader that they do not copy it.

**Say what a thing is.** Use the concrete words for it: "virtual devices
or general purpose storage", not "any data". A vague noun or verb leaves
the reader to guess.

**Talk to the programmer.** "You" and "your" are correct when the text
addresses the programmer. Do not twist a sentence to avoid them.

**Say each thing once, where the reader needs it.** Detail that a later
section or another datasheet owns gets a link, not a summary. Do not
explain a thing before the reader has a reason to need it.

## Rules

**Never lose a fact.** Do not change what a fact says. You may remove a
repeated statement of a fact, but at least one statement of it must
remain. State a fact in more than one place when the reader can meet it
first in either place. Put each statement where the reader already has
the knowledge to understand it, and move a statement that the reader
does not need yet to the section that owns it.

**One word for one meaning.** Use one word for one meaning, and use the
same word every time.

**Use each word in its exact meaning.** "Name" means to give a thing its
name, as in "`project()` names the project". It does not mean to use,
give or refer to a thing: write "`CMakeLists.txt` then uses the symbol",
not "names the symbol".

**Present tense and active voice.** Use the present tense and the active
voice. Give each sentence a subject. Do not invent a machine as the
subject of a sentence to avoid a passive or the word "you".

**Clear, not padded, not terse.** Write so the reader understands at
once. Say each thing once: do not repeat a fact or restate a point in
other words. Do not pad a sentence, and do not squeeze it into a terse
fragment. A short reason stays short.

**Short sentences.** Prefer short sentences. A sentence is as long as its
content requires.

**One instruction per sentence.** Write one instruction in each sentence.

**Noun clusters.** Do not use noun clusters of more than three words.

**No figures of speech, idioms or decoration.** Do not add humor, hype,
metaphor or idioms. The owner writes these where they matter, such as on
the index page and in introductions. Leave the ones already in the text.

**RFC 2119 words.** Use the RFC 2119 words with their RFC meanings. "Must"
and "must not" state a requirement. "Should" and "should not" state a
recommendation. "May" states an option. "Can" states an ability. A command
that does not run without an argument requires that argument. These rules
govern the RFC words when the text uses them. They do not require the text
to use them.

**Machines are not beings.** Machines and software have no motives,
feelings or personalities. State what they do as fact: "load replaces the
symbols" and "poke requires an address". Use the established term of the
field, such as "request" for an interrupt request.

**No first person.** No I, me, my, we, our, us. The manual is not a letter
from its author.

## Line width

Wrap prose at 79 columns.
