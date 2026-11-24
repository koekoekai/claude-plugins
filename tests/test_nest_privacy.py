"""Tests voor Nest-privacy: geheimen-check, push-hook en wat de catalogus van Anthropic vraagt."""
import json
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
PLUGIN = HIER / "plugins" / "nest-privacy"
sys.path.insert(0, str(PLUGIN / "scripts"))
import geheimen  # noqa: E402

# Nepwaarden worden opgebouwd, zodat scanners dit testbestand zelf niet als lek zien.
GITHUB = "gh" + "p_" + "a1B2c3D4" * 5
AWS = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
ANTHROPIC = "sk-" + "ant-" + "x" * 30
SLEUTEL_KOP = "-----BEGIN " + "RSA PRIVATE KEY-----"
BSN = "271" + "000" + "004"  # geldige elfproef, geen bekende testwaarde (die slaat de controle over)


def test_geheimen_gevonden_zonder_waarde_in_uitvoer(tmp_path, capsys):
    f = tmp_path / "app.py"
    f.write_text(f'TOKEN = "{GITHUB}"\nAWS = "{AWS}"\nK = "{ANTHROPIC}"\n{SLEUTEL_KOP}\n'
                 f'db = "postgres://app:Geheim123@db.local/app"\npassword = "Zomer2026!x"\n', encoding="utf-8")
    soorten = {v.soort for v in geheimen.controleer_bestanden([str(f)], str(tmp_path))}
    assert {"GITHUB-TOKEN", "AWS-SLEUTEL", "ANTHROPIC-SLEUTEL", "PRIVESLEUTEL", "WACHTWOORD-IN-URL", "WACHTWOORD"} <= soorten
    assert geheimen.main([str(f)]) == 1
    uit = capsys.readouterr().out
    assert GITHUB not in uit and "Zomer2026" not in uit


def test_voorbeelden_en_markering_tellen_niet(tmp_path):
    f = tmp_path / "config.py"
    f.write_text('password = "changeme-voorbeeld"\napi_key = "${API_KEY}"\n'
                 f'TOKEN = "{GITHUB}"  # geheim: ok\nnaam = "gewone tekst"\n', encoding="utf-8")
    assert geheimen.controleer_bestanden([str(f)], str(tmp_path)) == []


def test_negeerbestand(tmp_path):
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "fixtures" / "nep.txt").write_text(GITHUB, encoding="utf-8")
    (tmp_path / ".nest-geheim-negeer").write_text("fixtures/*\n", encoding="utf-8")
    assert geheimen.controleer_bestanden([str(tmp_path / "fixtures" / "nep.txt")], str(tmp_path)) == []


def _project(tmp_path: Path) -> Path:
    g = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    (tmp_path / "leesmij.txt").write_text("hallo\n", encoding="utf-8")
    subprocess.run([*g, "add", "-A"], check=True)
    subprocess.run([*g, "commit", "-qm", "start"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "update-ref", "refs/remotes/origin/main", "HEAD"], check=True)
    return tmp_path


def _hook(map_: Path, opdracht: str = "git push origin werk") -> subprocess.CompletedProcess:
    invoer = json.dumps({"cwd": str(map_), "tool_input": {"command": opdracht}})
    return subprocess.run([sys.executable, str(PLUGIN / "hooks" / "voor_push.py")], input=invoer,
                          capture_output=True, text=True, encoding="utf-8")


def _commit(map_: Path, naam: str, inhoud: str) -> None:
    g = ["git", "-C", str(map_), "-c", "user.name=t", "-c", "user.email=t@example.com"]
    (map_ / naam).write_text(inhoud, encoding="utf-8")
    subprocess.run([*g, "add", naam], check=True)
    subprocess.run([*g, "commit", "-qm", naam], check=True)


def test_hook_houdt_push_met_bsn_of_geheim_tegen_zonder_waarde(tmp_path):
    p = _project(tmp_path)
    _commit(p, "klant.py", f'BSN = "{BSN}"\nTOKEN = "{GITHUB}"\n')
    r = _hook(p)
    assert r.returncode == 2
    assert "klant.py:1 persoonsgegeven (BSN)" in r.stderr and "klant.py:2 geheim (GITHUB-TOKEN)" in r.stderr
    assert BSN not in r.stderr and GITHUB not in r.stderr


