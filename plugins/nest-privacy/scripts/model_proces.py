"""Draait in de eigen modelomgeving (zie model_installeren.py). Lokaal en offline; wordt door taalmodel.py gestart.

Het model wordt één keer geladen. Daarna leest het proces per regel een JSON-tekst van stdin ({"tekst": "..."})
en schrijft per regel de gevonden stukken terug ([{"begin":..,"eind":..,"soort":..}, ...]).
Zonder regels op stdin (oude manier): de hele invoer is één tekst.
"""
import json
import sys

from privacy_kit.core.detectors import BardsAiOnnxDetector


def stukken(detector, tekst: str) -> list:
    return [{"begin": s.start, "eind": s.end, "soort": s.label} for s in detector.detect(tekst)]


def main(argv: list) -> int:
    detector = BardsAiOnnxDetector()
    if "--doorlopend" not in argv:
        sys.stdout.write(json.dumps(stukken(detector, sys.stdin.buffer.read().decode("utf-8"))))
        return 0
    invoer = sys.stdin.buffer
    uit = sys.stdout.buffer
    for regel in iter(invoer.readline, b""):
        try:
            tekst = json.loads(regel.decode("utf-8"))["tekst"]
            antwoord = stukken(detector, tekst)
        except Exception:  # noqa: BLE001 - een fout bij één tekst stopt het proces niet
            antwoord = None
        uit.write((json.dumps(antwoord) + "\n").encode("utf-8"))
        uit.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
