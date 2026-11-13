# Handelsblatt Crime Fanwiki 🕵️

## Stand: 1.0.2

Live (privat, nur für Projektmitglieder): https://hbc-99d4bd.gitlab.io/ · Vorschau: [Claude-Artefakt](https://claude.ai/artifact/PSwuaMC4RpVazQB6aF99sB) · Änderungen: [CHANGELOG.md](CHANGELOG.md) · Releases: [GitLab](https://gitlab.com/tschernutter/hbc/-/releases)

**Stand 1.0.0:** alle 160 Folgen transkribiert und geprüft (156 Korrektur gelesen, 4 mit dem offiziellen Transkript abgeglichen), 4.469 Korrekturregeln, 258 Artikel (81 Fälle, 43 Themen, 45 Unternehmen, 89 Personen), über 5.400 Zitate mit Link zur Minute, alle Spotify-IDs zugeordnet.

Fanwiki zum Podcast [Handelsblatt Crime – spannende Streitfälle der deutschen Wirtschaft](https://open.spotify.com/show/3bzKxZUhiIRZKavCmKIYCx)
(Hosts Ina Karabasz und Solveig Gode, Investigativ-Team um Sönke Iwersen): Korruption, Betrug, Cum-Ex, Wirecard, Benko
und viele weitere Fälle – als **Obsidian-Vault** plus Website auf einer Seite. Privates Fanprojekt, nicht vom Handelsblatt.

## In Obsidian öffnen (am PC)
1. Repo herunterladen: auf GitLab **Code → zip** (oder `git clone https://gitlab.com/tschernutter/hbc.git`) und entpacken, z. B. nach `Dokumente/hbc`.
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

## Website (GitLab Pages, privat)

Die Website wird bei jedem Push auf `main` vom GitLab-CI-Job `pages` neu gebaut (`.gitlab-ci.yml`):
`scripts/build_site.py` macht aus dem Vault eine einzige Seite (`site/template.html` ist die Vorlage).
Lokal testen: `python scripts/build_site.py` → `_site/index.html` im Browser öffnen.

## Versionierung
Version in `package.json`, Eintrag oben in `CHANGELOG.md`, Kopfzeile `## Stand` hier im README.
Bei neuer Version legt der GitLab-CI-Job `release` das GitLab-Release `vX.Y.Z` an. Doku in Obsidian:
`Projekte/Handelsblatt Crime Fanwiki/` (Repo `tschernutter/notes-vault`).

## Prüfen und Releases von Hand

Code liegt lokal und privat auf GitLab (`gitlab.com/tschernutter/hbc`, Remote `origin`, Branch `main`).

- **Prüfen:** `python scripts/ci.py` (Website in einen Temp-Ordner bauen, Artikel und Version prüfen; veröffentlicht nichts) – dasselbe Skript ruft GitLab CI (`.gitlab-ci.yml`, Linux-Runner von gitlab.com) auf.
- **Release:** `node scripts/release.mjs --all-missing --title "Handelsblatt Crime Fanwiki"` legt fehlende Tags `vX.Y.Z` und GitLab-Releases mit dem CHANGELOG-Abschnitt an (am PC über glab, in GitLab CI über die GitLab-API). `--dry-run` zeigt nur an.
- **Nur für Alex, nie öffentlich** (Entscheidung Alex 07.11.2026: „handelsblatt crime bleibt privat nur für mich aufrufbar über gitlab“). Volltranskripte eines Verlagspodcasts ohne Erlaubnis. Die Seite baut der GitLab-CI-Job `pages` als GitLab Pages des **privaten** Projekts mit Zugriff „Only project members“ (`pages_access_level=private`): ohne Anmeldung als Projektmitglied ist nichts zu sehen. Kein anderes Hosting (kein Netlify, Vercel oder anderswo).
