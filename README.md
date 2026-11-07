# Handelsblatt Crime Fanwiki 🕵️

## Stand: 1.0.0

Live: https://tscherny86.github.io/hbc/ · Vorschau: [Claude-Artefakt](https://claude.ai/artifact/PSwuaMC4RpVazQB6aF99sB) · Änderungen: [CHANGELOG.md](CHANGELOG.md) · Neuestes Release: [v1.0.0](https://github.com/tscherny86/hbc/releases/latest) (07.11.2026)

**Stand 1.0.0:** alle 160 Folgen transkribiert und geprüft (156 Korrektur gelesen, 4 mit dem offiziellen Transkript abgeglichen), 4.469 Korrekturregeln, 258 Artikel (81 Fälle, 43 Themen, 45 Unternehmen, 89 Personen), über 5.400 Zitate mit Link zur Minute, alle Spotify-IDs zugeordnet.

Fanwiki zum Podcast [Handelsblatt Crime – spannende Streitfälle der deutschen Wirtschaft](https://open.spotify.com/show/3bzKxZUhiIRZKavCmKIYCx)
(Hosts Ina Karabasz und Solveig Gode, Investigativ-Team um Sönke Iwersen): Korruption, Betrug, Cum-Ex, Wirecard, Benko
und viele weitere Fälle – als **Obsidian-Vault** plus Website auf einer Seite. Privates Fanprojekt, nicht vom Handelsblatt.

## In Obsidian öffnen (am PC)
1. Repo herunterladen: grüner Button **Code → Download ZIP** (oder `git clone`) und entpacken, z. B. nach `Dokumente/hbc`.
2. Obsidian öffnen → **„Ordner als Vault öffnen“** → den Ordner `Handelsblatt-Crime-Wiki` wählen.
3. Startseite: **Handelsblatt Crime Wiki**.

## Inhalt
- `Handelsblatt-Crime-Wiki/Folgen/` – alle 160 Folgen (2021–2026) mit Shownotes, Dauer, Spotify-, MP3- und Handelsblatt-Link
- `Handelsblatt-Crime-Wiki/Fälle/`, `Themen/`, `Unternehmen/`, `Personen/` – Wiki-Artikel mit Hintergrundwissen und der
  Liste der Folgen; bei transkribierten Folgen mit Zitat und Link zur **genauen Minute** (Spotify `?t=Sekunden`)
- `Handelsblatt-Crime-Wiki/Transkripte/` – Wort-genaue Transkripte, Minute für Minute verlinkt

## Aktualisieren
```bash
python scripts/check_feed.py            # neue Folgen im Feed? (lädt auch offizielle Transkripte)
pip install faster-whisper
python scripts/transcribe_local.py      # fehlende Folgen am PC transkribieren (kostenlos, GPU wenn vorhanden)
python scripts/build_wiki.py            # Vault neu bauen (aus data/)
```
Neue Fälle, Themen, Unternehmen oder Personen: `data/topics/*.json` (Hosts und Team in `scripts/topics.py`).

## Daten
- `data/feed.xml` – RSS-Feed (https://hb-crime.podigee.io/feed/mp3, Stand 07.11.2026, 160 Folgen)
- `data/spotify_ids.json` – Spotify-Episoden-IDs (alle 160 zugeordnet)
- `data/transcripts/` – Rohtranskripte von Whisper mit Wort-Zeitstempeln
- `data/official/` – offizielle Podigee-Transkripte (4 Folgen); `data/alignment_report.json` zeigt, wie gut sie passen
- `data/review/` – Prüfberichte je Folge (`assignments/`), Funde der Prüfer (`out/`), Anleitung für Prüfer (`HELFER.md`)
- `data/corrections.tsv` – Korrekturliste für Hörfehler, Bericht je Folge in `data/corrections_report.json`
- `data/topic_exclusions.tsv` – von Hand geprüfte Fehlzuordnungen
- `data/proofread.txt` – vollständig Korrektur gelesene Folgen

## Website (GitHub Pages)

Die Website wird bei jedem Push automatisch neu gebaut (`.github/workflows/pages.yml`):
`scripts/build_site.py` macht aus dem Vault eine einzige Seite (`site/template.html` ist die Vorlage).
Lokal testen: `python scripts/build_site.py` → `_site/index.html` im Browser öffnen.

Einmalig einschalten: GitHub → Repo → **Settings → Pages → Source: „GitHub Actions“**.

## Versionierung
Version in `package.json`, Eintrag oben in `CHANGELOG.md`, Kopfzeile `## Stand` hier im README.
Beim Push legt `.github/workflows/release.yml` das GitHub-Release `vX.Y.Z` an. Doku in Obsidian:
`Projekte/Handelsblatt Crime Fanwiki/` (Repo `tscherny86/notes-vault`).
