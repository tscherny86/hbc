#!/usr/bin/env python3
"""Lädt die offiziellen Transkripte, die Podigee im RSS-Feed veröffentlicht
(<podcast:transcript url="…json" type="application/json">), nach data/official/<Folgen-ID>.json.

Aufruf:  python scripts/fetch_official.py            # alle Folgen, die eines haben und noch nicht gespeichert sind
         python scripts/fetch_official.py --force    # erneut laden

Die Dateien enthalten Segmente mit Start/Ende/Text; align_official.py führt den Wortlaut beim Bauen des Wikis
mit den Whisper-Wortzeitstempeln zusammen. Am 07.11.2026 hatten 4 von 160 Folgen eines.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_wiki import DATA, load_episodes  # noqa: E402

OUT = DATA / "official"
UA = "Mozilla/5.0 (handelsblatt-crime-fanwiki)"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")


def main() -> None:
    force = "--force" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for ep in load_episodes():
        if not ep["transcript_url"]:
            continue
        target = OUT / f"{ep['id']}.json"
        if target.exists() and not force:
            continue
        try:
            data = json.loads(fetch(ep["transcript_url"]))
        except Exception as err:  # noqa: BLE001
            print(f"  ! {ep['id']}: {err}")
            continue
        segs = data if isinstance(data, list) else data.get("segments") or data.get("transcript") or []
        words = sum(len(str(s.get("text", "")).split()) for s in segs if isinstance(s, dict))
        if words < 50:
            print(f"  ! {ep['id']}: Transkript leer, übersprungen")
            continue
        target.write_text(json.dumps(segs, ensure_ascii=False, indent=0), encoding="utf-8")
        n += 1
        print(f"  ✓ {ep['id']}  {words} Wörter, {len(segs)} Segmente")
        time.sleep(0.3)
    print(f"{n} offizielle Transkripte gespeichert, insgesamt {len(list(OUT.glob('*.json')))}")


if __name__ == "__main__":
    main()
