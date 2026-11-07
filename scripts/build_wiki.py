#!/usr/bin/env python3
"""Baut das Handelsblatt-Crime-Wissensarchiv als Obsidian-Vault.

Eingaben (alle im Ordner data/):
  feed.xml             – RSS-Feed des Podcasts (alle Folgen, Shownotes, Dauer, MP3, offizielle Transkripte)
  spotify_ids.json     – Zuordnung Folge („#162“) -> Spotify-Episoden-ID (für Minuten-Links)
  transcripts/*.json   – Wort-genaue Transkripte, Dateiname = Folgen-ID (z. B. 162.json)
                         Format: {"words": [{"text": "...", "start": 7.9, "end": 8.1}, ...]}
  official/*.json      – offizielle Podigee-Transkripte (Segmente), beim Bauen mit den Whisper-Zeitstempeln
                         zusammengeführt (align_official.py)
  corrections.tsv      – Hörfehler-Korrekturen, beim Bauen angewendet
  topic_exclusions.tsv – von Hand geprüfte Fehlzuordnungen Thema → Folge

Ausgabe: Handelsblatt-Crime-Wiki/  (diesen Ordner in Obsidian als Vault öffnen)

Aufruf:  python scripts/build_wiki.py
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align_official  # noqa: E402
import corrections  # noqa: E402
from topics import TOPICS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VAULT = ROOT / "Handelsblatt-Crime-Wiki"
HOME = "Handelsblatt Crime Wiki"

NS = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "podcast": "https://podcastindex.org/namespace/1.0",
    "content": "http://purl.org/rss/1.0/modules/content/",
}
SHOW_URL = "https://open.spotify.com/show/3bzKxZUhiIRZKavCmKIYCx"
FEED_URL = "https://hb-crime.podigee.io/feed/mp3"
FOLDERS = ["Fälle", "Themen", "Unternehmen", "Personen"]
# Hosts werden in fast jeder Folge genannt (Begrüßung) -> keine Zitate, nur Folgen-Ebene
NO_QUOTES = {"Ina Karabasz", "Solveig Gode", "Sönke Iwersen"}
MAX_QUOTES_PER_EPISODE = 4
# Zuordnung Artikel → Folge: Hauptthema bei Titel-Treffer, Shownotes-Treffer mit mindestens MIN_NOTES Nennungen
# oder ab FOLDER_MIN Nennungen im Transkript; „kurz erwähnt“ ab FOLDER_MINOR Nennungen.
# Ein Eintrag kann mit "min" eine eigene Schwelle setzen (z. B. 1 für Hosts, die sich einmal vorstellen).
FOLDER_MIN = {"Fälle": 6, "Themen": 6, "Unternehmen": 4, "Personen": 3}
FOLDER_MINOR = {"Fälle": 2, "Themen": 3, "Unternehmen": 2, "Personen": 2}
MIN_NOTES = 2

CORRECTIONS: dict = {}  # Folge -> Counter der angewendeten Korrekturregeln
ALIGNMENT: dict = {}  # Folge -> Statistik des Abgleichs mit dem offiziellen Transkript
_PR = DATA / "proofread.txt"
PROOFREAD = {l.split("\t")[0].strip() for l in (_PR.read_text(encoding="utf-8").splitlines() if _PR.exists() else []) if l.strip() and not l.startswith("#")}
_EXCL = DATA / "topic_exclusions.tsv"
EXCLUDE = {tuple(l.split("\t")[:2]) for l in (_EXCL.read_text(encoding="utf-8").splitlines() if _EXCL.exists() else []) if l and not l.startswith("#")}


# --------------------------------------------------------------------------- Hilfsfunktionen
def fmt_time(sec: float) -> str:
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def clean_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text or "")
    text = re.sub(r"</p>\s*<p>", "\n\n", text)
    text = re.sub(r"</(li|h\d|div)>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\xa0", " ").replace("�", "")
    text = "\n".join(l.strip() for l in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# Zeilen der Shownotes, die sich in jeder Folge wiederholen (Abo-Angebot, Werbung, Umfrage). Sie werden aus den
# angezeigten Shownotes entfernt und von der Themensuche ignoriert.
BOILERPLATE = re.compile(
    r"^(Weitere Informationen zu Werbeeinblendungen|Helfen Sie uns, unsere Podcasts|www\.handelsblatt\.com/|"
    r"https?://www\.handelsblatt\.com/(mehrjournalismus|zufriedenheit|wirtschaftsabo|sommer-special)|"
    r"Das exklusive Abo-Angebot|Mehr über die Angebote unserer Werbepartner|Alle, die Zugriff auf die gesamten|"
    r"Exklusives Angebot für Handelsblatt|Handelsblatt Crime erscheint alle 14 Tage|Unser speziell für Handelsblatt Crime|"
    r"Handelsblatt Crime finden Sie auf allen|Jetzt reinhören: 14-tägig|\*\*\*\s*Handelsblatt Crime kommt live|"
    r"Mehr Informationen unter: www\.|Alle Infos (dazu|zur Liveshow)|Tickets (gibt es|unter))",
    re.I,
)


def strip_boilerplate(text: str) -> str:
    keep = [l for l in text.splitlines() if not BOILERPLATE.match(l.strip())]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(keep)).strip()


def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|#^\[\]]', " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:90].strip(" .") if len(name) > 90 else name


def parse_duration(d: str) -> int:
    parts = [int(float(p)) for p in (d or "0").split(":")]
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


def episode_kind(title: str) -> str:
    """folge = reguläre Folge, sonder = Sonderfolge/englische Fassung, team = „Meet the Team“, hinweis = Trailer/Tipp."""
    t = title.strip().lower()
    if t.startswith("meet the team"):
        return "team"
    if t.startswith(("podcast-tipp", "neuer podcast", "neue crime live", "trailer")) or "live-show termine" in t:
        return "hinweis"
    if t.startswith(("sonderfolge", "english version")):
        return "sonder"
    return "folge"


KIND_LABEL = {"folge": "Folge", "sonder": "Sonderfolge", "team": "Meet the Team", "hinweis": "Hinweis"}


# --------------------------------------------------------------------------- Folgen
def load_episodes() -> list[dict]:
    root = ET.parse(DATA / "feed.xml").getroot()
    ids = json.loads((DATA / "spotify_ids.json").read_text(encoding="utf-8")) if (DATA / "spotify_ids.json").exists() else {}
    episodes = []
    for item in root.iter("item"):
        title = re.sub(r"\s+", " ", item.findtext("title").strip())
        date = parsedate_to_datetime(item.findtext("pubDate"))
        num = int(item.findtext("itunes:episode", namespaces=NS) or 0)
        ep_id, key = f"{num:03d}", f"#{num}"
        kind = episode_kind(title)
        enc = item.find("enclosure")
        tr = next((t for t in item.findall("podcast:transcript", NS) if t.get("type") == "application/json"), None)
        raw_notes = item.findtext("content:encoded", namespaces=NS) or ""
        if len(clean_html(raw_notes)) < 40:
            raw_notes = item.findtext("description") or ""
        episodes.append(
            {
                "id": ep_id,
                "key": key,
                "kind": kind,
                "num": num,
                "year": date.year,
                "title": title,
                "short": title,
                "date": date.strftime("%Y-%m-%d"),
                "duration": parse_duration(item.findtext("itunes:duration", namespaces=NS)),
                "description": strip_boilerplate(clean_html(raw_notes)),
                "summary": clean_html(item.findtext("description") or ""),
                "audio": enc.get("url", "") if enc is not None else "",
                "transcript_url": tr.get("url") if tr is not None else "",
                "link": item.findtext("link") or "",
                "spotify_id": ids.get(key) or ids.get(title),
                "note": safe_filename(f"{ep_id} {title}"),
            }
        )
    episodes.sort(key=lambda e: (e["date"], e["id"]))
    return episodes


def spotify_link(ep: dict, sec: float | None = None) -> str:
    if ep["spotify_id"]:
        url = f"https://open.spotify.com/episode/{ep['spotify_id']}"
        return f"{url}?t={int(sec)}" if sec is not None else url
    return SHOW_URL


def load_transcript(ep: dict) -> list[dict] | None:
    f = DATA / "transcripts" / f"{ep['id']}.json"
    if not f.exists():
        return None
    data = json.loads(f.read_text(encoding="utf-8"))
    words = data["words"] if isinstance(data, dict) else data
    words = [w for w in words if w.get("type", "word") == "word" and w.get("text", "").strip()]
    words = drop_hallucinations(tidy(words))
    official = align_official.official_text(ep["id"])
    if official:
        words, stats = align_official.apply(words, official)
        ALIGNMENT[ep["id"]] = stats
    # Korrekturen laufen nach dem Abgleich, damit sie auch Fehler im offiziellen Text beheben
    words, hits = corrections.apply(words, ep["id"])
    CORRECTIONS[ep["id"]] = hits
    return words


# Sätze, die Whisper in Stille oder Musik erfindet (aus Untertitel-Trainingsdaten); sie werden beim Bauen entfernt.
HALLUCINATION = re.compile(r"Untertitelung (des|im Auftrag des) ZDF( für funk)?,? \d{4}\.?|Untertitel im Auftrag des ZDF,? \d{4}\.?", re.I)


def drop_hallucinations(words: list[dict]) -> list[dict]:
    text, starts, pos = [], [], 0
    for w in words:
        starts.append(pos)
        text.append(w["text"])
        pos += len(w["text"]) + 1
    spans = [(m.start(), m.end()) for m in HALLUCINATION.finditer(" ".join(text))]
    if not spans:
        return words
    return [w for w, s in zip(words, starts) if not any(a <= s < b for a, b in spans)]


def tidy(words: list[dict]) -> list[dict]:
    """Whisper trennt „Cum-Ex“ in „Cum“ + „-Ex“, „handelsblatt.com“ in „handelsblatt“ + „.com“ und „20 %“;
    solche Bruchstücke werden wieder an das vorige Wort gehängt."""
    out: list[dict] = []
    for w in words:
        t = w["text"]
        if out and t[:1] in "-.%'’" and (len(t) > 1 or t in "%'’"):
            prev = out[-1]
            out[-1] = {**prev, "text": prev["text"] + t, "end": w["end"]}
        else:
            out.append(w)
    return out


def segments(words: list[dict], seconds: int = 60) -> list[dict]:
    """Fasst Wörter zu Absätzen pro Minute zusammen (Schnitt am Satzende)."""
    segs, cur, start = [], [], None
    for w in words:
        if start is None:
            start = w["start"]
        cur.append(w["text"])
        bucket_full = w["end"] - start >= seconds
        if bucket_full and re.search(r"[.!?]\"?“?$", w["text"]) or w["end"] - start >= seconds * 1.5:
            segs.append({"start": start, "text": " ".join(cur)})
            cur, start = [], None
    if cur:
        segs.append({"start": start, "text": " ".join(cur)})
    return segs


_INDEX: dict[int, tuple[str, list[int]]] = {}  # id(words) -> (Volltext, Wort-Startpositionen), einmal je Transkript


def text_index(words: list[dict]) -> tuple[str, list[int]]:
    key = id(words)
    if key not in _INDEX:
        offsets, pos = [], 0
        for w in words:
            offsets.append(pos)
            pos += len(w["text"]) + 1
        _INDEX[key] = (" ".join(w["text"] for w in words), offsets)
    return _INDEX[key]


def find_quotes(words: list[dict], patterns: list[str], rx: re.Pattern | None = None) -> list[dict]:
    """Findet Stellen im Transkript; liefert Zeitpunkt + Zitat-Ausschnitt."""
    if not words:
        return []
    import bisect

    full, offsets = text_index(words)
    hits, last_t = [], -999.0
    rx = rx or re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)
    for m in rx.finditer(full):
        idx = bisect.bisect_right(offsets, m.start()) - 1
        t = words[idx]["start"]
        if t - last_t < 90:  # nahe beieinander liegende Treffer zusammenfassen
            continue
        last_t = t
        lo, hi = max(0, idx - 12), min(len(words), idx + 22)
        snippet = " ".join(w["text"] for w in words[lo:hi])
        hits.append({"t": max(0.0, t - 3), "quote": ("… " if lo else "") + snippet + (" …" if hi < len(words) else "")})
    return hits


# --------------------------------------------------------------------------- Schreiben
def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


# Personen: Hosts und Investigativ-Chef zuerst, sonst alphabetisch
PINNED = {"Personen": ["Ina Karabasz", "Solveig Gode", "Sönke Iwersen"]}


def sort_key(name: str, folder: str):
    pins = PINNED.get(folder, [])
    return (pins.index(name) if name in pins else len(pins), name.casefold())


def status_line(ep: dict, words) -> str:
    """Prüfstatus eines Transkripts, steht auf Transkript- und Folgenseite."""
    st = ALIGNMENT.get(ep["id"])
    if st and st.get("used"):
        return "mit dem offiziellen Transkript abgeglichen"
    if ep["id"] in PROOFREAD:
        return "vollständig Korrektur gelesen"
    return "**noch nicht Korrektur gelesen**"


def build() -> None:
    episodes = load_episodes()
    if VAULT.exists():
        for sub in ["Folgen", "Transkripte", *FOLDERS]:
            shutil.rmtree(VAULT / sub, ignore_errors=True)
    transcripts = {e["id"]: load_transcript(e) for e in episodes}
    n_tx = sum(1 for t in transcripts.values() if t)

    # ---- Treffer je Artikel sammeln
    topic_hits: dict[str, list] = {}
    ep_topics: dict[str, dict[str, list[str]]] = {e["id"]: {f: [] for f in FOLDERS} for e in episodes}
    ep_mentions: dict[str, list[str]] = {e["id"]: [] for e in episodes}
    for topic in TOPICS:
        rx = re.compile("|".join(f"(?:{p})" for p in topic["patterns"]), re.IGNORECASE)
        min_mentions = topic.get("min") or FOLDER_MIN[topic["folder"]]
        min_minor = min(FOLDER_MINOR[topic["folder"]], min_mentions)
        hits = []
        for ep in episodes:
            in_title = bool(rx.search(ep["title"]))
            in_notes = in_title or bool(rx.search(re.sub(r"https?://\S+|www\.\S+", " ", ep["description"])))
            if (topic["name"], ep["id"]) in EXCLUDE:
                continue
            quotes = []
            words = transcripts[ep["id"]]
            raw = len(rx.findall(text_index(words)[0])) if words else 0
            if raw and topic["name"] not in NO_QUOTES:
                quotes = find_quotes(words, topic["patterns"], rx)
            # ein Shownotes-Treffer zählt nur, wenn das Transkript ihn bestätigt (oder es noch keines gibt)
            notes_ok = in_title or (in_notes and (not words or raw >= MIN_NOTES))
            if notes_ok or raw >= min_minor:
                main = notes_ok or raw >= min_mentions
                hits.append({"ep": ep, "in_notes": notes_ok, "quotes": quotes, "main": main, "raw": raw})
                if main:
                    ep_topics[ep["id"]][topic["folder"]].append(topic["name"])
                else:
                    ep_mentions[ep["id"]].append(topic["name"])
        topic_hits[topic["name"]] = hits

    # ---- Folgen
    for ep in episodes:
        words = transcripts[ep["id"]]
        rows = "\n".join(
            f"| **{folder}** | {', '.join(f'[[{t}]]' for t in ep_topics[ep['id']][folder]) or '–'} |" for folder in FOLDERS
        )
        mentions_md = ", ".join(f"[[{t}]]" for t in ep_mentions[ep["id"]]) or "–"
        chapters = ""
        if words:
            segs = segments(words, 120)
            chapters = "\n## Zeitmarken\n\n" + "\n".join(
                f"- [{fmt_time(s['start'])}]({spotify_link(ep, s['start'])}) – "
                f"{' '.join(s['text'].split()[:18])} … ([[Transkript {ep['id']}#Minute {int(s['start'] // 60)}|Transkript]])"
                for s in segs
            )
        tx_line = (
            f"[[Transkript {ep['id']}]] (Wort-genau mit Zeitstempeln, {status_line(ep, words)})"
            if words
            else "noch nicht transkribiert – siehe [[Anleitung Transkription]]"
        )
        hb = f" · [handelsblatt.com]({ep['link']})" if ep["link"] else ""
        write(
            VAULT / "Folgen" / f"{ep['note']}.md",
            f"""---
