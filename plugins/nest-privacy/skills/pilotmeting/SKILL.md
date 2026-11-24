---
name: pilotmeting
description: Meet offline hoe goed Nest-privacy gevoelige stukken in door de klant gemarkeerde teksten afdekt. Toon de klant alleen het telrapport.
argument-hint: "<map of bestanden>"
---

1. Gebruik de opgegeven lokale paden. Lees of bekijk de bronbestanden nooit, ook niet bij fouten. Vraag nooit om tekst te plakken. Laat alleen het meetscript de bronnen openen.
2. Voer `python "${CLAUDE_PLUGIN_ROOT}/scripts/pilotmeting.py" "<pad>"` uit. Gebruik zo nodig python3. Geef elk opgegeven pad als afzonderlijk, veilig geciteerd argument door.
3. Toon na succes de volledige JSON uit de scriptuitvoer. Hetzelfde rapport staat als `pilotmeting.json` in de werkmap. Laat de klant beslissen over delen en verstuur zelf niets. Geef bij een fout alleen de melding van het script door.
