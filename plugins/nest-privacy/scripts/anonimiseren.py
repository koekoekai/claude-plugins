# bouwsteen: anonimiseren/kern-python 0.1.5  (bron: github.com/koekoekai/anonimiseren)
"""Persoonsgegevens in tekst en CSV vinden en vervangen. Alleen de standaardbibliotheek, werkt offline.

Gebruik:
    from anonimiseren import anonimiseer
    r = anonimiseer("Mail jan@voorbeeld.nl, BSN 111222333", modus="maskeren")
    r.tekst      -> "Mail [EMAIL], BSN [BSN]"
    r.vondsten   -> {"EMAIL": 1, "BSN": 1}   (alleen aantallen, nooit de waarden)

Modi:
- maskeren:   elke vondst wordt [SOORT]. Niet terug te draaien.
- pseudoniem: elke vondst wordt [SOORT-abcdef123456], via HMAC-SHA256 met een geheime sleutel. Dezelfde waarde geeft overal
              hetzelfde pseudoniem, zodat koppelen en tellen blijft werken. Zonder sleutel weigeren we: een BSN of
              postcode heeft zo weinig mogelijke waarden dat een hash zonder sleutel in minuten terug te rekenen is.
              Let op (AVG): pseudonieme data blijft persoonsgegevens zolang iemand de sleutel heeft.

Wat we herkennen: EMAIL, IBAN (mod-97), BSN (elfproef), TELEFOON (NL en buitenland), ADRES (straat + nummer), POSTCODE,
GEBOORTEDATUM (na "geboren", "geb." e.d.), IP (v4 en v6), NAAM (na een aanhef
zoals "dhr." of "mevrouw", plus namen die je zelf meegeeft via extra_termen). Losse namen zonder aanhef herkennen we
niet; daarvoor is een taalmodel nodig (volgende stap: Presidio + spaCy nl, zie anonimiseren/README.md).
"""

from __future__ import annotations

import codecs
import csv
import hashlib
import hmac
import io
import ipaddress
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

MODI = ("maskeren", "pseudoniem")

# ---------------------------------------------------------------- controles


def elfproef(cijfers: str) -> bool:
    """BSN-elfproef: 9 cijfers, gewichten 9..2 en -1, som deelbaar door 11, niet allemaal nul."""
    c = re.sub(r"\D", "", cijfers)
    if len(c) == 8:
        c = "0" + c
    if len(c) != 9 or c == "000000000":
        return False
    som = sum(int(d) * w for d, w in zip(c, (9, 8, 7, 6, 5, 4, 3, 2, -1)))
    return som % 11 == 0


def iban_geldig(waarde: str) -> bool:
    """IBAN-controle met mod-97 (ISO 13616)."""
    s = re.sub(r"\s", "", waarde).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", s):
        return False
    omgezet = "".join(str(int(t, 36)) for t in s[4:] + s[:4])
    return int(omgezet) % 97 == 1


def telefoon_geldig(waarde: str) -> bool:
    """NL-nummer: na omzetten van +31/0031 naar 0 precies 10 cijfers. Buitenlands (+xx, niet +31): 8 tot 15 cijfers."""
    c = re.sub(r"[^\d+]", "", waarde.replace("(0)", ""))
    if c.startswith("+31"):
        c = "0" + c[3:]
    elif c.startswith("0031"):
        c = "0" + c[4:]
    elif c.startswith("+"):
        return 8 <= len(c) - 1 <= 15
    return c.startswith("0") and len(c) == 10 and c.isdigit()


def ip_geldig(waarde: str) -> bool:
    try:
        ipaddress.ip_address(waarde)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------- herkenners


@dataclass(frozen=True)
class Herkenner:
    soort: str
    patroon: re.Pattern[str]
    controle: Callable[[str], bool] | None = None
    groep: int = 0  # welke regex-groep vervangen wordt (NAAM: alleen de naam, niet de aanhef)


