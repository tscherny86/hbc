#!/usr/bin/env python3
"""CI für das Fanwiki – gleich am PC und in GitLab CI.

Aufruf: python scripts/ci.py
1. Website in einen Temp-Ordner bauen (scripts/build_site.py) und prüfen, dass eine vollständige Seite entsteht.
2. Artikel prüfen (scripts/check_topics.py), sofern vorhanden – ohne Netz.
3. Version in package.json = oberster Eintrag in CHANGELOG.md.
Veröffentlicht nichts. Netzprüfungen (check_feed, check_marks) bleiben Handarbeit.
"""
import json, os, re, subprocess, sys, tempfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fehler = []

def step(name):
    print(f"\n=== {name}", flush=True)

step("Website bauen")
with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, "index.html")
    r = subprocess.run([sys.executable, "scripts/build_site.py", out], cwd=ROOT)
    if r.returncode:
        fehler.append("build_site.py fehlgeschlagen")
    elif not os.path.exists(out) or os.path.getsize(out) < 10_000:
        fehler.append("build_site.py hat keine vollständige Seite erzeugt")
    else:
        html = open(out, encoding="utf-8").read()
        if "<html" not in html.lower() or "</html>" not in html.lower():
            fehler.append("index.html ist unvollständig")
        else:
            print(f"✓ index.html: {os.path.getsize(out) // 1024} KB")

if os.path.exists(os.path.join(ROOT, "scripts", "check_topics.py")):
    step("Artikel prüfen (check_topics.py)")
    if subprocess.run([sys.executable, "scripts/check_topics.py"], cwd=ROOT).returncode:
        fehler.append("check_topics.py meldet Fehler")

step("Version")
v = json.load(open(os.path.join(ROOT, "package.json"), encoding="utf-8"))["version"]
m = re.search(r"^##\s+\[?v?(\d+\.\d+\.\d+)", open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read(), re.M)
if not m or m.group(1) != v:
    fehler.append(f"package.json {v}, CHANGELOG oben {m and m.group(1)}")
else:
    print(f"✓ Version {v} = oberster CHANGELOG-Eintrag")

for f in fehler:
    print("✗", f)
print("\n✗ CI fehlgeschlagen." if fehler else "\n✓ CI grün.")
sys.exit(1 if fehler else 0)
