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


def test_naamherkenning_haalt_de_lat():
    """Gewone set: alles herkend. Moeilijke set: minstens de helft. Nooit een woord onterecht weg."""
    sys.path.insert(0, str(HIER / "tests" / "namen"))
    import meet
    m = meet.meet()
    assert m["herkend"] >= 0.95 and m["vals"] == 0


# ---------- naamherkenning via de eigen Nest-server (taalmodel.py) ----------

class _NepAntwoord:
    def __init__(self, data):
        self._data = json.dumps(data).encode()

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_server_alleen_met_eigen_adres_en_sleutel(monkeypatch):
    import taalmodel
    gevraagd = []
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=0: gevraagd.append(req) or _NepAntwoord({}))
    monkeypatch.delenv("NEST_URL", raising=False)
    monkeypatch.setenv("NEST_TOKEN", "nest_" + "x" * 20)
    assert taalmodel._via_server("tekst") is None and gevraagd == []  # geen standaardadres: nooit per ongeluk naar buiten
    monkeypatch.setenv("NEST_URL", "http://onveilig.voorbeeld/mcp")
    assert taalmodel._via_server("tekst") is None and gevraagd == []  # alleen https


def test_server_geeft_personen(monkeypatch):
    import taalmodel
    monkeypatch.setenv("NEST_URL", "https://nest.voorbeeld.nl/mcp")
    monkeypatch.setenv("NEST_TOKEN", "nest_" + "x" * 20)
    gevraagd = []

    def nep(req, timeout=0):
        gevraagd.append(json.loads(req.data))
        return _NepAntwoord({"result": {"structuredContent": {"personen": ["Kowalski", "Priya Sharma"]}}})
    monkeypatch.setattr("urllib.request.urlopen", nep)
    assert taalmodel._via_server("Volgens Kowalski ...") == {"Kowalski", "Priya Sharma"}
    assert gevraagd[0]["params"]["name"] == "herken_personen"


def test_server_uit_of_onbereikbaar_valt_terug(monkeypatch):
    import taalmodel
    monkeypatch.setenv("NEST_URL", "https://nest.voorbeeld.nl/mcp")
    monkeypatch.setenv("NEST_TOKEN", "nest_" + "x" * 20)
    uit = {"result": {"content": [{"type": "text", "text": json.dumps({"fout": "Naamherkenning staat uit op deze server."})}]}}
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=0: _NepAntwoord(uit))
    assert taalmodel._via_server("tekst") is None

    def kapot(req, timeout=0):
        raise OSError("geen verbinding")
    monkeypatch.setattr("urllib.request.urlopen", kapot)
    assert taalmodel._via_server("tekst") is None


def test_auto_stuurt_nooit_naar_een_server(monkeypatch):
    import taalmodel
    monkeypatch.setenv("NEST_URL", "https://nest.voorbeeld.nl/mcp")
    monkeypatch.setenv("NEST_TOKEN", "nest_" + "x" * 20)
    monkeypatch.setenv("NEST_PRIVACY_HERKENNER", "auto")
    gevraagd = []
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=0: gevraagd.append(req) or _NepAntwoord({}))
    taalmodel.personen("Volgens Kowalski werkt het.")
    assert gevraagd == []


def test_server_geeft_alle_soorten(monkeypatch):
    import taalmodel
    monkeypatch.setenv("NEST_URL", "https://nest.voorbeeld.nl/mcp")
    monkeypatch.setenv("NEST_TOKEN", "nest_" + "x" * 20)
    monkeypatch.setenv("NEST_PRIVACY_HERKENNER", "server")
    antwoord = {"result": {"structuredContent": {"stukken": [
        {"begin": 0, "eind": 8, "soort": "PERSON_NAME"}, {"begin": 99, "eind": 120, "soort": "HEALTH_DATA"}]}}}
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=0: _NepAntwoord(antwoord))
    assert taalmodel.spans("Kowalski heeft diabetes.") == [(0, 8, "PERSON_NAME")]  # posities buiten de tekst vallen af


def test_alle_avg_soorten_zonder_model():
    sys.path.insert(0, str(HIER / "tests" / "namen"))
    import os
    os.environ["NEST_PRIVACY_HERKENNER"] = "regels"
    import meet_gevoelig
    m = meet_gevoelig.meet()
    assert m["weg"] >= 0.75 and m["vals"] <= 0.05


def _zonder_model(monkeypatch):
    monkeypatch.setenv("NEST_PRIVACY_HERKENNER", "regels")


def test_aanhef_en_achternaam_na_voornaam(monkeypatch):
    _zonder_model(monkeypatch)
    import gevoelig

    uit, _ = gevoelig.vervang("Beste Caoimhe, de factuur staat klaar. Groet, team", modus="maskeren", eigen_woorden=[])
    assert "Caoimhe" not in uit and "factuur" in uit
    uit, _ = gevoelig.vervang("Hi team, de release staat klaar.", modus="maskeren", eigen_woorden=[])
    assert "team" in uit


def test_adres_zonder_gewone_woorden(monkeypatch):
    _zonder_model(monkeypatch)
    import gevoelig

    uit, _ = gevoelig.vervang("Het nieuwe adres is Roerdompweg 193 in Wapenveld.", modus="maskeren", eigen_woorden=[])
    assert uit.startswith("Het nieuwe adres is [ADRES] in")


def test_bijsnijden_houdt_tussenvoegsel():
    import gevoelig

    t = "Het nieuwe adres is Brem 12 in"
    assert t[slice(*gevoelig._bijsnijden(t, 0, len(t)))] == "Brem 12"
    t = "met van Wageningen gebeld"
    assert t[slice(*gevoelig._bijsnijden(t, 0, len(t)))] == "van Wageningen"


def test_taalmodel_via_eigen_omgeving(monkeypatch, tmp_path):
    """Zonder privacy_kit in deze Python gebruikt de plugin het model in de eigen omgeving, als lokaal proces."""
    import model_installeren
    import taalmodel

    nep = tmp_path / "python"
    nep.write_text("", encoding="utf-8")
    monkeypatch.setattr(model_installeren, "python_van_model", lambda: nep)
    monkeypatch.setitem(sys.modules, "privacy_kit", None)
    taalmodel._privacykit.cache_clear()
    try:
        d = taalmodel._privacykit()
        assert isinstance(d, taalmodel._ProcesDetector) and d.python == str(nep)
    finally:
        taalmodel._privacykit.cache_clear()
    monkeypatch.setattr(model_installeren, "python_van_model", lambda: tmp_path / "bestaat-niet")
    taalmodel._privacykit.cache_clear()
    assert taalmodel._privacykit() is None
    taalmodel._privacykit.cache_clear()


def test_model_status_zonder_installatie(monkeypatch, tmp_path):
    import model_installeren

    monkeypatch.setattr(model_installeren, "python_van_model", lambda: tmp_path / "geen")
    assert model_installeren.test() is False
    assert model_installeren.main(["--status"]) == 1
