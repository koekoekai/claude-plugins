---
name: nieuw-project
description: Een nieuw Koekoek-project starten met de Nest-startgenerator, met de bouwstenen en de fabriek (CI, AI-review, Dependabot) er meteen in.
argument-hint: "\"<naam>\" --soort website,server-app --stack python|node"
disable-model-invocation: true
---

1. Vraag wat ontbreekt: naam, soort (website, server-app, pwa, push, lokale-tool, server-config), stack (python of node), en de doelmap (standaard `~/code/<slug>`).
2. Laat eerst zien wat er komt (droog, als het script dat ondersteunt; zie `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" nieuw-project -h`), dan:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" nieuw-project $ARGUMENTS`
3. In het nieuwe project: `git init`, eerste commit `0.1.0 Start`, en vertel wat er nog in GitHub moet:
   - repo aanmaken (privé) onder de Koekoek-eigenaar;
   - secrets `NEST_TOKEN` en `CLAUDE_CODE_OAUTH_TOKEN` (of `ANTHROPIC_API_KEY`), tenzij ze op organisatieniveau staan;
   - de Claude GitHub App op de repo.
4. Het project komt in Nest `projecten.json` (het script stelt dat voor); dat gaat als PR naar Nest.

_Python: gebruik `python`; bestaat die niet (Linux-servers), gebruik dan `python3`._