_HOOFD = "A-ZÀ-ÖØ-Þ"
_KLEIN = "a-zß-öø-ÿ"
_NAAMDEEL = rf"[{_HOOFD}][{_KLEIN}'’-]+"
_TUSSENVOEGSEL = r"(?:[Vv]an|[Dd]e|[Dd]er|[Dd]en|[Hh]et|[Tt]en|[Tt]er|[Tt]e|[Ii]n\s't|[Oo]p\s(?:de|het))"
_STRAAT = r"(?:straat|laan|weg|plein|gracht|kade|singel|dijk|steeg|dreef|pad|markt|hof|park|plantsoen|erf|veld|baan|wal|haven|ring|allee)"
_MAAND = r"(?:jan(?:uari)?|feb(?:ruari)?|maart|mrt|apr(?:il)?|mei|jun[ie]?|jul[iy]?|aug(?:ustus)?|sep(?:t(?:ember)?)?|okt(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
_I = re.IGNORECASE

HERKENNERS: tuple[Herkenner, ...] = (
    Herkenner("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    # Hoofdletterongevoelig: een IBAN in kleine letters mag niet half blijven staan.
    Herkenner("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}(?:[ ]?[A-Z0-9]{1,3})?\b", _I), iban_geldig),
    # Geen letter of cijfer ervoor of erna: negen cijfers midden in een hash of id (lockfiles!) zijn geen BSN.
    Herkenner("BSN", re.compile(r"(?<![0-9A-Za-z])(?<!\d\.)(?:\d{9}|\d{4}\.\d{2}\.\d{3}|\d{3}[ .]\d{3}[ .]\d{3})(?![0-9A-Za-z])(?!\.\d)"), elfproef),
    Herkenner(
        "TELEFOON",
        re.compile(
            r"(?<![\w+])(?:"  # geen letter ervoor: anders vindt hij nummers midden in een code of IBAN
            r"(?:\+31|0031|0)[\s-]?(?:\(0\))?[\s-]?\d(?:[\s-]?\d){8}"  # NL
            r"|\(0\d{2,3}\)[\s-]?\d(?:[\s-]?\d){5,6}"  # (020) 123 4567
            r"|\+(?!31)\d{1,3}(?:[\s-]?\d){7,12}"  # buitenland
            r")(?!\d)"
        ),
        telefoon_geldig,
    ),
    Herkenner(
        "ADRES",
        re.compile(
            # Kerkstraat, Van der Valklaan. Alleen woorden met een hoofdletter of een tussenvoegsel ervoor, anders pakt
            # hij gewone woorden mee ("Het nieuwe adres is Kerkstraat 1").
            rf"(?:\b[{_HOOFD}][{_KLEIN}]+(?:[\s-](?:[{_HOOFD}][{_KLEIN}]+|{_TUSSENVOEGSEL}(?=[\s-][{_HOOFD}])))*{_STRAAT}"
            rf"|\b(?:Laan|Plein|Kade|Weg|Dijk|Hof|Singel|Gracht|Burgwal)\s+(?:{_TUSSENVOEGSEL}\s)*{_NAAMDEEL}(?:\s{_NAAMDEEL})*)"
            # toevoeging: 12a, 12-bis, 12 A of 12-3; niet "12 in" of "12 of"
            rf"\s+\d{{1,5}}(?:-?[A-Za-z]{{1,3}}\b|\s-?\s?[A-Z]\b|\s?-\s?\d{{1,4}})?\b"
        ),
    ),
    Herkenner("POSTCODE", re.compile(r"\b[1-9]\d{3}[ ]?(?![Ss][AaDdSs]\b)[A-Za-z]{2}\b")),
    Herkenner(
        "GEBOORTEDATUM",
        re.compile(
            rf"\b(?:geboortedatum|geb\.?\s?datum|geboren|geb\.|dob|date of birth)\s*(?:op\s+)?:?\s*"
            rf"(\d{{1,2}}[-/. ]\d{{1,2}}[-/. ]\d{{2,4}}|\d{{4}}-\d{{2}}-\d{{2}}|\d{{1,2}}\s+{_MAAND}\.?\s+\d{{4}})",
            _I,
        ),
        groep=1,
    ),
    Herkenner(
        "IP",
        re.compile(
            r"(?<!\d)(?<!\d\.)(?:\d{1,3}\.){3}\d{1,3}(?!\.?\d)"  # v4
            r"|(?<![\w:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:])"  # v6
        ),
        ip_geldig,
    ),
    Herkenner(
        "NAAM",
        re.compile(
            # Engelse aanspreekvormen alleen met hoofdletter: "200 ms Daarna" is geen naam.
            rf"\b(?:[Dd]hr|[Mm]evr|[Mm]w|[Mm]eneer|[Mm]evrouw|[Dd]e heer|[Hh]eer|Mr|Mrs|Ms)\.?\s+"
            rf"((?:[{_HOOFD}]\.\s?)*(?:{_TUSSENVOEGSEL}\s)*{_NAAMDEEL}(?:[\s-](?:{_TUSSENVOEGSEL}\s)*{_NAAMDEEL})*)"
        ),
        groep=1,
    ),
)

