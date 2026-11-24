"""Pseudoniemen met terugzetten, helemaal lokaal.

    python pseudoniem.py maak <invoer> -o <uitvoer>            # persoonsgegevens -> [SOORT-code], tabel lokaal bewaard
    python pseudoniem.py maak <invoer> -o <uitvoer> --maskeren # persoonsgegevens -> [SOORT], niet terug te zetten, geen tabel
    python pseudoniem.py maak <invoer> -o <uitvoer> --ook bedrag,organisatie,plaats   # ook die (standaard blijven ze staan)
    python pseudoniem.py terugzetten <invoer> -o <uitvoer>     # [SOORT-code] -> echte waarden (uitvoer bevat weer persoonsgegevens!)
    python pseudoniem.py wis [--alles]                         # tabellen ouder dan 30 dagen weg, of alles

Hoe het werkt:
- De sleutel wordt bij het eerste gebruik willekeurig gemaakt en staat alleen op deze computer (zie kluis.py).
  Dezelfde persoon krijgt zo overal dezelfde code, ook in een volgend bestand.
- Bij `maak` bewaart het script een vertaaltabel (code -> echte waarde), beschermd op deze computer. De tabel verlaat de
  computer nooit en Claude ziet hem niet: het script meldt alleen aantallen.
- Tabellen ouder dan 30 dagen worden bij elk gebruik vanzelf gewist. `wis --alles` gooit ze nu weg.
Toont nooit waarden; alleen aantallen. Alleen de standaardbibliotheek.
"""
from __future__ import annotations

import csv
import io
import os
import tempfile
import hmac
import json
import re
import secrets
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anonimiseren  # noqa: E402
import kluis  # noqa: E402
import gevoelig  # noqa: E402

BEWAARTERMIJN = 30 * 86400
CODE = re.compile(r"\[[A-Z]+-[0-9a-f]{12}\]")
NAAMKOLOM = re.compile(r"(?i)^(?:naam|name|voornaam|achternaam|tussenvoegsel|first[_ ]?name|last[_ ]?name|full[_ ]?name|klant(?:naam)?|contact(?:persoon)?|customer(?:[_ ]?name)?|client(?:[_ ]?name)?|patiënt|patient|medewerker|employee|aanvrager|afzender|sender)$")


def sleutel() -> bytes:
    s = kluis.lees("sleutel")
    if not s:
        s = secrets.token_bytes(32)
        kluis.bewaar("sleutel", s)
    return s


def opruimen(alles: bool = False) -> int:
    map_ = kluis.MAP / "tabellen"
    if not map_.is_dir():
        return 0
    weg = 0
    for f in map_.glob("*.tabel"):
        if alles or time.time() - f.stat().st_mtime > BEWAARTERMIJN:
            f.unlink()
            weg += 1
    return weg


def maak(invoer: Path, uitvoer: Path, maskeren: bool = False, extra: tuple[str, ...] = ()) -> tuple[dict, int]:
    """Pseudonimiseert (of maskeert) alle AVG-gevoelige gegevens en bewaart bij pseudoniemen de vertaaltabel.
    extra: ook BEDRAG, ORGANISATIE en/of PLAATS (geen persoonsgegevens, standaard blijven ze staan).
    Geeft (aantallen per soort, aantal codes in de tabel)."""
    tabel: dict[str, str] = {}
    origineel = anonimiseren._vervanging

    def onthoud(soort: str, waarde: str, modus: str, sleutel_: bytes | None) -> str:
        code = origineel(soort, waarde, modus, sleutel_)
        if modus == "pseudoniem":
            if waarde != anonimiseren._normaliseer(soort, waarde):
                digest = hmac.digest(sleutel_, ("exact:" + soort + ":" + waarde).encode(), "sha256").hex()
                code = f"[{soort}-{digest[:12]}]"
            tabel.setdefault(code, waarde)
        return code

    tekst = invoer.read_text(encoding="utf-8-sig")
    opties = {"modus": "maskeren"} if maskeren else {"modus": "pseudoniem", "sleutel": sleutel()}
    anonimiseren._vervanging = onthoud  # tijdelijk: zelfde vervanging, maar we onthouden de waarde
    try:
        if invoer.suffix.lower() == ".csv":
            try:
                sep = csv.Sniffer().sniff(tekst[:8192], delimiters=",;\t").delimiter
            except csv.Error:
                sep = ","
            kolommen = next(csv.reader(io.StringIO(tekst), delimiter=sep), [])
            r = anonimiseren.anonimiseer_csv(tekst, naam_kolommen=[k for k in kolommen if NAAMKOLOM.match(k)],
                                             scheidingsteken=sep, **opties)
            stroom = io.StringIO(newline="")
            schrijver = csv.writer(stroom, delimiter=sep, lineterminator="\n")
            for rij in csv.reader(io.StringIO(r.tekst, newline=""), delimiter=sep):
                nieuw = []
                for cel in rij:
                    uit, telling = gevoelig.vervang(cel, extra=extra, **opties)
                    r.vondsten.update(telling)
                    nieuw.append(uit)
                schrijver.writerow(nieuw)
            r = anonimiseren.Resultaat(stroom.getvalue(), r.vondsten)
        else:
            # alle AVG-soorten: onze controles, namen, taalmodel, bijzondere persoonsgegevens en de eigen woordenlijst
            uit, telling = gevoelig.vervang(tekst, extra=extra, **opties)
            r = anonimiseren.Resultaat(uit, anonimiseren.Counter(telling))
    finally:
        anonimiseren._vervanging = origineel
    if maskeren:
        tabel.clear()
    if tabel:
        kluis.bewaar(f"tabellen/{int(time.time())}-{secrets.token_hex(4)}.tabel", json.dumps(tabel).encode())
    _schrijf(uitvoer, r.tekst)
    return dict(r.vondsten), len(tabel)


