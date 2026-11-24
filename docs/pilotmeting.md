# Meet Nest-privacy op je eigen teksten

**1. Maak een lokale testmap.** Zet hierin kopieën van de teksten die je wilt meten. Bewaar ze als gewone tekst (.txt), in UTF-8 of UTF-16 met bytevolgordemarkering. Geef de map en bestanden neutrale namen, bijvoorbeeld `pilot` en `tekst1.txt`.

**2. Markeer alles wat weg moet.** Zet dubbele blokhaken om elke gevoelige waarde, elke keer dat die voorkomt. Bijvoorbeeld:

    Bel [[NAAM:Fien Voorbeeld]] over [[dossier zeven]].

De herkenner krijgt de gewone zin te zien. Met een soort zoals NAAM, EMAIL, TELEFOON, IBAN of BSN krijg je aparte aantallen. Zonder soort komt de markering bij ONGESPECIFICEERD. Gebruik alleen bekende soorten als voorvoegsel. Zet spaties buiten de haken en maak geen lege of geneste markeringen.

**3. Draai de meting.** Typ in Claude Code met de plugin Nest-privacy:

    /nest-privacy:pilotmeting "pilot"

Claude laat het lokale script de bestanden lezen. Plak de teksten zelf nooit in de chat. Je kunt ook vanuit de repository in een terminal meten:

    python plugins/nest-privacy/scripts/pilotmeting.py "pilot"

Op macOS of Linux heet Python soms `python3`. Je kunt ook losse bestandspaden opgeven. Bij een map telt het script de .txt-bestanden direct in die map. De meting gebruikt lokale modellen en regels. Bij afwezigheid van een model gebruikt ze de regels.

**4. Bekijk de aantallen.** Per soort en in totaal zie je hoeveel markeringen volledig, gedeeltelijk of helemaal gemist zijn. Volledig betekent dat elk teken wordt afgedekt. Bij gedeeltelijk blijft een deel leesbaar. Een woord telt één keer als onterecht weggehaald zodra de herkenner een ongemarkeerd deel van dat woord raakt. Dat telt bij de soort van de treffer. Een vergeten markering kan dit aantal verhogen.

**5. Deel alleen het rapport.** Je ziet het hele rapport op het scherm. In de map waar je de opdracht uitvoerde staat dezelfde inhoud in `pilotmeting.json`. Bekijk de aantallen, de soorten en de gebruikte herkenners. Als je ze wilt delen, stuur je zelf alleen dat bestand naar Koekoek. De teksten blijven bij jou. Verplaats het rapport voordat je opnieuw meet.