def test_hook_laat_schone_push_en_andere_opdrachten_door(tmp_path):
    p = _project(tmp_path)
    _commit(p, "app.py", "def som(a, b):\n    return a + b\n")
    assert _hook(p).returncode == 0
    _commit(p, "klant.py", f'BSN = "{BSN}"\n')
    assert _hook(p, "git status").returncode == 0
    assert _hook(p, "echo git pushen").returncode == 0


def test_hook_buiten_git_laat_door(tmp_path):
    assert _hook(tmp_path).returncode == 0


def test_klaar_voor_de_catalogus():
    m = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert m["name"] == "nest-privacy" and not m["name"].startswith(("claude", "anthropic"))
    assert m["license"] == "MIT" and (PLUGIN / "LICENSE").is_file()
    assert (PLUGIN / m["icon"].removeprefix("./")).is_file()
    for veld in ("homepage", "documentationUrl", "supportUrl", "privacyPolicyUrl"):
        assert m[veld].startswith("https://"), veld
    assert len((PLUGIN / "README.md").read_text(encoding="utf-8").split()) >= 40
    assert not (PLUGIN / ".mcp.json").exists()  # geen server: alles lokaal
    for f in PLUGIN.rglob("*"):
        assert f.is_symlink() is False and (f.is_dir() or f.suffix == ".png" or f.stat().st_size < 256 * 1024), f


def _lees_hook(bestand: Path) -> subprocess.CompletedProcess:
    invoer = json.dumps({"cwd": str(bestand.parent), "tool_name": "Read", "tool_input": {"file_path": str(bestand)}})
    return subprocess.run([sys.executable, str(PLUGIN / "hooks" / "voor_lezen.py")], input=invoer,
                          capture_output=True, text=True, encoding="utf-8")


def test_lees_hook_houdt_databestand_met_persoonsgegevens_tegen(tmp_path):
    f = tmp_path / "klanten.csv"
    f.write_text(f"naam;bsn\nKlant;{BSN}\n", encoding="utf-8")
    r = _lees_hook(f)
    assert r.returncode == 2 and "BSN" in r.stderr and BSN not in r.stderr and "anonimiseer" in r.stderr


def test_lees_hook_laat_code_schone_data_en_negeerlijst_door(tmp_path):
    code = tmp_path / "app.py"
    code.write_text(f'BSN = "{BSN}"\n', encoding="utf-8")
    assert _lees_hook(code).returncode == 0  # code: daar is de push-hook voor
    schoon = tmp_path / "producten.csv"
    schoon.write_text("product;prijs\nappel;1.20\n", encoding="utf-8")
    assert _lees_hook(schoon).returncode == 0
    p = _project(tmp_path / "proj")
    nep = p / "nep.csv"
    nep.write_text(f"bsn\n{BSN}\n", encoding="utf-8")
    (p / ".nest-pii-negeer").write_text("nep.csv\n", encoding="utf-8")
    assert _lees_hook(nep).returncode == 0


# ---------- codes en terugzetten (pseudoniem.py, kluis.py) ----------



MAIL = "piet.jansen@" + "bedrijfje.nl"


def _pseudoniem(tmp_path, monkeypatch):
    import kluis
    import pseudoniem
    monkeypatch.setattr(kluis, "MAP", tmp_path / "kluis")
    return pseudoniem, kluis


