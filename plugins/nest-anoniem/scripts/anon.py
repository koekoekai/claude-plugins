"""Eén ingang voor de anonimiseren-plugin: zoekt koekoekai/anonimiseren (zie bron.py) en draait de anonimiseerder.

    python anon.py kolommen <bestand.csv>     # alleen de kolomnamen (de inhoud komt niet in beeld)
    python anon.py <bestand> -o <uit> [--naamkolommen …] [--modus pseudoniem]
    python anon.py tool                        # lokale tool openen (Windows: met DPAPI-sleutel voor pseudoniemen)
    python anon.py pad | bijwerken
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bron import vind  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "kolommen":
        with open(argv[1], encoding="utf-8-sig", newline="") as f:
            regel = f.readline()
        sep = max(",;\t", key=regel.count)
        print(next(csv.reader([regel], delimiter=sep)))
        return 0
    if argv[0] == "bijwerken":
        (Path(os.environ.get("KOEKOEK_MAP") or Path.home() / ".koekoek") / "anonimiseren" / ".koekoek-bijgewerkt").unlink(missing_ok=True)
    bron = vind("anonimiseren")
    if not bron:
        print("koekoekai/anonimiseren is niet beschikbaar. Controleer je leesrechten en git-login, of zet ANONIMISEREN_MAP.", file=sys.stderr)
        return 1
    if argv[0] in ("pad", "bijwerken"):
        print(bron)
        return 0
    if argv[0] == "tool":
        if os.name == "nt":
            subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(bron / "Starten.ps1")],
                             creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen([sys.executable, "-I", str(bron / "python" / "lokale_tool.py")])
        print("De lokale tool start op http://127.0.0.1:8765")
        return 0
    return subprocess.run([sys.executable, "-I", str(bron / "python" / "anonimiseren.py"), *argv],
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"}).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
