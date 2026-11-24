"""Pseudoniemen met terugzetten, helemaal lokaal.

    python pseudoniem.py maak <invoer> -o <uitvoer>            # persoonsgegevens -> [SOORT-code], tabel lokaal bewaard
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

import json
import re
import secrets
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anonimiseren  # noqa: E402
import kluis  # noqa: E402

BEWAARTERMIJN = 30 * 86400
CODE = re.compile(r"\[[A-Z]+-[0-9a-f]{12}\]")


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


def maak(invoer: Path, uitvoer: Path) -> tuple[dict, int]:
    """Pseudonimiseert het bestand en bewaart de vertaaltabel. Geeft (aantallen per soort, aantal codes in de tabel)."""
    tabel: dict[str, str] = {}
    origineel = anonimiseren._vervanging

    def onthoud(soort: str, waarde: str, modus: str, sleutel_: bytes | None) -> str:
        code = origineel(soort, waarde, modus, sleutel_)
        tabel.setdefault(code, waarde)
        return code

    tekst = invoer.read_text(encoding="utf-8-sig")
    anonimiseren._vervanging = onthoud  # tijdelijk: zelfde vervanging, maar we onthouden de waarde
    try:
        if invoer.suffix.lower() == ".csv":
            r = anonimiseren.anonimiseer_csv(tekst, modus="pseudoniem", sleutel=sleutel())
        else:
            r = anonimiseren.anonimiseer(tekst, modus="pseudoniem", sleutel=sleutel())
    finally:
        anonimiseren._vervanging = origineel
    uitvoer.write_text(r.tekst, encoding="utf-8", newline="")
    if tabel:
        kluis.bewaar(f"tabellen/{int(time.time())}-{secrets.token_hex(4)}.tabel", json.dumps(tabel).encode())
    return dict(r.vondsten), len(tabel)


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

    uitvoer.write_text(CODE.sub(vervang, tekst), encoding="utf-8", newline="")
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
    pos = [a for i, a in enumerate(argv[1:], 1) if not a.startswith("-") and argv[i - 1] != "-o"]
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
        vondsten, codes = maak(invoer, uitvoer)
        samenvatting = ", ".join(f"{s} {n}" for s, n in sorted(vondsten.items())) or "niets gevonden"
        print(f"vervangen: {samenvatting} · {codes} code(s) in de lokale vertaaltabel · uitvoer: {uitvoer.name}")
    else:
        terug, onbekend = terugzetten(invoer, uitvoer)
        print(f"teruggezet: {terug} · onbekende codes: {onbekend} · uitvoer: {uitvoer.name} "
              "(bevat weer persoonsgegevens: niet in de chat lezen)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
