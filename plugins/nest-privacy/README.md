# Nest-privacy

Gratis plugin van [Koekoek](https://koekoek.ai) voor Claude Code. Houdt persoonsgegevens en geheimen uit je code. **Alles draait op je eigen computer; de plugin stuurt niets naar buiten** (geen server, geen telemetrie, geen netwerk).

## Wat je krijgt

| | |
|---|---|
| `/nest-privacy:controleer` | Controleert je code op persoonsgegevens (BSN met elfproef, IBAN met mod-97, e-mail, telefoon, adres, postcode, IP-adres, geboortedatum, namen na een aanhef) en op geheimen. |
| `/nest-privacy:anonimiseer <bestand>` | Zet een tekst- of CSV-bestand met echte data om naar een versie met `[SOORT]` in plaats van persoonsgegevens, zodat je veilig kunt testen of het aan een AI kunt geven. Optioneel pseudoniemen met een eigen sleutel. |
| `/nest-privacy:geheimen` | Zoekt naar API-sleutels (AWS, GitHub, Stripe, Anthropic, OpenAI, Google, Slack), privésleutels, JWT's en wachtwoorden in code of URL's. |
| **Geen klantdata naar het model** | Wil Claude een databestand lezen (CSV, TXT, JSON, LOG, …) waar persoonsgegevens in staan, dan houdt een hook dat tegen. De inhoud gaat dan niet naar het model; Claude stelt voor om eerst te anonimiseren. |
| **Automatisch vóór elke push** | Een hook controleert de gewijzigde bestanden zodra Claude `git push` wil doen. Staat er iets in, dan houdt hij de push tegen en laat hij bestand, regel en soort zien (nooit de waarde). |

## Installeren

```
/plugin marketplace add koekoekai/claude-plugins
/plugin install nest-privacy@koekoek
```

Nodig: Python 3.9 of nieuwer (`python` of `python3`) en git. Op Windows heeft Claude Code Git for Windows (Git Bash) nodig voor de hook.

## Wat de plugin draait

- `scripts/anonimiseren.py`: herkennen en vervangen van persoonsgegevens (alleen de standaardbibliotheek van Python).
- `scripts/geheimen.py`: herkennen van geheimen (alleen de standaardbibliotheek).
- `hooks/voor_lezen.py`: vóór de Read-tool van Claude, alleen bij databestanden: lokaal controleren op persoonsgegevens; zo ja, wordt het bestand niet gelezen.
- `hooks/voor_push.py`: vóór `git push` beide controles op de bestanden die sinds de upstream-branch (of `origin/main`) veranderden. Gebruikt alleen lokale `git`-opdrachten.

De plugin leest bestanden in je project en schrijft alleen het uitvoerbestand dat je bij `anonimiseer` opgeeft.

## Nepdata en uitzonderingen

Markeer nepdata met `pii: ok` of `geheim: ok` op de regel, of zet een patroon per regel in `.nest-pii-negeer` of `.nest-geheim-negeer` in de root van je project.

## Grenzen

De lees-hook houdt de Read-tool tegen, niet elke andere manier van lezen (bijvoorbeeld een shell-opdracht). Zet echte klantdata dus liever niet in je project. Losse namen zonder aanhef ("dhr.", "mevrouw") herkent de plugin niet; daarvoor is een taalmodel nodig. De geheimencontrole is een basiscontrole: gebruik in CI ook een volledige scanner zoals gitleaks.

## Meer van Koekoek

Wil je ook review en scans met de regels van Koekoek op een eigen, door ons beheerde server, of software en AI-agents op maat? Zie [koekoek.ai](https://koekoek.ai/#prijzen).

## Privacy, support en licentie

- Privacy: [koekoek.ai/privacy.html](https://koekoek.ai/privacy.html#plugins). De plugin verwerkt niets buiten je eigen computer.
- Support: [koekoek.ai/#contact](https://koekoek.ai/#contact).
- Licentie: MIT, zie [LICENSE](LICENSE).
