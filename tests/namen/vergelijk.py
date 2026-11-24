"""Meet de naamherkenning op alle sets: python tests/namen/vergelijk.py"""
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent.parent / "plugins" / "nest-privacy" / "scripts"))
import anonimiseren  # noqa: E402
import namen  # noqa: E402


def meet_set(bestand: Path) -> dict:
    data = json.loads(bestand.read_text(encoding="utf-8"))
    tot = gev = bl = vals = 0
    mis, ont = [], []
    for z in data["zinnen"]:
        r = namen.zoek_namen(z["t"])
        uit = anonimiseren.anonimiseer(namen.normaliseer(z["t"], r.varianten), extra_termen=r.namen).tekst
        for n in z["namen"]:
            tot += 1
            if n.lower() in uit.lower():
                mis.append(n)
            else:
                gev += 1
        for w in z["blijven"]:
            bl += 1
            if w not in uit:
                vals += 1
                ont.append(w)
    return {"herkend": gev / max(tot, 1), "vals": vals / max(bl, 1), "gemist": mis, "onterecht": ont, "n": tot, "b": bl}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for naam in ("testset.json", "moeilijk.json", "controle.json", "blind.json", "blind2.json"):
        m = meet_set(HIER / naam)
        print(f"{naam:14} herkend {m['herkend']:4.0%} van {m['n']:2}  vals {m['vals']:4.0%} van {m['b']:2}  gemist {m['gemist']}  onterecht {m['onterecht']}")
