"""Meet alle AVG-soorten: python tests/namen/meet_gevoelig.py
Weg = het stuk staat niet meer in de tekst. Vals = een woord dat moest blijven, is weg."""
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent.parent / "plugins" / "nest-privacy" / "scripts"))
import gevoelig  # noqa: E402


def meet() -> dict:
    data = json.loads((HIER / "gevoelig.json").read_text(encoding="utf-8"))
    tot = weg = bl = vals = 0
    mis, ont = [], []
    for z in data["zinnen"]:
        uit, _ = gevoelig.vervang(z["t"], modus="maskeren", eigen_woorden=[])
        for w in z["weg"]:
            tot += 1
            if w in uit:
                mis.append(w)
            else:
                weg += 1
        for w in z["blijven"]:
            bl += 1
            if w not in uit:
                vals += 1
                ont.append(w)
    return {"weg": weg / tot, "vals": vals / bl, "gemist": mis, "onterecht": ont, "n": tot, "b": bl}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    m = meet()
    print(f"gevoelig.json  weg {m['weg']:4.0%} van {m['n']}  vals {m['vals']:4.0%} van {m['b']}  gemist {m['gemist']}  onterecht {m['onterecht']}")
