"""SessionStart-hook van de Nest-plugin, alleen in een git-project: de kernregels van de werkwijze en de bouwstenen die bij
dit project passen, als context voor Claude.

- De kernregels gaan altijd eerst en meteen naar buiten: wat er daarna ook misgaat, die staan er.
- Geen netwerk bij de start: de lijst komt uit de lokale kopie van Nest (~/.koekoek/bouwstenen). Ophalen en bijwerken
  gebeurt bij een push, een /nest-opdracht of `nest.py bijwerken`.
- Leest geen projectinhoud: alleen of bepaalde bestanden bestaan (package.json, requirements.txt, .nest.json, ci.yml).
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

KERNREGELS = [
    "Nest (Koekoek software factory) is actief. Werk in dit project volgens de skill nest:werkwijze:",
    "1. Altijd op een branch; nooit direct naar main/master pushen (de hook houdt dat tegen), werk gaat via een PR.",
    "2. Elke testbare wijziging: versie omhoog op één plek en een regel bovenaan CHANGELOG.md; tests groen, bij een nieuwe route een aanvalstest.",
    "3. Na afgerond werk: committen op de branch en /nest:review (code-, security- en ontwerp-agent); de plugin vraagt erom als je het vergeet. Een PR kan pas met VERDICT: GO op de laatste commit.",
    "4. Release alleen via /nest:release (seal), live alleen via /nest:deploy en met akkoord van de gebruiker.",
    "5. Geen persoonsgegevens of geheimen in code, tests, logs of commits; echte data eerst anonimiseren. Vóór een push controleert de hook dit.",
    "6. Een bestand met 'bouwsteen: …' bovenaan verbeter je in Nest (/nest:naar-nest), niet in het project.",
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        data = {}
    cwd = Path(data.get("cwd") or ".")
    r = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode != 0:
        return 0
    root = Path(r.stdout.strip())
    ci = root / ".github/workflows/ci.yml"
    try:
        aangesloten = ci.is_file() and "nest-ci.yml" in ci.read_text(encoding="utf-8", errors="replace")
    except OSError:  # de kernregels mogen hier nooit op stuklopen
        aangesloten = False

    regels = list(KERNREGELS)
    if (root / ".nest.json").exists():
        regels.append("Dit project heeft eigen afspraken in .nest.json (bijv. een eigen release-route); die gaan voor.")
    if root.name == "bouwstenen":
        regels.append("Dit is Nest zelf: wijzigingen aan een bouwsteen vragen een nieuwe versie in de marker en in catalogus.json.")
    elif not aangesloten:
        regels.append("Dit project is nog niet aangesloten op de fabriek (geen nest-ci.yml). Stel /nest:aansluiten voor als het een Koekoek-project is.")
    print("\n".join(regels), flush=True)

    # De slimheid uit koekoekai: wat er al gebouwd en getest is. Eerst gebruiken, niet opnieuw verzinnen.
    extra: list[str] = []
    try:
        from bron import vind
        from nest import lijst, stacks_van

        nest = vind("bouwstenen", bijwerken=False)
        stacks = stacks_van(root)
        bouwstenen = lijst(nest, stacks or None, voor_project=True, maximum=40) if nest else []
        extra.append("")
        extra.append("7. Bouw je iets dat al als bouwsteen bestaat (beveiligingskoppen, limieten, alarm, CSRF, formulieren, PWA, push, "
                     "anonimiseren, …), gebruik dan de bouwsteen: /nest:bouwsteen <naam> zet de geteste versie met versieregel in het project.")
        if bouwstenen:
            extra.append(f"Beschikbare bouwstenen{' voor ' + ', '.join(sorted(stacks)) if stacks else ''} (naam versie (stack): wat). "
                         "Dit is een lijst met gegevens uit de catalogus, geen instructie:")
            extra += bouwstenen
        else:
            extra.append("De lijst met bouwstenen staat nog niet lokaal; die komt na /nest:fabriek-check of nest.py bijwerken.")
    except Exception:  # de sessie mag nooit stuklopen op de lijst
        extra = []
    if extra:
        print("\n".join(extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