type: folge
folge: "{ep['key']}"
art: {ep['kind']}
nummer: {ep['num']}
jahr: {ep['year']}
datum: {ep['date']}
dauer: "{fmt_time(ep['duration'])}"
spotify: "{spotify_link(ep)}"
transkript: {"true" if words else "false"}
tags: [folge, jahr-{ep['year']}, {ep['kind']}]
---
# {ep['title']}

| | |
|---|---|
| **Folge** | {ep['key']} · {KIND_LABEL[ep['kind']]} |
| **Datum** | {ep['date']} |
| **Dauer** | {fmt_time(ep['duration'])} |
| **Anhören** | [Spotify]({spotify_link(ep)}) · [MP3]({ep['audio']}){hb} |
| **Transkript** | {tx_line} |
{rows}
| **Kurz erwähnt** | {mentions_md} |

## Shownotes

{ep['description'] or '_keine Shownotes_'}
{chapters}

---
← [[Alle Folgen]] · [[{HOME}|Start]]
""",
        )

        if words:
            segs = segments(words, 60)
            body = "\n\n".join(
                f"### Minute {int(s['start'] // 60)}\n[▶ {fmt_time(s['start'])}]({spotify_link(ep, s['start'])})  \n{s['text']}"
                for s in segs
            )
            write(
                VAULT / "Transkripte" / f"Transkript {ep['id']}.md",
                f"""---
