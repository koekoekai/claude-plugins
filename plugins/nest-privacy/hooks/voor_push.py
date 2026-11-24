"""PreToolUse-hook van Nest-privacy: vóór een `git push` de gewijzigde bestanden controleren op persoonsgegevens en geheimen.

Vondst -> exit 2: Claude Code houdt de push tegen en krijgt bestand, regel en soort te zien (nooit de waarde).
Alles wat geen echte vondst is (geen git-repo, fout in het script) laat de push door. Draait lokaal; stuurt niets naar buiten.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def _git(map_: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(map_), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def basis(root: Path) -> str | None:
    """De commit waartegen we vergelijken: de upstream van de branch, anders origin/main of origin/master."""
    for ref in ("@{upstream}", "origin/main", "origin/master"):
        mb = _git(root, "merge-base", "HEAD", ref)
        if mb:
            return mb
    return None


def main() -> int:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not re.search(r"(^|[;&|]\s*|\s)git(\s+-C\s+\S+)?\s+push\b", cmd):
        return 0
    m = re.search(r"git\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)\s+push", cmd)
    cwd = Path(data.get("cwd") or ".")
    map_ = (cwd / m.group(1).strip("\"'")) if m else cwd
    root_tekst = _git(map_, "rev-parse", "--show-toplevel")
    if not root_tekst:
        return 0
    root = Path(root_tekst)
    try:
        import anonimiseren
        import geheimen
        import gevoelig
        from voor_lezen import DATA
        import fnmatch

        ref = basis(root)
        os.chdir(root)
        paden = geheimen.git_bestanden(".", ref)
        pii = anonimiseren.controleer_bestanden(paden, basis=ref)
        negeer = anonimiseren._negeer_patronen(".", ref)
        for pad in paden:
            bestand = Path(pad)
            if bestand.suffix.lower() not in DATA or bestand.is_symlink() or not bestand.is_file():
                continue
            if bestand.stat().st_size > anonimiseren.MAX_CONTROLE_BYTES or any(fnmatch.fnmatch(bestand.as_posix(), p) for p in negeer):
                continue
            with bestand.open("rb") as bron:
                codering = anonimiseren._utf16(bron.read(8192))
                bron.seek(0)
                for regel, zin in enumerate(anonimiseren._regels(bron, codering), 1):
                    if "pii: ok" not in zin:
                        pii.extend(anonimiseren.Melding(pad, regel, soort) for _, _, soort in gevoelig.vind(zin))
        sleutels = geheimen.controleer_bestanden(paden)
    except Exception:  # noqa: BLE001 - de hook mag een push nooit door een eigen fout tegenhouden
        return 0
    if not pii and not sleutels:
        return 0
    regels = [f"- {v.pad}:{v.regel} persoonsgegeven ({v.soort})" for v in pii[:30]]
    regels += [f"- {v.pad}:{v.regel} geheim ({v.soort})" for v in sleutels[:30]]
    print("Nest-privacy: push tegengehouden. In de gewijzigde bestanden staan mogelijk persoonsgegevens of geheimen:\n"
          + "\n".join(regels)
          + "\nHaal ze eruit (een gelekt geheim ook intrekken bij de leverancier), anonimiseer met /nest-privacy:anonimiseer,"
          " of markeer nepdata met 'pii: ok' of 'geheim: ok' op de regel.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
