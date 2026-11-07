#!/usr/bin/env python3
"""Befehl „check“: RSS-Feed neu laden und neue bzw. noch nicht transkribierte Folgen melden.

Aufruf:  python scripts/check_feed.py                 (lädt den Feed direkt von Podigee)
         python scripts/check_feed.py --file X.xml     (Feed aus Datei, z. B. Firecrawl-Ergebnis mit „rawHtml“,
                                                        falls podigee.io im Netz gesperrt ist)
Schreibt data/feed.xml nur bei Änderung und lädt neue offizielle Transkripte (fetch_official.py).
Ausgabe: eine Zeile pro Folge ohne Transkript, sonst „keine neuen Episoden“.
Exit-Code 0 = nichts zu tun, 10 = es gibt Folgen zum Transkribieren.
"""
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED_URL = "https://hb-crime.podigee.io/feed/mp3"
FEED = ROOT / "data" / "feed.xml"
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> int:
    old = FEED.read_bytes() if FEED.exists() else b""
    if "--file" in sys.argv:
        raw = Path(sys.argv[sys.argv.index("--file") + 1]).read_text(encoding="utf-8")
        if raw.lstrip().startswith("{"):
            import json
            raw = json.loads(raw)["rawHtml"]
        new = raw.encode("utf-8")
    else:
        try:
            req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0 (handelsblatt-crime-fanwiki)"})
            new = urllib.request.urlopen(req, timeout=60).read()
        except OSError as err:
            print(f"Feed direkt nicht erreichbar ({err}); anders laden und --file nutzen", file=sys.stderr)
            return 2
    if b"<rss" not in new[:2000]:
        print("Feed konnte nicht gelesen werden", file=sys.stderr)
        return 2
    if new != old:
        FEED.write_bytes(new)
    import build_wiki as b  # erst nach dem Schreiben laden, damit der neue Feed gilt

    eps = b.load_episodes()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "fetch_official.py")], check=False)
    missing = [e for e in eps if not (ROOT / "data" / "transcripts" / f"{e['id']}.json").exists()]
    print(f"Feed: {len(eps)} Folgen{' (aktualisiert)' if new != old else ''}")
    if not missing:
        print("keine neuen Episoden")
        return 0
    for e in missing:
        print(f"NEU/OHNE TRANSKRIPT\t{e['id']}\t{e['date']}\t{e['title']}")
    return 10


if __name__ == "__main__":
    sys.exit(main())