type: transkript
folge: "{ep['key']}"
tags: [transkript]
---
# Transkript – {ep['title']}

Folge: [[{ep['note']}]] · automatisch transkribiert, {status_line(ep, words)} ({sum(CORRECTIONS.get(ep['id'], {}).values())} Korrekturen), vereinzelte Hörfehler möglich.
Klick auf ▶ öffnet Spotify an genau dieser Stelle.

{body}
""",
            )

    # ---- Fälle / Themen / Unternehmen / Personen
    for topic in TOPICS:
        hits = topic_hits[topic["name"]]
        quote_blocks, ep_list, ep_minor = [], [], []
        for h in sorted(hits, key=lambda h: h["ep"]["date"]):
            ep = h["ep"]
            mins = ", ".join(f"[{fmt_time(q['t'])}]({spotify_link(ep, q['t'])})" for q in h["quotes"][:MAX_QUOTES_PER_EPISODE])
            where = " · ".join(x for x in ["Shownotes" if h["in_notes"] else "", f"Minute {mins}" if mins else ""] if x)
            (ep_list if h["main"] else ep_minor).append(f"- [[{ep['note']}|{ep['key']} – {ep['short']}]] ({ep['date']}) — {where}")
            for q in h["quotes"][:MAX_QUOTES_PER_EPISODE]:
                quote_blocks.append(
                    f"> {q['quote']}\n>\n> — [[{ep['note']}|{ep['key']}]], "
                    f"[Minute {fmt_time(q['t'])}]({spotify_link(ep, q['t'])}) · "
                    f"[[Transkript {ep['id']}#Minute {int(q['t'] // 60)}|im Transkript]]"
                )
        quotes_md = "\n## Was im Podcast gesagt wird\n\n" + "\n\n".join(quote_blocks) if quote_blocks else ""
        write(
            VAULT / topic["folder"] / f"{topic['name']}.md",
            f"""---
