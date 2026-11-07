#!/usr/bin/env python3
"""Übernimmt die Funde der Prüfer (data/review/out/proof-*.tsv, assign-*.tsv) in die Regeldateien.

- proof-*.tsv: FALSCH<TAB>RICHTIG<TAB>global|local<TAB>Folge<TAB>Grund → data/corrections.tsv
  Eine Regel wird nur übernommen, wenn FALSCH wirklich im fertigen Transkript dieser Folge vorkommt (ganzwortig, ohne
  Groß/Klein) und die Korrektur noch nicht bekannt ist. Regeln, die nicht greifen würden, werden aufgelistet.
- assign-*.tsv: NAME<TAB>Folge<TAB>Grund → data/topic_exclusions.tsv
  Nur Namen aus den Artikeln und bekannte Folgen-IDs werden übernommen.

Aufruf:  python scripts/apply_review.py            # nur Bericht
         python scripts/apply_review.py --write    # gültige Regeln anhängen
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_wiki as b  # noqa: E402
from topics import TOPICS  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = b.DATA / "review" / "out"
NAMES = {t["name"] for t in TOPICS}


def norm(s: str) -> str:
    return " ".join(re.sub(r"[^\w' ]+", " ", s.lower().replace("’", "'")).split())


def main() -> None:
    write = "--write" in sys.argv
    eps = {e["id"]: e for e in b.load_episodes()}
    texts = {}

    def text(eid):
        if eid not in texts:
            w = b.load_transcript(eps[eid]) or []
            texts[eid] = " " + norm(" ".join(x["text"] for x in w)) + " "
        return texts[eid]

    existing = {l.split("\t")[0].strip().lower() + "|" + (l.split("\t") + ["", "", ""])[3].strip()
                for l in (b.DATA / "corrections.tsv").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}
    good, bad, dup = [], [], []
    for f in sorted(OUT.glob("proof-*.tsv")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#") or line.lower().startswith(("falsch\t", "wrong\t")):
                continue
            p = [x.strip() for x in line.split("\t")] + ["", "", "", ""]
            wrong, right, scope, eid, reason = p[0], p[1], (p[2] or "local").lower(), p[3], p[4]
            eid = f"{int(eid):03d}" if eid.isdigit() else eid
            if not wrong or not right or norm(wrong) == norm(right):
                continue
            if scope == "global":
                where = [e for e in eps if (" " + norm(wrong) + " ") in text(e)]
                ok = bool(where)
            else:
                ok = eid in eps and (" " + norm(wrong) + " ") in text(eid)
            key = wrong.lower() + "|" + (eid if scope == "local" else "")
            if key in existing:
                dup.append((wrong, right, eid))
            elif ok:
                good.append((wrong, right, scope, eid if scope == "local" else "", reason, f.name))
                existing.add(key)
            else:
                bad.append((wrong, right, eid, f.name))
    excl_existing = {tuple(l.split("\t")[:2]) for l in (b.DATA / "topic_exclusions.tsv").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}
    ex_good, ex_bad = [], []
    for f in sorted(OUT.glob("assign-*.tsv")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            p = [x.strip() for x in line.split("\t")] + ["", ""]
            name, eid, reason = p[0], p[1], p[2]
            eid = f"{int(eid):03d}" if eid.isdigit() else eid
            if name in NAMES and eid in eps and (name, eid) not in excl_existing:
                ex_good.append((name, eid, reason)); excl_existing.add((name, eid))
            elif (name, eid) not in excl_existing:
                ex_bad.append((name, eid, f.name))
    print(f"Korrekturen: {len(good)} gültig, {len(bad)} nicht im Transkript gefunden, {len(dup)} schon bekannt")
    for w, r, e, f in bad[:40]:
        print(f"  NICHT GEFUNDEN [{f} {e}] {w!r} -> {r!r}")
    print(f"Ausschlüsse: {len(ex_good)} gültig, {len(ex_bad)} unbekannter Name/Folge")
    for n, e, f in ex_bad[:40]:
        print(f"  UNBEKANNT [{f}] {n!r} {e}")
    if write:
        with open(b.DATA / "corrections.tsv", "a", encoding="utf-8") as fh:
            for w, r, s, e, reason, _ in good:
                fh.write(f"{w}\t{r}\t{s}\t{e}\n")
        with open(b.DATA / "topic_exclusions.tsv", "a", encoding="utf-8") as fh:
            for n, e, reason in ex_good:
                fh.write(f"{n}\t{e}\t{reason}\n")
        print("geschrieben")


if __name__ == "__main__":
    main()
