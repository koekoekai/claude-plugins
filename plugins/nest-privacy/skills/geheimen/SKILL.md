---
name: geheimen
description: Zoekt offline naar geheimen in code (API-sleutels van AWS, GitHub, Stripe, Anthropic, OpenAI, Google, Slack, privésleutels, JWT's, wachtwoorden in code of URL's). Gebruik vóór een push of als de gebruiker vraagt of er sleutels in de code staan.
argument-hint: "[--sinds origin/main]"
---

1. Draai in de root van het git-project (bestaat `python` niet, gebruik `python3`):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/geheimen.py" $ARGUMENTS`
2. Toon per vondst alleen bestand, regel en soort, **nooit de waarde**.
3. Bij een echt geheim, altijd in deze volgorde:
   1. intrekken of vernieuwen bij de leverancier (het staat mogelijk al in de git-geschiedenis of op GitHub);
   2. uit de code halen en uit een omgevingsvariabele of kluis laden;
   3. eventueel de git-geschiedenis opschonen (alleen met akkoord: dat herschrijft commits).
4. Nepsleutel in een test: `geheim: ok` op de regel, of een patroon in `.nest-geheim-negeer`.

Dit is een basiscontrole. Voor CI raden we daarnaast een volledige scanner aan, zoals gitleaks.
Alles draait op deze computer; er gaat niets naar buiten.
