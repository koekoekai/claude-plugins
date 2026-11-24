"""PreToolUse-hook van de Nest-plugin: vóór een `git push` dezelfde snelle poorten als de fabriek.

Rood (persoonsgegevens) -> exit 2: Claude Code houdt de push tegen en krijgt de reden te zien.
Alles wat geen echte vondst is (geen git-repo, script kapot, timeout) laat de push door: de fabriek in CI is de echte poort,
deze hook is er om het eerder te zien. Toont nooit gevonden waarden.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from afspraken import HOOFDTAKKEN, instellingen, projectroot, push_doelen  # noqa: E402
from bron import vind  # noqa: E402


def main() -> int:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not re.search(r"(^|[;&|]\s*|\s)git(\s+-C\s+\S+)?\s+push\b", cmd):  # de if-filter is best-effort
        return 0
    m = re.search(r"git\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)\s+push", cmd)
    cwd = Path(data.get("cwd") or ".")
    map_ = (cwd / m.group(1).strip("\"'")) if m else cwd

    # Werkwijze: via een branch en een PR, nooit forceren op de hoofdtak.
    root = projectroot(map_)
    if root:
        doelen, force = push_doelen(cmd, root)
        hoofd = doelen & HOOFDTAKKEN
        if hoofd and force:
            print(f"Nest-werkwijze: force-push naar {', '.join(sorted(hoofd))} is nooit toegestaan.", file=sys.stderr)
            return 2
        if hoofd and not instellingen(root)["push_naar_main"]:
            print(f"Nest-werkwijze: niet direct naar {', '.join(sorted(hoofd))} pushen. Maak een branch "
                  "(git switch -c <naam>), push die en open een PR, zodat de fabriek en de review erover gaan. "
                  "Heeft dit project een eigen route, zet dan \"push_naar_main\": true in .nest.json.", file=sys.stderr)
            return 2

    nest = vind("bouwstenen")
    if not nest or not (nest / "fabriek" / "lokaal.py").exists():
        print("Nest-fabriek: Nest niet beschikbaar, de snelle poorten zijn overgeslagen (de CI controleert wel).", file=sys.stderr)
        return 0
    try:
        r = subprocess.run(
            [sys.executable, str(nest / "fabriek" / "lokaal.py"), "--snel", "--map", str(map_)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=100,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0
    if r.returncode == 1:
        uit = (r.stdout + r.stderr).strip()
        print("Nest-fabriek: push tegengehouden, deze poort wordt ook rood in de PR.\n" + uit[-3000:], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