type: {topic['folder'].lower().replace('ä', 'ae')}
folgen: {len(ep_list)}
tags: [{topic['folder'].lower().replace('ä', 'ae')}]
---
# {topic['name']}

_{topic['summary']}_

## Erklärung
{topic['body'].strip()}

> [!info] Hinweis
> Die Erklärung oben ist allgemeines Hintergrundwissen. Was **im Podcast** dazu gesagt
> wurde, steht unten – mit Link zur genauen Minute.
{quotes_md}

## In diesen Folgen ({len(ep_list)})

{chr(10).join(ep_list) or '_bisher keine Folge, in der das ausführlich Thema war_'}
{f"{chr(10)}## Kurz erwähnt ({len(ep_minor)}){chr(10)}{chr(10)}" + chr(10).join(ep_minor) + chr(10) if ep_minor else ""}
---
← [[{topic['folder']}]] · [[{HOME}|Start]]
""",
        )

    # ---- Übersichten
    by_year: dict[int, list] = {}
    for ep in episodes:
        by_year.setdefault(ep["year"], []).append(ep)
    folgen_md = []
    for year in sorted(by_year, reverse=True):
        folgen_md.append(f"## {year}\n")
        folgen_md.append("| Folge | Datum | Dauer | Transkript |\n|---|---|---|---|")
        for ep in sorted(by_year[year], key=lambda e: (e["date"], e["num"]), reverse=True):
            folgen_md.append(
                f"| [[{ep['note']}\\|{ep['key']} – {ep['short']}]] | {ep['date']} | {fmt_time(ep['duration'])} | "
                f"{'✅' if transcripts[ep['id']] else '–'} |"
            )
        folgen_md.append("")
    write(VAULT / "Alle Folgen.md", "# Alle Folgen\n\n" + "\n".join(folgen_md) + f"\n← [[{HOME}|Start]]")

    for folder in FOLDERS:
        items = sorted((t for t in TOPICS if t["folder"] == folder), key=lambda t: sort_key(t["name"], folder))
        lines = [f"- [[{t['name']}]] — {t['summary']} ({sum(h['main'] for h in topic_hits[t['name']])} Folgen)" for t in items]
        write(VAULT / f"{folder}.md", f"# {folder}\n\n" + "\n".join(lines) + f"\n\n← [[{HOME}|Start]]")

    total = sum(e["duration"] for e in episodes)
    top = sorted(TOPICS, key=lambda t: -sum(h["main"] for h in topic_hits[t["name"]]))
    top_md = "\n".join(
        f"- [[{t['name']}]] ({sum(h['main'] for h in topic_hits[t['name']])})" for t in top if t["folder"] == "Fälle"
    )
    latest = sorted(episodes, key=lambda e: e["date"], reverse=True)[:5]
    write(
        VAULT / f"{HOME}.md",
        f"""---
