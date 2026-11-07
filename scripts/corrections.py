"""Korrigiert typische Hörfehler der automatischen Transkription (z. B. "Kummex" -> "Cum-Ex").

Die Regeln stehen in data/corrections.tsv (eine Zeile pro Regel, Tab-getrennt):
    FALSCH <Tab> RICHTIG <Tab> global|local <Tab> Folgen (nur bei local, z. B. 020,162)

- FALSCH darf aus mehreren Wörtern bestehen ("Hanno Berger" aus "Hano Berger").
- Verglichen wird ganzwortig und ohne Groß-/Kleinschreibung; Satzzeichen am Rand bleiben erhalten.
- "global" gilt für alle Transkripte (auch künftige), "local" nur für die genannten Folgen.
- FALSCH == RICHTIG ist eine Schutzregel: der Ausdruck bleibt unverändert, auch wenn eine andere Regel greifen würde.

Die Rohdaten in data/transcripts/ bleiben unverändert; korrigiert wird beim Bauen des Wikis.
Folgen mit offiziellem Podigee-Transkript werden zusätzlich daran ausgerichtet (align_official.py).
"""
import re
from collections import Counter
from pathlib import Path

RULES_FILE = Path(__file__).resolve().parent.parent / "data" / "corrections.tsv"
EDGE = re.compile(r"^([^\w§]*)(.*?)([^\w%]*)$", re.S)


def _key(text: str) -> str:
    return " ".join(text.lower().split())


TRAIL = {}


def load_rules():
    """-> {Wortanzahl: {falsch_klein: [(richtig, None | set(folgen)), ...]}}"""
    rules = {}
    if not RULES_FILE.exists():
        return rules
    for line in RULES_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        wrong, right = parts[0].strip(), parts[1].strip()
        scope = parts[2].strip() if len(parts) > 2 else "global"
        eps = None if scope == "global" else {e.strip() for e in (parts[3] if len(parts) > 3 else "").split(",") if e.strip()}
        if wrong and right:
            # wrong == right: Schutzregel, der Ausdruck bleibt unverändert; auch reine Schreibweise (cum ex -> Cum-Ex).
            # Satzzeichen am Rand zählen wie beim Abgleich nicht mit.
            m = EDGE.match(wrong)
            core = m.group(2) or wrong
            if m.group(3):
                TRAIL[_key(core)] = m.group(3)  # gehört zum Fehler ("E .Y ." -> "EY", Punkt weg)
            rules.setdefault(len(core.split()), {}).setdefault(_key(core), []).append((right, eps))
    return rules


RULES = load_rules()
MAXN = max(RULES, default=0)


def _pick(cands, ep_id):
    # folgenspezifische Regel vor globaler
    return next((r for r, eps in cands if eps is not None and ep_id in eps), None) \
        or next((r for r, eps in cands if eps is None), None)


def _pass(words: list[dict], ep_id: str, hits: Counter):
    out, i = [], 0
    while i < len(words):
        done = False
        for n in range(min(MAXN, len(words) - i), 0, -1):
            table = RULES.get(n)
            if not table:
                continue
            chunk = words[i:i + n]
            m = EDGE.match(" ".join(w["text"] for w in chunk))
            lead, core, trail = m.group(1), m.group(2), m.group(3)
            prefix = ""
            right = _pick(table.get(_key(core), []), ep_id)
            if right and TRAIL.get(_key(core)) and trail.startswith(TRAIL[_key(core)]):
                trail = trail[len(TRAIL[_key(core)]):]
            if not right and n == 1:
                # Wortteil nach Bindestrich: Regel "-Ex -> -Ex" greift in "Cum-Ex" und "-Ex"
                if lead.endswith("-"):
                    right = _pick(table.get(_key("-" + core), []), ep_id)
                    if right:
                        lead, right = lead[:-1], right
                elif "-" in core[1:]:
                    head, tail = core.rsplit("-", 1)
                    right = _pick(table.get(_key("-" + tail), []), ep_id)
                    if right:
                        prefix = head
            if not right:
                continue
            if not prefix and core[:1].isupper() and right[:1].islower() and right[1:] == right[1:].lower():
                right = right[0].upper() + right[1:]  # Satzanfang beibehalten
            new = lead + prefix + right + trail
            old = " ".join(w["text"] for w in chunk)
            if new != old:
                hits[f"{core} → {prefix + right}"] += 1
            out.append({**chunk[0], "text": new, "end": chunk[-1]["end"]})
            i += n
            done = True
            break
        if not done:
            out.append(words[i])
            i += 1
    return out


def apply(words: list[dict], ep_id: str):
    """Gibt (korrigierte Wörter, Counter{"falsch → richtig": anzahl}) zurück.

    Zwei Durchgänge: Regeln aus der Korrekturlesung beziehen sich teils auf schon korrigierten Text.
    Im zweiten Durchgang zählen nur echte Änderungen.
    """
    hits = Counter()
    out = _pass(words, ep_id, hits)
    out = _pass(out, ep_id, hits)
    return out, hits
