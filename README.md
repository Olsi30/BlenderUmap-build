# BlenderUmap: experimenteller aktueller Build

Installierbare Windows-ZIP aus dem öffentlichen BlenderUmap2-Quellstand, angepasst an CUE4Parse und FortniteReplayDecompressor vom September 2026. Alle Quellen sind in `source-lock.json` auf feste Commits gesetzt.

**Fortnite 42.20 ist noch nicht getestet. Dieser Build ist keine bestätigte Lösung für vollständige 1:1-Kopien der fünf Ballistic-Maps.** Kompilierung und Replay-Lesen belegen keine vollständige Kartenrekonstruktion.

## Nachgewiesener Stand

Die angepasste Anwendung wurde lokal unter Linux kompiliert und mit zwei vorhandenen Replays getestet:

| Replay-Version | Engine | Eindeutige Actor-IDs | Mit Spawn-Transformation und aufgelöstem Archetyp | Parser-Warnungen |
| --- | --- | ---: | ---: | ---: |
| 37.30 | 5.7.0 | 1648 | 960 | 43 |
| 38.00 | 5.7.0 | 4902 | 3329 | 64 |

Dabei wurden keine Parser-Fehlermeldungen gezählt. Die Warnungen betreffen unter anderem neuere Netzwerkversionen und nicht vollständig gelesene Eigenschaften. Actors umfassen auch Spieler, Waffen und Geräte; die Zahlen sind keine Anzahl exportierter Gebäude.

Geometrie-/Materialexport, Darstellung in Blender und UEFN-Import sind noch nicht praktisch geprüft. Für die weitere Prüfung fehlen ein 42.20-Replay und die passenden Kartendateien.

## Installation

1. Unter **Actions → Build experimental Windows add-on → erfolgreicher Lauf → Artifacts** das Artefakt herunterladen.
2. Die äußere GitHub-Artefakt-ZIP entpacken. Darin liegt `BlenderUmap-0.1.0-experimental-win-x64.zip`.
3. Diese innere ZIP in Blender unter **Edit → Preferences → Add-ons → Install from Disk** installieren (ältere Blender-Versionen: **Install**) und aktivieren.
4. Der bisherige Importpfad benötigt einen passenden PSK/PSA-Importer. Alternativ existiert in den Add-on-Einstellungen **Use experimental PSK importer**. Blender 4.x/5.x wurden für diesen Build noch nicht praktisch getestet.

Die ZIP enthält die .NET-Laufzeit. Ein .NET-SDK wird auf dem Windows-PC zum Ausführen nicht benötigt.

## Replay zuerst unabhängig prüfen

Eine Kopie der inneren ZIP entpacken. Im Ordner `BlenderUmap` in PowerShell:

```powershell
.\BlenderUmap.exe --replay-info "C:\Pfad\Datei.replay" "C:\Pfad\report.json"
```

Der Bericht enthält Fortnite-/Engine-Version, Levelnamen, Actor-Zahlen, vollständige Archetyp-Pfade und Warnungen. Exitcode 0 bedeutet gelesene Actors ohne gezählte Parser-Fehler, nicht Vollständigkeit. Exitcode 1 bedeutet Abbruch; Exitcode 2 bedeutet keine Actors oder gezählte Parser-Fehler.

Persönliche Replays und Spieldateien werden nicht in dieses öffentliche Repository hochgeladen.

## Grenzen

- Der Adapter erhält vollständige Objektpfade und Spawn-Transformationen. Er behält beobachtete Actors nach dem Schließen ihres Kanals. Er rekonstruiert keine allgemeine Timeline aller replizierten Eigenschaften.
- Statische Actors ohne Spawn-Transformation werden beim Replay-Mesh-Export übersprungen. Ihre Ausgangsdaten können in Level- oder separat ausgelieferten Inhaltsdateien liegen.
- Modelle, Texturen und Materialdaten kommen aus passenden lokalen Spieldateien. Ein Replay enthält diese Assets nicht vollständig. UE-Version, Mappings und Kartenpakete müssen zusammenpassen.
- Die UE-Version anhand der verwendeten Assets setzen. Bei den zwei getesteten Replays ist 5.7.0 aufgezeichnet; nicht pauschal die neueste Version wählen.
- Jeden Export in einem neuen Ausgabeordner testen. Leere Replay-Exporte und fehlgeschlagene Mesh-/Textur-Exporte melden einen Fehler.
- Ein Blender-Modell ist noch kein fertiges UEFN-Level. Maßstab, Platzierungen, Materialien, Kollision, Beleuchtung und Spiellogik müssen separat geprüft werden.

## Build

Git, Python 3.10+ und .NET SDK 10 installieren, dann:

```console
python build.py --rid win-x64
```

Das Skript lädt die festgeschriebenen Quellen, wendet `patches/modernize.patch` an, baut mit enthaltener Laufzeit, prüft die ZIP und erzeugt SHA-256-Prüfsummen. Auf Windows werden zusätzlich Programmstart und die Ablehnung einer ungültigen Replay-Datei getestet. Die optionale native ACL-Bibliothek für Animationen wird nicht gebaut.

`--reuse-sources` ist nur für eine bereits vorbereitete und angepasste `.work/source`-Arbeitskopie. Für einen sauberen Neubau den erzeugten `.work`-Ordner vorher entfernen.

## Quellen und Lizenz

- [MinshuG/BlenderUmap2](https://github.com/MinshuG/BlenderUmap2)
- [FabianFG/CUE4Parse](https://github.com/FabianFG/CUE4Parse)
- [Shiqan/FortniteReplayDecompressor](https://github.com/Shiqan/FortniteReplayDecompressor)
- [Epic: Assets in UEFN importieren](https://dev.epicgames.com/documentation/de-de/fortnite/importing-assets-in-unreal-editor-for-fortnite)

Die Anpassung wird unter GPL-3.0-or-later bereitgestellt. Hinweise der jeweiligen Quellen bleiben erhalten. Die ZIP enthält den Build-Patch, die Quellenrevisionen und Buildanweisungen.
