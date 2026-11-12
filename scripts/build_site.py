#!/usr/bin/env python3
"""Baut die Website (eine einzige HTML-Datei) aus dem Obsidian-Vault.

Aufruf:
    python scripts/build_site.py                       # -> _site/index.html (lokale Vorschau)
    python scripts/build_site.py public/index.html     # GitLab-CI-Job pages (GitLab Pages, privat)
    python scripts/build_site.py out.html --fragment   # ohne <html>-Gerüst (Vorschau-Artefakt)

Der Vault (Handelsblatt-Crime-Wiki/) bleibt die Quelle. Dieses Skript liest die Notizen, macht daraus strukturierte
Daten (Folgen, Artikel, Zitate, Transkripte) und setzt sie in site/template.html ein. Wird bei jedem Push auf main
vom GitLab-CI-Job pages ausgeführt.
"""
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "Handelsblatt-Crime-Wiki"
TEMPLATE = ROOT / "site" / "template.html"
HOME = "Handelsblatt Crime Wiki"
KIND = {"Fälle": "fall", "Themen": "thema", "Unternehmen": "firma", "Personen": "person"}
INDEX = {"fälle": "faelle", "themen": "themen", "unternehmen": "unternehmen", "personen": "personen"}
PINNED = ["Ina Karabasz", "Solveig Gode", "Sönke Iwersen"]
_PR = ROOT / "data" / "proofread.txt"
PROOFREAD = {l.split("\t")[0].strip() for l in (_PR.read_text(encoding="utf-8").splitlines() if _PR.exists() else []) if l.strip() and not l.startswith("#")}

WIKI = re.compile(r"\[\[([^\]]+?)\]\]")
MDLINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
BARE = re.compile(r"https?://[^\s<>\"\x00]+")


def slugify(s: str) -> str:
    s = s.replace("ß", "ss").replace("&", " und ").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def split_fm(md: str):
    m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    if not m:
        return {}, md
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, md[m.end():]


def sections(body: str):
    """'## Titel' -> Inhalt"""
    out, cur, buf = {}, "_intro", []
    for line in body.split("\n"):
        if line.startswith("## "):
            out[cur] = "\n".join(buf).strip()
            cur, buf = line[3:].strip(), []
        else:
            buf.append(line)
    out[cur] = "\n".join(buf).strip()
    return out


