---
name: terugzetten
description: Zet codes zoals [NAAM-3cd5a9aa4bca] in een tekst weer om naar de echte namen, e-mails en nummers, op deze computer. Gebruik nadat je met /nest-privacy:anonimiseer in de stand "pseudoniem" gewerkt hebt en een antwoord of rapport voor echte mensen klaar is.
argument-hint: "<bestand-met-codes> [uitvoerbestand]"
---

1. Schrijf het antwoord of rapport met de codes erin (zoals `[NAAM-3cd5a9aa4bca]`) naar een bestand.
2. Draai (bestaat `python` niet, gebruik `python3`):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/pseudoniem.py" terugzetten "<bestand-met-codes>" -o "<uitvoer>"`
3. Meld alleen de regel `teruggezet: … · onbekende codes: …` en waar de uitvoer staat.
4. **Lees de uitvoer niet** (ook niet met cat, head of grep): daar staan weer echte persoonsgegevens in. De gebruiker opent hem zelf.
5. Onbekende codes? Die horen bij een tabel die gewist is of op een andere computer staat. Meld het; verzin geen waarden.

De vertaaltabel staat alleen op deze computer, beschermd (Windows: versleuteld met je eigen account; macOS/Linux: alleen leesbaar voor jou), en wordt na 30 dagen vanzelf gewist. Nu wissen: `python "${CLAUDE_PLUGIN_ROOT}/scripts/pseudoniem.py" wis --alles`.
