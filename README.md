# Koekoek Claude Code-plugins

Privé plugin-catalogus van Koekoek. Ieder werkt met zijn **eigen Claude-account**; de plugins zorgen dat iedereen op dezelfde manier werkt: volgens de software factory in [`koekoekai/bouwstenen`](https://github.com/koekoekai/bouwstenen) (Nest).

| Plugin | Wat | |
|---|---|---|
| **nest** | werkregels, bouwstenen, CI/CD-poorten vóór elke push, code- en security-review met eigen agenten, release-seal, begeleide deploy, nieuw project, aansluiten | standaard |
| **nest-anoniem** | data anonimiseren (BSN, IBAN, adres, namen, …) lokaal en offline, met [`koekoekai/anonimiseren`](https://github.com/koekoekai/anonimiseren) | optioneel |

## Installeren (eenmalig, in Claude Code)

```
/plugin marketplace add koekoekai/claude-plugins
/plugin install nest@koekoek
/plugin install nest-anoniem@koekoek        # optioneel
```

Je hebt leesrechten nodig op deze repo en op `koekoekai/bouwstenen` (en `koekoekai/anonimiseren` voor nest-anoniem). Je git moet zonder vragen kunnen inloggen bij GitHub (bijv. Git Credential Manager of `gh auth setup-git`).
Bijwerken: `/plugin marketplace update koekoek`, of zet automatisch bijwerken aan onder `/plugin` → Marketplaces.

## Wat de plugin afdwingt

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
