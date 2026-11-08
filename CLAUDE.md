# Handelsblatt Crime Fanwiki – Arbeitsregeln

Sprache mit Alex: Deutsch; Repo, Vault und Website ebenfalls Deutsch (der Podcast ist deutsch).
Live: https://tscherny86.github.io/hbc/ · Artefakt: https://claude.ai/artifact/PSwuaMC4RpVazQB6aF99sB
Obsidian: `Projekte/Handelsblatt Crime Fanwiki/` im Repo `tscherny86/notes-vault` (Pflicht bei jeder Änderung, siehe unten).
Schwesterprojekte mit derselben Struktur: ABC Podcast Fanwiki (`tscherny86/abcpodcast`) und Real Exam English Fanwiki
(`tscherny86/realexam`). Lokaler Projektordner auf Alex' PC: `C:\Users\tsche\hbc`.

## Kurzbefehle (vereinbart mit Alex am 06.11.2026 für das ABC-Projekt, gelten hier genauso)

Alex schreibt nur das Stichwort. Nicht nachfragen, sondern den ganzen Ablauf durchziehen und am Ende kurz berichten.

### „check“ – neue Folge?
1. Feed laden: `python scripts/check_feed.py` (lädt auch neue offizielle Podigee-Transkripte). Ist podigee.io im Netz
   gesperrt (Fehler 403), den Feed mit Firecrawl (`firecrawl_scrape`, URL `https://hb-crime.podigee.io/feed/mp3`,
   `formats: ["rawHtml"]`, `maxAge: 0`) holen und `python scripts/check_feed.py --file <gespeichertes Ergebnis>` aufrufen.
2. Meldet das Skript „keine neuen Episoden“ (Exit 0): Alex genau das antworten – **„keine neuen Episoden“** – fertig.
3. Sonst (Exit 10) für jede gemeldete Folge:
   - Spotify-Episoden-ID suchen (Show-Seite in Chrome, Spotify-MCP-Suche) und in `data/spotify_ids.json` eintragen
     (Schlüssel `#<Nummer>`); bei vielen Folgen `scripts/match_spotify.py` mit einer Liste `ID|Titelanfang`.
   - Transkribieren: `python -u scripts/transcribe_local.py <Nummer>` (GPU, etwa 20× Echtzeit; als eigener Prozess mit
     `Start-Process`, Fortschritt in `data/transcripts/progress.log`; Teilstände in `data/transcripts/partial/` werden
     nach einem Abbruch fortgesetzt).
   - Danach **alle Qualitätsprüfungen wie bei „quality“** für diese Folge.
   - Danach **Inhalte einpflegen** (Abschnitt unten).

### Neue Inhalte einpflegen (bei jeder neuen Folge)
Die Artikel stehen in `data/topics/*.json` (je Ordner `faelle-*.json`, `themen.json`, `unternehmen.json`,
`personen.json`; Felder `name`, `folder`, `patterns`, `summary`, `body`, optional `min`); Hosts und Investigativ-Team
in `scripts/topics.py`. Shownotes und Transkript der neuen Folge lesen und prüfen:
- **Neuer Fall:** Jede Folge mit einem eigenen Streitfall bekommt einen Fall-Artikel (oder hängt an einem bestehenden,
  z. B. Cum-Ex, Wirecard): `summary` ein Satz (max. 110 Zeichen, passt in drei Kachelzeilen), `body` = Hintergrundwissen
  (Chronologie, Beteiligte, Beträge, Stand), Suchmuster eng (`\b`, Hörfehler-Varianten der Namen).
- **Neue Personen und Unternehmen:** nur öffentlich bekannte Personen (Angeklagte, Ermittler, Anwälte, Manager,
  Politiker); Porträt mit Rolle, Werdegang, Bezug zum Fall, Verfahrensstand; Unschuldsvermutung beachten; keine
  privaten Daten. Hosts und Team: volle Namen, Reihenfolge Ina Karabasz, Solveig Gode, Sönke Iwersen, dann A–Z (`PINNED`).
- **Neue Begriffe/Hörfehler:** Namen, Firmen, Fachbegriffe richtig schreiben über `data/corrections.tsv` (global nur,
  wenn überall eindeutig; mehrdeutig → local mit Folgen-ID; Schutzregel `X<Tab>X`, wenn ein richtiger Ausdruck nicht
  angefasst werden darf). Folgenübergreifend prüfen, ob dieselbe Fehlform in anderen Folgen steht.
- **Zuordnung prüfen:** `python scripts/review_assignments.py` schreibt je Folge eine Prüfdatei; Fehltreffer mit Grund in
  `data/topic_exclusions.tsv`. Hauptthema nur bei Titel-/Shownotes-Treffer (mit Bestätigung im Transkript) oder ab den
  Schwellen in `build_wiki.FOLDER_MIN`, sonst „Kurz erwähnt“.
- **Darstellung:** Kacheln bleiben gleich groß (Titel max. 2 Zeilen, Beschreibung max. 3 Zeilen) – lange `summary`-Texte
  kürzen statt das Layout zu dehnen.

