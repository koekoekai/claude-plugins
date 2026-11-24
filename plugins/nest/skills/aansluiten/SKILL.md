---
name: aansluiten
description: Een bestaand Koekoek-project op de software factory aansluiten (CI met de bouwstenen, AI-review, Dependabot, PR-sjabloon), zonder bestaande bestanden te overschrijven.
argument-hint: "[projectmap]"
disable-model-invocation: true
---

Projectmap: `$ARGUMENTS`, of anders de huidige git-root.

1. Droog: `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" aansluiten <map>` en laat zien wat er nieuw komt en wat al bestaat.
2. Bestanden die al bestaan: vergelijk met de sjablonen in `<nest>/fabriek/sjabloon/` (`<nest>` = uitvoer van `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" pad`) en stel een samenvoeging voor; overschrijf niets zonder akkoord.
3. Na akkoord: maak een branch `fabriek-aansluiten`, draai `nest.py aansluiten <map> --schrijf`, controleer `python`/`node` in `.github/workflows/ci.yml`, en draai `/nest:fabriek-check --snel`.
4. Commit met expliciete bestandslijst, versie omhoog en CHANGELOG-regel volgens de werkwijze. Pushen en een PR openen alleen na akkoord.
5. Staat het project niet in Nest `projecten.json`? Stel de regel voor (naam, repo, soort, stack): dan weet de bouwstenen-poort wat nodig is.
6. Noem wat de gebruiker zelf in GitHub moet doen: secrets `NEST_TOKEN` en `CLAUDE_CODE_OAUTH_TOKEN` (tenzij op organisatieniveau) en de Claude GitHub App.

_Python: gebruik `python`; bestaat die niet (Linux-servers), gebruik dan `python3`._
