"""Grote, herhaalbare testset: python tests/namen/grote_set.py [aantal] [--meet]
Maakt realistische Nederlandse en Engelse zinnen (mails, tickets, notities, HR) met nep-gegevens. De set bevat zowel bekende als onbekende namen. De blinde zinnen zijn vooraf vastgelegd.
Vaste ruis (seed 2026): elke keer dezelfde set. Alle gegevens zijn verzonnen; geldig formaat (elfproef, mod-97, Luhn)."""
from __future__ import annotations

import json
import re
import random
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent.parent / "plugins" / "nest-privacy" / "scripts"))

VOORNAMEN = ["Wiebe", "Hidde", "Jorien", "Marit", "Ilona", "Gijsbert", "Jildou", "Siebren", "Tirza", "Folkert", "Meike", "Rutger",
             "Nadine", "Boudewijn", "Liesbeth", "Okan", "Elif", "Mehmet", "Samira", "Youssef", "Anouar", "Ngozi", "Tunde",
             "Dmitri", "Oksana", "Wojciech", "Agnieszka", "Raj", "Ananya", "Mei", "Hiroshi", "Camille", "Matteo", "Ines",
             "Caoimhe", "Rhys", "Bethany", "Declan", "Harriet", "Callum", "Esmée", "Thijmen", "Jurre", "Fenna", "Sietske"]
ACHTERNAMEN = ["Haverkamp", "Oosterbeek", "Klinkhamer", "Wijnstra", "Bergsma", "Hoogland", "Zwart", "Kuiperij", "Brouwershaven",
               "Yılmaz", "Kaya", "El Amrani", "Bouzid", "Okafor", "Adeyemi", "Nowak", "Wiśniewska", "Kuznetsov", "Petrenko",
               "Iyer", "Nakamura", "Lefèvre", "Romano", "Fitzgerald", "Llewellyn", "Ashworth", "Pemberton", "Harcourt",
               "van Wageningen", "de Wolff", "ter Horst", "van 't Hek", "Veldkamp-Mulder"]
STRATEN = ["Fluitekruidlaan", "Akkerwindestraat", "Kievitsbloem", "Zeeltstraat", "Roerdompweg", "Brem", "Gagelweg", "Ossekop"]
PLAATSEN_NIET_IN_LIJST = ["Oudewater-Noord", "Ruinerwold", "Wapenveld", "Hollandscheveld", "Ouddorp", "Vorden", "Lochem-Oost"]
BEDRIJVEN = ["Nordvik Logistiek", "Hapax Software", "Zuiderlicht BV", "Grafiet & Co", "Kade Analytics", "Pelikaan Zorggroep"]
PRODUCTEN = ["Odoo", "Moneybird", "Teamleader", "Monday.com", "Zendesk", "Shopify", "Asana", "Bitrix"]
ZIEKTES = ["diabetes", "burn-out", "depressie", "astma", "kanker", "epilepsie"]
ZIEKTES_EN = ["diabetes", "depression", "asthma", "cancer", "epilepsy"]


def bsn(r: random.Random) -> str:
    while True:
        c = [r.randint(0, 9) for _ in range(8)]
        som = sum(d * w for d, w in zip(c, range(9, 1, -1)))
        laatste = som % 11
        if laatste < 10 and c[0] != 0:
            s = "".join(map(str, c)) + str(laatste)
            if s not in ("111222333", "123456782"):
                return s


def iban(r: random.Random) -> str:
    bank = r.choice(["ABNA", "RABO", "INGB", "TRIO", "SNSB"])
    rek = "".join(str(r.randint(0, 9)) for _ in range(10))
    num = "".join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in bank + rek + "NL00")
    controle = 98 - int(num) % 97
    return f"NL{controle:02d}{bank}{rek}"


def telefoon(r: random.Random) -> str:
    return r.choice([f"06 {r.randint(10000000, 99999999)}", f"06-{r.randint(10000000, 99999999)}", f"+31 6 {r.randint(10000000, 99999999)}"])


