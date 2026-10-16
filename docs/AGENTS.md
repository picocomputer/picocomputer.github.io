# Picocomputer Manual

The manual is the Sphinx reStructuredText in `source/`. Write it for
engineers and programmers, in the style of a data sheet, in plain language.
The rules below are the writing rules of ASD-STE100 Simplified Technical
English, without its restricted dictionary.

## Write for the reader

The reader is a programmer who works through the manual in order. Write
each passage for what that reader is trying to do at that point, not for
how the system is arranged inside.

## Rules

**Never lose a fact.** Do not change what a fact says. You may remove a
repeated statement of a fact, but at least one statement of it must
remain.

**One word for one meaning.** Use one word for one meaning, and use the
same word every time.

**Use each word in its exact meaning.** "Name" means to give a thing its
name. It does not mean to use, give or refer to a thing.

**Present tense and active voice.** Use the present tense and the active
voice. Give each sentence a subject.

**Short sentences.** Prefer short sentences. A sentence is as long as its
content requires.

**One instruction per sentence.** Write one instruction in each sentence.

**Serial comma.** Put a comma before the "and" or "or" that ends a list
of three or more items.

**Noun clusters.** Do not use noun clusters of more than three words.

**No figures of speech, idioms or decoration.** Do not add humor, hype,
metaphor or idioms. The owner writes these where they matter. Leave the
ones already in the text.

**RFC 2119 words.** Use the RFC 2119 words with their RFC meanings. "Must"
and "must not" state a requirement. "Should" and "should not" state a
recommendation. "May" states an option. "Can" states an ability. A command
that does not run without an argument requires that argument. These rules
govern the RFC words when the text uses them. They do not require the text
to use them.

**Machines are not beings.** Machines and software have no motives,
feelings or personalities. State what they do as fact. Give a machine
only verbs for operations it performs. A verb for a human act, even a
plain one, gives it a personality. Use the established term of the field.

**No first person.** No I, me, my, we, our, us. The manual is not a letter
from its author.

**Errors.** Prefer solid systems and clear messages to documentation of
errors. Decide each case on its own. An error that the project does not
control may be documented. The errno lists on the API page are a contract
and must be complete and exact.

## Line width

Wrap prose at 79 columns.
