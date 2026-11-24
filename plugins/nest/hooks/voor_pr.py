"""PreToolUse-hook van de Nest-plugin: een PR openen (`gh pr create`) mag pas na een lokale review met VERDICT: GO
op de laatste commit (/nest:review). Uitzetten per project: "review_voor_pr": false in .nest.json."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from afspraken import instellingen, projectroot, review_is_vers  # noqa: E402


def main() -> int:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not re.search(r"(^|[;&|]\s*|\s)gh\s+pr\s+create\b", cmd):
        return 0
    root = projectroot(Path(data.get("cwd") or "."))
    if not root or not instellingen(root)["review_voor_pr"]:
        return 0
    goed, reden = review_is_vers(root)
    if goed:
        return 0
    print(f"Nest-werkwijze: eerst /nest:review, dan pas een PR ({reden}). Alleen een exacte VERDICT: GO op de laatste "
          "commit telt. Eigen route? Zet \"review_voor_pr\": false in .nest.json.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
