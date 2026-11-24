# Naamherkenning: meting (24-11-2026)

`python tests/namen/vergelijk.py`

| Set | Namen gevonden | Valse treffers | Opmerking |
|---|---|---|---|
| testset.json | 100% (40) | 0% (30) | eigen voorbeelden, de basis van de regels |
| moeilijk.json | 100% (21) | 0% (30) | daarna verbeterd, dus niet meer onafhankelijk |
| controle.json | 100% (23) | 3% (33) | de lijst met plaatsen en merken is gemaakt met kennis van deze set |
| **blind.json** | **91% (11)** | **50% (22)** | **eerlijk: niet op afgestemd** |

Vóór de naamherkenning: 18% op testset.json, 0% op moeilijk.json, 30% op controle.json.

**Wat het betekent:** hij vindt bijna alle namen, ook zonder aanhef. Maar onbekende plaatsen en merken midden in een zin
(Veenendaal, Exact, Twinfield, Dublin) worden ook weggehaald. Dat is veilig (liever te veel weg dan te weinig), maar de
tekst wordt er minder bruikbaar van.

**Volgende stap voor echte kwaliteit:** een lijst met Nederlandse woonplaatsen (open data van het CBS), een regel voor
"in/uit/te + plaats", en optioneel een lokaal taalmodel voor namen (spaCy nl), als dat geïnstalleerd is.
Meet daarna opnieuw op een nieuwe blinde set.
