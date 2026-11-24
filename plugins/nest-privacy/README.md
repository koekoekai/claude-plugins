# Nest-privacy

Gratis plugin van [Koekoek](https://koekoek.ai) voor Claude Code. Houdt persoonsgegevens en geheimen uit je code. **Alles draait op je eigen computer; de plugin stuurt niets naar buiten** (geen server, geen telemetrie, geen netwerk).

## Wat je krijgt

| | |
|---|---|
| `/nest-privacy:controleer` | Controleert je code op persoonsgegevens (BSN met elfproef, IBAN met mod-97, e-mail, telefoon, adres, postcode, IP-adres, geboortedatum, namen na een aanhef) en op geheimen. |
| `/nest-privacy:anonimiseer <bestand>` | Zet een tekst- of CSV-bestand met echte data om naar een versie met `[SOORT]` in plaats van persoonsgegevens, zodat je veilig kunt testen of het aan een AI kunt geven. Optioneel pseudoniemen met een eigen sleutel. |
| `/nest-privacy:terugzetten <bestand>` | Zet codes zoals `[NAAM-3cd5a9aa4bca]` weer om naar de echte gegevens. Zo laat je Claude een antwoord schrijven met codes, en zet je daarna op je eigen computer de echte namen erin. |
| `/nest-privacy:geheimen` | Zoekt naar API-sleutels (AWS, GitHub, Stripe, Anthropic, OpenAI, Google, Slack), privésleutels, JWT's en wachtwoorden in code of URL's. |
| **Geen klantdata naar het model** | Wil Claude een databestand lezen (CSV, TXT, JSON, LOG, …) waar persoonsgegevens in staan, dan houdt een hook dat tegen. De inhoud gaat dan niet naar het model; Claude stelt voor om eerst te anonimiseren. |
| **Automatisch vóór elke push** | Een hook controleert de gewijzigde bestanden zodra Claude `git push` wil doen. Staat er iets in, dan houdt hij de push tegen en laat hij bestand, regel en soort zien (nooit de waarde). |

## Installeren

Nieuw met Claude Code? Volg de [installatiehandleiding voor Windows en Mac](../../docs/installeren.md).

```
/plugin marketplace add koekoekai/claude-plugins
/plugin install nest-privacy@koekoek
```

Nodig: Python 3.9 of nieuwer (`python` of `python3`) en git. Op Windows heeft Claude Code Git for Windows (Git Bash) nodig voor de hook.

## Welke gegevens

Alles wat volgens de AVG gevoelig is, wordt een code (bijv. `[NAAM-3cd5a9aa4bca]`, `[GEZONDHEID-f64c84a9171a]`):
naam, geboortedatum, adres, postcode, BSN en andere persoonsnummers, paspoort, telefoon, e-mail, IBAN, betaalkaart en CVC,
wachtwoorden en sleutels, IP-adres, kenteken, accounts, en de bijzondere persoonsgegevens (gezondheid, vakbond, politiek,
geloof, afkomst, geaardheid, strafrecht). Bedragen, bedrijfsnamen en plaatsen blijven standaard staan; aanzetten kan met
`--ook bedrag,organisatie,plaats`. Eigen termen (klanten, projecten, servers) die altijd weg moeten: één per regel in
`.nest-privacy-woorden` in je project, of in `~/.koekoek/nest-privacy/woorden.txt`.

**Beter met het lokale taalmodel (aanbevolen):** typ `/nest-privacy:taalmodel`, of draai
`python scripts/model_installeren.py`. Dat zet Privacy Kit (bards-ai, Apache-2.0, geen torch) eenmalig in een eigen omgeving
in `~/.koekoek/nest-privacy/model` (een paar minuten, ongeveer 0,5 GB). Daarna werkt het offline; er gaat geen tekst over het netwerk.
Gemeten op twee sets van elk 300 Nederlandse en Engelse zinnen met verzonnen gegevens (zie `tests/namen/UITSLAG.md`).
Een waarde telt alleen als weg als hij helemaal is afgedekt; "te veel" telt een selectie gewone woorden die moeten blijven.

| | weg | te veel weg |
|---|---|---|
| zonder model | 81 tot 92% | 13 tot 24% |
| met model | **98,3 tot 99,7%** | **0%** |

Eerlijk: de zinnen zijn door ons gemaakt, en een deel van de voornamen in de blinde set staat ook in de namenlijst van de regels.

Geen enkel hulpmiddel vindt alles. Controleer de uitkomst bij belangrijke data zelf.

**AVG-verantwoording:** een [handleiding](../../docs/dpia-handleiding.md) en een invulbaar [DPIA-sjabloon](../../docs/dpia-sjabloon.md) voor je eigen gebruik.

## Hoe anonimiseren werkt zonder dat Claude de data leest

1. **Een programma op je eigen computer doet het werk.** Claude start alleen `anonimiseren.py` of `pseudoniem.py` met de bestandsnaam. Het programma leest het bestand, vervangt de persoonsgegevens en schrijft een nieuw bestand. Claude ziet alleen aantallen, zoals `vervangen: NAAM 12, EMAIL 30`.
2. **Een slot op het lezen.** Wil Claude een databestand met persoonsgegevens openen, dan houdt de plugin dat tegen.
3. **Codes en terugzetten (pseudoniemen).** Dezelfde persoon krijgt overal dezelfde code, bijv. `[NAAM-3cd5a9aa4bca]`. De **sleutel** wordt bij het eerste gebruik willekeurig gemaakt en de **vertaaltabel** (code → echte waarde) wordt bewaard, allebei **alleen op jouw computer**: op Windows versleuteld met je eigen account (DPAPI), op macOS en Linux in een bestand dat alleen jij kunt lezen (`~/.koekoek/nest-privacy`). Claude ziet de tabel nooit. Tabellen worden na 30 dagen vanzelf gewist.

## Wat de plugin draait

- `scripts/anonimiseren.py`: herkennen en vervangen van persoonsgegevens (alleen de standaardbibliotheek van Python).
- `scripts/pseudoniem.py` en `scripts/kluis.py`: codes maken en terugzetten; sleutel en vertaaltabel lokaal en beschermd.
- `scripts/geheimen.py`: herkennen van geheimen (alleen de standaardbibliotheek).
- `hooks/voor_lezen.py`: vóór de Read-tool van Claude, alleen bij databestanden: lokaal controleren op persoonsgegevens; zo ja, wordt het bestand niet gelezen.
- `hooks/voor_push.py`: vóór `git push` beide controles op de bestanden die sinds de upstream-branch (of `origin/main`) veranderden. Gebruikt alleen lokale `git`-opdrachten.

De plugin leest bestanden in je project en schrijft alleen het uitvoerbestand dat je bij `anonimiseer` opgeeft.

## Nepdata en uitzonderingen

Markeer nepdata met `pii: ok` of `geheim: ok` op de regel, of zet een patroon per regel in `.nest-pii-negeer` of `.nest-geheim-negeer` in de root van je project.

## Grenzen

De lees-hook houdt de Read-tool tegen, niet elke andere manier van lezen (bijvoorbeeld een shell-opdracht). Zet echte klantdata dus liever niet in je project. Losse namen zonder aanhef ("dhr.", "mevrouw") herkent de plugin niet; daarvoor is een taalmodel nodig. De geheimencontrole is een basiscontrole: gebruik in CI ook een volledige scanner zoals gitleaks.

## Zonder garantie

Nest-privacy is een hulpmiddel, geen garantie. Hij vindt veel, maar niet alles: losse namen zonder aanhef bijvoorbeeld niet, en een nieuw soort sleutel misschien ook niet. Controleer de uitkomst dus zelf. Je gebruikt de plugin op eigen risico; Koekoek is niet aansprakelijk voor schade door het gebruik ervan (zie ook de [licentie](LICENSE)).

## Meer van Koekoek

Wil je ook review en scans met de regels van Koekoek op een eigen, door ons beheerde server, of software en AI-agents op maat? Zie [koekoek.ai](https://koekoek.ai/#prijzen).

## Privacy, support en licentie

- Privacy: [koekoek.ai/privacy.html](https://koekoek.ai/privacy.html#plugins). De plugin verwerkt niets buiten je eigen computer.
- Support: [koekoek.ai/#contact](https://koekoek.ai/#contact).
- Licentie: MIT, zie [LICENSE](LICENSE).

---

## In English

**Nest-privacy** is a free Claude Code plugin by [Koekoek](https://koekoek.ai) that keeps personal data and secrets out of your code. **It runs entirely on your own computer and sends nothing anywhere** (no server, no telemetry, no network calls).

| | |
|---|---|
| `/nest-privacy:controleer` | Checks your code for personal data (Dutch BSN with checksum, IBAN with mod-97, e-mail, phone, address, postcode, IP address, date of birth, names after a title) and for secrets. |
| `/nest-privacy:anonimiseer <file>` | Turns a text or CSV file with real data into a copy where personal data is replaced by `[TYPE]`, so you can test with it or give it to an AI. Optional keyed pseudonyms. |
| `/nest-privacy:terugzetten <file>` | Turns codes like `[NAAM-3cd5a9aa4bca]` back into the real data, on your own computer. Let Claude draft a reply with codes, then put the real names back locally. |
| `/nest-privacy:taalmodel` | Installs the local language model (Privacy Kit, Apache-2.0) once, in its own environment (~0.5 GB). Then it runs offline and also finds unknown names. Measured on 600 made-up Dutch and English sentences: 98.3–99.7% fully removed, 0% of a selection of ordinary words removed (without the model: 81–92%). Method and limits: `tests/namen/UITSLAG.md`. |
| `/nest-privacy:geheimen` | Looks for API keys (AWS, GitHub, Stripe, Anthropic, OpenAI, Google, Slack), private keys, JWTs and passwords in code or URLs. |
| **Customer data stays out of Claude** | A `PreToolUse` hook on Claude's Read tool checks data files (CSV, TXT, JSON, LOG, …) locally. If they contain personal data, the file is not read, so its contents never reach the model; Claude suggests anonymising it first. |
| **Before every push** | A `PreToolUse` hook on `git push` checks the changed files and blocks the push if it finds personal data or secrets. It shows file, line and type, never the value. |

**Pseudonyms and restoring:** the key is created randomly on first use and the lookup table (code → real value) is stored **only on your computer**: on Windows encrypted with your own account (DPAPI), on macOS/Linux in a file only you can read (`~/.koekoek/nest-privacy`). Claude never sees the table. Tables are deleted automatically after 30 days.

**What it runs:** `scripts/anonimiseren.py` and `scripts/geheimen.py` (Python standard library only), `hooks/voor_lezen.py` and `hooks/voor_push.py` (started by `hooks/py.sh`, which picks `python` or `python3`). The hooks only use local `git` commands. The plugin reads files in your project and writes only the output file you name for `anonimiseer`.

**Requirements:** Python 3.9+ and git. On Windows, Claude Code needs Git for Windows (Git Bash) for hooks.

**Limits:** no tool finds everything, so check important data yourself; without the language model, names without a title are often missed; the secret check is a baseline, so also use a full scanner such as gitleaks in CI. The Read hook guards Claude's Read tool, not every other way of reading a file.

No warranty: use at your own risk and check the results yourself (MIT, see [LICENSE](LICENSE)). Privacy: <https://koekoek.ai/privacy.html#plugins>. Support: <https://koekoek.ai/#contact>. Security: see [SECURITY.md](SECURITY.md).

