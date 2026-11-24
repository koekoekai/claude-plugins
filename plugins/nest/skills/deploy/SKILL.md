---
name: deploy
description: Begeleide deploy volgens de Nest-standaard (updates/README.md): alleen een gesealde, groene versie, met akkoord, daarna controleren en weten hoe je terugdraait. Geen API-sleutel nodig.
argument-hint: "[versie]"
disable-model-invocation: true
---

Standaard: `<nest>/updates/README.md`, kopje "Deploy" (`<nest>` = `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" pad`). Live zetten gebeurt **alleen na expliciet akkoord** in dit gesprek, per project.

1. **Wat gaat live:** de versie uit `$ARGUMENTS`, anders de laatste tag. Controleer: tag bestaat, `main` bevat hem, werkmap schoon, en (indien bekend) de CI van die commit is groen.
2. **Hoe dit project deployt:** zoek in deze volgorde en gebruik alleen wat het project zelf vastlegt:
   - `scripts/deploy.*` of een `deploy`-script in `package.json`;
   - het kopje "Deploy" / "Terugdraaien" in `README.md` of `CLAUDE.md`;
   - een pull-deploy op de server (bijv. een sync-timer): dan is deployen = pushen naar de branch die de server volgt.
   Niets gevonden? Stop en stel voor het eerst vast te leggen (één commando voor deploy, één voor terugdraaien). Verzin geen servercommando's.
3. **Vóór livegang:** `python "<nest>/security/veiligheidscheck/veiligheidscheck.py" --map .` (met de live site als `veiligheidscheck.json` een url heeft). Rood = niet live.
4. Toon het plan: versie, commando, terugdraaicommando, wat er daarna gecontroleerd wordt. **Vraag akkoord.**
5. Na akkoord: draai het deploycommando. Verifieer daarna altijd met:
   `python "<nest>/fabriek/verifieer.py" <url> --versie <versie> --terug "<terugdraaicommando>"`
   Dit wacht tot precies de nieuwe versie live en gezond is (`/api/gezondheid`, bouwsteen `bewaking/gezondheid`). Groene tests zijn geen bewijs dat het live werkt.
   Heeft de app nog geen `/api/gezondheid`: stel voor de bouwsteen toe te voegen (`/nest:bouwsteen bewaking/gezondheid-python` of `-node`), en controleer tot die tijd `/api/version` met de hand.
6. Mislukt de verificatie (ROOD): meld het direct en bied het terugdraaicommando aan (niet zelf uitvoeren zonder akkoord).

_Python: gebruik `python`; bestaat die niet (Linux-servers), gebruik dan `python3`._
