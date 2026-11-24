"""Eén ingang voor de Nest-plugin: zoekt bouwstenen (zie bron.py) en draait het juiste script.

    python nest.py pad                         # waar Nest staat (om standaarden te lezen)
    python nest.py bouwstenen [--stack python] # welke bouwstenen er zijn (naam, versie, wat)
    python nest.py bouwsteen <naam> [doel]     # een bouwsteen in het huidige project zetten (met versieregel)
    python nest.py fabriek-check [--snel]      # fabriek/lokaal.py in het huidige project
    python nest.py aansluiten [map] [--schrijf]
    python nest.py nieuw-project "<naam>" --soort … --stack …
    python nest.py bouwstenen-check            # welke projecten achterlopen
    python nest.py bijwerken                   # Nest nu meteen bijwerken
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bron import vind  # noqa: E402

SCRIPTS = {
    "fabriek-check": "fabriek/lokaal.py",
    "aansluiten": "fabriek/aansluiten.py",
    "nieuw-project": "scripts/nieuw_project.py",
    "bouwstenen-check": "scripts/bouwstenen_check.py",
}


# Onderdelen van de fabriek zelf (komen via /nest:aansluiten) en van Claude/Nest: niet tonen als bouwsteen voor een project.
GEREEDSCHAP = ("fabriek/", "security/claude", "security/env-namen", "website/fragmentcheck")


def catalogus(nest: Path) -> dict:
    """De bouwstenen uit catalogus.json; alleen regels die een dict zijn. Kapot of ontbrekend: lege catalogus."""
    try:
        cat = json.loads((nest / "catalogus.json").read_text(encoding="utf-8")).get("bouwstenen", {})
    except (OSError, ValueError, AttributeError):
        return {}
    return {n: b for n, b in cat.items() if isinstance(b, dict)} if isinstance(cat, dict) else {}


def stacks_van(map_: Path) -> set[str]:
    """Stack van een project: package.json -> node (+ browser), requirements/pyproject -> python."""
    s = set()
    if (map_ / "package.json").exists():
        s |= {"node", "browser"}
    if any((map_ / n).exists() for n in ("requirements.txt", "pyproject.toml", "setup.py")):
        s.add("python")
    return s


def _schoon(tekst: object, max_: int) -> str:
    """Eén regel platte tekst: geen regeleinden of stuurtekens (die zouden in Claude's context als extra regel lezen)."""
    t = re.sub(r"[\x00-\x1f\x7f\u2028\u2029]+", " ", str(tekst)).strip()
    return t if len(t) <= max_ else t[: max_ - 1] + "…"


def lijst(nest: Path, stacks: set[str] | None = None, breed: int = 110, voor_project: bool = False, maximum: int = 0) -> list[str]:
    """Eén regel per bouwsteen: naam versie (stack): wat. Met `stacks` alleen wat bij het project past (+ 'alle').
    Alle velden worden opgeschoond: de catalogus is gegevens, geen instructie."""
    regels = []
    for naam, b in sorted(catalogus(nest).items()):
        if not re.fullmatch(r"[a-z0-9][\w/-]{0,60}", naam) or not re.fullmatch(r"\d+\.\d+\.\d+", str(b.get("versie", ""))):
            continue
        if stacks and b.get("stack") not in stacks | {"alle"}:
            continue
        if (stacks or voor_project) and naam.startswith(GEREEDSCHAP):  # Nest-gereedschap, geen bouwsteen voor een project
            continue
        regels.append(f"- {naam} {b['versie']} ({_schoon(b.get('stack', ''), 12)}): {_schoon(b.get('wat', ''), breed)}")
    if maximum and len(regels) > maximum:
        regels = regels[:maximum] + [f"- … en {len(regels) - maximum} meer: nest.py bouwstenen"]
    return regels


def zet_bouwsteen(nest: Path, naam: str, doel: str | None, project: Path, overschrijf: bool = False) -> Path:
    cat = catalogus(nest)
    if naam not in cat:
        deel = naam.rstrip("/").split("/")[-1]
        dichtbij = [n for n in cat if deel and deel in n]
        raise SystemExit(f"Onbekende bouwsteen {naam!r}." + (f" Bedoel je: {', '.join(dichtbij)}?" if dichtbij else ""))
    nest_echt, project_echt = nest.resolve(), project.resolve()
    bron = (nest / cat[naam]["pad"]).resolve()
    if not bron.is_relative_to(nest_echt) or (nest / cat[naam]["pad"]).is_symlink() or not bron.is_file():
        raise SystemExit(f"Het pad van {naam!r} in de catalogus wijst niet naar een gewoon bestand in Nest; niets gezet.")
    doelpad = project / (doel or Path(cat[naam]["pad"]).name)
    if (doel and Path(doel).is_absolute()) or doelpad.is_symlink() or not doelpad.resolve().is_relative_to(project_echt):
        raise SystemExit(f"Doel {doel!r} ligt buiten het project (of is een symlink); kies een pad binnen het project.")
    if ".git" in doelpad.resolve().relative_to(project_echt).parts:
        raise SystemExit("Een bouwsteen hoort niet in .git.")
    if doelpad.exists() and not overschrijf:
        raise SystemExit(f"{doelpad} bestaat al. Vergelijk eerst; overschrijven kan met --overschrijf.")
    marker = f"bouwsteen: {naam} {cat[naam].get('versie', '')}"
    if marker not in bron.read_text(encoding="utf-8", errors="replace")[:600]:
        raise SystemExit(f"De bron van {naam!r} heeft niet de versieregel '{marker}'; Nest is niet in orde, niets gezet.")
    doelpad.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(bron, doelpad)
    return doelpad


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] not in {*SCRIPTS, "pad", "bijwerken", "bouwstenen", "bouwsteen"}:
        print(__doc__)
        return 2
    opdracht, rest = argv[0], argv[1:]
    if opdracht == "bijwerken":
        (Path(os.environ.get("KOEKOEK_MAP") or Path.home() / ".koekoek") / "bouwstenen" / ".koekoek-bijgewerkt").unlink(missing_ok=True)
    nest = vind("bouwstenen")
    if not nest:
        print("Nest (koekoekai/bouwstenen) is niet beschikbaar. Controleer je leesrechten en git-login, of zet NEST_MAP.", file=sys.stderr)
        return 1
    if opdracht in ("pad", "bijwerken"):
        print(nest)
        return 0
    if opdracht in ("bouwstenen", "bouwsteen") and not catalogus(nest):
        print(f"De catalogus van Nest ontbreekt of is kapot ({nest / 'catalogus.json'}). Werk bij met: nest.py bijwerken", file=sys.stderr)
        return 1
    if opdracht == "bouwstenen":
        i = rest.index("--stack") if "--stack" in rest else -1
        if i >= 0 and i + 1 >= len(rest):
            print("Gebruik: nest.py bouwstenen --stack python|node|browser|nginx|systemd", file=sys.stderr)
            return 2
        stacks = {rest[i + 1]} if i >= 0 else None
        print("\n".join(lijst(nest, stacks, breed=1000)))
        return 0
    if opdracht == "bouwsteen":
        pos = [a for a in rest if not a.startswith("--")]
        if not pos:
            print("Gebruik: nest.py bouwsteen <naam> [doelpad]   (namen: nest.py bouwstenen)", file=sys.stderr)
            return 2
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        project = Path(r.stdout.strip()) if r.returncode == 0 else Path.cwd()
        pad = zet_bouwsteen(nest, pos[0], pos[1] if len(pos) > 1 else None, project, "--overschrijf" in rest)
        print(f"Gezet: {pad.relative_to(project) if pad.is_relative_to(project) else pad} "
              f"(bouwsteen {pos[0]} {catalogus(nest)[pos[0]]['versie']}, met versieregel bovenaan)")
        return 0
    script = nest / SCRIPTS[opdracht]
    if not script.exists():
        print(f"{SCRIPTS[opdracht]} staat niet in deze versie van Nest ({nest}). Werk bij met: nest.py bijwerken", file=sys.stderr)
        return 1
    return subprocess.run([sys.executable, str(script), *rest], env={**os.environ, "PYTHONIOENCODING": "utf-8"}).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