SOORTEN = tuple(h.soort for h in HERKENNERS)


# ---------------------------------------------------------------- kern


@dataclass
class Resultaat:
    tekst: str
    vondsten: Counter = field(default_factory=Counter)


def _normaliseer(soort: str, waarde: str) -> str:
    """Zelfde persoon = zelfde pseudoniem, ook als de schrijfwijze verschilt."""
    if soort in ("IBAN", "BSN", "POSTCODE"):
        return re.sub(r"[\s.]", "", waarde).upper()
    if soort == "TELEFOON":
        c = re.sub(r"\D", "", waarde.replace("(0)", ""))
        return "0" + c[2:] if c.startswith("31") else ("0" + c[4:] if c.startswith("0031") else c)
    if soort in ("EMAIL", "NAAM"):
        return " ".join(waarde.lower().split())
    return waarde


def _vervanging(soort: str, waarde: str, modus: str, sleutel: bytes | None) -> str:
    if modus == "maskeren":
        return f"[{soort}]"
    code = hmac.new(sleutel or b"", f"{soort}:{_normaliseer(soort, waarde)}".encode(), hashlib.sha256).hexdigest()[:12]  # 48 bits: botsingen pas rond miljoenen waarden
    return f"[{soort}-{code}]"


def _zoek(tekst: str, soorten: Iterable[str], extra_termen: Iterable[str]) -> list[tuple[int, int, str]]:
    gekozen = set(soorten)
    treffers: list[tuple[int, int, str]] = []
    for h in HERKENNERS:
        if h.soort not in gekozen:
            continue
        for m in h.patroon.finditer(tekst):
            waarde = m.group(h.groep)
            if h.controle and not h.controle(waarde):
                continue
            treffers.append((m.start(h.groep), m.end(h.groep), h.soort))
    for term in sorted({t.strip() for t in extra_termen if t and t.strip()}, key=len, reverse=True):
        for m in re.finditer(rf"(?<!\w){re.escape(term)}(?!\w)", tekst, flags=re.IGNORECASE):
            treffers.append((m.start(), m.end(), "NAAM"))
    # Overlap: de vroegste wint, bij gelijke start de langste.
    treffers.sort(key=lambda t: (t[0], -(t[1] - t[0])))
    gekozen_treffers: list[tuple[int, int, str]] = []
    einde = -1
    for t in treffers:
        if t[0] >= einde:
            gekozen_treffers.append(t)
            einde = t[1]
    return gekozen_treffers


def anonimiseer(
    tekst: str,
    modus: str = "maskeren",
    sleutel: str | bytes | None = None,
    soorten: Iterable[str] = SOORTEN,
    extra_termen: Iterable[str] = (),
) -> Resultaat:
    """Vervang persoonsgegevens in `tekst`. Geeft de nieuwe tekst en per soort het aantal vondsten."""
    if modus not in MODI:
        raise ValueError(f"onbekende modus {modus!r}, kies uit {MODI}")
    if isinstance(sleutel, str):
        sleutel = sleutel.encode()
    if modus == "pseudoniem" and (not sleutel or len(sleutel) < 16):
        raise ValueError("pseudoniem vraagt een geheime sleutel van minstens 16 tekens (zet ANONIEM_SLEUTEL)")
    if isinstance(soorten, str):
        soorten = [s.strip() for s in soorten.split(",")]
    soorten = [s.upper() for s in soorten]
    onbekend = set(soorten) - set(SOORTEN)
    if onbekend:
        raise ValueError(f"onbekende soort(en): {', '.join(sorted(onbekend))}")
    uit: list[str] = []
    vondsten: Counter = Counter()
    pos = 0
    for begin, eind, soort in _zoek(tekst, soorten, extra_termen):
        uit.append(tekst[pos:begin])
        uit.append(_vervanging(soort, tekst[begin:eind], modus, sleutel))
        vondsten[soort] += 1
        pos = eind
    uit.append(tekst[pos:])
    return Resultaat("".join(uit), vondsten)


