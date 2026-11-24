"""PreToolUse-hook van Nest-privacy: voorkomt dat Claude een databestand met persoonsgegevens leest.

Leest Claude een bestand, dan gaat de inhoud naar het model. Voor databestanden (CSV, TSV, TXT, LOG, JSON, XML, EML, …)
kijkt deze hook eerst lokaal of er persoonsgegevens in staan. Zo ja: exit 2, Claude leest het bestand niet en krijgt het advies
om eerst te anonimiseren (/nest-privacy:anonimiseer). Toont nooit de gevonden waarden.

Code-bestanden worden niet tegengehouden (daar zorgt de push-hook voor). Uitzonderen kan met een patroon in .nest-pii-negeer.
Grens: dit houdt de Read-tool tegen, niet elke andere manier van lezen (bijv. een shell-opdracht). Draait lokaal.
"""
import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

DATA = {".csv", ".tsv", ".txt", ".log", ".json", ".ndjson", ".jsonl", ".xml", ".eml", ".msg", ".vcf", ".sql", ".tab", ".dat"}
MAX_BYTES = 20_000_000


def _negeer(bestand: Path) -> bool:
    r = subprocess.run(["git", "-C", str(bestand.parent), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode != 0:
        return False
    root = Path(r.stdout.strip())
    lijst = root / ".nest-pii-negeer"
    if not lijst.is_file():
        return False
    try:
        rel = bestand.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return False
    patronen = [p.strip() for p in lijst.read_text(encoding="utf-8", errors="replace").splitlines()
                if p.strip() and not p.startswith("#")]
    return any(fnmatch.fnmatch(rel, p) for p in patronen)


def main() -> int:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    pad = (data.get("tool_input") or {}).get("file_path", "")
    if not pad:
        return 0
    bestand = Path(pad) if os.path.isabs(pad) else Path(data.get("cwd") or ".") / pad
    import kluis
    if bestand.resolve().suffix.lower() == ".tabel" or bestand.resolve() == (kluis.MAP / "sleutel").resolve():
        return 2
    if bestand.suffix.lower() not in DATA or not bestand.is_file() or bestand.stat().st_size > MAX_BYTES:
        return 0
    try:
        if _negeer(bestand):
            return 0
        import gevoelig

        tekst = bestand.read_bytes().decode("utf-8", errors="replace")
        soorten = sorted({soort for _, _, soort in gevoelig.vind(tekst)})
    except Exception:  # noqa: BLE001 - nooit blokkeren door een eigen fout
        return 0
    if not soorten:
        return 0
    print(f"Nest-privacy: {bestand.name} bevat mogelijk persoonsgegevens ({', '.join(soorten)}). Het is niet gelezen, zodat de "
          "inhoud niet naar het model gaat. Maak eerst een anonieme versie met /nest-privacy:anonimiseer en lees die. "
          "Is het nepdata? Zet dan een patroon in .nest-pii-negeer.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
