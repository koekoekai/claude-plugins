"""Draait in de eigen modelomgeving (zie model_installeren.py). Leest tekst van stdin, geeft de gevonden stukken als JSON.
Lokaal en offline; wordt door taalmodel.py als apart proces gestart."""
import json
import sys

from privacy_kit.core.detectors import BardsAiOnnxDetector


def main() -> int:
    tekst = sys.stdin.buffer.read().decode("utf-8")
    stukken = [{"begin": s.start, "eind": s.end, "soort": s.label} for s in BardsAiOnnxDetector().detect(tekst)]
    sys.stdout.write(json.dumps(stukken))
    return 0


if __name__ == "__main__":
    sys.exit(main())