### „quality“ – alles Ungeprüfte prüfen
Gilt für jede Folge mit Transkript, die weder mit einem offiziellen Transkript abgeglichen ist
(`data/alignment_report.json`, `"used": true`) noch in `data/proofread.txt` steht:
1. **Transkript polieren:** vollständig Zeile für Zeile lesen (Helfer, je 2–3 Folgen), Hörfehler bei Namen, Firmen,
   Fachbegriffen **und Alltagswörtern** finden. Regeln in `data/corrections.tsv`, keine Glättung von Umgangssprache oder
   Grammatik. Danach ID mit Datum in `data/proofread.txt`. Prüfen, wie viele Regeln greifen
   (`data/corrections_report.json`), nicht greifende nachbessern (`scripts/apply_review.py` übernimmt Helfer-Listen
   `data/review/out/proof-*.tsv` nur, wenn die Fehlform wirklich im Transkript steht). `scripts/qa_scan.py` markiert
   verdächtige Stellen (Wortdoppelungen, zusammengeklebte Wörter, seltene Wörter, Lücken).
2. **Zuordnung prüfen:** für die Folge alle Zuordnungen Fall/Thema/Unternehmen/Person mit Zitaten prüfen
   (`scripts/review_assignments.py`): echtes Thema oder Fehltreffer/Nebensatz? Fehlzuordnungen mit Begründung in
   `data/topic_exclusions.tsv`. Systematische Fehltreffer → Suchmuster schärfen (oder `min` erhöhen).
3. **Bauen und prüfen:** `python scripts/build_wiki.py`, `python scripts/build_site.py`, Seiten im Browser (Desktop und
   390 px) ohne JS-Fehler und ohne Überlauf ansehen (`.claude/launch.json`: Vorschau auf Port 8766).
4. **Ausliefern** (Reihenfolge unten), Artefakt neu veröffentlichen (`build_site.py … --fragment`) und Alex eine Tabelle
   **Korrekturen je Folge** und die entfernten Zuordnungen schicken.

Ist nichts ungeprüft: „alles geprüft, nichts offen“ antworten.

## Auslieferung (jede Änderung)
1. `package.json` Version (Patch für Korrekturen/Kleines, Minor für neue Funktionen), Eintrag oben in `CHANGELOG.md`,
   `## Stand: X.Y.Z` im README. Reine Transkript-Commits sind Inhalt, keine Version.
2. Obsidian `Projekte/Handelsblatt Crime Fanwiki/`: „Aktuelle Version“ im Steckbrief, Eintrag oben im Änderungsprotokoll
   (`## TT.MM.JJJJ – Version X.Y.Z`), Ist-Stand, Chronik, Offene Punkte abhaken, bei Korrekturen auch
   „Transkription und Korrekturen“. Alex' Vault liegt lokal unter `D:\notes\notes` (Obsidian Git schreibt mit):
   vor dem Push `git pull --rebase`; keine Git-Befehle, die nicht committete Änderungen verwerfen. Notizen auf Deutsch.
3. Push auf `main`; GitHub Pages baut automatisch, `release.yml` legt das Release an.
4. Projekt-Cockpit: das Projekt ist in `cockpit.config.ts` (Repo `tscherny86/projekt-cockpit`, lokal
   `C:\Users\tsche\OneDrive\Projekt-Cockpit`) eingetragen; dort ist nur etwas zu tun, wenn Repo, Live-URL oder
   Dateinamen sich ändern.

## Ohne GitHub prüfen und Releases anlegen (Notfallweg)

Seit der GitHub-Sperre vom 07.11.2026 hängt nichts mehr allein an GitHub. Code liegt lokal, auf GitHub und privat auf GitLab (`gitlab.com/tschernutter/hbc`); `git push origin` geht zuerst an GitLab.

- **Prüfen:** `python scripts/ci.py` (Website in einen Temp-Ordner bauen, Artikel und Version prüfen; veröffentlicht nichts) – dasselbe Skript ruft GitLab CI (`.gitlab-ci.yml`, seit 08.11.2026 Linux-Runner von gitlab.com statt acespc) auf.
- **Release:** `node scripts/release.mjs --all-missing --title "Handelsblatt Crime Fanwiki"` legt fehlende Tags `vX.Y.Z` und Releases mit dem CHANGELOG-Abschnitt an – auf GitLab (glab) und, wenn erreichbar, auf GitHub (gh). `--dry-run` zeigt nur an.
- **Nur für Alex, nie öffentlich** (Entscheidung Alex 07.11.2026: „handelsblatt crime bleibt privat nur für mich aufrufbar über gitlab“). Volltranskripte eines Verlagspodcasts ohne Erlaubnis. Die Seite baut der GitLab-CI-Job `pages` als GitLab Pages des **privaten** Projekts mit Zugriff „Only project members“ (`pages_access_level=private`): ohne Anmeldung als Projektmitglied ist nichts zu sehen. GitHub Pages (`pages.yml`) bleibt aus (nur per Hand und nur mit `PAGES_FREIGABE=ja`, die nicht gesetzt wird); kein Hosting auf Netlify, Vercel oder anderswo.
