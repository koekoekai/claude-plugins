"""Optionele herkenning van personen met een bestaand, lokaal taalmodel. Zonder model: None, en namen.py valt terug op regels.

Keuze met NEST_PRIVACY_HERKENNER:
  auto    (standaard) GLiNER als die er is, anders spaCy, anders regels
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


def personen(tekst: str) -> set[str] | None:
    """Namen van personen volgens een lokaal taalmodel, of None als er geen model is (of als 'regels' gekozen is)."""
    k = keuze()
    if k == "regels":
        return None
    if k in ("auto", "gliner"):
        model = _gliner()
        if model is not None:
            gevonden = set()
            for stuk in _stukken(tekst):
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


def _stukken(tekst: str, maximaal: int = 1500) -> list[str]:
    """GLiNER werkt op korte stukken: knip op alinea's en zinnen."""
    stukken, huidig = [], ""
    for zin in re.split(r"(?<=[.!?\n])\s+", tekst):
        if len(huidig) + len(zin) > maximaal and huidig:
            stukken.append(huidig)
            huidig = ""
        huidig += zin + " "
    if huidig.strip():
        stukken.append(huidig)
    return stukken
