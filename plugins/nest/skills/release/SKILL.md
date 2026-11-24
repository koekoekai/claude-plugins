---
name: release
description: Een release maken met de Nest-release-seal: versie, CHANGELOG, review met VERDICT: GO, alle poorten groen, commit van een expliciete bestandslijst en een tag. Lokaal, zonder API-sleutel. Pushen pas na akkoord.
argument-hint: "<versie> \"<titel>\""
disable-model-invocation: true
---

Standaard: `<nest>/updates/README.md`, "Release met seal" (`<nest>` = `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" pad`).

1. Versie en titel uit `$ARGUMENTS`; ontbreekt iets, vraag het (semver, hoger dan de vorige tag).
2. Zet de versie op één plek (`package.json`, `pyproject.toml` of `VERSION.txt`) en een regel bovenaan `CHANGELOG.md`:
   `## <versie> · <DD-MM-JJJJ> · <titel>` met daaronder in gewone taal wat de gebruiker merkt. Laat de tekst zien en vraag akkoord.
3. Bepaal de **expliciete bestandslijst** voor de commit (`git status --short`): alleen wat bij deze release hoort, nooit alles blind. Laat de lijst zien.
4. Review: bestaat `.nest-review.txt` niet of noemt hij niet de huidige commit (`COMMIT: <sha>`), draai eerst `/nest:review`. Alleen een exacte `VERDICT: GO` telt.
5. Seal, eerst droog:
   `python "<nest>/fabriek/seal.py" <versie> "<titel>" --review .nest-review.txt --droog -- <bestanden…>`
   Daarna zonder `--droog`. Elke ROOD-regel: stoppen, uitleggen, oplossen. Nooit een controle omzeilen.
6. De seal maakt een lokale commit en tag; daarmee hoort de review niet meer bij de laatste commit. Draai daarom
   `/nest:review` nog één keer (alleen versie en CHANGELOG zijn veranderd, dus dat gaat snel) vóór je een PR opent.
7. Vraag akkoord voor pushen (`git push` en `git push origin v<versie>`, of via een PR als `main` beschermd is). Live zetten is een aparte stap: `/nest:deploy`.

_Python: gebruik `python`; bestaat die niet (Linux-servers), gebruik dan `python3`._
