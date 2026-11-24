"""Stop-hook van de Nest-plugin: na afgerond werk zelf reviewen, zonder dat de gebruiker erom vraagt.

Als Claude klaar is met een beurt en er staan op een werkbranch commits die nog niet gereviewd zijn, laat deze hook Claude
doorgaan met /nest:review (en bij NO-GO: oplossen en opnieuw reviewen). Er gebeurt niets als:
- het geen git-project is, je op main/master zit, of er geen commits buiten de hoofdtak zijn;
- er voor de laatste commit al een review is (GO of NO-GO), of de hook er voor deze commit al om vroeg: één keer per
  stand, ook als de review mislukte (geen herhaling bij elke beurt);
- deze stop zelf al het gevolg was van deze hook (stop_hook_active);
- het project "review_automatisch": false heeft in .nest.json.
Kosten: een review gebruikt je eigen Claude-abonnement (geen API-sleutel).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from afspraken import al_gevraagd, instellingen, ongereviewd_werk, projectroot  # noqa: E402


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if data.get("stop_hook_active"):
        return 0
    root = projectroot(Path(data.get("cwd") or "."))
    if not root or not instellingen(root)["review_automatisch"]:
        return 0
    reden = ongereviewd_werk(root)
    if not reden or al_gevraagd(root):
        return 0
    print(json.dumps({
        "decision": "block",
        "reason": (f"Nest-werkwijze: {reden}. Draai nu zelf /nest:review (code-, security- en ontwerp-agent). "
                   "Bij NO-GO: los de HOOG-bevindingen op, commit, en review opnieuw. Meld daarna kort het VERDICT aan de "
                   "gebruiker. Push of open geen PR zonder dat de gebruiker daarom vraagt."),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
