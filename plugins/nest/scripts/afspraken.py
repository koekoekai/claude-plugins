"""Nest-afspraken die de hooks afdwingen, en de uitzonderingen per project.

Per project kan `.nest.json` in de root afwijken (bijv. een eigen release-route):
    {"push_naar_main": true,   # direct naar main/master pushen mag (standaard: nee, werk via branch + PR)
     "review_voor_pr": false,  # een PR openen zonder /nest:review (standaard: review met VERDICT: GO verplicht)
     "review_automatisch": false}  # niet zelf reviewen na afgerond werk (standaard: wel)
Een force-push naar main/master blijft altijd tegengehouden.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

HOOFDTAKKEN = {"main", "master"}
STANDAARD = {"push_naar_main": False, "review_voor_pr": True, "review_automatisch": True}


def git(map_: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(map_), *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def projectroot(map_: Path) -> Path | None:
    top = git(map_, "rev-parse", "--show-toplevel")
    return Path(top) if top else None


def instellingen(root: Path) -> dict:
    pad = root / ".nest.json"
    try:
        eigen = json.loads(pad.read_text(encoding="utf-8")) if pad.exists() else {}
    except (ValueError, OSError):
        eigen = {}
    return {**STANDAARD, **{k: v for k, v in eigen.items() if k in STANDAARD and isinstance(v, bool)}}


def _naar_tak(ref: str, huidige: str) -> str:
    ref = ref.lstrip("+")
    if ":" in ref:
        ref = ref.split(":", 1)[1]
    if ref in ("HEAD", "@", ""):
        ref = huidige
    return ref.removeprefix("refs/heads/")


def push_doelen(opdracht: str, root: Path) -> tuple[set[str], bool]:
    """Welke takken een `git push` raakt, en of het een force-push is. Bij twijfel: de hoofdtak (veilige kant)."""
    try:
        delen = shlex.split(opdracht, posix=True)
    except ValueError:
        return set(HOOFDTAKKEN), False
    try:
        i = next(j for j, d in enumerate(delen) if d == "push" and j > 0 and "git" in delen[j - 1:j] + delen[max(0, j - 3):j])
    except StopIteration:
        return set(), False
    rest = []
    for d in delen[i + 1:]:
        if d in ("&&", "||", ";", "|"):
            break
        rest.append(d)
    force = any(d in ("-f", "--force") or d.startswith("--force-with-lease") or d.startswith("--force-if-includes") for d in rest)
    if any(d in ("--all", "--mirror") for d in rest):
        return set(HOOFDTAKKEN), force
    posities = [d for d in rest if not d.startswith("-")]
    huidige = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    refs = posities[1:]  # posities[0] is de remote
    force = force or any(r.startswith("+") for r in refs)
    if not refs:
        return {huidige or "main"}, force
    return {_naar_tak(r, huidige) for r in refs}, force


def review_voor_head(root: Path) -> tuple[str | None, str]:
    """De tekst van .nest-review.txt als die bij de huidige commit hoort, anders (None, reden).
    Telt alleen als het bestand NIET in git staat (een meegecommitte 'review' van iemand anders telt nooit) en een regel
    `COMMIT: <sha>` heeft die gelijk is aan HEAD. De wijzigingsdatum van het bestand telt niet (die verandert bij uitchecken)."""
    pad = root / ".nest-review.txt"
    if not pad.is_file():
        return None, "er is nog geen review (.nest-review.txt ontbreekt)"
    if git(root, "ls-files", "--", ".nest-review.txt"):
        return None, ".nest-review.txt staat in git; een meegecommitte review telt niet"
    tekst = pad.read_text(encoding="utf-8", errors="replace")
    head = git(root, "rev-parse", "HEAD")
    commits = {r.split(":", 1)[1].strip() for r in tekst.splitlines() if r.startswith("COMMIT:")}
    if not head or head not in commits:
        return None, "de review hoort niet bij de laatste commit"
    return tekst, ""


def review_is_vers(root: Path) -> tuple[bool, str]:
    """Een review van de huidige commit met exact 'VERDICT: GO' en nergens NO-GO."""
    tekst, reden = review_voor_head(root)
    if tekst is None:
        return False, reden
    if "VERDICT: NO-GO" in tekst or "VERDICT: GO" not in [r.strip() for r in tekst.splitlines()]:
        return False, "de laatste review gaf geen exacte VERDICT: GO"
    return True, ""


def basis_ref(root: Path) -> str | None:
    """De hoofdtak op de remote (origin/main of origin/master), of None."""
    for ref in ("origin/main", "origin/master"):
        if git(root, "rev-parse", "--verify", "--quiet", ref):
            return ref
    return None


def ongereviewd_werk(root: Path) -> str | None:
    """Een reden om nu te reviewen, of None. Alleen op een werkbranch met commits die nog niet in de hoofdtak staan,
    en alleen als er voor de laatste commit nog geen review is (GO of NO-GO): zo reviewt Claude één keer per stand."""
    tak = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    basis = basis_ref(root)
    if not basis or tak in HOOFDTAKKEN | {"HEAD", ""}:
        return None
    aantal = git(root, "rev-list", "--count", f"{basis}..HEAD")
    if not aantal or aantal == "0":
        return None
    if review_voor_head(root)[0] is not None:
        return None
    # Bewust geen branchnaam of andere projecttekst: deze reden wordt een opdracht aan Claude (prompt-injectie).
    return f"{int(aantal)} commit(s) op deze branch zijn nog niet gereviewd" if aantal.isdigit() else "er zijn ongereviewde commits"



def al_gevraagd(root: Path) -> bool:
    """Heeft de Stop-hook voor deze commit al om een review gevraagd? Dan niet nog eens, ook als de review mislukte:
    geen herhaling bij elke volgende beurt. De stand staat buiten het project, in ~/.koekoek/stop/."""
    import os

    head = git(root, "rev-parse", "HEAD")
    if not head:
        return True
    import time

    map_ = Path(os.environ.get("KOEKOEK_MAP") or Path.home() / ".koekoek") / "stop"
    teken = map_ / head
    if teken.exists():
        return True
    try:
        map_.mkdir(parents=True, exist_ok=True)
        teken.write_text("", encoding="utf-8")
        grens = time.time() - 30 * 86400  # oude tekens opruimen: de map groeit niet eindeloos
        for oud in map_.iterdir():
            if oud.stat().st_mtime < grens:
                oud.unlink(missing_ok=True)
    except OSError:
        return True  # kan de stand niet bewaren: liever niet vragen dan bij elke beurt opnieuw
    return False
