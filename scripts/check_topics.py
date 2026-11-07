#!/usr/bin/env python3
"""Prüft die Artikel in data/topics/*.json und scripts/topics.py: gültige Suchmuster, eindeutige Namen über alle
Ordner (gleiche Namen würden im Vault und in den Website-Routen kollidieren), Kurzbeschreibung bis 110 Zeichen,
Dateinamen ohne verbotene Zeichen.

Aufruf:  python scripts/check_topics.py          # nur Bericht
         python scripts/check_topics.py --fix    # Dubletten auflösen: Unternehmen, die es schon als Fall gibt, entfallen;
                                                 # Fälle mit Personennamen heißen „Fall <Name>“; Kurzbeschreibungen kürzen
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "data" / "topics"
BAD = re.compile(r'[\\/:*?"<>|#^\[\]]')

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    fix = "--fix" in sys.argv
    sys.path.insert(0, str(ROOT / "scripts"))
    import topics as tp  # noqa: E402  (lädt auch die JSON-Dateien)

    files = {f: json.loads(f.read_text(encoding="utf-8")) for f in sorted(FOLDER.glob("*.json"))}
    where = defaultdict(list)
    for t in tp.TOPICS:
        if t["name"] not in {x["name"] for d in files.values() for x in d}:
            where[t["name"]].append(("topics.py", t["folder"]))
    for f, d in files.items():
        for t in d:
            where[t["name"]].append((f.name, t["folder"]))
    problems = 0
    for f, d in files.items():
        for t in d:
            for p in t["patterns"]:
                try:
                    re.compile(p, re.I)
                except re.error as err:
                    print(f"  Muster kaputt [{f.name}] {t['name']}: {p} ({err})"); problems += 1
            if len(t["summary"]) > 110:
                print(f"  Kurzbeschreibung zu lang [{f.name}] {t['name']}: {len(t['summary'])} Zeichen"); problems += 1
                if fix:
                    s = t["summary"][:108].rsplit(" ", 1)[0].rstrip(",;:– ") + " …"
                    t["summary"] = s
            if BAD.search(t["name"]):
                print(f"  verbotenes Zeichen im Namen [{f.name}] {t['name']}"); problems += 1
    dups = {n: v for n, v in where.items() if len(v) > 1}
    for n, v in dups.items():
        print(f"  Dublette: {n} -> {v}"); problems += 1
    if fix and dups:
        for n, v in dups.items():
            folders = {fo for _, fo in v}
            if "Fälle" in folders and "Unternehmen" in folders:
                for f, d in files.items():
                    files[f] = [t for t in d if not (t["name"] == n and t["folder"] == "Unternehmen")]
                print(f"  -> Unternehmen {n!r} entfernt (Fall bleibt)")
            elif "Fälle" in folders and "Personen" in folders:
                for f, d in files.items():
                    for t in d:
                        if t["name"] == n and t["folder"] == "Fälle":
                            t["name"] = f"Fall {n}"
                print(f"  -> Fall umbenannt in {'Fall ' + n!r}")
            elif "Themen" in folders and len(folders) > 1:
                for f, d in files.items():
                    files[f] = [t for t in d if not (t["name"] == n and t["folder"] == "Themen")]
                print(f"  -> Thema {n!r} entfernt")
            else:  # gleicher Ordner in zwei Dateien: zweite Fassung entfällt
                seen = False
                for f, d in files.items():
                    out = []
                    for t in d:
                        if t["name"] == n:
                            if seen:
                                continue
                            seen = True
                        out.append(t)
                    files[f] = out
                print(f"  -> zweite Fassung von {n!r} entfernt")
    if fix:
        for f, d in files.items():
            f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    total = sum(len(d) for d in files.values())
    print(f"{total} Artikel in {len(files)} Dateien, {problems} Befunde{' (behoben, soweit möglich)' if fix else ''}")


if __name__ == "__main__":
    main()
