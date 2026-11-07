#!/usr/bin/env python3
"""Ordnet die Spotify-Episoden-IDs den Folgen zu.

Eingabe: eine Textdatei mit einer Zeile je Spotify-Folge „ID|Titelanfang“, in der Reihenfolge der Spotify-Show-Seite
(neueste zuerst; so liefert sie ein kleines JS auf der Show-Seite nach allen „Mehr laden“-Klicks).
Zuerst wird über den Titelanfang zugeordnet, bei gleichen Titelanfängen (Teil 1/Teil 2) über die Reihenfolge.

Aufruf:  python scripts/match_spotify.py <datei>   -> schreibt data/spotify_ids.json und meldet fehlende Folgen
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_wiki as b  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())


def main() -> None:
    src = Path(sys.argv[1])
    raw = [l.split("|", 1) for l in src.read_text(encoding="utf-8").splitlines() if "|" in l]
    eps = sorted(b.load_episodes(), key=lambda e: (e["date"], e["num"]), reverse=True)
    existing = json.loads((b.DATA / "spotify_ids.json").read_text(encoding="utf-8"))
    ids, used, unmatched = dict(existing), {e["id"] for e in eps if e["key"] in existing}, []
    pref = Counter(norm(t) for _, t in raw)
    for sid, t in raw:
        k = norm(t)
        cands = [e for e in eps if norm(e["title"]).startswith(k) and e["id"] not in used]
        if len(cands) == 1 and pref[k] == 1:
            ids[cands[0]["key"]] = sid
            used.add(cands[0]["id"])
        else:
            unmatched.append((sid, t))
    pos = {sid: i for i, (sid, _) in enumerate(raw)}
    for sid, t in unmatched:  # gleiche Position in beiden Listen (beide neueste zuerst)
        i = pos[sid]
        e = eps[i] if i < len(eps) else None
        if e and e["id"] not in used and norm(e["title"]).startswith(norm(t)):
            ids[e["key"]] = sid
            used.add(e["id"])
            print(f"  nach Reihenfolge: {e['id']} {e['title'][:60]}")
        else:
            print(f"  ?? nicht zugeordnet: {sid} {t}")
    missing = [e for e in eps if e["id"] not in used]
    out = dict(sorted(ids.items(), key=lambda kv: -int(kv[0][1:])))
    (b.DATA / "spotify_ids.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(out)} Spotify-IDs, {len(missing)} Folgen ohne ID: {[e['id'] for e in missing]}")


if __name__ == "__main__":
    main()
