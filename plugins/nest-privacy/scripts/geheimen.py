"""Basiscontrole op geheimen in code: API-sleutels, tokens, privésleutels en wachtwoorden die als tekst in een bestand staan.

    python geheimen.py [bestanden...]          # leeg = alle bestanden in git
    python geheimen.py --sinds origin/main     # alleen bestanden die sindsdien veranderden

Meldt alleen bestand, regel en soort, nooit de waarde. Exitcode 1 bij een vondst.
Overslaan: 'geheim: ok' op de regel (bijv. een nepsleutel in een test), of een patroon per regel in .nest-geheim-negeer.
Alleen de standaardbibliotheek, werkt offline. Dit is een basiscontrole; gebruik in CI ook een volledige scanner zoals gitleaks.
"""
from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
from dataclasses import dataclass

MAX_BYTES = 2_000_000
VOORBEELD = re.compile(r"(voorbeeld|example|changeme|dummy|placeholder|xxx+|\*\*\*|<[^>]+>|\$\{|\{\{|your[_-]?)", re.I)

SOORTEN: list[tuple[str, re.Pattern]] = [
    ("PRIVESLEUTEL", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----")),
    ("AWS-SLEUTEL", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GITHUB-TOKEN", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})\b")),
    ("SLACK-TOKEN", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("STRIPE-SLEUTEL", re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b")),
    ("ANTHROPIC-SLEUTEL", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("OPENAI-SLEUTEL", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b")),
    ("GOOGLE-SLEUTEL", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("WACHTWOORD-IN-URL", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s@/]{6,}@[^\s/]+", re.I)),
    ("WACHTWOORD", re.compile(
        r"""\b(?:password|passwd|wachtwoord|secret|api[_-]?key|token|client[_-]?secret)\b\s*[:=]\s*["']([^"'\s]{8,})["']""", re.I)),
]


@dataclass
class Vondst:
    pad: str
    regel: int
    soort: str


def _negeer(map_: str) -> list[str]:
    pad = os.path.join(map_, ".nest-geheim-negeer")
    if not os.path.isfile(pad):
        return []
    with open(pad, encoding="utf-8", errors="replace") as f:
        return [r.strip() for r in f if r.strip() and not r.startswith("#")]


def controleer_regel(tekst: str) -> list[str]:
    if "geheim: ok" in tekst:
        return []
    soorten = []
    for soort, patroon in SOORTEN:
        m = patroon.search(tekst)
        if not m:
            continue
        waarde = m.group(1) if m.groups() else m.group(0)
        if soort == "WACHTWOORD" and (VOORBEELD.search(waarde) or soorten):
            continue  # voorbeeldwaarde, of de regel is al gemeld als een bepaalde sleutel
        soorten.append(soort)
    return soorten


def controleer_bestanden(paden: list[str], map_: str = ".") -> list[Vondst]:
    negeer = _negeer(map_)
    vondsten: list[Vondst] = []
    for pad in paden:
        rel = os.path.relpath(pad, map_).replace(os.sep, "/")
        if rel == ".nest-geheim-negeer" or any(fnmatch.fnmatch(rel, p) for p in negeer):
            continue
        if not os.path.isfile(pad) or os.path.islink(pad) or os.path.getsize(pad) > MAX_BYTES:
            continue
        with open(pad, "rb") as f:
            data = f.read()
        if b"\0" in data[:8000]:
            continue  # binair
        for nr, regel in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
            for soort in controleer_regel(regel):
                vondsten.append(Vondst(rel, nr, soort))
    return vondsten


def git_bestanden(map_: str, sinds: str | None) -> list[str]:
    git = ["git", "-C", map_, "-c", "core.quotePath=false"]
    cmd = [*git, "diff", "--name-only", "-z", "--diff-filter=d", f"{sinds}...HEAD"] if sinds else [*git, "ls-files", "-z"]
    uit = subprocess.run(cmd, capture_output=True, check=True).stdout.decode("utf-8", "surrogateescape")
    return [os.path.join(map_, r) for r in uit.split("\0") if r]


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sinds = argv[argv.index("--sinds") + 1] if "--sinds" in argv else None
    paden = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--sinds")]
    paden = paden or git_bestanden(".", sinds)
    vondsten = controleer_bestanden(paden)
    for v in vondsten:
        print(f"::error file={v.pad},line={v.regel}::mogelijk geheim ({v.soort}); haal het uit de code en trek het in bij de leverancier")
    print(f"geheimen: {len(vondsten)} melding(en) in {len(paden)} bestand(en)", file=sys.stderr)
    return 1 if vondsten else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
