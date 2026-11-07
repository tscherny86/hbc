"""Gleicht das automatische (Whisper-)Transkript mit dem offiziellen Podigee-Transkript ab.

Whisper liefert Wort-Zeitstempel, verhört sich aber; das offizielle Transkript (data/official/<ID>.json,
geladen von fetch_official.py) hat den richtigen Wortlaut, aber nur Segment-Zeiten. Dieses Modul führt beides zusammen:

- übereinstimmende Wörter behalten ihren Whisper-Zeitstempel und übernehmen Schreibweise/Satzzeichen des Originals,
- abweichende Wortfolgen werden durch die offiziellen Wörter ersetzt, gleichmäßig über die von Whisper gehörte Spanne verteilt,
- von Whisper erfundene Wörter fallen weg, fehlende werden mit interpolierten Zeiten eingefügt.

Ergebnis: der offizielle Text, Minute für Minute. apply() liefert (Wörter, Statistik); die Statistik enthält den
Anteil übereinstimmender Wörter (ein niedriger Wert heißt, das offizielle Transkript gehört vermutlich zu einem anderen
Schnitt der Folge, der Abgleich wird dann nicht verwendet).
"""
import json
import re
from pathlib import Path

OFFICIAL = Path(__file__).resolve().parent.parent / "data" / "official"
MIN_RATIO = 0.6  # darunter wird der offizielle Text ignoriert
LONG_RUN = 25  # längere Läufe sind Passagen, die im offiziellen Text fehlen oder verschoben sind, keine Hörfehler

_NORM = re.compile(r"[^a-z0-9äöüß']+")


def norm(s: str) -> str:
    return _NORM.sub("", s.lower().replace("’", "'"))


def tokens(text: str) -> list[str]:
    return [t for t in text.replace("\xa0", " ").split() if norm(t)]


def official_text(ep_id: str) -> str | None:
    """Text des offiziellen Transkripts (JSON-Segmente von Podigee oder reiner Text), sonst None."""
    f = OFFICIAL / f"{ep_id}.json"
    if f.exists():
        data = json.loads(f.read_text(encoding="utf-8"))
        segs = data if isinstance(data, list) else data.get("segments") or data.get("transcript") or []
        text = " ".join(str(s.get("text", "")).strip() for s in segs if isinstance(s, dict))
    else:
        f = OFFICIAL / f"{ep_id}.txt"
        if not f.exists():
            return None
        text = f.read_text(encoding="utf-8")
    text = re.sub(r"…(?=\w)", "… ", text)
    return text


def _spread(items: list[str], start: float, end: float) -> list[dict]:
    """Verteilt Wörter gleichmäßig zwischen start und end."""
    n = len(items)
    if n == 0:
        return []
    step = max(0.0, (end - start)) / n
    out = []
    for k, t in enumerate(items):
        s = round(start + k * step, 2)
        out.append({"text": t, "type": "word", "start": s, "end": round(s + step, 2)})
    return out


def apply(words: list[dict], text: str):
    """Liefert (abgeglichene Wörter, {"ratio": Anteil Treffer, "replaced": n, "inserted": n, "deleted": n})."""
    import difflib

    off = tokens(text)
    if not words or not off:
        return words, {"ratio": 0.0}
    a = [norm(w["text"]) for w in words]
    b = [norm(t) for t in off]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out, matched, rep, ins, dele = [], 0, 0, 0, 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                out.append({**words[i], "text": off[j]})
            matched += i2 - i1
        elif tag == "replace":
            out.extend(_spread(off[j1:j2], words[i1]["start"], words[i2 - 1]["end"]))
            rep += j2 - j1
        elif tag == "insert":
            if j2 - j1 > LONG_RUN:  # ganze Passage, die der offizielle Text woanders hat: Zeit unbekannt, auslassen
                continue
            prev_end = out[-1]["end"] if out else (words[i1]["start"] if i1 < len(words) else 0.0)
            next_start = words[i1]["start"] if i1 < len(words) else prev_end + 0.3 * (j2 - j1)
            out.extend(_spread(off[j1:j2], prev_end, max(next_start, prev_end)))
            ins += j2 - j1
        elif tag == "delete":
            if i2 - i1 > LONG_RUN:  # ganze Passage fehlt im offiziellen Text: behalten, was Whisper gehört hat
                out.extend(words[i1:i2])
                continue
            dele += i2 - i1
    ratio = matched / max(1, len(a))
    if ratio < MIN_RATIO:
        return words, {"ratio": round(ratio, 3), "used": False}
    return out, {"ratio": round(ratio, 3), "replaced": rep, "inserted": ins, "deleted": dele, "used": True}