def maak(aantal: int, seed: int = 2026) -> list[dict]:
    r = random.Random(seed)
    zinnen = []
    for _ in range(aantal):
        v, a = r.choice(VOORNAMEN), r.choice(ACHTERNAMEN)
        naam = f"{v} {a}"
        mail = f"{v.lower()}.{a.lower().replace(' ', '').replace(chr(39), '')}@{r.choice(['voorbeeldmail.nl', 'testpost.com'])}"
        mail = mail.encode("ascii", "ignore").decode()
        straat, nr = r.choice(STRATEN), r.randint(1, 240)
        bedrijf, product, plaats = r.choice(BEDRIJVEN), r.choice(PRODUCTEN), r.choice(PLAATSEN_NIET_IN_LIJST)
        bedrag = f"€ {r.randint(80, 9800)},{r.randint(0, 99):02d}"
        sjablonen = [
            (f"Beste {v}, je factuur van {bedrag} van {bedrijf} staat klaar.", [v], [bedrag.split()[1], bedrijf.split()[0]]),
            (f"Gisteren belde {naam} over de levering via {product}.", [v, a], [product, "levering"]),
            (f"Klant {naam} ({mail}) vraagt om een terugbelverzoek.", [v, a, mail], ["terugbelverzoek"]),
            (f"Het nieuwe adres is {straat} {nr} in {plaats}, schreef {v}.", [f"{straat} {nr}", v], ["nieuwe"]),
            (f"Graag het salaris overmaken naar {iban(r)} t.n.v. {naam}.", [naam.split()[0], "NL"], ["salaris"]),
            (f"BSN van de medewerker: {bsn(r)}. Telefoon {telefoon(r)}.", ["BSN_WAARDE", "TEL_WAARDE"], ["medewerker"]),
            (f"{v} heeft zich ziek gemeld met {r.choice(ZIEKTES)}.", [v, "ziek", "ZIEKTE"], ["gemeld"]),  # "ziek" zelf is ook een gezondheidsgegeven (AP)
            (f"Please ask {naam} to send the signed contract to {bedrijf}.", [v, a], ["contract", bedrijf.split()[0]]),
            (f"{v} mentioned an {r.choice(ZIEKTES_EN)} diagnosis during the meeting.", [v, "ZIEKTE"], ["meeting"]),
            (f"Ticket #{r.randint(1000, 9999)}: {product} geeft een foutmelding bij het exporteren.", [], [product, "foutmelding"]),
            (f"De offerte van {bedrijf} voor {bedrag} is goedgekeurd door de directie.", [], [bedrijf.split()[0], "directie"]),
            (f"Our warehouse in {plaats} ships orders via {product} on weekdays.", [], [product, "warehouse"]),
        ]
        t, weg, blijven = r.choice(sjablonen)
        echte_weg = []
        for w in weg:
            if w == "BSN_WAARDE":
                echte_weg.append(t.split("medewerker: ")[1].split(".")[0])
            elif w == "TEL_WAARDE":
                echte_weg.append(t.split("Telefoon ")[1].rstrip("."))
            elif w == "ZIEKTE":
                echte_weg += [z for z in ZIEKTES + ZIEKTES_EN if z in t][:1]
            elif w == "NL":
                echte_weg.append(t.split("naar ")[1].split(" ")[0])
            else:
                echte_weg.append(w)
        zinnen.append({"t": t, "weg": echte_weg, "blijven": [b for b in blijven if b]})
    return zinnen


BLIND_V = ["Lotte", "Sanne", "Bram", "Koen", "Iris", "Floor", "Ruben", "Nikita", "Priya", "Aleksander", "Zeynep", "Kofi",
           "Siobhan", "Gareth", "Imogen", "Ewout", "Hanneke", "Douwe", "Aafke", "Mirjam", "Yara", "Bilal", "Ilse", "Teun"]
BLIND_A = ["Doornbos", "Wesselink", "Hofstede", "Kramer", "Dekker", "van Leeuwen", "de Graaf", "Sahin", "Demir", "Mensah",
           "O'Brien", "Hughes", "Kowalczyk", "Ivanova", "Patel", "Tanaka", "Boer", "Nijenhuis", "Scholten", "van der Meulen"]
