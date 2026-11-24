"""Vindt een Koekoek-repo (bouwstenen, anonimiseren) voor de plugin, en houdt hem bij.

Volgorde:
1. een omgevingsvariabele (NEST_MAP voor bouwstenen, ANONIMISEREN_MAP voor anonimiseren): je eigen checkout, voor ontwikkelen;
2. de beheerde kopie in ~/.koekoek/<repo>: hooguit eens per 12 uur `git pull --ff-only` van main;
3. bestaat die nog niet: `git clone` van github.com/koekoekai/<repo> met je eigen git-login (je hebt leesrechten nodig):
   eerst via https, lukt dat niet dan via SSH (servers met alleen een SSH-sleutel). Forceren: KOEKOEK_GIT=ssh of https.

Lukt bijwerken of clonen niet (offline, geen rechten), dan gebruikt hij wat er is, of geeft hij None. Nooit interactief:
geen wachtwoordvraag die een hook laat hangen.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ORGANISATIE = os.environ.get("KOEKOEK_ORG", "koekoekai")
THUIS = Path(os.environ.get("KOEKOEK_MAP") or Path.home() / ".koekoek")
VARIABELE = {"bouwstenen": "NEST_MAP", "anonimiseren": "ANONIMISEREN_MAP"}
INTERVAL = 12 * 3600


def _git(*args: str, timeout: int = 60) -> bool:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=15")  # nooit om een wachtwoord vragen
    try:
        return subprocess.run(["git", *args], capture_output=True, timeout=timeout, env=env).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _weg(map_: Path) -> None:
    """Map weghalen, ook op Windows waar git-objecten alleen-lezen zijn."""
    import shutil
    import stat

    def schrijfbaar_en_opnieuw(functie, pad, _fout):
        try:
            os.chmod(pad, stat.S_IWRITE)
            functie(pad)
        except OSError:
            pass

    if map_.exists():
        shutil.rmtree(map_, onerror=schrijfbaar_en_opnieuw)


def vind(repo: str, bijwerken: bool = True) -> Path | None:
    eigen = os.environ.get(VARIABELE.get(repo, ""), "")
    if eigen:
        p = Path(eigen).expanduser()
        return p if p.exists() else None
    doel = THUIS / repo
    if not (doel / ".git").exists():
        if not bijwerken:
            return None
        THUIS.mkdir(parents=True, exist_ok=True)
        print(f"Eerste keer: {ORGANISATIE}/{repo} ophalen naar {doel} ...", file=sys.stderr)
        adressen = {"https": f"https://github.com/{ORGANISATIE}/{repo}.git", "ssh": f"git@github.com:{ORGANISATIE}/{repo}.git"}
        keuze = os.environ.get("KOEKOEK_GIT", "").lower()
        volgorde = [keuze] if keuze in adressen else ["https", "ssh"]
        # Eerst naar een tijdelijke map; pas na een geslaagde clone hernoemen. Een afgebroken clone laat zo niets
        # half achter dat daarna voor een echte kopie wordt aangezien. Een halve map van vroeger ruimen we eerst op.
        if doel.exists():
            _weg(doel)
        tijdelijk = THUIS / f".{repo}.bezig-{os.getpid()}"
        _weg(tijdelijk)
        gelukt = any(_git("clone", "--quiet", "--depth", "50", adressen[v], str(tijdelijk), timeout=180) for v in volgorde)
        if not gelukt or not (tijdelijk / ".git").exists():
            _weg(tijdelijk)
            print(f"Ophalen van {ORGANISATIE}/{repo} lukte niet via {' of '.join(volgorde)} (leesrechten? git-login of SSH-sleutel? offline?).",
                  file=sys.stderr)
            return None
        try:
            tijdelijk.rename(doel)
        except OSError:  # bijv. tegelijk door een andere sessie gemaakt
            _weg(tijdelijk)
        if not (doel / ".git").exists():
            return None
        (doel / ".koekoek-bijgewerkt").write_text(str(time.time()), encoding="utf-8")
        return doel
    stempel = doel / ".koekoek-bijgewerkt"
    oud = time.time() - float(stempel.read_text(encoding="utf-8") or 0) if stempel.exists() else INTERVAL + 1
    if bijwerken and oud > INTERVAL:
        if _git("-C", str(doel), "pull", "--quiet", "--ff-only"):
            stempel.write_text(str(time.time()), encoding="utf-8")
    return doel


def main(argv: list[str]) -> int:
    """python bron.py <repo> [--bijwerken] : print het pad (voor skills), exit 1 als hij er niet is."""
    if not argv:
        print(__doc__)
        return 2
    if "--bijwerken" in argv:
        stempel = THUIS / argv[0] / ".koekoek-bijgewerkt"
        stempel.unlink(missing_ok=True)
    p = vind(argv[0])
    if not p:
        return 1
    print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
