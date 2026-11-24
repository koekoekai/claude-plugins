---
name: scan
description: Zoek kwetsbaarheden, gelekte geheimen en kwetsbare pakketten met open scanners en laat de Nest-server ze beoordelen. Gebruik vóór een release of als periodieke check.
---

1. Vraag de MCP-tool `nest` → `scanners` om de lijst met commando's.
2. Draai de scanners die geïnstalleerd zijn en die bij het project passen (bijv. geen npm-audit zonder package.json). Ontbreekt er een, meld dat en ga door.
3. Geef de JSON-uitvoer per scanner aan `nest` → `beoordeel_scan` (soort + uitvoer).
4. Toon de bevindingen samen, hoog eerst, en bied fixes aan. Bij een gelekt geheim altijd eerst: intrekken bij de provider.

Toon nooit geheime waarden uit de scanneruitvoer in het gesprek.