# ---------------------------------------------------------------- CSV


_GETAL = re.compile(r"[-+]?\d+(?:[.,]\d+)*")


def _veilige_cel(waarde: str) -> str:
    """Tegen formule-injectie in Excel (standaard lokale-tool). Een gewoon getal als -5 of +3,50 blijft staan."""
    if waarde[:1] in ("=", "+", "-", "@", "\t", "\r") and not _GETAL.fullmatch(waarde):
        return "'" + waarde
    return waarde


def _naamdelen(naam: str) -> list[str]:
    """'Piet van der Klaassen' -> de hele naam plus 'Piet' en 'Klaassen' (los gebruikt in notities).
    Tussenvoegsels en delen korter dan 3 letters niet: die zouden overal treffers geven."""
    delen = [d for d in re.split(r"[\s,]+", naam.strip()) if len(d) >= 3 and not re.fullmatch(_TUSSENVOEGSEL, d)]
    return [naam.strip(), *delen]


def anonimiseer_csv(
    invoer: str,
    kolommen: Iterable[str] | None = None,
    naam_kolommen: Iterable[str] = (),
    scheidingsteken: str | None = None,
    **opties,
) -> Resultaat:
    """Anonimiseer een CSV-tekst (eerste regel = kolomnamen).
    `kolommen`: alleen deze kolommen doorzoeken (standaard alle).
    `naam_kolommen`: de hele cel is een naam en gaat altijd weg; de naam en de losse delen (voornaam, achternaam)
    worden ook in de andere kolommen van dezelfde rij opgezocht, bijv. in vrije notities.
    `scheidingsteken`: standaard automatisch (, ; of tab). Een onbekende kolomnaam is een fout, geen stille overslag."""
    if invoer.startswith("\ufeff"):
        invoer = invoer[1:]
    if not invoer.strip():
        return Resultaat("", Counter())
    if scheidingsteken:
        sep = scheidingsteken
    else:
        try:
            sep = csv.Sniffer().sniff(invoer[:8192], delimiters=",;\t").delimiter
        except csv.Error:
            sep = ","  # bijv. één kolom
    rijen = list(csv.reader(io.StringIO(invoer, newline=""), delimiter=sep))
    kop = rijen[0]
    naam_kolommen = list(naam_kolommen)
    onbekend = [k for k in [*(kolommen or []), *naam_kolommen] if k not in kop]
    if onbekend:
        raise ValueError(f"onbekende kolom(men): {', '.join(onbekend)}; aanwezig: {', '.join(kop)}")
    namen_i = [kop.index(k) for k in naam_kolommen]
    doen_i = [kop.index(k) for k in kolommen] if kolommen else list(range(len(kop)))
    totaal: Counter = Counter()
    uit = io.StringIO()
    schrijver = csv.writer(uit, delimiter=sep, lineterminator="\n")
    schrijver.writerow(kop)
    for rij in rijen[1:]:
        termen = [t for i in namen_i if i < len(rij) and rij[i].strip() for t in _naamdelen(rij[i])]
        nieuw: list[str] = []
        for i, waarde in enumerate(rij):  # ook cellen voorbij de kop: niets valt stil weg
            if i in namen_i and waarde.strip():
                r = anonimiseer(waarde, extra_termen=[waarde], **opties)
            elif i in doen_i or i >= len(kop):
                r = anonimiseer(waarde, extra_termen=termen, **opties)
            else:
                nieuw.append(_veilige_cel(waarde))
                continue
            totaal.update(r.vondsten)
            nieuw.append(_veilige_cel(r.tekst))
        schrijver.writerow(nieuw)
    return Resultaat(uit.getvalue(), totaal)


# ---------------------------------------------------------------- controleren (poort in de fabriek)

