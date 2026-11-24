---
name: anonimiseer
description: Persoonsgegevens (namen, e-mail, IBAN, BSN, telefoon, adres, postcode, geboortedatum, IP) uit een tekst- of CSV-bestand halen met de Koekoek-anonimiseerder, lokaal en offline. Gebruik vóór data gedeeld, getest of aan een AI gegeven wordt.
argument-hint: "<bestand> [--naamkolommen naam] [--modus pseudoniem]"
disable-model-invocation: true
---

Werk met `python "${CLAUDE_PLUGIN_ROOT}/scripts/anon.py"`. Die haalt `koekoekai/anonimiseren` op en houdt hem bij. Alles draait lokaal; er gaat niets naar internet.

**Belangrijk:** lees het bronbestand zelf NIET in (geen Read, cat, head of grep op de invoer): dan komt de inhoud met persoonsgegevens in dit gesprek. Werk alleen met de scripts en hun samenvatting (aantallen per soort). Kolomnamen van een CSV mag je ophalen met:
`python "${CLAUDE_PLUGIN_ROOT}/scripts/anon.py" kolommen <bestand.csv>`

Stappen voor `$ARGUMENTS`:
1. Uitvoerbestand: `<naam>-anoniem.<ext>` naast het origineel. Overschrijf nooit het origineel.
2. Bij een CSV: haal de kolomnamen op en vraag welke kolom(men) namen bevatten, als dat niet is opgegeven.
3. Draai: `python "${CLAUDE_PLUGIN_ROOT}/scripts/anon.py" <bestand> -o <uitvoer> [--naamkolommen …] [--modus pseudoniem]`
   Pseudoniem werkt alleen met `ANONIEM_SLEUTEL` in de omgeving (de lokale tool maakt en bewaart die met DPAPI); nooit een sleutel in dit gesprek vragen of tonen.
4. Meld het uitvoerbestand en de aantallen per soort. Wijs erop dat losse namen zonder aanhef niet altijd gevonden worden en dat een steekproef met de hand nodig is vóór delen.

Liever een venster? `python "${CLAUDE_PLUGIN_ROOT}/scripts/anon.py" tool` opent de lokale tool op http://127.0.0.1:8765.

_Python: gebruik `python`; bestaat die niet (Linux-servers), gebruik dan `python3`._
