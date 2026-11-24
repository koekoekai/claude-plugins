import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/nest-privacy/scripts/pilotmeting.py"


def draai(map_, *paden):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, paden)], cwd=map_,
                          env={**os.environ, "NEST_PRIVACY_HERKENNER": "regels"},
                          capture_output=True, text=True)


def test_pilot_utf16_en_privacy(tmp_path):
    bron = tmp_path / "fictieve-bronnaam.txt"
    mail = "voorbeeld@example.invalid"
    bron.write_text(f"[[EMAIL:{mail}]] en [[{mail} extra]] of [[proefwoord]]. Los: diabetes.",
                    encoding="utf-16")
    run = draai(tmp_path, tmp_path, bron)
    assert run.returncode == 0
    rapport = (tmp_path / "pilotmeting.json").read_text(encoding="utf-8")
    assert run.stdout == rapport
    for geheim in (mail, "proefwoord", "extra", "diabetes", bron.name):
        assert geheim not in rapport + run.stderr
    data = json.loads(rapport)
    assert data["bestanden"] == 1
    assert data["herkenners"] == ["regels"]
    assert data["per_soort"]["EMAIL"]["volledig"] == 1
    assert data["per_soort"]["GEZONDHEID"]["onterecht_woorden"] == 1
    assert data["totaal"] == dict(gemarkeerd=3, volledig=1, gedeeltelijk=1, gemist=1, onterecht_woorden=1)
    assert draai(tmp_path, bron).returncode != 0
    assert (tmp_path / "pilotmeting.json").read_text(encoding="utf-8") == rapport


@pytest.mark.parametrize("tekst", [None, "[[proefwaarde", "proefwaarde]]", "[[NAAM:]]", "[[a[[b]]c]]"])
def test_pilot_fout_zonder_waarden(tmp_path, tekst):
    if tekst is not None:
        (tmp_path / "proefwaarde.txt").write_text(tekst, encoding="utf-8")
    run = draai(tmp_path, tmp_path)
    assert run.returncode != 0
    assert "proefwaarde" not in run.stdout + run.stderr
    assert not (tmp_path / "pilotmeting.json").exists()