def test_codes_heen_en_terug_zonder_waarden_in_de_uitvoer(tmp_path, monkeypatch, capsys):
    pseudoniem, kluis = _pseudoniem(tmp_path, monkeypatch)
    invoer = tmp_path / "mail.txt"
    invoer.write_text(f"Beste dhr. Jansen, uw BSN is {BSN} en uw mail {MAIL}.\n", encoding="utf-8")
    assert pseudoniem.main(["maak", str(invoer), "-o", str(tmp_path / "mail.code.txt")]) == 0
    code_tekst = (tmp_path / "mail.code.txt").read_text(encoding="utf-8")
    assert BSN not in code_tekst and MAIL not in code_tekst and "[BSN-" in code_tekst
    uit = capsys.readouterr().out
    assert BSN not in uit and MAIL not in uit and "vervangen:" in uit

    codes = pseudoniem.CODE.findall(code_tekst)
    antwoord = tmp_path / "antwoord.code.txt"
    antwoord.write_text(f"Geachte {codes[0]}, we hebben {codes[-1]} bijgewerkt. [NAAM-000000000000]\n", encoding="utf-8")
    assert pseudoniem.main(["terugzetten", str(antwoord), "-o", str(tmp_path / "antwoord.txt")]) == 0
    terug = (tmp_path / "antwoord.txt").read_text(encoding="utf-8")
    assert "Jansen" in terug and MAIL in terug and "[NAAM-000000000000]" in terug  # onbekende code blijft staan
    uit = capsys.readouterr().out
    assert "teruggezet: 2" in uit and "onbekende codes: 1" in uit and MAIL not in uit


def test_zelfde_persoon_zelfde_code_ook_in_een_ander_bestand(tmp_path, monkeypatch):
    pseudoniem, _ = _pseudoniem(tmp_path, monkeypatch)
    for naam in ("a", "b"):
        (tmp_path / f"{naam}.txt").write_text(f"mail: {MAIL}\n", encoding="utf-8")
        pseudoniem.maak(tmp_path / f"{naam}.txt", tmp_path / f"{naam}.code.txt")
    a = pseudoniem.CODE.findall((tmp_path / "a.code.txt").read_text(encoding="utf-8"))
    b = pseudoniem.CODE.findall((tmp_path / "b.code.txt").read_text(encoding="utf-8"))
    assert a and a == b


def test_sleutel_en_tabel_niet_leesbaar_en_alleen_voor_jou(tmp_path, monkeypatch):
    pseudoniem, kluis = _pseudoniem(tmp_path, monkeypatch)
    (tmp_path / "x.txt").write_text(f"mail: {MAIL}\n", encoding="utf-8")
    pseudoniem.maak(tmp_path / "x.txt", tmp_path / "x.code.txt")
    tabellen = list((kluis.MAP / "tabellen").glob("*.tabel"))
    assert len(tabellen) == 1
    ruw = tabellen[0].read_bytes()
    if sys.platform == "win32":
        assert MAIL.encode() not in ruw  # versleuteld met DPAPI
    else:
        assert oct(tabellen[0].stat().st_mode & 0o777) == "0o600"
        assert oct((kluis.MAP / "sleutel").stat().st_mode & 0o777) == "0o600"


def test_wissen_en_oude_tabellen_verdwijnen_vanzelf(tmp_path, monkeypatch):
    import os
    import time
    pseudoniem, kluis = _pseudoniem(tmp_path, monkeypatch)
    (tmp_path / "x.txt").write_text(f"mail: {MAIL}\n", encoding="utf-8")
    pseudoniem.maak(tmp_path / "x.txt", tmp_path / "x.code.txt")
    tabel = next((kluis.MAP / "tabellen").glob("*.tabel"))
    oud = time.time() - 31 * 86400
    os.utime(tabel, (oud, oud))
    assert pseudoniem.opruimen() == 1
    pseudoniem.maak(tmp_path / "x.txt", tmp_path / "x.code.txt")
    assert pseudoniem.main(["wis", "--alles"]) == 0
    assert not list((kluis.MAP / "tabellen").glob("*.tabel"))


def test_lees_hook_houdt_het_teruggezette_bestand_tegen(tmp_path, monkeypatch):
    pseudoniem, _ = _pseudoniem(tmp_path, monkeypatch)
    (tmp_path / "x.txt").write_text(f"klant;bsn\nKlant;{BSN}\n", encoding="utf-8")
    pseudoniem.maak(tmp_path / "x.txt", tmp_path / "x.code.txt")
    pseudoniem.terugzetten(tmp_path / "x.code.txt", tmp_path / "terug.txt")
    assert _lees_hook(tmp_path / "terug.txt").returncode == 2
    assert _lees_hook(tmp_path / "x.code.txt").returncode == 0  # de versie met codes mag Claude wel lezen
