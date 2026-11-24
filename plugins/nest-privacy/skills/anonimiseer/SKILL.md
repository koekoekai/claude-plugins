---
name: anonimiseer
description: Zet een tekst- of CSV-bestand met echte (klant)data om naar een versie zonder persoonsgegevens, offline. Namen, e-mail, telefoon, IBAN, BSN, adressen, postcodes, IP-adressen en geboortedata worden [SOORT]. Gebruik als de gebruiker echte data wil testen, delen of aan een AI wil geven.
argument-hint: "<bestand> [uitvoerbestand]"
---

1. Bepaal het invoerbestand uit `$ARGUMENTS`. Uitvoer: het tweede argument, anders `<naam>.anoniem.<ext>` naast het origineel.
2. **Lees het invoerbestand zelf niet** (ook niet met cat, head of grep): dan gaan de persoonsgegevens alsnog naar het model. Laat alleen het script ermee werken. Lees daarna alleen de uitvoer.
3. Draai (bestaat `python` niet, gebruik `python3`):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/anonimiseren.py" "<invoer>" -o "<uitvoer>"`
   - CSV: alleen bepaalde kolommen met `--kolommen a,b`; kolommen met namen met `--naamkolommen voornaam,achternaam`.
   - Namen die altijd weg moeten (zonder aanhef worden losse namen niet herkend): een bestand met één naam per regel via `--namen <bestand>`.
   - Pseudoniemen in plaats van `[SOORT]` (zelfde waarde = zelfde pseudoniem, handig voor koppelen): `--modus pseudoniem` met een geheime sleutel in de omgevingsvariabele `ANONIEM_SLEUTEL`. Let op: dat blijven persoonsgegevens zolang iemand de sleutel heeft.
4. Meld de regel `vervangen: …` (alleen aantallen) en waar de uitvoer staat. Raad aan de uitvoer steekproefsgewijs na te kijken: losse namen zonder aanhef kunnen blijven staan.
5. Controleer daarna de uitvoer: `python "${CLAUDE_PLUGIN_ROOT}/scripts/anonimiseren.py" controleer "<uitvoer>"`.

Alles draait op deze computer; er gaat niets naar buiten.
