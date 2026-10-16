# Picocomputer Manual

The manual is the Sphinx reStructuredText in `source/`. Write it for
engineers and programmers, in the style of a data sheet, in plain language.
The rules below are the writing rules of ASD-STE100 Simplified Technical
English, without its restricted dictionary.

## Rules

**Keep every fact.** An edit for the voice changes how the text says a
thing, never what it says. Do not add a fact, drop a fact, widen or narrow
a claim, or change a number, a name, a limit or a condition. When the
meaning of a sentence is unclear, read the source code before you rewrite
it. When the code does not settle it, keep the original meaning and report
it.

**One word for one meaning.** Use the terms in GLOSSARY.md when it exists.
Within a page, never alternate synonyms for variety. Defined terms of the
manual (canvas, plane, fill layer, console, terminal, monitor, console
manifold, ROM, asset, memory chunk, named asset, XRAM, XREG, XSTACK, portal,
null drive, save) keep their defined meaning.

**Present tense.** "The call returns", not "the call will return". Remove
"will" and "would" unless they state a real conditional that cannot be
said in the present.

**Active voice, and every sentence has a subject.** "The RIA writes the
block", not "the block is written". A passive is acceptable only when the
actor is unknown or irrelevant and an active form is clumsier, and a
stative adjective ("is connected", "is open", "is empty") is not a passive.
Imperatives are correct for instructions to the reader; their subject is the
reader.

**Clear, not padded, not terse.** Write so the reader understands at
once. Say each thing once: do not repeat a fact or restate a point in
other words. Do not pad a sentence, and do not squeeze it into a terse
fragment. A short reason stays short.

**Short sentences.** Split sentences joined by em dashes, semicolons or
long chains of "and". Do not chop a sentence into fragments: a sentence is
as long as its content requires. An em dash that joins two clauses becomes
two sentences or a colon. An em dash in a definition list item ("**Term** —
definition") may stay.

**One instruction per sentence.** "Hold BOOTSEL. Plug the Pico into a
computer." In numbered procedures, each step may hold several sentences.

**Noun clusters of three words or fewer.** Break longer clusters with a
preposition or a verb: "the address of the configuration structure", not
"the configuration structure address". A product name, protocol name or
register name counts as one word ("USB CDC ACM", "RIA_ATTR_RLN_WIDTH").

**No figures of speech, idioms or decoration.** Do not add humor, hype,
metaphor or idioms. The owner writes these where they matter, such as on
the index page and in introductions. Leave the ones already in the text.

**RFC 2119 words.** These rules govern the RFC words when the text uses
them. They do not require the text to use them.
- "must" / "must not": a requirement on the reader or on a program.
- "should" / "should not": a recommendation.
- "may": an option that the reader or a program is free to take.
- "can": an ability or a possibility. "Reads can return 0 bytes", never
  "reads may return 0 bytes".
- A word from this list must not appear with its everyday meaning. Do not
  use "must" for a fact about a machine ("the light must be on" means a
  requirement; "the light is on" is a fact).
- A command, function or argument that does not work without something
  "requires" it. Do not say "takes" or "accepts" for a required argument
  when the requirement is the point.

**Machines are not beings.** Do not give a machine, program, file or
device a motive, a feeling or a personality. State what it does as fact,
in the established term of the field.

**No contractions.** Write "does not", "it is", "cannot".

**No first person.** No I, me, my, we, our, us. The manual is not a letter
from its author.

**Second person.** Prefer a subject that is the actor: "a program", "the
6502", "the RIA", "the build", "the user" (the person at the machine). Use
the imperative for an instruction to the reader. Use "you" only where
neither fits, and never as filler ("you'll want to", "you can simply").

## What must not change

- Code in code blocks, literal text in ``double backquotes``, directive
  names and options, labels (``.. _name:``), :ref:/:doc:/:c:func: targets,
  URLs, file names, image paths, table structure and column widths.
- A comment inside a code block may change only when it breaks the voice
  rules plainly, and only the comment text changes.
- RST structure: indentation, blank lines, list markers, table cells,
  ``.. tab::`` blocks.

## Line width

Wrap prose at 79 columns, at word boundaries, with the same indentation.
Tables, code and long links may run longer. Do not rewrap a paragraph you
did not change.
