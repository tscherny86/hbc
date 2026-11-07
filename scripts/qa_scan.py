#!/usr/bin/env python3
"""Qualitätsscan der fertigen Transkripte (nach Abgleich und Korrekturen).

Markiert Stellen, die nach Transkriptionsschäden aussehen, damit ein Prüfer zuerst dort hinschaut:
  - ein Wort zweimal hintereinander („die die“)
  - Wörter, an denen Satzzeichen oder Ziffern kleben („Wort.Nächstes“, „B -2“)
  - seltene Wörter: kommen nur in einem Transkript vor und in keinem offiziellen Transkript (wahrscheinlich Hörfehler)
  - ungewöhnliche Zeichen außerhalb des deutschen Zeichensatzes
  - sehr lange Lücken zwischen zwei Wörtern (> 20 s) – Zeichen für verlorenes Audio oder falsche Zeitstempel

Aufruf:  python scripts/qa_scan.py            -> data/review/scan.md (ein Abschnitt je Folge)
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_wiki as b  # noqa: E402

OUT = b.DATA / "review"
WORD = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'’-]*")
COMMON_OK = set("ok okay ja nee nö hm hmm äh ähm mhm naja halt quasi sozusagen".split())


def main() -> None:
    eps = b.load_episodes()
    tx = {e["id"]: b.load_transcript(e) for e in eps}
    official_vocab: set[str] = set()
    for eid in tx:
        text = b.align_official.official_text(eid)
        if text:
            official_vocab.update(w.lower() for w in WORD.findall(text))
    df: Counter = Counter()
    per_ep: dict[str, Counter] = {}
    for eid, words in tx.items():
        if not words:
            continue
        c = Counter(w.lower() for t in words for w in WORD.findall(t["text"]))
        per_ep[eid] = c
        df.update(c.keys())
    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["# QA-Scan aller Transkripte (nach Abgleich und Korrekturen)", ""]
    total = 0
    for ep in eps:
        words = tx[ep["id"]]
        if not words:
            continue
        flags = []
        prev = None
        for i, w in enumerate(words):
            t = w["text"]
            core = t.strip(".,!?;:\"'()[]…–-„“")
            if prev and core and core.lower() == prev.lower() and core.isalpha() and len(core) > 2:
                flags.append((w["start"], f"Wortdoppelung: „{prev} {t}“"))
            if re.search(r"[A-Za-zäöüß][.!?][A-Za-zÄÖÜ]", t) or re.search(r"\s-\w|\w -\w", t):
                flags.append((w["start"], f"zusammengeklebt/getrennt: „{t}“"))
            if re.search(r"[^\x00-\x7FäöüÄÖÜß’‘“”„…–—€§°]", t):
                flags.append((w["start"], f"ungewöhnliches Zeichen: „{t}“"))
            if i and w["start"] - words[i - 1]["end"] > 20:
                flags.append((w["start"], f"Lücke von {w['start'] - words[i-1]['end']:.0f} s vor „{t}“"))
            prev = core
        rare = sorted(w for w, n in per_ep[ep["id"]].items() if df[w] == 1 and w not in official_vocab
                      and w not in COMMON_OK and len(w) > 3 and n == 1)
        aligned = b.ALIGNMENT.get(ep["id"], {}).get("used")
        lines.append(f"## {ep['id']} – {ep['title']} ({'mit offiziellem Transkript abgeglichen' if aligned else 'nur Whisper'})")
        for s, msg in sorted(flags)[:40]:
            lines.append(f"- {b.fmt_time(s)}: {msg}")
        if rare:
            lines.append(f"- seltene Wörter (nur hier): {', '.join(rare[:40])}")
        if not flags and not rare:
            lines.append("- nichts auffällig")
        lines.append("")
        total += len(flags)
    (OUT / "scan.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{total} Markierungen -> {OUT / 'scan.md'}")


if __name__ == "__main__":
    main()
