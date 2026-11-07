#!/usr/bin/env python3
"""Schreibt je Folge eine Prüfdatei mit allen Zuordnungen Fall/Thema/Unternehmen/Person und den Belegen dahinter
(Nennungen, Titel-/Shownotes-Treffer, Zitat-Ausschnitte), damit ein Prüfer beurteilen kann, ob die Zuordnung stimmt.

Aufruf:  python scripts/review_assignments.py            -> data/review/assignments/<Folgen-ID>.md
         python scripts/review_assignments.py 162 161    -> nur diese Folgen
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_wiki as b  # noqa: E402
from topics import TOPICS  # noqa: E402

OUT = b.DATA / "review" / "assignments"


def main() -> None:
    wanted = {f"{int(x):03d}" for x in sys.argv[1:] if x.isdigit()}
    eps = b.load_episodes()
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for ep in eps:
        if wanted and ep["id"] not in wanted:
            continue
        words = b.load_transcript(ep)
        if not words:
            continue
        text = " ".join(w["text"] for w in words)
        out = [f"# {ep['id']} – {ep['title']}", "", f"Shownotes: {ep['description'][:600]}", "",
               "Spalten: Ordner | Name | Status | Beleg. Status: HAUPT = Hauptthema, KURZ = kurz erwähnt, AUSGESCHLOSSEN = in topic_exclusions.tsv.", ""]
        for topic in TOPICS:
            rx = re.compile("|".join(f"(?:{p})" for p in topic["patterns"]), re.IGNORECASE)
            in_title = bool(rx.search(ep["title"]))
            in_notes = in_title or bool(rx.search(re.sub(r"https?://\S+|www\.\S+", " ", ep["description"])))
            raw = len(rx.findall(text))
            min_main = topic.get("min") or b.FOLDER_MIN[topic["folder"]]
            min_minor = min(b.FOLDER_MINOR[topic["folder"]], min_main)
            notes_ok = in_title or (in_notes and raw >= b.MIN_NOTES)
            if (topic["name"], ep["id"]) in b.EXCLUDE:
                status = "AUSGESCHLOSSEN"
            elif notes_ok or raw >= min_main:
                status = "HAUPT"
            elif raw >= min_minor:
                status = "KURZ"
            else:
                continue
            quotes = b.find_quotes(words, topic["patterns"])[:4]
            why = ("Titel" if in_title else "Shownotes" if in_notes else "") + f" {raw} Nennungen"
            out.append(f"## {topic['folder']} | {topic['name']} | {status} | {why.strip()}")
            for q in quotes:
                out.append(f"- {b.fmt_time(q['t'])}: {q['quote']}")
            out.append("")
            n += 1
        (OUT / f"{ep['id']}.md").write_text("\n".join(out), encoding="utf-8")
    print(f"{n} Zuordnungen in {len(list(OUT.glob('*.md')))} Dateien -> {OUT}")


if __name__ == "__main__":
    main()
