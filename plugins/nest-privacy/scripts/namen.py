"""Namen herkennen in Nederlandse en Engelse tekst, ook zonder aanhef en met spelfouten. Lokaal, alleen de standaardbibliotheek.

    from namen import zoek_namen
    r = zoek_namen("Beste Piet, ... Met vriendelijke groet,\\nAnna de Vries")
    r.namen      -> {"Piet", "Anna de Vries", ...}   (voor anonimiseren.anonimiseer(..., extra_termen=r.namen))
    r.varianten  -> {"Janssen": "Jansen"}            (spelfout -> gevonden schrijfwijze, zodat beide dezelfde code krijgen)

Hoe: (1) lijsten met veelvoorkomende Nederlandse en Engelse voor- en achternamen; (2) aanwijzingen in de tekst: aanhef
(Beste, Dear, Hi), afsluiting (Met vriendelijke groet, Kind regards) met de naam op de regel erna, labels (naam:, name:,
klant:), voorletters (J.P.), tussenvoegsels (van der) en de naam in een e-mailadres (piet.jansen@); (3) spelfouten:
een hoofdletterwoord dat 1 letter (of bij lange namen 2) afwijkt van een gevonden naam, telt ook als die naam.
Grenzen: een naam die nergens op lijkt en zonder aanwijzing in een zin staat, mist hij nog. Controleer de uitkomst.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import taalmodel
from plaatsen import PLAATSEN

# Veelvoorkomende voornamen (NL en EN), kleine letters. Bewust geen woorden die meestal iets anders betekenen.
VOORNAMEN = set("""
aad aafke aart abdel abdul abel abraham adam adri adriaan adrie agnes ahmed aisha albert alex alexander alexandra ali alice
amber amelia amina amir amy andre andrea andreas andrew angela anita anja anke ann anna anne anneke annemarie annet annie
anouk antoon anton arend arie arjan arjen arnold arthur astrid aukje barbara bart bas bastiaan bea beatrix ben benjamin
bernard bert betty bianca bob boris bram brenda brian bruno carla carmen carol caroline casper cathy cees charles charlie
charlotte chantal chris christa christian christine cindy claire claudia cor corine cornelis daan daisy dana daniel daniëlle
danny david debby dennis diana dick diederik dirk dominique donna dorothy douwe dylan edith eduard edwin eline elisabeth
eliza ellen els elsa emily emma eric erik ester esther eva evelien fatima femke fleur floor floris frans freek frits gabriel
gerard gerrit gert gijs ginny gerda gert-jan geert hanna hannah hans harm harry hein hélène helen hendrik henk henry herman
hilde hugo ibrahim ilse inge ingrid iris isa isabel isabella ivo jaap jack jacob jacqueline jaime jan jana jane janet janneke
jasper jayden jelle jennifer jenny jeroen jesse jessica jet joanna jochem joep johan johanna john jolanda jonas joost jop
joris jos jose josé joseph josephine joyce judith julia julian julie jurgen justin karel karin kate katie kees kelly kevin
kim klaas koen kris laura lars laurens lea lena leo leon lieke lisa liam lies lieke linda lisanne lotte louis lucas lucy
luuk maaike maarten madelief manon marco marcel margriet maria marianne marie marieke marijke marjolein mark marleen martin
martine mary matthijs max maya melissa michael michel michelle mike milan mila mirjam mohamed mohammed monique nadia nathalie
nick nicole niels nina noah noor nora olivia olaf oliver otto patrick paul paula pauline peter petra piet pieter priscilla
quinten rachel ralph ramon raymond rebecca remco renate rené richard rick rik rinus rob robert robin roel roos ruben rudy
ruud sabine sam samuel sandra sanne sara sarah sebastiaan sem sharon simon sjaak sjoerd sophia sophie stefan stephanie
steven susan suzanne sven tamara tessa teun thijs thomas tim tineke tobias tom tommy tonnie ton twan valerie vera victor
vincent wendy wesley willem wim wouter yara yasmin yusuf yvonne zoe
""".split())

# Woorden die ook een gewoon woord zijn: alleen een naam met extra bewijs (achternaam erna, of een aanwijzing ervoor).
TWIJFEL = set("""bill bob bas daisy dick frank frans may june mark rose roos will grace hope joy faith iris amber floor
fleur jet ivo noor sam ben jack mike max victor guy art august floris olive pat ray sky storm summer wolf""".split())

ACHTERNAMEN = set("""
jansen janssen jansens de vries van den berg van dijk bakker visser smit meijer meyer mulder de boer bos vos peters hendriks
van leeuwen dekker brouwer de wit dijkstra smits de graaf van der meer van der linden kok jacobs de haan vermeulen van den
heuvel van der veen van den broek de bruijn de bruin van der heijden schouten van beek willems van vliet van de ven hoekstra
maas verhoeven koster van dam van der wal prins blom huisman peeters kuipers van wijk post kuiper veenstra kramer van den
brink scholten van wijngaarden martens vos de jong de jonge jonker de groot groot bosch van der berg hermans timmermans
wouters verbeek van rijn de lange lange postma koopman van es hoogendoorn schipper evers hofman van der laan
smith johnson williams brown jones miller davis wilson anderson taylor thomas moore martin jackson thompson white harris
clark lewis robinson walker young allen king wright scott green baker adams nelson hill campbell mitchell roberts carter
phillips evans turner parker collins edwards stewart morris murphy cook rogers morgan cooper peterson reed bailey bell kelly
""".split())

GEWONE_WOORDEN = set("""de het een en of in op aan met voor van te bij naar uit over onder door om als dan dus maar ook nog
wel niet geen dit dat deze die wie wat waar hoe waarom wanneer ik jij je u hij zij ze wij we jullie hun hen mij me mijn jouw
uw zijn haar ons onze beste geachte lieve hoi hallo dag groet groeten vriendelijke hartelijke bedankt dank alvast graag
the a an and or in on at to for of with from by as is are was were be been this that these those who what where when why
how i you he she we they my your his her our their dear hi hello hey regards kind best sincerely thanks thank cheers yours
maandag dinsdag woensdag donderdag vrijdag zaterdag zondag januari februari maart april mei juni juli augustus september
oktober november december monday tuesday wednesday thursday friday saturday sunday january february march april may june
july august september october november december nederland amsterdam rotterdam utrecht den haag eindhoven groningen
factuur offerte klant bestelling order invoice project team bedrijf afdeling""".split())

# Plaatsen, organisaties, merken en software: midden in een zin met hoofdletter, maar geen persoon.
GEEN_PERSOON = set("""
nederland belgië duitsland frankrijk engeland europa benelux amsterdam rotterdam utrecht haarlem leiden delft zwolle
amersfoort eindhoven groningen tilburg breda nijmegen arnhem apeldoorn enschede almere maastricht leeuwarden den bosch
hilversum loosdrecht london paris berlin brussel brussels antwerpen new york
gemeente provincie belastingdienst rijksoverheid overheid politie ministerie kamer van koophandel kvk uwv svb duo
microsoft google apple amazon meta facebook instagram whatsapp linkedin twitter youtube tiktok netflix spotify
windows office outlook excel word powerpoint teams sharepoint onedrive azure aws gmail chrome edge firefox safari
slack jira confluence trello asana notion zoom github gitlab claude chatgpt openai anthropic stripe mollie ideal paypal
coolblue bol albert heijn jumbo lidl aldi ikea hema kpn ziggo vodafone ing rabobank abn amro
portal dashboard app website menu instellingen beveiliging werkwijze klanten klant support helpdesk servicedesk
financiën hr it sales marketing directie team afdeling
lente zomer herfst winter spring summer autumn fall winter
""".split())
# Achtervoegsels van afgeleide achternamen: Pieter+sen, Hendrik+sen, John+son
AFGELEID = ("ssen", "sen", "sz", "szoon", "son", "sson", "se", "s")

_HOOFD = "A-ZÀ-ÖØ-Þ"
_KLEIN = "a-zß-öø-ÿ"
WOORD = rf"[{_HOOFD}][{_KLEIN}'’-]+"
TUSSEN = r"(?:van der|van den|van de|van|de|der|den|ten|ter|te|in 't|op de|op het|le|la|du|von|mc|o')"
VOORLETTERS = rf"(?:[{_HOOFD}]\.\s?){{1,4}}"
# Een volledige naam: (voorletters of voornaam) + (tussenvoegsels) + achternaam (+ dubbele naam met streepje)
NAAMREEKS = rf"(?:{VOORLETTERS}|{WOORD}\s+)?(?:{TUSSEN}\s+)?{WOORD}(?:-{WOORD})?"

AANHEF = re.compile(rf"\b(?:[Bb]este|[Gg]eachte|[Ll]ieve|[Hh]oi|[Hh]allo|[Dd]ag|[Dd]ear|[Hh]i|[Hh]ello|[Hh]ey)\s+(?:(?:heer|mevrouw|mr|mrs|ms|dr)\.?\s+)?({NAAMREEKS})")
AFSLUITING = re.compile(rf"(?im)^\s*(?:met\s+)?(?:vriendelijke|hartelijke|beste|warme)?\s*(?:groet(?:en)?|mvg|m\.v\.g\.|kind\s+regards|best\s+regards|regards|best|sincerely|cheers|thanks|groetjes)[,!.]?\s*\n\s*({NAAMREEKS})\s*$")
LABEL = re.compile(rf"(?i:\b(?:naam|name|klant|client|customer|contactpersoon|contact|patiënt|patient|medewerker|employee|van|from|aan|to|cc|t\.a\.v\.|attn)\s*:)[ \t]*({NAAMREEKS})")
VOORLETTERNAAM = re.compile(rf"(?<![\w.])({VOORLETTERS}(?:{TUSSEN}\s+)?{WOORD}(?:-{WOORD})?)")
TUSSENNAAM = re.compile(rf"\b({WOORD}\s+{TUSSEN}\s+{WOORD}(?:-{WOORD})?)")
HOOFDWOORD = re.compile(rf"(?<![\w@.]){WOORD}(?!\w)")
EMAIL = re.compile(r"\b([A-Za-z]+)[._-]([A-Za-z]+)@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


@dataclass
class Namen:
    namen: set[str] = field(default_factory=set)
    varianten: dict[str, str] = field(default_factory=dict)


def _afstand(a: str, b: str) -> int:
    """Damerau-Levenshtein (omwisselen telt als 1): genoeg voor tikfouten."""
    a, b = a.lower(), b.lower()
    d = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            kost = a[i - 1] != b[j - 1]
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + kost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]


def _toegestaan(woord: str) -> int:
    return 1 if len(woord) < 8 else 2


GEEN_NAAM_EINDE = re.compile(r"(?i)(?:ing|heid|tie|teit|schap|lijk|ment|kantoor|centrum|dienst|afdeling|groep|bedrijf|service|systeem|tion|ness|ment|ship)$")


def _schoon(naam: str) -> str | None:
    naam = re.sub(r"\s+", " ", naam).strip(" .,'’-")
    delen = [d for d in re.split(r"[\s-]", naam) if d]
    if any(GEEN_NAAM_EINDE.search(d) for d in delen if len(d) > 4):
        return None
    if not delen or all(d.lower().rstrip(".") in GEWONE_WOORDEN for d in delen):
        return None
    # Een gewoon woord achteraan (bijv. "Piet Graag") hoort er niet bij.
    while len(delen) > 1 and delen[-1].lower() in GEWONE_WOORDEN:
        naam = naam[: naam.rfind(delen[-1])].strip()
        delen = delen[:-1]
    return naam if len(naam) >= 2 else None


def _midden_in_zin(tekst: str, begin: int) -> bool:
    """Staat dit woord midden in een zin (dus niet aan het begin, na een punt, uitroepteken, vraagteken of dubbele punt)?"""
    regel = tekst[:begin].rsplit("\n", 1)[-1]  # alleen de huidige regel: een nieuwe regel is een nieuw begin
    voor = regel.rstrip(" \t\"'(“‘")
    return bool(voor) and voor[-1] not in ".!?:;•-–—"


PLAATS_VOOR = re.compile(r"(?i)\b(?:in|uit|te|vanuit|richting|regio|gemeente|provincie|stad|city)\s+$")


def _is_merk_of_code(woord: str) -> bool:
    """HubSpot, PostNL, iDEAL, SharePoint, B2B: hoofdletters of cijfers middenin = merk of code, geen persoonsnaam."""
    return any(c.isdigit() for c in woord) or any(c.isupper() for c in woord[1:]) and "-" not in woord and "'" not in woord


def _is_plaats(tekst: str, begin: int, woord: str) -> bool:
    return woord.lower() in PLAATSEN or bool(PLAATS_VOOR.search(tekst[:begin]))


def _afgeleid(woord: str) -> bool:
    """Pietersen, Hendriksen, Gerritsen, Johnson: een voornaam met een achtervoegsel."""
    w = woord.lower()
    for eind in AFGELEID:
        stam = w[: -len(eind)] if w.endswith(eind) else None
        if stam and len(stam) >= 3 and (stam in VOORNAMEN or stam.rstrip("s") in VOORNAMEN):
            return True
    return False


def zoek_namen(tekst: str) -> Namen:
    r = Namen()

    def voeg_toe(kandidaat: str | None) -> None:
        naam = _schoon(kandidaat or "")
        if naam:
            r.namen.add(naam)

    # 0. Een lokaal taalmodel, als dat er is (taalmodel.py). Het vervangt de zwakke regel "hoofdletter midden in een zin".
    model = taalmodel.personen(tekst)
    for naam in model or ():
        # Twijfelt het model bij een plaats, merk of gewoon woord, dan wint de lijst.
        if not all(d.lower() in PLAATSEN or d.lower() in GEEN_PERSOON or d.lower() in GEWONE_WOORDEN
                   for d in re.split(r"[\s-]+", naam.strip()) if d):
            voeg_toe(naam)

    # 1. Aanwijzingen in de tekst
    for patroon in (AANHEF, AFSLUITING, LABEL, VOORLETTERNAAM, TUSSENNAAM):
        for m in patroon.finditer(tekst):
            voeg_toe(m.group(1))
    # 2. Namen in e-mailadressen (piet.jansen@...)
    for m in EMAIL.finditer(tekst):
        for deel in m.groups():
            if len(deel) >= 2 and deel.lower() not in GEWONE_WOORDEN:
                r.namen.add(deel.capitalize())
    # 3. Lijsten: bekende voornaam (eventueel met achternaam erna) en bekende achternaam
    woorden = list(HOOFDWOORD.finditer(tekst))
    for i, m in enumerate(woorden):
        w = m.group(0)
        laag = w.lower()
        volgende = woorden[i + 1] if i + 1 < len(woorden) else None
        aansluitend = volgende and re.fullmatch(rf"\s+(?:{TUSSEN}\s+)?", tekst[m.end():volgende.start()])
        if laag in VOORNAMEN:
            if aansluitend and volgende.group(0).lower() not in GEWONE_WOORDEN:
                voeg_toe(tekst[m.start():volgende.end()])
            elif laag not in TWIJFEL:
                voeg_toe(w)
        elif laag in ACHTERNAMEN or _afgeleid(w):
            voeg_toe(w)
        elif (model is None and _midden_in_zin(tekst, m.start()) and laag not in GEWONE_WOORDEN and laag not in GEEN_PERSOON
              and len(w) >= 3 and not GEEN_NAAM_EINDE.search(w) and not _is_merk_of_code(w)
              and not _is_plaats(tekst, m.start(), w)):
            # Midden in een zin met hoofdletter: in het Nederlands bijna altijd een naam, plaats of merk.
            # Plaatsen en merken staan in GEEN_PERSOON; wat overblijft behandelen we als naam (liever te veel dan te weinig).
            begin = m.start()
            j = i
            while j + 1 < len(woorden) and re.fullmatch(rf"\s+(?:{TUSSEN}\s+)?|'", tekst[woorden[j].end():woorden[j + 1].start()]) and woorden[j + 1].group(0).lower() not in GEWONE_WOORDEN | GEEN_PERSOON:
                j += 1
            voeg_toe(tekst[begin:woorden[j].end()])
    # Meerdelige achternamen uit de lijst (van der Meer)
    for achternaam in (a for a in ACHTERNAMEN if " " in a):
        for m in re.finditer(rf"\b{re.escape(achternaam)}\b", tekst, re.IGNORECASE):
            if any(deel[:1].isupper() for deel in m.group(0).split()):
                voeg_toe(m.group(0))
    for m in re.finditer(rf"(?<![\w@.])[{_KLEIN}]{{5,}}(?![\w@])", tekst):
        if m.group(0) not in GEWONE_WOORDEN and _afgeleid(m.group(0)):
            r.namen.add(m.group(0))
    # 4. Spelfouten: hoofdletterwoorden die bijna gelijk zijn aan een gevonden naamdeel
    delen = {d for n in r.namen for d in re.split(r"[\s-]", n) if len(d) >= 4 and d.lower() not in GEWONE_WOORDEN
             and not re.fullmatch(TUSSEN, d.lower())}
    for m in woorden:
        w = m.group(0)
        if len(w) < 4 or w.lower() in GEWONE_WOORDEN or w in delen:
            continue
        beste = min(delen, key=lambda d: _afstand(w, d), default=None)
        if beste and w.lower() != beste.lower() and _afstand(w, beste) <= _toegestaan(beste) and w[0].lower() == beste[0].lower():
            r.varianten[w] = beste
    return r


def normaliseer(tekst: str, varianten: dict[str, str]) -> str:
    """Zet spelvarianten om naar de gevonden schrijfwijze, zodat ze dezelfde code krijgen."""
    for fout, goed in sorted(varianten.items(), key=lambda kv: -len(kv[0])):
        tekst = re.sub(rf"(?<!\w){re.escape(fout)}(?!\w)", goed, tekst)
    return tekst
