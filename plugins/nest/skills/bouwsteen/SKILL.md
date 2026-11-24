---
name: bouwsteen
description: Een geteste Nest-bouwsteen uit koekoekai (bijv. beveiligingskoppen, limieten, alarm, CSRF-herkomst, contactformulier, PWA, push, anonimiseren) in het huidige project zetten, met versieregel. Gebruik dit wanneer je iets gaat bouwen dat al als bouwsteen bestaat, in plaats van het opnieuw te schrijven.
argument-hint: "[naam] [doelpad]"
---

De bouwstenen zijn de geteste, gedeelde code van Koekoek in `koekoekai/bouwstenen`. Opnieuw verzinnen wat er al is, kost tijd en geeft fouten die al eens zijn opgelost.

1. Welke er zijn: `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" bouwstenen` (alles) of met `--stack python|node`.
   De lijst voor dit project staat ook al in je context vanaf de start van de sessie.
2. Kies de bouwsteen die past bij `$ARGUMENTS` of bij wat er gebouwd moet worden. Lees bij twijfel de standaard: `<nest>/<onderwerp>/README.md` (`<nest>` = `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" pad`). Daar staat ook hoe je hem inregelt.
3. Zet hem in het project, op de plek die bij de projectindeling past (bijv. `app/bouwstenen/koppen.py` of `lib/bouwstenen/koppen.js`):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" bouwsteen <naam> <doelpad>`
   Bestaat het doel al: vergelijk eerst en vraag of overschrijven mag (`--overschrijf`).
4. Sluit hem aan volgens de standaard (bijv. `voeg_koppen_toe(app)`), en voeg tests toe voor het gedrag in dit project.
5. **Verander de bouwsteen zelf niet in het project.** Moet er iets anders of beter: doe dat in Nest via `/nest:naar-nest`, en zet daarna de nieuwe versie hier.
6. Versie en CHANGELOG van het project bijwerken volgens de werkwijze. De bouwstenen-poort in de fabriek ziet de versieregel en meldt later als hij achterloopt.

_Python: gebruik `python`; bestaat die niet (Linux-servers), gebruik dan `python3`._
