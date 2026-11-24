# Je eigen gebruik van Nest-privacy beoordelen

> Dit is een hulpmiddel, geen juridisch advies. Jij blijft verantwoordelijk voor je verwerking. Twijfel je, vraag dan je FG of een jurist. Koekoek helpt graag bij het invullen.

Wat zou iemand kunnen overkomen als je deze tekst verwerkt of deelt? Met een gegevensbeschermingseffectbeoordeling (DPIA) beantwoord je die vraag vóór je begint. Een DPIA is verplicht als de verwerking waarschijnlijk een hoog risico oplevert voor mensen. Beoordeel het hele werkproces, van bronbestand tot verwijderd antwoord. Kopieer het [invulbare sjabloon](dpia-sjabloon.md) naar je eigen besloten werkomgeving.

## Kies wat je nodig hebt

Beschrijf één concrete taak. Kan die met verzonnen tekst? Dan kun je de echte dossiers buiten het proces houden. Heb je echte tekst nodig, leg dan vast welke passages nodig zijn en wie de uitkomst krijgt.

Deze handleiding gaat uit van Nest-privacy 0.4.0. Controleer welke versie en instellingen je zelf gebruikt. Bij de beoordeelde werkwijze leest een programma het bronbestand op je computer en schrijft het lokaal een bewerkte kopie. Het optionele taalmodel wordt apart geïnstalleerd en verwerkt tekst daarna lokaal.

- **Maskeren** vervangt een herkende waarde door een soortnaam zoals `[NAAM]`. Kies dit als je de echte waarde later niet nodig hebt. Het origineel blijft bestaan. Iemand kan ook na maskeren herkenbaar blijven door de combinatie van functie, plaats en gebeurtenis.
- **Pseudoniemen** vervangen waarden door herkenbare codes. Dat maakt koppelen mogelijk. De lokale vertaaltabel koppelt codes aan oorspronkelijke waarden en maakt terugzetten mogelijk. De sleutel en de tabel staan onder het gebruikersaccount. Windows gebruikt accountgebonden versleuteling, macOS en Linux gebruiken bestandsrechten. Behandel de uitvoer als persoonsgegevens. Beperk toegang tot de tabel en houd haar buiten gedeelde mappen en AI-gesprekken.
- **Bewaren** vraagt een eigen keuze. Bij gebruik van het pseudoniemprogramma ruimt het tabellen op die langer dan 30 dagen geleden zijn gewijzigd. Zonder volgend gebruik kunnen ze langer blijven staan. Regel zelf tijdige verwijdering, ook voor originelen, herstelde teksten en reservekopieën.

## Controleer vóór je deelt

De herkenner kan namen missen en gewone woorden ten onrechte vervangen. De leesbeveiliging bewaakt bepaalde databestanden bij gebruik van de Read-tool. Een shell-opdracht kan zo'n bestand via een andere route lezen. Test je werkwijze met verzonnen tekst en laat iemand de echte uitvoer lokaal controleren op gemiste gegevens, herkenbare context en betekenisverlies.

**Fictief voorbeeld.** Een medewerker maskeert een klacht. De naam verdwijnt, maar “de enige nachtwaker van de vestiging” wijst nog naar één persoon. De medewerker schrapt die passage en controleert opnieuw voordat de tekst wordt gedeeld.

Plak je de uitvoer in een AI-dienst, dan ontvangt die dienst de ingediende tekst. Ook het antwoord en de gespreksgeschiedenis kunnen persoonsgegevens bevatten. Leg vooraf vast wie de aanbieder is, waarvoor die de tekst mag gebruiken, wie toegang krijgt, waar verwerking plaatsvindt en wanneer kopieën worden gewist. Controleer dit voor je eigen account, contract en instellingen.

## Neem een besluit

Vul het sjabloon samen met de proceseigenaar in. Vraag advies aan je functionaris voor gegevensbescherming (FG) als die er is. Leg per risico vast wie de maatregel uitvoert en hoe je weet dat die werkt. Blijft een hoog risico bestaan dat je onvoldoende kunt beperken, raadpleeg dan vóór de verwerking de bevoegde toezichthouder. Plan een nieuwe beoordeling zodra de werkwijze of het risico verandert. Zie [AVG, artikelen 35 en 36 (EUR-Lex)](https://eur-lex.europa.eu/legal-content/NL/TXT/?uri=CELEX:32016R0679).
