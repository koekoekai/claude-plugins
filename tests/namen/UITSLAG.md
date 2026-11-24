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

## Tweede ronde (plaatsenlijst, regel "in/uit/te + plaats")

| Set | Namen gevonden | Valse treffers |
|---|---|---|
| blind.json (nu deels bekend) | 82% | 36% |
| **blind2.json (nieuw, niet op afgestemd)** | **100% (10)** | **19% (21)** |

Plaatsen gaan goed, onbekende merken (Pipedrive, Salesforce, Figma, Visma) niet. "in + naam" kost soms een naam ("loop in Aoife").
**Conclusie:** met regels blijf je schuiven tussen namen missen en merken wegpoetsen. Volgende stap: een bestaand lokaal taalmodel
voor namen (spaCy of GLiNER) als optionele herkenner; de vaste regels blijven voor BSN, IBAN en telefoon, en de vertaaltabel blijft.

## Ronde 3: bestaand taalmodel (spaCy 3.8, nl_core_news_md en en_core_web_md)

`NEST_PRIVACY_HERKENNER=spacy python tests/namen/vergelijk.py` (met spaCy geïnstalleerd)

| Set | Regels: gevonden / vals | spaCy: gevonden / vals |
|---|---|---|
| testset.json | 100% / 0% | 100% / 3% |
| moeilijk.json | 100% / 0% | 86% / 0% |
| controle.json | 100% / 3% | 91% / 3% |
| **blind.json** | 82% / 36% | **91% / 0%** |
| **blind2.json** | 100% / 19% | **100% / 0%** |

Met een bestaand model zakken de valse treffers op de blinde sets naar 0%. Licenties: spaCy MIT, en_core_web_md MIT,
nl_core_news_md CC BY-SA 4.0 (de gebruiker installeert het zelf; wij leveren het model niet mee).