BLIND_STRAAT = ["Lindelaan", "Spoorstraat", "Molenweg", "Esdoornhof", "Kerkplein", "Beukenlaan"]


def maak_blind(aantal: int, seed: int = 7) -> list[dict]:
    """Blinde set: andere zinsbouw en andere namen dan maak(). Vastgelegd vóór het meten; niet op afstemmen."""
    r = random.Random(seed)
    zinnen = []
    for _ in range(aantal):
        v, a = r.choice(BLIND_V), r.choice(BLIND_A)
        straat, nr = r.choice(BLIND_STRAAT), r.randint(2, 180)
        tel, b = telefoon(r), bsn(r)
        product = r.choice(PRODUCTEN)
        sjablonen = [
            (f"Hoi {v},\nKun je morgen even naar {product} kijken? Groet, team support", [v], [product, "morgen"]),
            (f"Notitie: {v} {a} wil voortaan op dinsdag werken.", [v, a], ["dinsdag", "Notitie"]),
            (f"Afspraak met mevrouw {a} verplaatst naar vrijdag.", [a], ["vrijdag", "Afspraak"]),
            (f"Bezorgadres: {straat} {nr}, tel. {tel}.", [f"{straat} {nr}", tel], ["Bezorgadres"]),
            (f"Ik heb {v} gevraagd de rapportage in {product} af te ronden.", [v], [product, "rapportage"]),
            (f"Dear {v}, thanks for your patience with the {product} migration.", [v], [product, "migration"]),
            (f"{v} {a} is sinds maandag met zwangerschapsverlof.", [v, a], ["maandag"]),
            (f"Controleer BSN {b} van {v} voor de loonstrook.", [b, v], ["loonstrook"]),
            (f"The invoice was sent to {v} {a} last week.", [v, a], ["invoice", "week"]),
            ("Overleg over de planning van Q3 staat op donderdag.", [], ["planning", "donderdag", "Overleg"]),
            (f"De koppeling tussen {product} en de webshop is hersteld.", [], [product, "webshop"]),
            (f"Release 2.4 van {product} staat klaar voor de test.", [], [product, "Release"]),
        ]
        t, weg, blijven = r.choice(sjablonen)
        zinnen.append({"t": t, "weg": weg, "blijven": blijven})
    return zinnen


def meet(zinnen: list[dict]) -> dict:
    import gevoelig

    tot = weg = bl = vals = 0
    mis, ont = {}, {}
    for z in zinnen:
        tekst = z["t"]
        bedekt = set()
        for begin, eind, _ in gevoelig.vind(tekst, eigen_woorden=[]):
            bedekt.update(range(begin, eind))

        def posities(woord):
            return {i for m in re.finditer(re.escape(woord), tekst)
                    for i in range(m.start(), m.end()) if not tekst[i].isspace()}

        for w in z["weg"]:
            tot += 1
            verwacht = posities(w)
            if not verwacht or not verwacht <= bedekt:
                mis[w] = mis.get(w, 0) + 1
            else:
                weg += 1
        for w in z["blijven"]:
            bl += 1
            if posities(w) & bedekt:
                vals += 1
                ont[w] = ont.get(w, 0) + 1
    return {"weg": weg / tot, "vals": vals / bl, "n": tot, "b": bl,
            "gemist": sorted(mis.items(), key=lambda kv: -kv[1])[:12], "onterecht": sorted(ont.items(), key=lambda kv: -kv[1])[:12]}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    aantal = int(next((a for a in sys.argv[1:] if a.isdigit()), "300"))
    blind = "--blind" in sys.argv
    zinnen = maak_blind(aantal) if blind else maak(aantal)
    naam = "groot_blind.json" if blind else "groot.json"
    (HIER / naam).write_text(json.dumps({"uitleg": __doc__, "zinnen": zinnen}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(zinnen)} zinnen in tests/namen/{naam}")
    if "--meet" in sys.argv:
        m = meet(zinnen)
        print(f"{naam}  weg {m['weg']:.1%} van {m['n']}  geselecteerde controlewoorden geraakt {m['vals']:.1%} van {m['b']}")
        print("  meest gemist:", m["gemist"])
        print("  meest onterecht weg:", m["onterecht"])
