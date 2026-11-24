---
name: fabriek-check
description: Draai lokaal dezelfde poorten als de Koekoek-fabriek in CI (persoonsgegevens, bouwstenen, veiligheidscheck) op het huidige project, zodat je vóór een push of PR ziet wat rood wordt.
argument-hint: "[--snel]"
---

Draai in de root van het huidige git-project:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" fabriek-check $ARGUMENTS
```

- Zonder argument: persoonsgegevens, bouwstenen en de volledige veiligheidscheck (draait ook de tests).
- `--snel`: alleen persoonsgegevens en bouwstenen.

Vat de uitkomst kort samen per poort (groen/rood/waarschuwing). Bij rood: leg uit wat er moet gebeuren en bied aan het op te lossen. Toon nooit gevonden persoonsgegevens; de scripts geven alleen bestand, regel en soort.

_Python: gebruik `python`; bestaat die niet (Linux-servers), gebruik dan `python3`._
