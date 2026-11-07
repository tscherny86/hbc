"""Fälle, Themen, Unternehmen und Personen des Handelsblatt-Crime-Wikis.

Jeder Eintrag erzeugt einen Artikel im Vault. Aufbau:
  name     – Titel des Artikels (= Dateiname)
  folder   – Unterordner (Fälle, Themen, Unternehmen, Personen)
  patterns – Regex-Muster (ohne Groß/Klein-Unterscheidung), mit denen Folgen-Titel, Shownotes und Transkripte
             durchsucht werden; eng fassen (Wortgrenzen \\b), keine Wörter, die in anderen stecken
  min      – optional: Nennungen im Transkript, ab denen die Folge als Hauptthema zählt
             (Standard je Ordner in build_wiki.FOLDER_MIN; 1 für Hosts, die sich einmal vorstellen)
  summary  – Ein-Satz-Beschreibung für Übersichten und Kacheln (ca. 110 Zeichen)
  body     – Erklärtext (Allgemeinwissen, NICHT aus dem Podcast). Was im Podcast gesagt wurde, ergänzt der
             Generator automatisch mit Folge + Minute.

Neue Einträge einfach hier ergänzen und `python scripts/build_wiki.py` laufen lassen.
Die ausführlichen Einträge stehen in data/topics/*.json (ein JSON je Ordner) und werden unten geladen; diese Datei
hält nur die Hosts und das Team, damit der Generator auch ohne die JSON-Dateien läuft.
"""
import json
from pathlib import Path

