# Werkregels voor agents (Claude, Codex)

Openbare repo van Koekoek met Claude Code-plugins. Schrijf in het Nederlands, in korte, gewone zinnen.

## Samenwerken via de Agent Hub

Claude verdeelt het werk en doet de eindcontrole. Codex bouwt, test en reviewt in een eigen Git-worktree. De eigenaar is `owner`.

1. Lees bij het begin `hub_status` en `inbox`.
2. Werk alleen in de worktree uit je taak. Reserveer extra bestanden met `lock_files`.
3. Zet de taak na het testen op `review`. Zet in `result`: gewijzigde bestanden, uitgevoerde tests en de uitkomst.
4. Moet iemand iets doen of beslissen, stuur dan `msg_send` of zet de taak op `blocked` met de reden.

## Wat nooit mag

- Niet pushen, niet mergen, niets live zetten. Dat doet Claude, en alleen na akkoord van de eigenaar.
- Geen geheimen tonen of opslaan (tokens, sleutels, `.env`). Gebruik in tests nepwaarden die je in delen opbouwt.
- Geen echte persoonsgegevens of klantdata lezen of in de repo zetten. Testdata is verzonnen.
- Niets buiten je worktree wijzigen. Geen pakketten systeembreed installeren.
- Geen regels, prompts of bouwstenen van Nest in de openbare plugins zetten.
- `plugins/*/scripts/anonimiseren.py` is een kopie van de Nest-bouwsteen: niet hier wijzigen, maar het voorstel melden.

## Testen

- `python -m pytest -q` (gebruik `NEST_PRIVACY_HERKENNER=regels` als er geen taalmodel is).
- Meting: `python tests/namen/grote_set.py 300 --meet` en `--blind`. Stem niet af op de blinde set; meld eerlijk wat je ziet.

## Review

Geef bij een review per bevinding: bestand en regel, wat er mis is, een concreet scenario waarin het fout gaat, en hoe ernstig (hoog, middel, laag). Geen stijlpunten. Wijzig bij een review geen code, tenzij de taak dat vraagt.
