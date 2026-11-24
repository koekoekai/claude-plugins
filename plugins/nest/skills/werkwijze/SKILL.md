---
name: werkwijze
description: De Nest-werkwijze van Koekoek voor elk stuk code in een Koekoek-project. Gebruik bij bouwen, fixen, reviewen, releasen of een nieuw project, en als het gaat over bouwstenen, de fabriek, CHANGELOG, versies, beveiliging, AVG of persoonsgegevens.
---

# Nest-werkwijze (Koekoek)

Nest (repo `koekoekai/bouwstenen`) is de software factory van Koekoek. De plugin haalt Nest zelf op en houdt hem bij; het pad krijg je met `python "${CLAUDE_PLUGIN_ROOT}/scripts/nest.py" pad`.
Lees bij twijfel de standaard van het onderwerp: `<nest>/<onderwerp>/README.md` (security, website, pwa, formulieren, server, updates, avg, ai, lokale-tool, fabriek, anonimiseren, …).

## Elke wijziging
1. **Op een branch, via een pull request.** Nooit direct op `main`. De PR gaat door de fabriek: tests, veiligheidscheck, bouwstenen, persoonsgegevens, Semgrep, gitleaks, audit, AI-review, en een mens keurt goed.
2. **Versie omhoog** (semver, op één plek: `package.json`, `pyproject.toml` of `VERSION.txt`) en **een regel bovenaan `CHANGELOG.md`**:
   `## 1.4.2 · DD-MM-JJJJ · Korte titel` met daaronder in gewone taal wat de gebruiker merkt.
3. **Tests groen**; bij een nieuwe route ook een aanvalstest. Een controle zwak je nooit af om hem groen te krijgen.
4. **Commit** `1.4.2 Korte titel`, in het Nederlands. Commit met een expliciete bestandslijst, nooit `git add -A` in scripts.
5. Live zetten alleen na akkoord van de eigenaar van het project, per project en elke keer opnieuw.

## Bouwstenen
- **Eerst kijken wat er al is.** Gaat het om beveiliging, limieten, formulieren, PWA, push, anonimiseren of een lokale tool, gebruik dan de bouwsteen: `/nest:bouwsteen <naam>` (lijst: in je context bij de start, of `nest.py bouwstenen`). Niet opnieuw schrijven wat al getest bestaat.
- Een bestand met een regel `bouwsteen: <naam> <versie>` bovenaan komt uit Nest. **Niet in het project verbeteren**: eerst in Nest (code, tests, versie in de marker én in `catalogus.json`, regel in de Nest-CHANGELOG), daarna terugkopiëren.
- Iets goeds gebouwd, een valkuil ontdekt of een nieuwe check gemaakt die breder bruikbaar is? Stel aan het eind van het werk voor het naar Nest te brengen (`/nest:naar-nest`).
- Nieuw project: `/nest:nieuw-project`. Bestaand project op de fabriek: `/nest:aansluiten`.

## Review, release en deploy (lokaal, op je eigen Claude-account)
- Vóór een PR of release: `/nest:review` (twee onafhankelijke agenten: code en security, met één VERDICT).
- Release: `/nest:release <versie> "<titel>"` (de Nest-seal: alleen met `VERDICT: GO`, alle poorten groen, expliciete bestandslijst, tag).
- Live: `/nest:deploy` (alleen met akkoord, daarna verifiëren en weten hoe je terugdraait).

## Veiligheid (kort; volledig: security/claude/claude-security-guidance.md en security/CHECKS.md)
- Elke query op gebruikersdata filtert op de eigenaar; een id uit URL of body altijd tegen het ingelogde account controleren.
- Login en rol op de server; de server negeert rol, prijs, eigenaar en status van de client.
- Alleen prepared statements; geen SQL met f-strings of `+`.
- Geen inline scripts (CSP `script-src 'self'`); geen shell met invoer (`shell: false` of een strikte witte lijst).
- Sleutels alleen uit de omgeving of een kluis; nooit in code, front-end of tests.
- Logs en foutmeldingen zonder persoonsgegevens, stack traces of geheimen.
- Lokale tools (draaien op de eigen pc en openen in de browser): volg `<nest>/lokale-tool/README.md`. Alleen 127.0.0.1, Host- en Origin-check op elke API-route, schrijfacties met eigen kop of token, geen shell met invoer, geheimen in de Windows-kluis, Excel-export zonder formule-injectie, versie zichtbaar in de app.

## Persoonsgegevens en AVG
- Nooit echte klantdata in code, tests, fixtures, logs of issues. Testdata is nep (bijv. `111222333`, `NL91ABNA0417164300`, `…@voorbeeld.nl`).
- Echte data nodig voor analyse of een AI? Eerst anonimiseren: `/nest-anoniem:anonimiseer` (plugin nest-anoniem). Pseudoniemen alleen met de sleutel uit de kluis.
- De fabriek blokkeert een PR met persoonsgegevens; markeer echte nepdata met `pii: ok` of in `.nest-pii-negeer`.

## Stijl
- Communicatie, commits en documentatie in het Nederlands, in gewone taal.
- Nooit hard-coded personen, bedrijven, domeinen of servers: via instellingen met een veilige standaard.
- Geen werkgevernamen in Koekoek-code (de veiligheidscheck controleert dit met een lokale lijst).

_Python: gebruik `python`; bestaat die niet (Linux-servers), gebruik dan `python3`._
