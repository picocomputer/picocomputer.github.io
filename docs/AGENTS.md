# Picocomputer Manual

The manual is the Sphinx reStructuredText in `source/`. Write it for
engineers and programmers, in the style of a data sheet, in plain language.
The rules below are the writing rules of ASD-STE100 Simplified Technical
English, without its restricted dictionary.

## Write for the reader

The reader is a programmer who works through the manual in order. Write
each passage for what that reader is trying to do at that point, not for
how the system is arranged inside.

**Edit the passage, not the sentence.** Before any change, read the
section from its start, as the reader who arrives there. Decide what that
reader needs from the passage at that point. Make every sentence serve
that need, and remove a sentence that does not. A change to one sentence
is a change to its passage, so read the whole passage again after the
change, and before you report it.

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

## Glossary

**6502 RAM.** The 64 KB address space of the 6502.

**API call.** One request that a 6502 program makes to the RIA. The
program writes the operation ID of the API call to RIA_OP.

**asset.** A file that `rp6502_asset()` packages into a ROM.

**canvas.** The grid of pixels that the VGA draws.

**console.** The main terminal, connected to stdin, stdout, stderr, CON:,
and TTY:.

**debug overlay.** The windows of machine state that `--debug` draws
over the emulator window, such as the CPU, the VIA, and the memory
editors.

**device name.** A name that ends in ":" and that can begin a path, such
as CON:, ROM:, SAVE:, MSC0:, and FS:.

**directory.** A container of files. The manual does not use "folder".

**drive.** A storage device, such as a USB drive. Each drive has its own
device name, such as MSC0:.

**emulator.** RP6502-EMU, the program `rp6502-emu`.

**exit code.** The integer that `exit()` takes and `main()` returns.

**extended RAM (XRAM).** The 64 KB of memory outside the address space of
the 6502.

**extended register (XREG).** A 16-bit register of a PIX device, set with
`xreg()`.

**extended stack (XSTACK).** The 512-byte stack in the RIA for the
arguments and the returned data of API calls.

**file name.** The last part of a path.

**fill layer.** The text, tile, or bitmap layer of a plane.

**host.** The modern side behind the RIA registers that does the work of
API calls: the Pico 2, the soft CPU of the RP6502-FPGA, the computer under
the RP6502-EMU, or the browser under the RP6502-WEB.

**keycode.** The USB HID usage number of a key.

**line editor.** The editor of the RIA that reads a line of text from the
console. The source code calls it RLN. The manual calls it the line
editor.

**machine.** One implementation of the Picocomputer: RP6502-PICO,
RP6502-FPGA, RP6502-EMU, or RP6502-WEB.

**monitor.** The program that an RP6502-PICO runs on the console for
configuration and for loading ROMs.

**opcode.** A 6502 instruction byte.

**operation ID.** The name or the number that a program writes to RIA_OP
to make an API call, such as RIA_OP_ARGV.

**passkey.** The key that a telnet client sends to connect.

**path.** The string that locates a file or a directory, with an optional
device name.

**Pico 2.** The Raspberry Pi Pico 2 board that runs the RIA or the VGA
firmware.

**PIX.** The arrangement of device interfaces in XRAM. The PIX bus is the
5-wire bus between the RIA and the VGA on an RP6502-PICO.

**program.** The code that the 6502 runs, as the actor of an action. A
program reads input, writes output, draws, and opens files.

**RIA.** The RP6502 Interface Adapter: the 32 registers at $FFE0-$FFFF
and what implements them.

**ROM.** A file that ends in `.rp6502`, and the unit that starts, stops,
receives arguments, and returns an exit code.

**scanline.** One row of pixels of the canvas.

**Side Bar.** The part of the VS Code window that shows Run and Debug,
CMake, Testing, and other views.

**template.** The GitHub project template. A project made from it is
"your project".

**terminal.** A device that a user types into and reads from.

**USB drive.** Removable USB storage that the RIA mounts as MSC0: to
MSC9:.

**VGA.** The RP6502 Video Graphics Array. The VGA module is the Pico 2
that runs the VGA firmware on an RP6502-PICO.

**web player.** `rp6502-<version>-web.zip`, and the files that
`rp6502_web()` makes from it with a ROM.
