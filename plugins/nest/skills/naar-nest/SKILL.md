---
name: naar-nest
description: Een verbetering uit een project terugbrengen naar Nest (de bouwstenen), zodat alle projecten ervan profiteren. Gebruik aan het eind van een stuk werk als er een nieuwe check, een bruikbaar stuk code of een geleerde les is.
---

Doel: wat in een project beter werd, komt eerst in Nest, en gaat daarna terug naar de projecten.

1. Bepaal wat het is: een **regel** (in de standaard `<onderwerp>/README.md`), **code** (bouwsteen met tests) of een **losse functie** (`TOOLS.md`).
2. Waar staat Nest lokaal? Gebruik `NEST_MAP`, anders een eigen checkout zoals `~/code/bouwstenen` of `~/Desktop/github/bouwstenen`. Bestaat geen lokale kopie, vraag of je hem mag clonen. Werk nooit in de plugin-cache of in de beheerde kopie `~/.koekoek/bouwstenen`: die wordt automatisch bijgewerkt.
3. In Nest, op een branch:
   - code en tests aanpassen of toevoegen; geen projectnamen, domeinen of servers erin (via instellingen);
   - versie omhoog in de markerregel én in `catalogus.json` (de test controleert dat ze gelijk zijn);
   - een regel in `CHANGELOG.md` van Nest;
   - `python -m pytest -q` groen.
4. PR naar Nest (door de fabriek). Na de merge laat `python scripts/bouwstenen_check.py` zien welke projecten moeten volgen.
5. Nooit klantdata, geheimen of persoonsgegevens meenemen naar Nest.
