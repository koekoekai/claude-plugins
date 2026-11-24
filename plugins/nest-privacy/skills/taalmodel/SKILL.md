---
name: taalmodel
description: Installeert, controleert of verwijdert het lokale taalmodel (Privacy Kit) waarmee Nest-privacy ook onbekende namen en meer soorten persoonsgegevens herkent. Gebruik als de gebruiker betere herkenning wil, vraagt of het model werkt, of het model wil verwijderen.
argument-hint: "[--status | --verwijder]"
---

Draai (bestaat `python` niet, gebruik `python3`):

`python "${CLAUDE_PLUGIN_ROOT}/scripts/model_installeren.py" $ARGUMENTS`

- Zonder argument: installeert het model eenmalig in een eigen omgeving in `~/.koekoek/nest-privacy/model`. Dat duurt een paar minuten en downloadt ongeveer 0,5 GB (Privacy Kit van bards-ai, Apache-2.0). Vraag de gebruiker vooraf of dat goed is. Git en internet zijn nodig.
- `--status`: zegt of het model er staat en werkt.
- `--verwijder`: haalt de omgeving en het model weer weg.

Daarna gebruikt de plugin het model vanzelf. Het draait offline op deze computer: er gaat geen tekst over het netwerk.
