#!/usr/bin/env python3
"""Prüft, ob die Minuten-Links wirklich auf die Wörter zeigen, die sie versprechen.

Für eine Stichprobe von Stellen je Folge wird ein paar Sekunden Audio am Zeitstempel ausgeschnitten, mit Whisper
transkribiert und mit den Transkriptwörtern an derselben Stelle verglichen. Geringe Ähnlichkeit heißt: Zeitstempel
(oder der abgeglichene Text dort) stimmt nicht.

Aufruf:  python scripts/check_marks.py            # 4 Stichproben je Folge
         python scripts/check_marks.py --per 8    # mehr Stichproben
         python scripts/check_marks.py 162 161    # nur diese Folgen
Ausgabe: data/review/marks.md und eine Zusammenfassung. Audio wird in data/review/audio/ zwischengespeichert.
"""
import argparse
import difflib
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_wiki as b  # noqa: E402
from transcribe_local import UA, add_cuda_dlls  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CLIP = 8.0  # Sekunden
OUT = b.DATA / "review"
CACHE = OUT / "audio"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9äöüß ]+", "", s.lower().replace("’", "'"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--per", type=int, default=4)
    args = ap.parse_args()
    wanted = {f"{int(x):03d}" for x in args.ids}
    add_cuda_dlls()
    from faster_whisper import WhisperModel

    try:
        model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
    except Exception:  # noqa: BLE001
        model = WhisperModel("small", device="cpu", compute_type="int8")
    CACHE.mkdir(parents=True, exist_ok=True)
    rows, bad = [], 0
    for ep in b.load_episodes():
        if wanted and ep["id"] not in wanted:
            continue
        words = b.load_transcript(ep)
        if not words or len(words) < 200:
            continue
        mp3 = CACHE / f"{ep['id']}.mp3"
        if not mp3.exists():
            req = urllib.request.Request(ep["audio"], headers={"User-Agent": UA})
            mp3.write_bytes(urllib.request.urlopen(req, timeout=180).read())
        dur = words[-1]["end"]
        points = [dur * (k + 1) / (args.per + 1) for k in range(args.per)]
        for t in points:
            raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-t", str(CLIP), "-i", str(mp3),
                                  "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
            audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
            segs, _ = model.transcribe(audio, language="de", vad_filter=False)
            heard = norm(" ".join(s.text for s in segs))
            expected = norm(" ".join(w["text"] for w in words if t - 1 <= w["start"] <= t + CLIP + 1))
            ratio = difflib.SequenceMatcher(None, heard.split(), expected.split(), autojunk=False).ratio()
            ok = ratio >= 0.5 or (heard and heard.split()[:3] == expected.split()[:3])
            if not ok:
                bad += 1
            rows.append((ep["id"], t, ratio, ok, heard[:90], expected[:90]))
            print(f"{'ok ' if ok else 'BAD'} {ep['id']} {b.fmt_time(t)} {ratio:.2f}", flush=True)
    lines = ["# Prüfung der Audiomarken", "", f"{len(rows)} Stichproben, {bad} Abweichungen (Ähnlichkeit < 0,5)", ""]
    for eid, t, r, ok, heard, exp in rows:
        if not ok:
            lines += [f"## {eid} {b.fmt_time(t)} – Ähnlichkeit {r:.2f}", f"- gehört:   {heard}", f"- erwartet: {exp}", ""]
    (OUT / "marks.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(rows)} Stichproben, {bad} Abweichungen -> {OUT / 'marks.md'}")


if __name__ == "__main__":
    main()
