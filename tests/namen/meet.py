"""Meet hoe goed de naamherkenning werkt: python tests/namen/meet.py
Herkend = de naam staat niet meer in de gemaskeerde tekst. Vals = een woord dat moest blijven, is weg."""
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent.parent / "plugins" / "nest-privacy" / "scripts"))
import anonimiseren  # noqa: E402
import namen  # noqa: E402


def meet(bestand: str = "testset.json") -> dict:
    data = json.loads((HIER / bestand).read_text(encoding="utf-8"))
    totaal = gevonden = blijven = vals = 0
    gemist, onterecht = [], []
    for z in data["zinnen"]:
        r = namen.zoek_namen(z["t"])
        tekst = namen.normaliseer(z["t"], r.varianten)
        uit = anonimiseren.anonimiseer(tekst, extra_termen=r.namen).tekst
        for n in z["namen"]:
            totaal += 1
            if n.lower() in uit.lower():
                gemist.append((n, z["t"].replace("\n", " ")))
            else:
                gevonden += 1
        for w in z["blijven"]:
            blijven += 1
            if w not in uit:
                vals += 1
                onterecht.append((w, z["t"].replace("\n", " ")))
    return {"herkend": gevonden / totaal, "vals": vals / blijven, "gemist": gemist, "onterecht": onterecht,
            "aantal_namen": totaal, "aantal_blijven": blijven}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    m = meet()
    print(f"Namen herkend: {m['herkend']:.0%} van {m['aantal_namen']}  ·  valse treffers: {m['vals']:.0%} van {m['aantal_blijven']}")
    for n, z in m["gemist"]:
        print(f"  gemist: {n!r} in: {z}")
    for w, z in m["onterecht"]:
        print(f"  onterecht weg: {w!r} in: {z}")