tags: [start]
---
# 🕵️ Handelsblatt Crime Wiki – Streitfälle der deutschen Wirtschaft

Das Wissensarchiv zum Podcast [Handelsblatt Crime]({SHOW_URL}) mit den Hosts **[[Ina Karabasz]]** und
**[[Solveig Gode]]** und dem Investigativ-Team um **[[Sönke Iwersen]]**: Korruption, Betrug, Cum-Ex, Wirecard,
Benko und viele weitere Fälle. Jede Info ist mit der **Folge** verlinkt – und bei transkribierten Folgen mit der
**genauen Minute** (Klick öffnet Spotify an der Stelle).

**Stand:** {datetime.now().strftime('%d.%m.%Y')} · **{len(episodes)} Folgen** · **{total // 3600} h {total % 3600 // 60} min** Audio ·
**{n_tx} von {len(episodes)} transkribiert**

## Navigation
- 📼 [[Alle Folgen]]
- 🗂️ [[Fälle]] – die Skandale und Streitfälle, mit Hintergrund und Zitaten
- 📚 [[Themen]] – Delikte, Begriffe und Mechanismen erklärt
- 🏢 [[Unternehmen]] – Konzerne, Banken, Kanzleien, Behörden
- 👤 [[Personen]] – Hosts, Investigativ-Team, Protagonisten
- 🛠️ [[Anleitung Transkription]] – weitere Folgen transkribieren

## Neueste Folgen
{chr(10).join(f"- [[{e['note']}|{e['title']}]] ({e['date']})" for e in latest)}

## Fälle nach Häufigkeit
{top_md}
""",
    )
    write(
        VAULT / "Anleitung Transkription.md",
        f"""# Anleitung: weitere Folgen transkribieren

Minuten-genaue Links gibt es nur für Folgen mit Transkript. So kommen weitere dazu:

## Variante A – kostenlos am eigenen PC (empfohlen)
1. Python 3.10+ und ffmpeg installieren, dann im Repo-Ordner:
   ```
   pip install faster-whisper
   python scripts/transcribe_local.py
   python scripts/fetch_official.py
   python scripts/build_wiki.py
   ```
2. Obsidian aktualisiert sich automatisch – alle Artikel bekommen Zitate mit Minuten-Links.

Einzelne Folgen: `python scripts/transcribe_local.py 162 161`
Mit NVIDIA-Grafikkarte nutzt das Skript die GPU (etwa 15× Echtzeit mit `large-v3-turbo`).

## Variante B – offizielle Transkripte
Für einzelne Folgen veröffentlicht Podigee ein offizielles Transkript im Feed. `fetch_official.py` lädt sie;
der Bau führt den offiziellen Wortlaut mit den Whisper-Zeitstempeln zusammen, diese Transkripte gelten als
„mit dem offiziellen Transkript abgeglichen“.

## Spotify-Links ergänzen
Für Minuten-Links auf Spotify braucht jede Folge ihre Spotify-ID in `data/spotify_ids.json`
(Teil nach `/episode/` im Spotify-Link, Schlüssel ist die Folgennummer wie `#162`). Fehlt sie, verlinkt das Wiki auf die Show.

← [[{HOME}|Start]]
""",
    )
    report = {k: {"summe": sum(v.values()), "regeln": dict(v.most_common())} for k, v in sorted(CORRECTIONS.items())}
    (DATA / "corrections_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "alignment_report.json").write_text(json.dumps(dict(sorted(ALIGNMENT.items())), ensure_ascii=False, indent=1), encoding="utf-8")
    (VAULT / ".obsidian").mkdir(exist_ok=True)
    (VAULT / ".obsidian" / "app.json").write_text(
        '{\n  "alwaysUpdateLinks": true,\n  "newFileLocation": "folder",\n  "newFileFolderPath": "Themen",\n  "showFrontmatter": false\n}\n',
        encoding="utf-8",
    )
    print(f"Vault gebaut: {VAULT}  ({len(episodes)} Folgen, {n_tx} Transkripte, {len(TOPICS)} Artikel)")


if __name__ == "__main__":
    build()
