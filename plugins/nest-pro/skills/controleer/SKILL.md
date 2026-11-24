---
name: controleer
description: Gratis en offline. Controleert je code op persoonsgegevens (BSN, IBAN, e-mail, telefoon, adressen, namen na een aanhef, IP-adressen, geboortedata) op je eigen computer. Er gaat niets naar Koekoek en je hebt geen sleutel nodig. Gebruik vóór een commit, push of PR.
argument-hint: "[--sinds origin/main]"
---

1. Draai in de root van het git-project (bestaat `python` niet, gebruik `python3`):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/anonimiseren.py" controleer $ARGUMENTS`
   Zonder argument controleert hij alle bestanden in git, met `--sinds origin/main` alleen wat sindsdien veranderde.
2. Exitcode 0: er is niets gevonden. Exitcode 1: er staan mogelijk persoonsgegevens in.
3. Toon per vondst alleen bestand, regel en soort, **nooit de waarde**.
4. Help het op te lossen: echte data eruit halen, of nepdata markeren met `pii: ok` op de regel of een patroon in `.nest-pii-negeer`.
5. Wil de gebruiker een tekst of CSV anonimiseren:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/anonimiseren.py" <bestand> -o <uitvoer>`
   Persoonsgegevens worden dan `[SOORT]`.

Dit draait helemaal op deze computer. Met een Nest-sleutel (`NEST_TOKEN`) kun je daarnaast `/nest-pro:review` en `/nest-pro:scan` gebruiken: zie koekoek.ai/#prijzen.
