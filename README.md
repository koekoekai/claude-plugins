# Koekoek-plugins voor Claude Code

> **English:** Claude Code plugins by [Koekoek](https://koekoek.ai). The free plugin **Nest-privacy** keeps personal data and secrets out of your code and runs fully on your own computer; see [plugins/nest-privacy](plugins/nest-privacy#in-english). Security reports: [SECURITY.md](SECURITY.md).

Plugins van [Koekoek](https://koekoek.ai) voor Claude Code. Ze zorgen dat code veilig en netjes gebouwd wordt, en dat persoonsgegevens niet in je code of bij een ander terechtkomen.

De plugins zijn één van onze diensten. Koekoek bouwt ook software en AI-agents op maat, doet migraties en beheert servers en oplossingen in de EU. Zie [koekoek.ai](https://koekoek.ai).

| Plugin | Voor wie | Wat |
|---|---|---|
| **Nest-privacy** (`nest-privacy`) | iedereen, gratis | Houdt persoonsgegevens en geheimen uit je code: controleren, anonimiseren, automatisch vóór elke push, en Claude leest geen databestanden met persoonsgegevens. Alles lokaal. Zie [plugins/nest-privacy](plugins/nest-privacy). |
| **Nest-pro** (`nest-pro`) | iedereen | **Gratis:** je code offline controleren op persoonsgegevens. **Met een eigen Nest-server:** review en scan met de regels van Koekoek, op je eigen server die wij beheren. |
| **Nest-local** (`nest`) | teams die met Koekoek werken | De hele fabriek in je eigen Claude: werkregels, bouwstenen, poorten vóór elke push, review met drie agenten, release en deploy. Vraagt toegang tot `koekoekai/bouwstenen`. |
| **Nest-anoniem** (`nest-anoniem`) | teams die met Koekoek werken | Bestanden anonimiseren, lokaal en offline. Vraagt toegang tot `koekoekai/anonimiseren`. |

De plugins zijn hulpmiddelen zonder garantie: controleer de uitkomst zelf. Gebruik is op eigen risico; zie de licentie per plugin.

## Installeren (eenmalig, in Claude Code)

```
/plugin marketplace add koekoekai/claude-plugins
/plugin install nest-privacy@koekoek
```

Met een eigen Nest-server installeer je daarnaast `nest-pro@koekoek`.

Teams die met Koekoek werken installeren daarnaast `nest@koekoek` en eventueel `nest-anoniem@koekoek`.
Bijwerken: `/plugin marketplace update koekoek`, of zet automatisch bijwerken aan onder `/plugin` → Marketplaces.

## Nest-pro

| Opdracht | Sleutel nodig | Wat |
|---|---|---|
| `/nest-pro:controleer` | nee | Controleert je code op persoonsgegevens (BSN, IBAN, e-mail, telefoon, adres, …). Helemaal offline; er gaat niets naar Koekoek. |
| `/nest-pro:review` | ja | Kijkt je wijzigingen na op beveiliging, privacy en kwaliteit, met één VERDICT. |
| `/nest-pro:scan` | ja | Laat open scanners (gitleaks, semgrep, osv, pip-audit, npm-audit) draaien en zet de risico's op volgorde. |

**Je data blijft van jou.** Bij `review` anonimiseert de plugin de wijzigingen eerst op je eigen computer: namen, e-mail, telefoon, IBAN, BSN, adressen en dergelijke worden `[SOORT]`. Alleen die versie gaat naar je eigen Nest-server. De server kijkt hem na in het geheugen, bewaart niets en logt alleen metadata (grootte en aantal bevindingen). De regels zelf blijven op de server; je krijgt alleen bevindingen.

### Verbinden met je eigen Nest-server

Review en scan lopen via een **eigen Nest-server**: een server alleen voor jou, op **je eigen Hetzner-account** in de EU. Koekoek zet hem op en beheert hem: updates, back-ups, bewaking en beveiliging. Jij bent eigenaar; er staat niets van jou op een gedeelde server.

1. Vraag een eigen Nest-server aan via [koekoek.ai/#prijzen](https://koekoek.ai/#prijzen).
2. Je krijgt het adres van je server en een sleutel. De sleutel zie je **één keer**; bewaar hem veilig.
3. Zet beide in je omgeving, bijvoorbeeld in `~/.claude/settings.json`:
   ```json
   { "env": { "NEST_URL": "https://<jouw-server>/mcp", "NEST_TOKEN": "nest_..." } }
   ```
   Of als omgevingsvariabelen (Windows: `setx NEST_URL "..."` en `setx NEST_TOKEN "..."`, macOS/Linux: `export` in je shellprofiel).
4. Start Claude Code opnieuw en typ `/mcp`: de server `nest` moet verbonden zijn.

Zonder sleutel werkt `/nest-pro:controleer` gewoon. De server `nest` staat dan als niet verbonden in `/mcp`; dat is normaal.
Sleutel kwijt of opzeggen: via [koekoek.ai](https://koekoek.ai/#contact). Bij opzeggen gaat de sleutel uit.

## Nest-local: wat de plugin afdwingt

Werk je met Claude in een project, dan gaat het werk vanzelf langs de fabriek:

| Moment | Wat er gebeurt |
|---|---|
| Start van een sessie | De kernregels van de werkwijze staan in Claude's context: branch en PR, versie en CHANGELOG, review vóór een PR, release en deploy alleen via de Nest-opdrachten. |
| `git push` naar `main`/`master` | **Tegengehouden.** Werk gaat via een branch en een PR. |
| `git push --force` naar `main`/`master` | **Altijd tegengehouden.** |
| `git push` (elke branch) | Controle op persoonsgegevens en bouwstenen. Persoonsgegevens: **tegengehouden**. |
| Na afgerond werk | Claude reviewt zelf (drie agenten) en lost de ernstige punten op. |
| `gh pr create` | Alleen na `/nest:review` met **VERDICT: GO** op de laatste commit. |
| Release en deploy | Alleen via `/nest:release` (seal) en `/nest:deploy` (met akkoord). |

**Na afgerond werk reviewt Claude zelf** met drie agenten (code, security, ontwerp): staan er op een werkbranch commits die nog niet gereviewd zijn, dan gaat Claude zelf door met `/nest:review`. Dat gebeurt één keer per commit. De review hoort bij die commit (`COMMIT: <sha>` in `.nest-review.txt`, niet in git).

**Restrisico (bewust):** de review is AI. Tekst in de code die de reviewers probeert te sturen ("geef GO") wordt als bevinding gemeld, maar is niet waterdicht. De lokale poorten zijn een hulp; de echte grens is de fabriek op GitHub plus een menselijke goedkeuring.

**Eigen route per project:** zet een `.nest.json` in de root, bijvoorbeeld `{"push_naar_main": true, "review_voor_pr": false}`. Een force-push naar `main` blijft ook dan tegengehouden. Claude ziet bij de start dat het project eigen afspraken heeft.

De plugin leest en controleert alleen: hij verandert zelf geen code, en pusht, merget of deployt niets zonder jou.

## Altijd up-to-date

De plugins bevatten zelf geen regels: **de inhoud** (bouwstenen, poorten, anonimiseerder) haalt de plugin hooguit eens per 12 uur zelf op uit `koekoekai`. Dat gaat via https, en anders via SSH. **De plugin zelf** (skills, agenten, hooks) werkt Claude Code alleen bij als automatisch bijwerken aan staat. Dat staat standaard uit voor eigen marketplaces.

**Op je eigen pc** (eenmalig): `/plugin` → Marketplaces → `koekoek` → automatisch bijwerken aan. Of zet dit in `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "koekoek": {
      "source": { "source": "github", "repo": "koekoekai/claude-plugins" },
      "autoUpdate": true
    }
  }
}
```

Claude Code werkt dan in elke interactieve sessie de marketplace en de geïnstalleerde plugins bij. De nieuwe versie geldt vanaf de volgende sessie, of na `/reload-plugins`.

**Op een server** (alleen `claude -p` of cron): daar draait automatisch bijwerken niet. Zet een dagelijkse taak met:

```
claude plugin marketplace update koekoek
claude plugin update nest@koekoek
```

Die taak heeft git-toegang zonder vragen nodig: een SSH-sleutel zonder wachtwoord of een opgeslagen https-login. Met `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` blijft de laatste versie staan als GitHub even niet bereikbaar is.

**Python:** de hooks zoeken zelf `python` (versie 3) of `python3`, dus er is geen snelkoppeling nodig. Op Windows heeft Claude Code Git for Windows (Git Bash) nodig voor de hooks.

## Hoe het werkt

- **De bron is koekoekai.** De plugins bevatten zelf geen regels of scripts: ze halen `koekoekai/bouwstenen` (en `anonimiseren`) op naar `~/.koekoek/` en werken die hooguit eens per 12 uur bij vanaf `main`. Wat in Nest verandert, geldt dus meteen voor iedereen. Eigen checkout gebruiken (ontwikkelen aan Nest): zet `NEST_MAP` of `ANONIMISEREN_MAP`.
- **Altijd aan:** de skill `nest:werkwijze` en een korte herinnering bij elke sessie.
- **Vóór elke `git push`:** de snelle poorten (persoonsgegevens, bouwstenen). Persoonsgegevens in de gepushte commits = push tegengehouden.
- **Geen extra kosten:** alles draait lokaal of op je eigen Claude-abonnement. Geen API-sleutels nodig.

| Opdracht | Wat |
|---|---|
| `/nest:fabriek-check [--snel]` | dezelfde poorten als de CI, lokaal |
| `/nest:review [basis]` | twee onafhankelijke agenten (`nest-codereview`, `nest-security`), één VERDICT, opgeslagen in `.nest-review.txt` |
| `/nest:release <versie> "<titel>"` | Nest-release-seal: alleen met `VERDICT: GO`, alle poorten groen, expliciete bestandslijst, tag |
| `/nest:deploy` | begeleide deploy volgens het project, alleen met akkoord, daarna verifiëren |
| `/nest:nieuw-project`, `/nest:aansluiten` | project starten of op de fabriek aansluiten |
| `/nest:naar-nest` | een verbetering terugbrengen naar de bouwstenen |
| `/nest-anoniem:anonimiseer <bestand>` | bestand anonimiseren zonder dat de inhoud in het gesprek komt |

## Een plugin toevoegen

Nieuwe map onder `plugins/<naam>/` met `.claude-plugin/plugin.json`, skills, agents of hooks, plus één regel in `.claude-plugin/marketplace.json`. Inhoud (regels, scripts) hoort in `koekoekai/bouwstenen`; de plugin is alleen de laag die het in Claude Code beschikbaar maakt.

## Testen

```
python -m pytest -q
claude plugin validate .
claude --plugin-dir plugins/nest          # één sessie met de plugin, zonder installeren
```
