"""Alle gevoelige gegevens volgens de AVG vinden en vervangen door codes (terug te zetten met de vertaaltabel).

Bronnen, samengevoegd:
1. Onze controles (anonimiseren.py): e-mail, IBAN (mod-97), BSN (elfproef), telefoon, adres, postcode, geboortedatum, IP.
2. Geheimen (geheimen.py) en hieronder: wachtwoorden na "wachtwoord:", betaalkaarten (Luhn) en CVC.
3. Namen (namen.py): ook zonder aanhef, spelvarianten, afgeleide achternamen.
4. Een lokaal taalmodel (taalmodel.py, Privacy Kit), als dat er is: persoonsnummers, kentekens, accounts, adressen enz.
5. Bijzondere persoonsgegevens (AVG art. 9 en 10) met woordenlijsten: gezondheid, vakbond, politiek, geloof, afkomst,
   geaardheid, strafrecht.
6. Een eigen woordenlijst (klantnamen, projecten, servers): .nest-privacy-woorden in het project of ~/.koekoek/nest-privacy/woorden.txt

Standaard blijven staan (geen persoonsgegevens): bedrijven, bedragen, plaatsen zonder huisnummer, producten.
Aanzetten kan met extra=("BEDRAG", "ORGANISATIE", "PLAATS").
"""
from __future__ import annotations

import re
from pathlib import Path

import anonimiseren
import geheimen
import namen
import taalmodel

# Model-label -> onze soort (alleen letters: de code is [SOORT-abcdef123456])
MODEL_SOORT = {
    "PERSON_NAME": "NAAM", "PERSON_ALIAS": "NAAM", "DATE_OF_BIRTH": "GEBOORTEDATUM",
    "PERSON_IDENTIFIER": "PERSOONSNUMMER", "DOCUMENT_IDENTIFIER": "DOCUMENTNUMMER",
    "EMAIL_ADDRESS": "EMAIL", "PHONE_NUMBER": "TELEFOON", "POSTAL_ADDRESS": "ADRES",
    "BANK_ACCOUNT_IDENTIFIER": "REKENING", "PAYMENT_CARD": "BETAALKAART", "PAYMENT_CARD_SECURITY": "CVC",
    "AUTH_SECRET": "GEHEIM", "ACCOUNT_IDENTIFIER": "ACCOUNT", "CONTACT_HANDLE": "ACCOUNT",
    "DEVICE_IDENTIFIER": "APPARAAT", "IP_ADDRESS": "IP", "VEHICLE_IDENTIFIER": "KENTEKEN",
    "IDENTIFYING_LINK": "LINK", "GEO_LOCATION": "LOCATIE", "PERSON_ATTRIBUTE": "KENMERK",
    "HEALTH_DATA": "GEZONDHEID", "ETHNIC_ORIGIN": "AFKOMST", "RELIGION_OR_BELIEF": "GELOOF",
    "POLITICAL_OPINION": "POLITIEK", "SEXUAL_ORIENTATION": "GEAARDHEID", "TRADE_UNION_MEMBERSHIP": "VAKBOND",
    "BIOMETRIC_DATA": "BIOMETRIE", "CRIMINAL_OFFENCE_DATA": "STRAFRECHT",
    # alleen met extra=...:
    "FINANCIAL_AMOUNT": "BEDRAG", "ORGANIZATION_NAME": "ORGANISATIE", "ORGANIZATION_IDENTIFIER": "ORGANISATIE",
    "LOCATION": "PLAATS",
}
OPTIONEEL = {"BEDRAG", "ORGANISATIE", "PLAATS"}

