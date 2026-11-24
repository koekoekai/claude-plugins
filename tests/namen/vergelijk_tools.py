"""Vergelijk bestaande tools op onze Nederlandse en Engelse testsets: python tests/namen/vergelijk_tools.py <tool>
tool: presidio | privacykit | gliner | regels
Elke tool levert de namen van personen die hij vindt. Die gaan door dezelfde meting als onze eigen versie: de naam moet uit de
tekst verdwijnen, en woorden die moeten blijven, mogen niet weg."""
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent.parent / "plugins" / "nest-privacy" / "scripts"))
import anonimiseren  # noqa: E402

SETS = ("testset.json", "moeilijk.json", "controle.json", "blind.json", "blind2.json")


def presidio():
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    nlp = NlpEngineProvider(nlp_configuration={"nlp_engine_name": "spacy", "models": [
        {"lang_code": "nl", "model_name": "nl_core_news_md"}, {"lang_code": "en", "model_name": "en_core_web_md"}]}).create_engine()
    engine = AnalyzerEngine(nlp_engine=nlp, supported_languages=["nl", "en"])

    def vind(tekst: str) -> set[str]:
        namen = set()
        for taal in ("nl", "en"):  # beide talen; een zin is nl of en
            for r in engine.analyze(text=tekst, language=taal, entities=["PERSON"]):
                namen.add(tekst[r.start:r.end])
        return namen
    return vind


def privacykit():
    from privacy_kit.core.detectors import build_detector

    detector = build_detector()
    return lambda tekst: {tekst[s.start:s.end] for s in detector.detect(tekst) if s.label == "PERSON_NAME"}


def gliner():
    from gliner import GLiNER

    model = GLiNER.from_pretrained("urchade/gliner_multi_pii-v1")
    return lambda tekst: {e["text"] for e in model.predict_entities(tekst, ["person"], threshold=0.5)}


def regels():
    import namen
    return lambda tekst: namen.zoek_namen(tekst).namen


def meet(vind) -> None:
    for naam in SETS:
        data = json.loads((HIER / naam).read_text(encoding="utf-8"))
        tot = gev = bl = vals = 0
        mis, ont = [], []
        for z in data["zinnen"]:
            uit = anonimiseren.anonimiseer(z["t"], soorten=["NAAM"], extra_termen=vind(z["t"])).tekst
            for n in z["namen"]:
                tot += 1
                if n.lower() in uit.lower():
                    mis.append(n)
                else:
                    gev += 1
            for w in z["blijven"]:
                bl += 1
                if w not in uit:
                    vals += 1
                    ont.append(w)
        print(f"{naam:14} herkend {gev / tot:4.0%} van {tot:2}  vals {vals / bl:4.0%} van {bl:2}  gemist {mis}  onterecht {ont}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    meet({"presidio": presidio, "privacykit": privacykit, "gliner": gliner, "regels": regels}[sys.argv[1]]())
