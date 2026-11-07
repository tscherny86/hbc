# Changelog – Handelsblatt Crime Fanwiki

Neueste Version oben. Jede ausgelieferte Version bekommt hier einen Eintrag und ein GitHub-Release mit Tag `vX.Y.Z`
(legt `.github/workflows/release.yml` automatisch an). Uhrzeiten in MEZ.
Neue Transkripte (Commits „Transkript NNN“) sind Inhalt, keine eigene Version.

## Unveröffentlicht

- Betrieb (07.11.2026, GitHub-Sperre): `scripts/ci.py` und `scripts/release.mjs`; `release.yml` und die neue `.gitlab-ci.yml` (Runner acespc) rufen nur noch diese Skripte auf. `pages.yml` läuft nicht mehr bei Push, nur per Hand mit `PAGES_FREIGABE=ja` (Veröffentlichung gesperrt, bis Alex entscheidet). Keine neue Version, die Seite ist unverändert.

## 1.0.0 – 07.11.2026
- **Alle 160 Folgen transkribiert** (faster-whisper `large-v3-turbo` auf der GPU, zwei Prozesse parallel, 1,23 Mio. Wörter) und **vollständig geprüft**: 156 Folgen von 33 Helfergruppen Zeile für Zeile Korrektur gelesen, 4 Folgen mit dem offiziellen Podigee-Transkript abgeglichen (Übereinstimmung 62–87 %). **4.469 Korrekturregeln, 9.117 Korrekturen** – vor allem Namen (Brorhilker in über 30 Hörvarianten, Marsalek, Olearius, Iwersen, Karabasz, Votsmeier, Signa, Veltins, Erffa), Firmen und Alltagswörter.
- **Artikel:** 81 Fälle, 43 Themen, 45 Unternehmen, 89 Personen (Hosts, Investigativ-Team, Protagonisten); neu die Fälle **Greensill Bank** und **Gröner Group**. Über 5.400 Zitate mit Link zur Minute.
- **Zuordnung geprüft:** 2.297 Zuordnungen Folge → Artikel mit Belegen kontrolliert, **294 Fehlzuordnungen** entfernt, 62 Suchmuster geschärft (z. B. „ey“ ist nicht EY, „Barth“ nicht nur Jürgen Barth, „Volkswagen-Stiftung“ nicht Volkswagen, „Mandat“ nicht Strafverteidigung, „unter den Nagel reißen“ nicht Lars-Marten Nagel).
- **Korrektur-Engine:** schneller (Bau 2 statt 5 Minuten), korrigiert jetzt auch Teile von Bindestrich-Wörtern („Krum-Ex-Verfahren“ → Cum-Ex-Verfahren, „Porsche-Pierch“ → Porsche-Piëch) ohne Doppelungen; Whisper-Phantomsätze („Untertitelung des ZDF …“) werden entfernt; globale Regeln, die echte Wörter treffen würden, gelten nur in ihrer Folge.
- **Website:** geprüft bei 320, 360, 390, 800, 960, 1024, 1100 und 1440 px auf allen 418 Seiten ohne Überlauf. Behoben: Logo und Minuten-Chips teilten sich CSS-Klassen (helle Pille ums Logo), Menü auf Tablet und kleinen Handys („Firmen“ statt „Unternehmen“ unter 380 px), große Überschrift bricht nicht mehr mitten im Wort, lange Links in Shownotes werden zu kurzen Links („handelsblatt.com/…“), lange Komposita umbrechen.

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