# Bijzondere persoonsgegevens: woorden die op zichzelf al gevoelig zijn als ze over een persoon gaan (NL en EN).
BIJZONDER = {
    "GEZONDHEID": """diabetes suikerziekte kanker tumor leukemie depressie depressief burn-out burnout overspannen adhd autisme
        autistisch epilepsie astma copd hartaanval hartinfarct beroerte herseninfarct dementie alzheimer parkinson multiple-sclerose hiv aids
        hepatitis zwanger zwangerschap miskraam abortus verslaving verslaafd alcoholisme psychose schizofrenie bipolair angststoornis
        paniekaanvallen eetstoornis anorexia boulimia ptss trauma chemotherapie dialyse insuline antidepressiva ziekteverlof
        arbeidsongeschikt wia wao diagnose depression depressed cancer anxiety pregnant pregnancy miscarriage addiction
        schizophrenia bipolar dementia epilepsy asthma chemotherapy disability""",
    "VAKBOND": """fnv cnv vcp fnv-lid vakbond vakbondslid vakbondslidmaatschap unison gmb trade-union""",
    "POLITIEK": """vvd pvda groenlinks groenlinks-pvda d66 cda pvv christenunie sgp pvdd ja21 bbb nsc fvd 50plus tories""",
    "GELOOF": """moslim moslima islamitisch christen christelijk katholiek rooms-katholiek protestant protestants gereformeerd hervormd
        joods jood hindoe hindoeïstisch boeddhist boeddhistisch atheïst sikh muslim christian catholic jewish hindu buddhist
        atheist""",
    "GEAARDHEID": """homo homoseksueel lesbisch lesbienne biseksueel transgender transvrouw transman non-binair queer
        gay lesbian bisexual""",
    "AFKOMST": """marokkaans turks surinaams antilliaans afghaans syrisch eritrees roma sinti""",
    "STRAFRECHT": """strafblad veroordeeld veroordeling gedetineerd detentie gevangenis taakstraf diefstal fraude oplichting
        mishandeling geweldsdelict zedendelict drugsdelict witwassen verduistering vog-geweigerd proeftijd reclassering
        convicted conviction criminal-record theft assault""",
}


def _woorden_patroon(lijst: str) -> re.Pattern:
    termen = sorted({t.replace("-", r"[\s-]") for t in lijst.split()}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(termen) + r")(?!\w)", re.IGNORECASE)


BIJZONDER_RE = {soort: _woorden_patroon(lijst) for soort, lijst in BIJZONDER.items()}
# "Partij voor de Dieren", "Forum voor Democratie" als meerdere woorden
POLITIEK_LANG = re.compile(r"(?i)\b(?:partij\s+voor\s+de\s+dieren|forum\s+voor\s+democratie|unite\s+the\s+union)\b")
# na ":" of "=" telt elke waarde; na "is"/"was" alleen een waarde met cijfers of tekens ("is verlopen" is geen wachtwoord)
WACHTWOORD = re.compile(r"(?i)\b(?:wachtwoord|password|passwd|pincode|pin)(?:\s*[:=]\s*['\"]?(\S{4,}?)|\s+(?:is|was)\s+['\"]?((?=\S*[\d!@#$%^&*?_])\S{4,}?))['\".,;]?(?=\s|$)")
WACHTWOORD_LOS = re.compile(r"(?i)\b(?:wachtwoord|password|passwd)\s+((?=\S*[\d!@#$%^&*?_])\S{6,}?)['\".,;]?(?=\s|$)")
CVC = re.compile(r"(?i)\b(?:cvc|cvv|cvc2|beveiligingscode)\s*:?\s*(\d{3,4})\b")
KAART = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")


def _luhn(cijfers: str) -> bool:
    c = [int(x) for x in re.sub(r"\D", "", cijfers)][::-1]
    return 13 <= len(c) <= 19 and sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(c)) % 10 == 0


def woordenlijst(map_: Path | None = None) -> list[str]:
    """Eigen termen die altijd weg moeten: projectbestand .nest-privacy-woorden en ~/.koekoek/nest-privacy/woorden.txt."""
    import kluis

    termen = []
    for pad in ((map_ or Path.cwd()) / ".nest-privacy-woorden", kluis.MAP / "woorden.txt"):
        if pad.is_file():
            termen += [r.strip() for r in pad.read_text(encoding="utf-8").splitlines() if r.strip() and not r.startswith("#")]
    return termen