# Strenge set: weinig valse treffers in code. Namen, adressen en postcodes geven in broncode te veel ruis.
CONTROLE_SOORTEN = ("BSN", "IBAN", "EMAIL", "TELEFOON")
# Bekende, openbare testwaarden en voorbeelddomeinen: die mogen.
TESTWAARDEN = {"111222333", "123456782", "NL91ABNA0417164300", "0612345678", "0201234567", "0123456789"}
_TESTDOMEIN = re.compile(
    r"@(?:[\w.-]+\.)?(?:example\.(?:com|org|net|nl)|voorbeeld\.nl|test|localhost|invalid)\b"
    r"|^(?:no-?reply|noreply)@"
    r"|^\w@\w\.\w{2,3}$"  # a@b.nl: duidelijk nep
    r"|^git@(?:github\.com|gitlab\.com|bitbucket\.org|ssh\.dev\.azure\.com)$",  # SSH-adres van een git-host, geen persoon
    re.I,
)
# Alleen media en lettertypen mogen op extensie overgeslagen worden, en dan ALLEEN als de inhoud ook echt binair is
# (anders is het tekst met een valse extensie en wordt hij gewoon gecontroleerd). Documenten, archieven, spreadsheets,
# databases en onbekend binair geven altijd een melding: de AI-reviewer kan ze lezen, de poort niet.
_MEDIA = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".woff", ".woff2", ".ttf", ".otf", ".eot",
          ".mp3", ".mp4", ".wav", ".ogg", ".webm", ".onnx", ".pt", ".bin", ".safetensors", ".exe", ".dll"}
MAX_PII_OK_REGEL = 500  # 'pii: ok' geldt alleen voor gewone regels, niet voor een hele export op één regel
_REGELEINDE = re.compile(r"\r\n|\r|\n")


@dataclass(frozen=True)
class Melding:
    pad: str
    regel: int
    soort: str


def _negeer_patronen(map_: str, basis: str | None = None) -> list[str]:
    """Patronen uit .nest-pii-negeer in de root van de repo. Met `basis` (een git-ref) uit die commit, NIET uit de
    werkmap: zo kan een PR de poort niet uitzetten door zelf een regel `*` toe te voegen. Een nieuwe uitzondering werkt
    dus pas na de merge (na menselijk akkoord). Geen negeerlijst of een onbekende ref: niets wordt genegeerd."""
    import os
    import subprocess

    if basis:
        r = subprocess.run(["git", "-C", map_, "show", f"{basis}:.nest-pii-negeer"], capture_output=True)
        tekst = r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""
    else:
        pad = os.path.join(map_, ".nest-pii-negeer")
        if not os.path.exists(pad):
            return []
        with open(pad, encoding="utf-8") as f:
            tekst = f.read()
    return [r.strip() for r in tekst.splitlines() if r.strip() and not r.startswith("#")]


def controleer_tekst(tekst: str, pad: str = "-") -> list[Melding]:
    """Zoek persoonsgegevens per regel. Geeft alleen pad, regel en soort, nooit de waarde.
    Een regel met 'pii: ok' (bijv. in commentaar) wordt overgeslagen, maar alleen als hij korter is dan 500 tekens."""
    meldingen = []
    for nr, regel in enumerate(_REGELEINDE.split(tekst), 1):
        if "pii: ok" in regel and len(regel) <= MAX_PII_OK_REGEL:
            continue
        for begin, eind, soort in _zoek(regel, CONTROLE_SOORTEN, ()):
            waarde = regel[begin:eind]
            if _normaliseer(soort, waarde) in TESTWAARDEN or (soort == "EMAIL" and _TESTDOMEIN.search(waarde)):
                continue
            meldingen.append(Melding(pad, nr, soort))
    return meldingen


MAX_CONTROLE_BYTES = 200_000_000  # daarboven: rood, nooit stil overslaan


def _decodeer(regel: bytes) -> str:
    """UTF-8, anders Windows-1252 (Excel-exports): een andere codering mag nooit betekenen dat er niet gekeken wordt."""
    try:
        return regel.decode("utf-8")
    except UnicodeDecodeError:
        return regel.decode("cp1252", errors="replace")