def _schrijf(pad: Path, tekst: str) -> None:
    fd, tijdelijk = tempfile.mkstemp(dir=pad.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as bestand:
            bestand.write(tekst)
        os.replace(tijdelijk, pad)
    finally:
        Path(tijdelijk).unlink(missing_ok=True)


def alle_tabellen() -> dict[str, str]:
    samen: dict[str, str] = {}
    map_ = kluis.MAP / "tabellen"
    for f in sorted(map_.glob("*.tabel")) if map_.is_dir() else []:
        data = kluis.lees(f"tabellen/{f.name}")
        if data:
            samen.update(json.loads(data))
    return samen


def terugzetten(invoer: Path, uitvoer: Path) -> tuple[int, int]:
    """Zet codes terug naar de echte waarden. Geeft (teruggezet, onbekend)."""
    tabel = alle_tabellen()
    tekst = invoer.read_text(encoding="utf-8-sig")
    teller = {"terug": 0, "onbekend": 0}

    def vervang(m: re.Match) -> str:
        if m.group(0) in tabel:
            teller["terug"] += 1
            return tabel[m.group(0)]
        teller["onbekend"] += 1
        return m.group(0)

    _schrijf(uitvoer, CODE.sub(vervang, tekst))
    return teller["terug"], teller["onbekend"]


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] not in ("maak", "terugzetten", "wis"):
        print(__doc__)
        return 2
    opgeruimd = opruimen()
    if argv[0] == "wis":
        weg = opgeruimd + opruimen(alles="--alles" in argv)
        print(f"Gewist: {weg} vertaaltabel(len).")
        return 0
    pos = [a for i, a in enumerate(argv[1:], 1) if not a.startswith("-") and argv[i - 1] not in ("-o", "--ook")]
    if not pos or "-o" not in argv or argv.index("-o") + 1 >= len(argv):
        print(f"Gebruik: pseudoniem.py {argv[0]} <invoer> -o <uitvoer>", file=sys.stderr)
        return 2
    invoer, uitvoer = Path(pos[0]), Path(argv[argv.index("-o") + 1])
    if not invoer.is_file():
        print("Invoerbestand niet gevonden.", file=sys.stderr)
        return 2
    if invoer.resolve() == uitvoer.resolve():
        print("Kies een ander uitvoerbestand dan het invoerbestand.", file=sys.stderr)
        return 2
    if argv[0] == "maak":
        ook = argv[argv.index("--ook") + 1].upper().split(",") if "--ook" in argv and argv.index("--ook") + 1 < len(argv) else []
        extra = tuple(o for o in ook if o in gevoelig.OPTIONEEL)
        vondsten, codes = maak(invoer, uitvoer, maskeren="--maskeren" in argv, extra=extra)
        samenvatting = ", ".join(f"{s} {n}" for s, n in sorted(vondsten.items())) or "niets gevonden"
        print(f"vervangen: {samenvatting} · {codes} code(s) in de lokale vertaaltabel · uitvoer: {uitvoer.name}")
    else:
        terug, onbekend = terugzetten(invoer, uitvoer)
        print(f"teruggezet: {terug} · onbekende codes: {onbekend} · uitvoer: {uitvoer.name} "
              "(bevat weer persoonsgegevens: niet in de chat lezen)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
