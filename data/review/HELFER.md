# Anleitung für Prüf-Helfer (Korrekturlesen und Zuordnungsprüfung)

Du prüfst Transkripte des Podcasts „Handelsblatt Crime“ (deutsch, Wirtschaftskriminalität; Hosts Ina Karabasz und
Solveig Gode, Investigativ-Chef Sönke Iwersen; häufige Namen: Jan Marsalek, Markus Braun, Hanno Berger, Anne Brorhilker,
René Benko, Christian Olearius, Cum-Ex, Wirecard, EY, Signa, Warburg, LBBW, Staatsanwaltschaft Köln, Landgericht Bonn).

Für jede dir zugeteilte Folge NNN:
1. Lies `Handelsblatt-Crime-Wiki/Transkripte/Transkript NNN.md` **vollständig** (Minute für Minute; der Text ist schon
   mit `data/corrections.tsv` korrigiert). Finde Hörfehler bei Namen, Firmen, Orten, Fachbegriffen **und Alltagswörtern**
   (z. B. „Kummex“ → Cum-Ex, „Marsalik“ → Marsalek, „Wire Card“ → Wirecard, „Landesgericht“ → Landgericht, „Staatsanwalt
   Schaft“ → Staatsanwaltschaft, falsch getrennte Komposita, falsche Zahlen wie „Milliarden“ ↔ „Millionen“ nur wenn aus
   dem Zusammenhang eindeutig). Keine Glättung von Umgangssprache, Grammatik oder Füllwörtern; nichts umformulieren.
2. Schreibe die Funde nach `data/review/out/proof-NNN.tsv`, eine Regel je Zeile, Tab-getrennt:
   `FALSCH<Tab>RICHTIG<Tab>global|local<Tab>NNN<Tab>Grund`
   - FALSCH exakt so, wie es im Transkript steht (ganze Wörter, ggf. mehrere Wörter; Groß/Klein egal).
   - `global` nur, wenn die Fehlform in JEDEM denkbaren Zusammenhang falsch ist (z. B. „Marsalik“); sonst `local`.
   - Die Regel wird nur übernommen, wenn FALSCH wirklich im Transkript vorkommt – also genau abschreiben.
3. Lies `data/review/assignments/NNN.md`: dort steht jede Zuordnung Fall/Thema/Unternehmen/Person → diese Folge mit
   Belegen (Nennungen, Zitate). Prüfe: Ist das wirklich Thema der Folge (HAUPT) oder nur ein Nebensatz/Fehltreffer
   (z. B. „Berger“ trifft eine andere Person, „Conti“ ist nicht Continental)? Fehlzuordnungen nach
   `data/review/out/assign-NNN.tsv`: `NAME<Tab>NNN<Tab>Grund` (NAME exakt wie im Prüfbericht).
   Sind Suchmuster systematisch falsch (treffen Wörter in anderen Wörtern), notiere das im Grund.
4. Antworte am Ende nur mit einer Tabelle: Folge | Zahl der Korrekturregeln | Zahl der entfernten Zuordnungen | auffällige
   Muster (ein Satz).

Schreibe die TSV-Dateien mit dem Write-Tool (UTF-8). Lies nichts außerhalb dieser Dateien, ändere keine anderen Dateien.
