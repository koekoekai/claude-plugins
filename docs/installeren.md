# Nest-privacy installeren en uitproberen

Met Nest-privacy maak je op je eigen computer een kopie van een tekst waarin persoonsgegevens zijn vervangen. Oefen eerst met het verzonnen bericht hieronder.

## 1. Controleer wat je nodig hebt

**Windows:** open via Start het programma PowerShell. **Mac:** zoek met het vergrootglas naar Terminal en open het. In dit venster kun je een opdracht typen. Druk na elke opdracht op Enter.

| Wat heb je nodig? | Hoe controleer je het? | Hoe kom je eraan? |
|---|---|---|
| Claude Code met toegang via je abonnement | Typ `claude --version`. Zie je een versienummer, dan staat het programma erop. Vraag bij een werkaccount of Claude Code aanstaat voor jou. | Anthropic noemt Pro, Max, Ultra, Team en Enterprise. Volg op de officiële pagina stap 1 voor **Windows PowerShell** of **macOS**. [Claude Code installeren bij Anthropic](https://code.claude.com/docs/en/quickstart) |
| Python 3.9 of nieuwer | Typ op Windows `python --version` en op de Mac `python3 --version`. Een versie als 3.12 is goed. | Kies de download voor je computer. [Python downloaden](https://www.python.org/downloads/) |
| Git (om de plugin en het taalmodel op te halen) | Typ `git --version`. Je moet een versienummer zien. Zoek op Windows ook in Start naar **Git Bash**. Dat heeft de automatische controle nodig. | Installeer op Windows [Git for Windows](https://git-scm.com/downloads/win). Biedt de Mac aan om hulpprogramma’s te installeren, kies dan **Installeer**. [Git voor Mac](https://git-scm.com/downloads/mac) |

Heb je iets geïnstalleerd? Open PowerShell of Terminal opnieuw en herhaal de controle.

## 2. Installeer Nest-privacy

1. Maak in Verkenner (Windows) of Finder (Mac) een lege map met de naam `Nest-oefening`.
2. Open een opdrachtvenster **in die map**. Op Windows open je de map, klik je in de adresbalk, typ je `powershell` en druk je op Enter. Op de Mac typ je in Terminal `cd` gevolgd door een spatie. Sleep de map uit Finder naar dat venster en druk op Enter.
3. Typ `claude` en druk op Enter. Meld je de eerste keer aan via je browser. Ga terug naar het opdrachtvenster. Als Claude vraagt of je de oefenmap vertrouwt, controleer dan de mapnaam en bevestig.
4. Je typt nu **in Claude Code**. Voer deze twee opdrachten één voor één uit. De eerste voegt de lijst van Koekoek toe. De tweede installeert Nest-privacy.

   ```text
   /plugin marketplace add koekoekai/claude-plugins
   /plugin install nest-privacy@koekoek
   ```

5. Sluit Claude Code met `/exit`. Typ in hetzelfde venster opnieuw `claude`. Installeer het taalmodel met de opdracht hieronder. Geef toestemming voor de eenmalige download van ongeveer 0,5 GB. Dit kan een paar minuten duren.

   ```text
   /nest-privacy:taalmodel
   ```

6. Typ `/nest-privacy:taalmodel --status`. Bij succes staat er “Taalmodel: geïnstalleerd en werkt.” Vanaf nu gebruikt Nest-privacy het model op je computer.

[schermafbeelding: de geslaagde statuscontrole in Claude Code]

## 3. Probeer het met een verzonnen bericht

Open Kladblok op Windows of Teksteditor op de Mac. Kies op de Mac bij **Opmaak** voor platte tekst. Typ de volgende regel en bewaar het bestand als `bericht.txt` in de oefenmap.

> Stuur de afspraak naar oefenklant@example.org.

**Een adres weghalen.** Typ in Claude Code:

```text
/nest-privacy:anonimiseer bericht.txt veilig.txt
```

Open `veilig.txt` zelf. Op de plek van het adres hoort nu `[EMAIL]` te staan. Dit label kun je niet terugzetten.

**Een adres later terugzetten.** Geef Claude Code eerst deze instructie: “Gebruik bij de volgende opdracht codes die ik later kan terugzetten.” Gebruik daarna opnieuw het oorspronkelijke bestand:

```text
/nest-privacy:anonimiseer bericht.txt codes.txt
```

Controleer of Claude meldt dat er een code in de lokale vertaaltabel staat. Open `codes.txt` zelf. Nu staat er een code die begint met `[EMAIL-`. Zet het adres terug op dezelfde computer, met hetzelfde gebruikersaccount:

```text
/nest-privacy:terugzetten codes.txt hersteld.txt
```

Open `hersteld.txt` zelf en vergelijk het adres met je oefenbericht. Bij dit voorbeeld hoort Claude één teruggezette code en nul onbekende codes te melden. Behandel bestanden met terugzetbare codes ook als persoonsgegevens.

## 4. Als iets misgaat

- **Python niet gevonden?** Probeer ook `python3 --version`. Werkt geen van beide opdrachten, installeer Python via de link hierboven. Vink op Windows de optie om Python aan *PATH* toe te voegen aan als je die ziet. Open het venster opnieuw. Zonder werkende Python slaat de plugin de automatische controle over.
- **Git ontbreekt?** Volg de Git-stap in de tabel. Open een nieuw venster en controleer opnieuw met `git --version`.
- **Het taalmodel installeert niet?** Controleer je internetverbinding en de Git-versie. Start Claude Code opnieuw vanuit de oefenmap en herhaal de installatie en de statuscontrole. Vraag je IT-collega om hulp als je werknetwerk downloads blokkeert.
- **Claude mag een bestand niet lezen?** De automatische controle (de ‘hook’) houdt lezen tegen als die gevoelige gegevens vindt. Dat is de bedoeling. Gebruik de opdracht van stap 3 met de bestandsnaam. Plak de inhoud niet in de chat.

Nest-privacy geeft geen garantie dat alle persoonsgegevens weg zijn. Lees de kopie zelf na voordat je die deelt. Hulp nodig? [Neem contact op met Koekoek](https://koekoek.ai/#contact).
