"""Het lokale taalmodel (Privacy Kit) installeren in een eigen, afgeschermde omgeving. Eén keer:

    python model_installeren.py            # installeren of bijwerken
    python model_installeren.py --status   # staat het erop, en werkt het?
    python model_installeren.py --verwijder

Wat het doet:
- maakt een eigen Python-omgeving in ~/.koekoek/nest-privacy/model (los van je eigen Python);
- installeert daarin Privacy Kit (bards-ai, Apache-2.0), vastgezet op een gecontroleerde versie;
- downloadt het model één keer van Hugging Face (ongeveer 0,5 GB) en test het.
Daarna werkt alles offline: de plugin praat met het model via een lokaal proces; er gaat geen tekst over het netwerk.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kluis  # noqa: E402

PAKKET = "privacy-kit @ git+https://github.com/bards-ai/privacy-kit@a07d8ae645c92d379d2d2175b1f14ffb8b851c16"
MAP = kluis.MAP / "model"
HF_MAP = kluis.MAP / "hf"


def python_van_model() -> Path:
    return MAP / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def omgeving() -> dict:
    return {**os.environ, "HF_HOME": str(HF_MAP), "HF_HUB_DISABLE_TELEMETRY": "1", "PYTHONWARNINGS": "ignore"}


def test() -> bool:
    py = python_van_model()
    if not py.is_file():
        return False
    proef = "from privacy_kit.core.detectors import BardsAiOnnxDetector as D; print(any(s.label=='PERSON_NAME' for s in D().detect('Mail Jan Jansen even.')))"
    r = subprocess.run([str(py), "-c", proef], capture_output=True, text=True, env={**omgeving(), "HF_HUB_OFFLINE": "1"}, timeout=300)
    return r.returncode == 0 and r.stdout.strip().endswith("True")


def installeer() -> int:
    print(f"Eigen omgeving in {MAP} ...", flush=True)
    MAP.parent.mkdir(parents=True, exist_ok=True)
    if not python_van_model().is_file():
        venv.EnvBuilder(with_pip=True, clear=True).create(MAP)
    py = str(python_van_model())
    print("Privacy Kit installeren (eenmalig, een paar minuten) ...", flush=True)
    r = subprocess.run([py, "-m", "pip", "install", "-q", "--disable-pip-version-check", "--timeout", "180", PAKKET], env=omgeving())
    if r.returncode != 0:
        print("Installeren lukte niet. Is git geïnstalleerd en is er internet?", file=sys.stderr)
        return 1
    print("Model downloaden en testen (eenmalig) ...", flush=True)
    subprocess.run([py, "-c", "from privacy_kit.core.detectors import BardsAiOnnxDetector as D; D().detect('test')"],
                   env=omgeving(), capture_output=True, timeout=1800)
    if not test():
        print("Het model laadt niet. Probeer het later opnieuw, of draai met --verwijder en daarna opnieuw.", file=sys.stderr)
        return 1
    (MAP / "nest-privacy.json").write_text(json.dumps({"pakket": PAKKET}), encoding="utf-8")
    print("Klaar. Het taalmodel staat lokaal en werkt offline.")
    return 0


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if "--status" in argv:
        werkt = test()
        print("Taalmodel: geïnstalleerd en werkt." if werkt else "Taalmodel: niet geïnstalleerd (of werkt niet). Installeren: python model_installeren.py")
        return 0 if werkt else 1
    if "--verwijder" in argv:
        for m in (MAP, HF_MAP):
            shutil.rmtree(m, ignore_errors=True)
        print("Taalmodel verwijderd.")
        return 0
    return installeer()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