TOPICS = [
    # ------------------------------------------------------------------ Hosts
    {
        "name": "Ina Karabasz",
        "folder": "Personen",
        "patterns": [r"\bKarabasz\b", r"\bIna\b"],
        "min": 1,
        "summary": "Host von Handelsblatt Crime seit dem Start 2021, Ressortleiterin Podcast, Live und Video beim Handelsblatt.",
        "body": "**Ina Karabasz** moderiert Handelsblatt Crime seit der ersten Folge im Dezember 2021. Sie ist seit 2013 beim Handelsblatt, war Reporterin im Unternehmensressort (Telekommunikation, Technologie, IT-Sicherheit), leitete ab 2018 „Handelsblatt Live“ und seit Juli 2022 das Ressort Podcast, Live und Video. Die studierte Volkswirtin ist Absolventin der Georg von Holtzbrinck-Schule für Wirtschaftsjournalisten.",
    },
    {
        "name": "Solveig Gode",
        "folder": "Personen",
        "patterns": [r"\bGode\b", r"\bSolveig\b"],
        "min": 1,
        "summary": "Zweite Host seit 2024, stellvertretende Ressortleiterin Podcasts, Video und Live beim Handelsblatt.",
        "body": "**Solveig Gode** ist seit Frühjahr 2024 neben Ina Karabasz Host von Handelsblatt Crime. Sie kam vom Business Insider zum Handelsblatt und ist dort stellvertretende Ressortleiterin für Podcasts, Video und Live. Ihre Vorstellung gab es in der Mini-Serie „Meet the Team“ (#72).",
    },
    {
        "name": "Sönke Iwersen",
        "folder": "Personen",
        "patterns": [r"\bIwersen\b", r"\bSönke\b"],
        "min": 1,
        "summary": "Leiter des Handelsblatt-Investigativteams; erzählt im Podcast die meisten Fälle, von Cum-Ex bis Wirecard.",
        "body": "**Sönke Iwersen** leitet das Investigativ-Team des Handelsblatts (zeitweise als Co-Leiter mit Volker Votsmeier) und ist die prägende Stimme der Recherchen im Podcast. Mehrfach ausgezeichnet, unter anderem für die Recherchen zu Cum-Ex, Wirecard und den Tesla-Files. Seine Vorstellung in „Meet the Team“ ist Folge #77.",
    },
    # ------------------------------------------------------------------ Investigativ-Team
    *[
        {"name": n, "folder": "Personen", "patterns": p, "min": 2, "summary": s, "body": b}
        for n, p, s, b in [
            ("Volker Votsmeier", [r"\bVotsmeier\b"], "Investigativ-Redakteur und Co-Leiter des Investigativteams; Schwerpunkte Cum-Ex, Banken, Justiz.",
             "**Volker Votsmeier** gehört zur Leitung des Handelsblatt-Investigativteams und berichtet im Podcast vor allem über Cum-Ex, Landesbanken, die Hamburger Warburg-Affäre und Gerichtsverfahren. Vorstellung in „Meet the Team“ (#92)."),
            ("Lars-Marten Nagel", [r"\bLars[- ]Marten\b", r"\bNagel\b(?<!den Nagel)(?! (gerissen|reißen|zu))"], "Investigativ-Redakteur; Fälle rund um Immobilien, Anlegerbetrug und Insolvenzen.",
             "**Lars-Marten Nagel** ist Investigativ-Redakteur beim Handelsblatt und recherchiert unter anderem zu Immobilienpleiten, Anlegerskandalen und Insolvenzen. Vorstellung in „Meet the Team“ (#88)."),
            ("Christian Heinemann", [r"\bHeinemann\b"], "Produzent des Podcasts; zuständig für Schnitt, Ton und Produktion von Handelsblatt Crime.",
             "**Christian Heinemann** produziert Handelsblatt Crime: Schnitt, Ton und die Produktion der Folgen. Vorstellung in „Meet the Team“ (#85)."),
            ("Martin Murphy", [r"\bMurphy\b"], "Investigativ-Redakteur; Autoindustrie, Dieselgate, Porsche und Volkswagen.",
             "**Martin Murphy** berichtet im Investigativteam vor allem über die Autoindustrie – den Dieselskandal bei Volkswagen und Audi, Porsche und Tesla. Vorstellung in „Meet the Team“ (#83)."),
            ("Vinzenz Neumaier", [r"\bNeumaier\b"], "Investigativ-Redakteur; Fälle um Finanzinvestoren, Private Equity und Tech-Unternehmer.",
             "**Vinzenz Neumaier** ist Investigativ-Redakteur beim Handelsblatt, unter anderem mit Recherchen zu Finanzinvestoren, Private Equity und Wirtschaftskriminalität im Tech-Umfeld. Vorstellung in „Meet the Team“ (#81)."),
            ("Michael Verfürden", [r"\bVerfürden\b", r"\bVerfuerden\b"], "Investigativ-Redakteur; Tesla-Files, Datenlecks und Technologiekonzerne.",
             "**Michael Verfürden** gehört zum Investigativteam und hat mit Sönke Iwersen die Tesla-Files ausgewertet. Vorstellung in „Meet the Team“ (#79)."),
            ("René Bender", [r"\bBender\b"], "Investigativ-Redakteur; Immobilien, Benko/Signa und Finanzskandale.",
             "**René Bender** recherchiert im Investigativteam unter anderem zu René Benko und der Signa-Pleite sowie zu Finanz- und Immobilienskandalen. Vorstellung in „Meet the Team“ (#73)."),
            ("Felix Holtermann", [r"\bHoltermann\b"], "Finanzkorrespondent; Wirecard-Experte und Autor des Buchs „Geniale Betrüger“.",
             "**Felix Holtermann** ist Finanzkorrespondent des Handelsblatts und einer der Journalisten, die den Wirecard-Skandal am längsten verfolgt haben; Autor des Buchs „Geniale Betrüger“ über Wirecard."),
            ("Bert Fröndhoff", [r"\bFröndhoff\b", r"\bFroendhoff\b"], "Handelsblatt-Redakteur (Unternehmen, Chemie und Pharma); im Podcast bei Wirecard und Konzernfällen.",
             "**Bert Fröndhoff** ist Redakteur im Unternehmensressort des Handelsblatts und war im Podcast unter anderem bei den Folgen zum Wirecard-Prozess dabei."),
            ("Sebastian Matthes", [r"\bMatthes\b"], "Chefredakteur des Handelsblatts; Gast in einer Sonderfolge zu Recherche und Pressefreiheit.",
             "**Sebastian Matthes** ist seit 2020 Chefredakteur des Handelsblatts. In der Sonderfolge #154 spricht er über die Rolle investigativer Recherche, Pressefreiheit und den Umgang mit juristischem Druck auf Redaktionen."),
        ]
    ],
]


def _load_json_topics() -> None:
    """Ausführliche Artikel aus data/topics/*.json (fälle.json, themen.json, unternehmen.json, personen.json)."""
    folder = Path(__file__).resolve().parent.parent / "data" / "topics"
    if not folder.exists():
        return
    names = {t["name"] for t in TOPICS}
    for f in sorted(folder.glob("*.json")):
        for t in json.loads(f.read_text(encoding="utf-8")):
            if t["name"] in names:  # JSON ersetzt den Kurztext aus dieser Datei
                TOPICS[[x["name"] for x in TOPICS].index(t["name"])].update(t)
            else:
                TOPICS.append(t)
                names.add(t["name"])


_load_json_topics()