def vind(tekst: str, extra: tuple[str, ...] = (), eigen_woorden: list[str] | None = None) -> list[tuple[int, int, str]]:
    """Alle gevoelige stukken: (begin, eind, soort), zonder overlap."""
    s: list[tuple[int, int, str, int]] = []  # (begin, eind, soort, voorrang: hoger wint bij gelijke lengte)
    al_code = [(m.start(), m.end()) for m in re.finditer(r"\[[A-Z]+(?:-[0-9a-f]{12})?\]", tekst)]  # bestaande codes laten staan

    def zet(b: int, e: int, soort: str, voorrang: int) -> None:
        if e > b:
            s.append((b, e, soort, voorrang))

    # 1. onze controles (met controlegetal: hoogste voorrang)
    for b, e, soort in anonimiseren._zoek(tekst, anonimiseren.SOORTEN, ()):
        zet(b, e, soort, 3)
    # 2. geheimen, wachtwoorden, betaalkaarten
    for soort, patroon in geheimen.SOORTEN:
        for m in patroon.finditer(tekst):
            if soort == "WACHTWOORD":  # alleen de waarde, niet het woord "password"
                zet(m.start(1), m.end(1), "GEHEIM", 3)
            else:
                zet(m.start(), m.end(), "GEHEIM", 3)
    for m in WACHTWOORD.finditer(tekst):
        g = 1 if m.group(1) else 2
        zet(m.start(g), m.end(g), "GEHEIM", 3)
    for m in WACHTWOORD_LOS.finditer(tekst):  # "wachtwoord Zomer2026!x": een waarde met cijfers of tekens erin
        zet(m.start(1), m.end(1), "GEHEIM", 3)
    for m in CVC.finditer(tekst):
        zet(m.start(1), m.end(1), "CVC", 3)
    for m in KAART.finditer(tekst):
        if _luhn(m.group(0)):
            zet(m.start(), m.start() + len(m.group(0).rstrip(" -")), "BETAALKAART", 3)
    # 3. namen (ook spelvarianten): elke vindplaats
    gevonden = namen.zoek_namen(tekst)
    for naam in sorted(set(gevonden.namen) | set(gevonden.varianten), key=len, reverse=True):
        for m in re.finditer(rf"(?<!\w){re.escape(naam)}(?!\w)", tekst, re.IGNORECASE):
            zet(m.start(), m.end(), "NAAM", 2)
    # 4. taalmodel (alle soorten)
    for b, e, label in taalmodel.spans(tekst) or ():
        soort = MODEL_SOORT.get(label)
        if not soort:
            continue
        if soort == "PLAATS" and any(c.isdigit() for c in tekst[b:e]):
            soort = "ADRES"  # straat met huisnummer is een adres, een losse plaats niet
        if soort in OPTIONEEL and soort not in extra:
            continue
        zet(b, e, soort, 1)
    # 5. bijzondere persoonsgegevens
    for soort, patroon in BIJZONDER_RE.items():
        for m in patroon.finditer(tekst):
            zet(m.start(), m.end(), soort, 2)
    for m in POLITIEK_LANG.finditer(tekst):
        zet(m.start(), m.end(), "VAKBOND" if "union" in m.group(0).lower() else "POLITIEK", 2)
    # 6. eigen woordenlijst
    for term in sorted(set(eigen_woorden if eigen_woorden is not None else woordenlijst()), key=len, reverse=True):
        for m in re.finditer(rf"(?<!\w){re.escape(term)}(?!\w)", tekst, re.IGNORECASE):
            zet(m.start(), m.end(), "EIGEN", 3)

    # Overlap: langste wint, bij gelijke lengte de hoogste voorrang, dan de vroegste.
    s.sort(key=lambda t: (-(t[1] - t[0]), -t[3], t[0]))
    bezet: list[tuple[int, int]] = list(al_code)
    gekozen = []
    for b, e, soort, _ in s:
        if any(b < be and e > bb for bb, be in bezet):
            continue
        bezet.append((b, e))
        gekozen.append((b, e, soort))
    return sorted(gekozen)


def vervang(tekst: str, modus: str = "pseudoniem", sleutel: bytes | None = None, extra: tuple[str, ...] = (),
            eigen_woorden: list[str] | None = None, onthoud=None) -> tuple[str, dict[str, int]]:
    """Vervangt alles wat vind() oplevert. onthoud(code, waarde) wordt aangeroepen voor de vertaaltabel."""
    uit, pos, telling = [], 0, {}
    for b, e, soort in vind(tekst, extra, eigen_woorden):
        waarde = tekst[b:e]
        code = anonimiseren._vervanging(soort, waarde, modus, sleutel)
        if onthoud:
            onthoud(code, waarde)
        uit += [tekst[pos:b], code]
        telling[soort] = telling.get(soort, 0) + 1
        pos = e
    uit.append(tekst[pos:])
    return "".join(uit), telling