def label_to_sec(t: str) -> int:
    p = [int(x) for x in t.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


class Site:
    def __init__(self):
        self.notes = {}  # Name -> (Ordner, Frontmatter, Text)
        for p in sorted(VAULT.rglob("*.md")):
            rel = p.relative_to(VAULT)
            folder = rel.parts[0] if len(rel.parts) > 1 else ""
            fm, body = split_fm(p.read_text(encoding="utf-8"))
            self.notes[p.stem] = (folder, fm, body)
        self.route = {}
        for name, (folder, fm, _) in self.notes.items():
            if folder == "Folgen":
                self.route[name.lower()] = "folge-" + name.split()[0]
            elif folder == "Transkripte":
                self.route[name.lower()] = "transkript-" + name.split()[-1]
            elif folder in KIND:
                self.route[name.lower()] = f"{KIND[folder]}-{slugify(name)}"
        self.route.update({HOME.lower(): "start", "alle folgen": "folgen", **INDEX})

    # ---------- Links & kleines Markdown ----------
    def wiki_target(self, inner: str):
        inner = inner.replace("\\|", "|")
        target, _, alias = inner.partition("|")
        name, _, anchor = target.partition("#")
        r = self.route.get(name.strip().lower())
        if r and anchor.startswith("Minute "):
            r += "-m" + anchor.split()[-1]
        return r, (alias or name).strip()

    def inline(self, s: str) -> str:
        tokens = []

        def keep(h):
            tokens.append(h)
            return f"\x00{len(tokens) - 1}\x00"

        def wl(m):
            r, text = self.wiki_target(m.group(1))
            return keep(f'<a href="#{r}">{html.escape(text)}</a>' if r else html.escape(text))

        s = WIKI.sub(wl, s)
        s = MDLINK.sub(lambda m: keep(f'<a href="{html.escape(m.group(2))}" target="_blank" rel="noopener">'
                                      f'{html.escape(m.group(1))}</a>'), s)

        def bare(m):  # nackte Links aus den Shownotes kurz und klickbar: „handelsblatt.com/…“
            url = m.group(0).rstrip(".,;:")
            rest = m.group(0)[len(url):]
            host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
            label = host + ("/…" if len(url.split("/", 3)) > 3 and url.split("/", 3)[3] else "")
            return keep(f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(label)}</a>') + html.escape(rest)

        s = BARE.sub(bare, s)
        s = html.escape(s, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)
        s = re.sub(r"(?<![\w*])_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<em>\1</em>", s)
        return re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m.group(1))], s)

    def blocks(self, md: str) -> str:
        """Absätze, Listen, Zitate. Obsidian-Callouts werden weggelassen."""
        out, para, items, quote = [], [], [], []

        def flush():
            if para:
                out.append("<p>" + self.inline(" ".join(para)) + "</p>")
                para.clear()
            if items:
                out.append("<ul>" + "".join(f"<li>{self.inline(i)}</li>" for i in items) + "</ul>")
                items.clear()
            if quote:
                if not quote[0].startswith("[!"):
                    out.append("<blockquote><p>" + self.inline(" ".join(quote)) + "</p></blockquote>")
                quote.clear()

        for line in md.split("\n"):
            s = line.strip()
            if not s or s in {"_", "---"}:
                flush()
            elif s.startswith(">"):
                if para or items:
                    flush()
                quote.append(s.lstrip(">").strip())
            elif re.match(r"^[-*] ", s):
                if para or quote:
                    flush()
                items.append(s[2:])
            elif items and line.startswith("  "):
                items[-1] += " " + s
            else:
                if items or quote:
                    flush()
                para.append(s)
        flush()
        return "".join(out)

    # ---------- Inhalte ----------
    def episodes(self):
        eps = []
        for name, (folder, fm, body) in self.notes.items():
            if folder != "Folgen":
                continue
            sec = sections(body)
            title = re.search(r"^# (.+)$", body, re.M).group(1).strip()
            mp3 = re.search(r"\[MP3\]\((\S+?)\)", body)
            hb = re.search(r"\[handelsblatt\.com\]\((\S+?)\)", body)

            def row_links(label):
                out = []
                row = re.search(rf"^\| \*\*{label}\*\* \| (.*) \|$", body, re.M)
                for m in WIKI.finditer(row.group(1) if row else ""):
                    r, text = self.wiki_target(m.group(1))
                    if r:
                        out.append([r, text])
                return out

            topics = [t for lab in KIND for t in row_links(lab)]
            minor = row_links("Kurz erwähnt")
            marks = []
            for line in sec.get("Zeitmarken", "").splitlines():
                m = re.match(r"- \[(\d+:\d{2}(?::\d{2})?)\]\(\S+?\) – (.*?) \(\[\[", line)
                if m:
                    marks.append([label_to_sec(m.group(1)), m.group(2)])
            spotify = fm.get("spotify", "")
            ep_id = name.split()[0]
            tx_status = re.search(r"\| \*\*Transkript\*\* \| \[\[Transkript [^\]]+\]\] \([^,]+, (.*?)\)", body)
            eps.append({
                "id": ep_id, "label": fm.get("folge", ""), "kind": fm.get("art", "folge"), "num": int(fm.get("nummer", 0)),
                "title": title, "year": int(fm.get("jahr", 0)), "date": fm.get("datum", ""),
                "dur": fm.get("dauer", ""), "spotify": spotify if "/episode/" in spotify else "",
                "mp3": mp3.group(1) if mp3 else "", "hb": hb.group(1) if hb else "", "tx": fm.get("transkript") == "true",
                "status": (tx_status.group(1).replace("*", "") if tx_status else ""),
                "topics": topics, "minor": minor, "notes": self.blocks(sec.get("Shownotes", "")), "marks": marks,
            })
        eps.sort(key=lambda e: (e["date"], e["num"]), reverse=True)
        return eps

    def entries(self):
        out = []
        for name, (folder, fm, body) in self.notes.items():
            if folder not in KIND:
                continue
            sec = sections(body)
            lead = re.search(r"^_(.+)_$", sec["_intro"], re.M)
            quotes = []
            for block in re.split(r"\n\s*\n", sec.get("Was im Podcast gesagt wird", "")):
                lines = [l[1:].strip() for l in block.splitlines() if l.startswith(">")]
                text = " ".join(l for l in lines if l and not l.startswith("—"))
                src = next((l for l in lines if l.startswith("—")), "")
                ep = re.search(r"\[\[(\d{3}) ", src)
                tm = re.search(r"\[Minute (\d+:\d{2}(?::\d{2})?)\]", src)
                if text and ep and tm:
                    quotes.append([ep.group(1), label_to_sec(tm.group(1)), text.strip("… ").strip()])

            def ep_lines(prefix):
                out = []
                key = next((k for k in sec if k.startswith(prefix)), None)
                for line in (sec.get(key, "") if key else "").splitlines():
                    m = re.match(r"- \[\[(\d{3}) ", line)
                    if m:
                        times = [label_to_sec(t) for t in re.findall(r"\[(\d+:\d{2}(?::\d{2})?)\]\(", line)]
                        out.append([m.group(1), "Shownotes" in line, times])
                return out

            eps, minor = ep_lines("In diesen Folgen"), ep_lines("Kurz erwähnt")
            out.append({
                "r": self.route[name.lower()], "name": name, "kind": KIND[folder],
                "lead": lead.group(1) if lead else "",
                "count": len(eps), "pin": PINNED.index(name) if name in PINNED else -1,
                "expl": self.blocks(sec.get("Erklärung", "")), "quotes": quotes, "eps": eps, "minor": minor,
            })
        out.sort(key=lambda e: e["name"].lower())
        return out

    def transcripts(self):
        tx = {}
        for name, (folder, fm, body) in self.notes.items():
            if folder != "Transkripte":
                continue
            rows = [[label_to_sec(m.group(1)), m.group(2).strip()] for m in re.finditer(
                r"^### Minute \d+\n\[▶ (\d+:\d{2}(?::\d{2})?)\]\(\S+\)\s*\n(.*?)(?=\n### |\Z)", body, re.S | re.M)]
            tx[name.split()[-1]] = rows
        return tx

    def hours(self):
        h = re.search(r"\*\*(\d+) h (\d+) min\*\*", self.notes[HOME][2])
        return [int(h.group(1)), int(h.group(2))] if h else [0, 0]


CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src data:; media-src https:; connect-src 'none'; "
       "base-uri 'none'; form-action 'none'; object-src 'none'")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fragment = "--fragment" in sys.argv
    out = Path(args[0]) if args else ROOT / "_site" / "index.html"
    site = Site()
    eps = site.episodes()
    data = {"eps": eps, "entries": site.entries(), "tx": site.transcripts(), "hours": site.hours()}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    page = TEMPLATE.read_text(encoding="utf-8").replace("__VERSION__", version).replace("__DATA__", payload)
    if not fragment:
        page = ('<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                # Sicherheits-Header (R13): die statische Seite liefert keine eigenen HTTP-Header aus, daher als Meta-Tags,
                # soweit Browser das unterstützen (CSP ohne frame-ancestors, Referrer-Policy).
                f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
                '<meta name="referrer" content="strict-origin-when-cross-origin">\n'
                '<meta name="description" content="Handelsblatt Crime Fanwiki – Streitfälle der deutschen Wirtschaft. '
                'Jeder Fall, jede Person, jedes Zitat mit Link zur Folge und zur genauen Minute.">\n' + page + "\n</html>\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    if not fragment:
        (out.parent / ".nojekyll").touch()
    print(f"{len(eps)} Folgen, {len(data['entries'])} Einträge, {len(data['tx'])} Transkripte -> {out} "
          f"({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
