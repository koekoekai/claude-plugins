"""Optionele herkenning van personen met een bestaand, lokaal taalmodel. Zonder model: None, en namen.py valt terug op regels.

Keuze met NEST_PRIVACY_HERKENNER:
  auto    (standaard) Privacy Kit, anders GLiNER, anders spaCy, anders regels. Stuurt nooit tekst naar een server.
  privacykit  Privacy Kit (EU-model met Nederlands, geen torch)   pip install "privacy-kit @ git+https://github.com/bards-ai/privacy-kit"
  gliner  GLiNER (meertalig, gemaakt voor persoonsgegevens)   pip install gliner
  spacy   spaCy met nl_core_news_md en en_core_web_md          pip install spacy && python -m spacy download nl_core_news_md en_core_web_md
  regels  geen taalmodel

Alles draait op deze computer. Alleen het eenmalig downloaden van een model gaat over het netwerk; de tekst nooit.
GLiNER-model: NEST_PRIVACY_GLINER (standaard urchade/gliner_multi_pii-v1).
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

NL_WOORDEN = re.compile(r"(?i)\b(?:de|het|een|en|van|met|voor|niet|ook|wij|ik|je|graag|bedankt|groet)\b")
EN_WOORDEN = re.compile(r"(?i)\b(?:the|and|of|with|for|not|also|we|you|please|thanks|regards)\b")


def keuze() -> str:
    return os.environ.get("NEST_PRIVACY_HERKENNER", "auto").lower()


class _Stuk:
    def __init__(self, start: int, end: int, label: str):
        self.start, self.end, self.label = start, end, label


class _ProcesDetector:
    """Privacy Kit in de eigen modelomgeving (model_installeren.py), als lokaal proces. Geen netwerk."""

    def __init__(self, python: str):
        self.python = python

    def detect(self, tekst: str) -> list:
        import json
        import subprocess
        from pathlib import Path

        import model_installeren

        r = subprocess.run([self.python, str(Path(__file__).with_name("model_proces.py"))], input=tekst.encode("utf-8"),
                           capture_output=True, timeout=600, env={**model_installeren.omgeving(), "HF_HUB_OFFLINE": "1"})
        if r.returncode != 0:
            raise RuntimeError("het lokale taalmodel gaf een fout")
        return [_Stuk(int(s["begin"]), int(s["eind"]), str(s["soort"])) for s in json.loads(r.stdout.decode("utf-8") or "[]")]


@lru_cache(maxsize=1)
def _privacykit():
    """Privacy Kit (bards-ai, Apache-2.0): EU-model met Nederlands, ONNX, geen torch nodig.
    Eerst in deze Python; anders in de eigen modelomgeving (python model_installeren.py)."""
    try:
        from privacy_kit.core.detectors import BardsAiOnnxDetector  # type: ignore
        return BardsAiOnnxDetector()
    except Exception:  # noqa: BLE001 - niet in deze Python
        pass
    try:
        import model_installeren

        py = model_installeren.python_van_model()
        return _ProcesDetector(str(py)) if py.is_file() else None
    except Exception:  # noqa: BLE001
        return None


@lru_cache(maxsize=1)
def _gliner():
    try:
        from gliner import GLiNER  # type: ignore
    except Exception:  # noqa: BLE001 - niet geïnstalleerd
        return None
    try:
        return GLiNER.from_pretrained(os.environ.get("NEST_PRIVACY_GLINER", "urchade/gliner_multi_pii-v1"))
    except Exception:  # noqa: BLE001 - model niet te laden (offline en nog niet gedownload)
        return None


@lru_cache(maxsize=2)
def _spacy(taal: str):
    try:
        import spacy  # type: ignore
        return spacy.load("nl_core_news_md" if taal == "nl" else "en_core_web_md", disable=["parser", "lemmatizer"])
    except Exception:  # noqa: BLE001
        return None


def _taal(tekst: str) -> str:
    return "nl" if len(NL_WOORDEN.findall(tekst)) >= len(EN_WOORDEN.findall(tekst)) else "en"


@lru_cache(maxsize=32)
def _pk_stukken(tekst: str) -> tuple[tuple[int, int, str], ...] | None:
    """Eén keer het model per tekst: namen en alle andere soorten komen uit dezelfde aanroep."""
    detector = _privacykit()
    if detector is None:
        return None
    try:
        return tuple((s.start, s.end, s.label) for s in detector.detect(tekst))
    except Exception:  # Een onvolledige modelomgeving kan ook tijdens detectie falen.
        return None


def personen(tekst: str) -> set[str] | None:
    """Namen van personen volgens een lokaal taalmodel, of None als er geen model is (of als 'regels' gekozen is)."""
    k = keuze()
    if k == "regels":
        return None
    if k in ("auto", "privacykit"):
        gevonden_pk = _pk_stukken(tekst)
        if gevonden_pk is not None:
            return {tekst[b:e].strip() for b, e, label in gevonden_pk if label == "PERSON_NAME"}
        if k == "privacykit":
            return None
    if k in ("auto", "gliner"):
        model = _gliner()
        if model is not None:
            gevonden = set()
            for begin, stuk in _stukken(tekst):
                for e in model.predict_entities(stuk, ["person", "first name", "last name"], threshold=0.5):
                    gevonden.add(e["text"].strip())
            return gevonden
        if k == "gliner":
            return None
    if k in ("auto", "spacy"):
        nlp = _spacy(_taal(tekst))
        if nlp is not None:
            return {e.text.strip() for e in nlp(tekst).ents if e.label_ in ("PER", "PERSON")}
    return None


GLINER_LABELS = {"person": "PERSON_NAME", "email": "EMAIL_ADDRESS", "phone number": "PHONE_NUMBER",
                 "address": "POSTAL_ADDRESS", "date of birth": "DATE_OF_BIRTH", "bank account number": "BANK_ACCOUNT_IDENTIFIER",
                 "credit card number": "PAYMENT_CARD", "passport number": "DOCUMENT_IDENTIFIER",
                 "license plate": "VEHICLE_IDENTIFIER", "medical condition": "HEALTH_DATA"}


def spans(tekst: str) -> list[tuple[int, int, str]] | None:
    """Alle gevoelige stukken volgens een lokaal model: (begin, eind, label) met labels zoals Privacy Kit ze noemt
    (PERSON_NAME, PHONE_NUMBER, HEALTH_DATA, ...). None als er geen model is."""
    k = keuze()
    if k == "regels":
        return None
    if k in ("auto", "privacykit"):
        gevonden_pk = _pk_stukken(tekst)
        if gevonden_pk is not None:
            return list(gevonden_pk)
        if k == "privacykit":
            return None
    if k in ("auto", "gliner"):
        model = _gliner()
        if model is not None:
            uit = []
            for begin, stuk in _stukken(tekst):
                for e in model.predict_entities(stuk, list(GLINER_LABELS), threshold=0.5):
                    uit.append((begin + e["start"], begin + e["end"], GLINER_LABELS[e["label"]]))
            return uit
    return None


def _stukken(tekst: str, maximaal: int = 1500) -> list[tuple[int, str]]:
    stukken = []
    begin = 0
    while begin < len(tekst):
        eind = min(begin + maximaal, len(tekst))
        if eind < len(tekst):
            grenzen = list(re.finditer(r"\s+", tekst[begin:eind]))
            if grenzen:
                eind = begin + grenzen[-1].end()
        stukken.append((begin, tekst[begin:eind]))
        begin = eind
    return stukken
