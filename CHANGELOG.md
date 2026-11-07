# Changelog – Handelsblatt Crime Fanwiki

Neueste Version oben. Jede ausgelieferte Version bekommt hier einen Eintrag und ein GitHub-Release mit Tag `vX.Y.Z`
(legt `.github/workflows/release.yml` automatisch an). Uhrzeiten in MEZ.
Neue Transkripte (Commits „Transkript NNN“) sind Inhalt, keine eigene Version.

## 0.1.0 – 07.11.2026
- **Grundgerüst nach dem Konzept der Schwesterprojekte** (ABC Podcast Fanwiki, Real Exam English Fanwiki): RSS-Feed von
  Podigee (160 Folgen, Dezember 2021 bis November 2026, 128 h Audio), Spotify-Episoden-IDs für alle 160 Folgen (von der
  Show-Seite gelesen, `scripts/match_spotify.py`), Obsidian-Vault `Handelsblatt-Crime-Wiki/` mit Folgen, Transkripten
  und den Ordnern Fälle, Themen, Unternehmen, Personen (`scripts/build_wiki.py`, Artikel in `data/topics/*.json`).
- **Transkription** mit faster-whisper `large-v3-turbo` auf der GPU (`scripts/transcribe_local.py`, Deutsch,
  Wort-Zeitstempel, Fortsetzen nach Abbruch); offizielle Podigee-Transkripte (4 Folgen) werden geladen
  (`scripts/fetch_official.py`) und beim Bauen mit den Whisper-Zeitstempeln zusammengeführt (`scripts/align_official.py`).
- **Website** auf einer Seite (`scripts/build_site.py`, `site/template.html`), Design „Akte“ in Nachtblau und Orange
  wie das Podcast-Cover: Startseite mit Suche, Kacheln für Fälle und Themen, Folgenliste mit Jahres- und Art-Filter,
  Folgen-, Artikel- und Transkriptseiten, eigener Audio-Player (MP3 von Podigee, Minuten-Chips, ±15 s, Tempo,
  „Spotify ↗“ an der aktuellen Stelle), Volltextsuche über Artikel, Folgen und Transkripte, Hell/Dunkel.
- **Workflows:** GitHub Pages (`pages.yml`) und Releases (`release.yml`); Sicherheits-Header als Meta-Tags (CSP,
  Referrer-Policy) wie bei den Schwesterprojekten.
- `CLAUDE.md` mit den Kurzbefehlen „check“ und „quality“ und der Auslieferungsreihenfolge.
