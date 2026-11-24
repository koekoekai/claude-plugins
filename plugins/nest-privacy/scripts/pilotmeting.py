"""Meet lokaal de afdekking van handmatig gemarkeerde tekst."""
import codecs
from contextlib import ExitStack, contextmanager
import json
import os
from pathlib import Path
import re
import sys
from unittest.mock import patch

VELDEN = ("gemarkeerd", "volledig", "gedeeltelijk", "gemist", "onterecht_woorden")
TEKSTBESTANDEN = {".txt", ".md", ".csv", ".eml"}
KRITISCH = ("BSN", "IBAN", "GEZONDHEID")  # hier mag niets van gemist worden (lat van de pilot)
LAT_VOLLEDIG = 0.98
RAPPORT = "pilotmeting.json"


def markeringen(bron, soorten):
    delen = []
    markeringen = []
    begin = None
    vorige = positie = 0
    for teken in re.finditer(r"\[\[|\]\]", bron):
        deel = bron[vorige:teken.start()]
        if teken.group() == "[[":
            if begin is not None:
                raise ValueError
            begin = positie + len(deel)
        else:
            if begin is None:
                raise ValueError
            soort, scheiding, waarde = deel.partition(":")
            if scheiding and soort in soorten:
                deel = waarde
            else:
                soort = "ONGESPECIFICEERD"
            if not deel.strip():
                raise ValueError
            markeringen.append((begin, begin + len(deel), soort))
            begin = None
        delen.append(deel)
        positie += len(deel)
        vorige = teken.end()
    if begin is not None:
        raise ValueError
    delen.append(bron[vorige:])
    return "".join(delen), markeringen


def tel(tekst, markeringen, treffers, rijen):
    def rij(soort):
        return rijen.setdefault(soort, dict.fromkeys(VELDEN, 0))

    geraakt = bytearray(len(tekst))
    bedoeld = bytearray(len(tekst))
    for b, e, _ in treffers:
        geraakt[b:e] = bytes([1]) * (e - b)
    for b, e, soort in markeringen:
        bedoeld[b:e] = bytes([1]) * (e - b)
        aantal = sum(geraakt[b:e])
        uitkomst = "volledig" if aantal == e - b else "gedeeltelijk" if aantal else "gemist"
        rij(soort)["gemarkeerd"] += 1
        rij(soort)[uitkomst] += 1

    # Eén woord telt één keer, bij de eerste treffer op een ongemarkeerde letter.
    woorden = iter(re.finditer(r"\w+", tekst))
    woord = next(woorden, None)
    for b, e, soort in treffers:
        while woord and woord.start() < e:
            links, rechts = max(b, woord.start()), min(e, woord.end())
            if links < rechts and 0 in bedoeld[links:rechts]:
                rij(soort)["onterecht_woorden"] += 1
            elif woord.end() > e:
                break
            woord = next(woorden, None)


@contextmanager
def stille_herkenning():
    # Ook meldingen van native modelbibliotheken mogen geen brontekst tonen.
    with ExitStack() as stack:
        nul = stack.enter_context(open(os.devnull, "wb"))
        for stream in (sys.stdout, sys.stderr):
            stream.flush()
            fd = stream.fileno()
            origineel = os.dup(fd)
            stack.callback(os.close, origineel)
            stack.callback(os.dup2, origineel, fd)
            os.dup2(nul.fileno(), fd)
            stack.callback(stream.flush)
        yield


def volg_model(stack, module, functie, naam, gebruikt):
    oorspronkelijk = getattr(module, functie)

    def gevolgd(*args):
        resultaat = oorspronkelijk(*args)
        if resultaat is not None:
            gebruikt.add(naam)
        return resultaat

    stack.enter_context(patch.object(module, functie, gevolgd))


def meet(paden):
    import gevoelig
    import taalmodel

    gebruikt = set()
    rijen = {}
    soorten = set(gevoelig.anonimiseren.SOORTEN) | set(gevoelig.MODEL_SOORT.values()) | {"EIGEN"}
    with ExitStack() as stack:
        for functie, naam in (("_pk_stukken", "privacykit"), ("_gliner", "gliner"), ("_spacy", "spacy")):
            volg_model(stack, taalmodel, functie, naam, gebruikt)
        for pad in paden:
            data = pad.read_bytes()
            utf16 = data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE))
            tekst, merken = markeringen(data.decode("utf-16" if utf16 else "utf-8-sig"), soorten)
            tel(tekst, merken, gevoelig.vind(tekst), rijen)
    totaal = {k: sum(r[k] for r in rijen.values()) for k in VELDEN}
    return {"bestanden": len(paden), "herkenners": ["regels"] + sorted(gebruikt),
            "per_soort": rijen, "totaal": totaal, "samenvatting": samenvatting(rijen, totaal)}


def samenvatting(rijen, totaal):
    """In een oogopslag: hoeveel procent helemaal weg, en of er iets kritisch is blijven staan."""
    deel = totaal["volledig"] / totaal["gemarkeerd"] if totaal["gemarkeerd"] else 0.0
    kritisch = {s: rijen[s]["gedeeltelijk"] + rijen[s]["gemist"] for s in KRITISCH if s in rijen}
    return {"volledig_weg_procent": round(deel * 100, 1),
            "kritisch_niet_helemaal_weg": kritisch,
            "lat_gehaald": deel >= LAT_VOLLEDIG and not any(kritisch.values()),
            "lat": f"minstens {LAT_VOLLEDIG:.0%} helemaal weg en niets van {', '.join(KRITISCH)} gemist"}


def main(args):
    if not args:
        print("Gebruik: pilotmeting.py <map of bestanden>")
        return 2
    try:
        paden = set()
        for arg in args:
            pad = Path(arg)
            if pad.is_dir():
                paden.update(p.resolve() for p in pad.iterdir() if p.suffix.lower() in TEKSTBESTANDEN and p.is_file())
            elif pad.is_file():
                paden.add(pad.resolve())
            else:
                raise ValueError
        if not paden:
            print("Geen tekstbestanden gevonden.")
            return 1
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
        with stille_herkenning():
            rapport = meet(sorted(paden))
        inhoud = json.dumps(rapport, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
        with open(RAPPORT, "x", encoding="utf-8") as bestand:
            bestand.write(inhoud)
        print(inhoud, end="")
        return 0
    except FileExistsError:
        print("Er bestaat al een pilotmeting.json. Verplaats het vorige rapport.")
    except Exception:
        print("Meting mislukt. Controleer de invoer, markeringen en schrijfrechten.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
