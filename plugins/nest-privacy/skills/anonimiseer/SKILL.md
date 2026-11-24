---
name: anonimiseer
description: Zet een tekst- of CSV-bestand met echte (klant)data om naar een versie zonder persoonsgegevens, offline. Namen, e-mail, telefoon, IBAN, BSN, adressen, postcodes, IP-adressen en geboortedata worden [SOORT]. Gebruik als de gebruiker echte data wil testen, delen of aan een AI wil geven.
argument-hint: "<bestand> [uitvoerbestand]"
---

1. Bepaal het invoerbestand uit `$ARGUMENTS`. Uitvoer: het tweede argument, anders `<naam>.anoniem.<ext>` naast het origineel.
2. **Lees het invoerbestand zelf niet** (ook niet met cat, head of grep): dan gaan de persoonsgegevens alsnog naar het model. Laat alleen het script ermee werken. Lees daarna alleen de uitvoer.
3. Draai (bestaat `python` niet, gebruik `python3`):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/pseudoniem.py" maak "<invoer>" -o "<uitvoer>" --maskeren`
   - **Wil je later terug naar de echte gegevens** (bijv. een antwoord aan een echte klant), of moet dezelfde persoon overal dezelfde code krijgen? Gebruik dan pseudoniemen:
     `python "${CLAUDE_PLUGIN_ROOT}/scripts/pseudoniem.py" maak "<invoer>" -o "<uitvoer>"`
     Dan wordt `Jan Jansen` bijv. `[NAAM-3cd5a9aa4bca]`, overal dezelfde code. De sleutel en de vertaaltabel staan alleen op deze computer, beschermd. Terugzetten: `/nest-privacy:terugzetten`. Let op: zolang de tabel bestaat, blijven het voor de AVG persoonsgegevens.
4. Meld de regel `vervangen: …` (alleen aantallen) en waar de uitvoer staat. Raad aan de uitvoer steekproefsgewijs na te kijken: losse namen zonder aanhef kunnen blijven staan.
5. Controleer daarna de uitvoer: `python "${CLAUDE_PLUGIN_ROOT}/scripts/anonimiseren.py" controleer "<uitvoer>"`.

Alles draait op deze computer; er gaat niets naar buiten.
