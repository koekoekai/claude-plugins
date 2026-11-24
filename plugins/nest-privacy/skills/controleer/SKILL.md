---
name: controleer
description: Controleert je code offline op persoonsgegevens (BSN, IBAN, e-mail, telefoon, adressen, postcodes, IP-adressen, geboortedata, namen na een aanhef) en op geheimen (API-sleutels, tokens, privésleutels, wachtwoorden). Gebruik vóór een commit, push of PR, of als de gebruiker vraagt of er gevoelige data in de code staat.
argument-hint: "[--sinds origin/main]"
---

Draai in de root van het git-project (bestaat `python` niet, gebruik `python3`):

1. Persoonsgegevens: `python "${CLAUDE_PLUGIN_ROOT}/scripts/anonimiseren.py" controleer $ARGUMENTS`
2. Geheimen: `python "${CLAUDE_PLUGIN_ROOT}/scripts/geheimen.py" $ARGUMENTS`

Zonder argument worden alle bestanden in git gecontroleerd, met `--sinds origin/main` alleen wat sindsdien veranderde.
Exitcode 0 = niets gevonden, 1 = mogelijk iets gevonden.

Toon per vondst alleen bestand, regel en soort, **nooit de waarde**. Help het op te lossen:
- echte persoonsgegevens: eruit halen, of anonimiseren met `/nest-privacy:anonimiseer`;
- een geheim: uit de code halen, in een omgevingsvariabele of kluis zetten, en **intrekken bij de leverancier** (het staat mogelijk al in de git-geschiedenis);
- nepdata in tests: `pii: ok` of `geheim: ok` op de regel, of een patroon in `.nest-pii-negeer` of `.nest-geheim-negeer`.

Alles draait op deze computer; er gaat niets naar buiten.