def _utf16(begin: bytes) -> str | None:
    """'utf-16' als het begin UTF-16 is: een BOM, of NUL om de byte (PowerShell 5, Excel 'Unicode-tekst') én het begin
    is strikt als UTF-16 te lezen. Een binair bestand dat toevallig op het patroon lijkt, valt zo niet als tekst door."""
    if begin[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return "utf-16"
    paar = begin[: len(begin) - len(begin) % 2]
    if len(paar) < 4:
        return None
    oneven, even = paar[1::2], paar[0::2]
    for codering, nullen, tekens in (("utf-16-le", oneven, even), ("utf-16-be", even, oneven)):
        if nullen.count(0) > 0.9 * len(nullen) and tekens.count(0) < 0.1 * len(tekens):
            try:  # incrementeel: een teken dat over de grens van het blok valt is geen fout
                codecs.getincrementaldecoder(codering)("strict").decode(paar, final=False)
            except UnicodeDecodeError:
                return None
            return codering
    return None


def _regels(f, codering: str | None):
    """Regels van een open (binair) bestand als tekst; grote bestanden worden niet in één keer ingelezen.
    UTF-16 wordt strikt gelezen: een UTF-16-voorstuk met daarna iets anders geeft UnicodeDecodeError (= melding)."""
    import io

    if codering:
        yield from io.TextIOWrapper(f, encoding=codering, errors="strict", newline="")
    else:
        for ruw in f:
            yield _decodeer(ruw)


def _binair(begin: bytes) -> bool:
    return b"\0" in begin


def controleer_bestanden(paden: Iterable[str], map_: str = ".", basis: str | None = None) -> list[Melding]:
    """Controleert bestanden regel voor regel, ook grote, UTF-16- en Windows-1252-bestanden. Kan een bestand niet
    gecontroleerd worden (ontbreekt, te groot, onleesbaar, binair, symlink naar buiten de repo), dan is dat een melding:
    de poort slaat nooit stil iets over. Bewust overgeslagen: mappen (submodules), symlinks binnen de repo (het doel wordt
    zelf gecontroleerd), echte media en lettertypen (extensie én binaire inhoud) en .nest-pii-negeer (uit `basis`)."""
    import fnmatch
    import os

    negeer = _negeer_patronen(map_, basis)
    repo = os.path.realpath(map_)
    meldingen: list[Melding] = []
    for pad in paden:
        rel = os.path.relpath(pad, map_).replace(os.sep, "/")
        if any(fnmatch.fnmatch(rel, p) for p in negeer):
            continue
        if os.path.islink(pad):
            doel = os.path.realpath(pad)
            if os.path.commonpath([repo, doel]) != repo:
                meldingen.append(Melding(rel, 1, "NIET-GECONTROLEERD (symlink naar buiten de repo)"))
            continue
        if os.path.isdir(pad):
            continue
        if not os.path.isfile(pad):
            meldingen.append(Melding(rel, 1, "NIET-GECONTROLEERD (bestand niet gevonden)"))
            continue
        if os.path.getsize(pad) > MAX_CONTROLE_BYTES:
            meldingen.append(Melding(rel, 1, "NIET-GECONTROLEERD (te groot; zet het in .nest-pii-negeer als het geen data is)"))
            continue
        try:
            with open(pad, "rb") as f:
                begin = f.read(8192)
                codering = _utf16(begin)
                if _binair(begin) and not codering:
                    if os.path.splitext(pad)[1].lower() in _MEDIA:
                        continue  # echte afbeelding, lettertype of model
                    meldingen.append(Melding(rel, 1, "NIET-GECONTROLEERD (binair: document, archief, spreadsheet of database; "
                                                     "anonimiseer of zet het na akkoord in .nest-pii-negeer)"))
                    continue
                f.seek(0)
                teller = 0  # eigen regelteller over \r\n, \r en \n, gelijk aan controleer_tekst
                try:
                    for tekst in _regels(f, codering):
                        delen = _REGELEINDE.split(tekst)
                        if delen and delen[-1] == "":
                            delen.pop()  # het regeleinde zelf
                        for i, deel in enumerate(delen or [""]):
                            meldingen.extend(Melding(rel, teller + i + 1, m.soort) for m in controleer_tekst(deel, rel))
                        teller += len(delen or [""])
                except UnicodeDecodeError:
                    meldingen.append(Melding(rel, teller + 1, "NIET-GECONTROLEERD (gemengde codering)"))
        except OSError:
            meldingen.append(Melding(rel, 1, "NIET-GECONTROLEERD (onleesbaar)"))
    return meldingen


# ---------------------------------------------------------------- CLI


def controleer_main(argv: list[str]) -> int:
    """python anonimiseren.py controleer [bestanden...]   (leeg = alle bestanden in git)
    python anonimiseren.py controleer --sinds origin/main   (alleen gewijzigd t.o.v. die ref)
    Exitcode 1 bij een vondst. Overslaan: .nest-pii-negeer (glob per regel) of 'pii: ok' op de regel."""
    import argparse
    import subprocess
    import sys

    p = argparse.ArgumentParser(prog="anonimiseren.py controleer", description=controleer_main.__doc__)
    p.add_argument("bestanden", nargs="*")
    p.add_argument("--sinds", help="git-ref; alleen bestanden die sindsdien veranderden")
    a = p.parse_args(argv)
    if a.bestanden:
        paden = a.bestanden
    else:
        # -z en core.quotePath=false: paden met spaties of bijzondere tekens (klanten-ö.csv) komen letterlijk terug.
        # --diff-filter=d: alles behalve verwijderd (ook hernoemd, gekopieerd en van type veranderd, bijv. symlink -> bestand).
        git = ["git", "-c", "core.quotePath=false"]
        cmd = [*git, "diff", "--name-only", "-z", "--diff-filter=d", f"{a.sinds}...HEAD"] if a.sinds else [*git, "ls-files", "-z"]
        uit = subprocess.run(cmd, capture_output=True, check=True).stdout.decode("utf-8", "surrogateescape")
        paden = [r for r in uit.split("\0") if r]
    # Met --sinds komt de negeerlijst uit de basis: een PR kan de poort niet voor zichzelf uitzetten.
    meldingen = controleer_bestanden(paden, basis=a.sinds)
    for m in meldingen:
        # GitHub-annotatie: verschijnt bij de regel in de PR, zonder de waarde.
        print(f"::error file={m.pad},line={m.regel}::mogelijk persoonsgegeven ({m.soort}); anonimiseer, of markeer met 'pii: ok' als het nep is")
    print(f"persoonsgegevens: {len(meldingen)} melding(en) in {len(paden)} bestand(en)", file=sys.stderr)
    return 1 if meldingen else 0


def main(argv: list[str] | None = None) -> int:
    import argparse
    import os
    import sys

    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["controleer"]:
        return controleer_main(argv[1:])
    p = argparse.ArgumentParser(
        description="Persoonsgegevens vervangen in tekst of CSV (offline). Controleren: 'anonimiseren.py controleer -h'."
    )
    p.add_argument("bestand", nargs="?", help="tekst- of .csv-bestand; leeg = stdin")
    p.add_argument("-o", "--uit", help="uitvoerbestand; leeg = stdout")
    p.add_argument("--modus", choices=MODI, default="maskeren")
    p.add_argument("--soorten", help=f"kommalijst uit {','.join(SOORTEN)} (standaard alle)")
    p.add_argument("--kolommen", help="CSV: alleen deze kolommen")
    p.add_argument("--naamkolommen", help="CSV: kolommen die een naam bevatten")
    p.add_argument("--namen", help="bestand met namen (één per regel) die altijd weg moeten")
    a = p.parse_args(argv)

    tekst = open(a.bestand, encoding="utf-8-sig", newline="").read() if a.bestand else sys.stdin.read()
    opties = {
        "modus": a.modus,
        "sleutel": os.environ.get("ANONIEM_SLEUTEL"),
        "soorten": a.soorten.split(",") if a.soorten else SOORTEN,
    }
    try:
        if a.bestand and a.bestand.lower().endswith(".csv"):
            r = anonimiseer_csv(
                tekst,
                kolommen=a.kolommen.split(",") if a.kolommen else None,
                naam_kolommen=a.naamkolommen.split(",") if a.naamkolommen else (),
                **opties,
            )
        else:
            termen = open(a.namen, encoding="utf-8").read().splitlines() if a.namen else ()
            r = anonimiseer(tekst, extra_termen=termen, **opties)
    except ValueError as fout:
        print(f"fout: {fout}", file=sys.stderr)
        return 2
    if a.uit:
        with open(a.uit, "w", encoding="utf-8", newline="") as f:
            f.write(r.tekst)
    else:
        sys.stdout.write(r.tekst)
    samenvatting = ", ".join(f"{s} {n}" for s, n in sorted(r.vondsten.items())) or "niets gevonden"
    print(f"vervangen: {samenvatting}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
