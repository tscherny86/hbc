#!/usr/bin/env python3
"""Einmalige Schärfung der Suchmuster nach dem Prüflauf vom 07.11.2026 (Befunde der Helfer in
data/review/pattern_todo.md). Setzt Muster und Schwellen in data/topics/*.json; danach build_wiki.py laufen lassen."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = {
    # Name: (neue Muster oder None = unverändert, neue Schwelle oder None)
    "Prozess gegen Hanno Berger": ([r"\bHanno[- ]Bergers?\b", r"\bSteuer[- ]?Guru\b", r"\bMister Cum[- ]?Ex\b"], 4),
    "Kronzeuge Benjamin Frey": ([r"\bBenjamin Frey\b", r"\bKai[- ]Uwe Steck\b", r"\bStecks?\b", r"\bMann mit der Maske\b"], 6),
    "Landesbanken im Cum-Ex-Skandal": ([r"\bLandesbank(en)?\b(?=.{0,200}Cum)", r"\bLBBW\b", r"\bJaschinski\b", r"\bjustizfreie Zone\b", r"\bWestLB\b"], 6),
    "HSH Nordbank und Cum-Ex": ([r"\bHSH\b", r"\bHSH[- ]Nordbank\b", r"\bHamburg Commercial Bank\b", r"\bHCOB\b"], 6),
    "Hermes-Deal (Wirecard in Indien)": ([r"\bHermes\b", r"\bMauritius\b", r"\bRahul Sharma\b", r"\bChennai\b"], 6),
    "Marsalek-Brief": ([r"\bMarsalek[- ]Brief\b", r"\bBrief (von|des) (Jan )?Marsaleks?\b", r"\bSchreiben (von|des) Marsaleks?\b", r"\bMarsaleks? Brief\b"], 3),
    "Dieselgate (Volkswagen)": ([r"\bDieselgate\b", r"\bDiesel[- ]?skandal\w*", r"\bAbgas[- ]?skandal\w*", r"\bWinterkorns?\b", r"\bAbschalteinrichtung\w*", r"\bVolkswagen\b(?![- ]?Stiftung)"], 8),
    "Cyberangriff auf Continental": ([r"\bContinental\b(?=.{0,160}(Hacker|Cyber|Angriff|Daten|Lock ?Bit|Erpress|Darknet))", r"\bLock[- ]?Bit\b"], 3),
    "Aldi-Familienstreit": ([r"\bAldi\b", r"\bAldi[- ]Nord\b", r"\bAldi[- ]Süd\b", r"\bBabette\b", r"\bJakobus[- ]Stiftung\b", r"\bAlbrecht[- ](Erben|Familie|Brüder)\b"], 8),
    "Tesla-Files": ([r"\bTesla[- ]?Files\b", r"\bKrupskis?\b", r"\bKrupsky\b", r"\bDatenleck bei Tesla\b"], 3),
    "BSI-Affäre Schönbohm": ([r"\bSchönbohms?\b", r"\bSchoenbohm\b", r"\bBöhmermanns?\b", r"\bCyber[- ]?Sicherheitsrat\b"], 3),
    "Signa und René Benko": (None, 10),
    "BND-Spionage": ([r"\bCarsten L\b", r"\bArthur E\b", r"\bBND\b", r"\bBundesnachrichtendienst\w*"], 8),
    "Elbtower": ([r"\bElb[- ]?[Tt]owers?\b", r"\bChipperfield\b"], 4),
    "Porsche-Ikone vor Gericht": ([r"\bJürgen Barth\b", r"\bLe Mans\b", r"\bOriginal und Kopie\b"], 3),
    "Fall Jens Lehmann": ([r"\bJens Lehmanns?\b", r"\bMad Jens\b", r"\bLehmanns?\b(?=.{0,120}(Torwart|Nationaltorwart|Kettensäge|Garage|Starnberg))"], 3),
    "Syntellix und Utz Claassen": ([r"\bSyntellix\b", r"\bUtz Claassen\b"], 3),
    "Falscher Baron von Krupp": ([r"\bBohlen und Halbach\b", r"\bfalsche[rn]? Baron\b", r"\bBaron von Krupp\b"], 3),
    "Volksbank Köln Bonn (Bordell-Kredit)": ([r"\bVolksbank Köln[\s-]?Bonn\b", r"\bPascha\b", r"\bBrockhaus\b"], 6),
    "Hanno Berger": ([r"\bHanno Bergers?\b", r"\bMister Cum-?Ex\b"], 3),
    "Elon Musk": (None, 8),
    "René Benko": (None, 6),
    "Jens Lehmann": ([r"\bJens Lehmanns?\b", r"\bMad Jens\b"], 2),
    "Stefan Effenberg": ([r"\bStefan Effenberg\b", r"\bEffenbergs?\b(?![- ]?Bank)"], 3),
    "Utz Claassen": ([r"\bUtz Claassens?\b", r"\bClaassens?\b(?=.{0,80}Syntellix)"], 2),
    "Peter Koppe": ([r"\bPeter Koppes?\b", r"\bKoppes?\b"], 3),
    "Jürgen Barth": ([r"\bJürgen Barths?\b"], 2),
    "Insolvenzverwalter": ([r"\bInsolvenzverwalter\w*", r"\bSachwalter\w*", r"\bInsolvenzmasse\b"], 6),
    "Steuerfahndung": ([r"\bSteuerfahnd\w+", r"\bSelbstanzeige\w*", r"\bBetriebsprüf\w+"], 6),
    "Geldwäsche": ([r"\bGeldwäsche\w*", r"\bScheinfirm\w+", r"\bSteueroase\w*"], 6),
    "Whistleblower": ([r"\bWhistleblower\w*", r"\bHinweisgeber\w*", r"\bHinweisgeberschutz\w*"], 4),
    "Wirtschaftsprüfung": ([r"\bWirtschaftsprüf\w+", r"\bAbschlussprüf\w+", r"\bTestat\w*", r"\btestier\w+", r"\bAPAS\b"], 8),
    "Spionage": ([r"\bSpionage\w*", r"\bSpion(e|in|innen|en)?\b", r"\bLandesverrat\w*", r"\bAgentenführer\w*"], 6),
    "Cyberangriff und Ransomware": ([r"\bCyberangriff\w*", r"\bCyberattack\w*", r"\bHackerangriff\w*", r"\bRansomware\b", r"\bErpressungstrojaner\w*"], 4),
    "Datenleck": ([r"\bDatenleck\w*", r"\bDatendieb\w+", r"\bDatenklau\b", r"\bTesla[- ]?Files\b"], 4),
    "Strafverteidigung": ([r"\bStrafverteidig\w+", r"\bVerteidiger(in|innen|s|n)?\b", r"\bWahlverteidiger\w*", r"\bPflichtverteidiger\w*", r"\bBefangenheit\w*"], 8),
    "Pressefreiheit und Presserecht": ([r"\bPressefreiheit\b", r"\bPresserecht\w*", r"\bGegendarstellung\w*", r"\bUnterlassungs(erklärung|klage|anspruch)\w*", r"\b(Medien|Presse)anwält\w*"], 4),
    "Genossenschaftsbanken": ([r"\bGenossenschaftsbank\w*", r"\bGenossenschaftlich\w*", r"\bSicherungseinrichtung\b", r"\bBVR\b", r"\bGenossenschaftsverband\w*"], 4),
    "Rüstungsexporte und Provisionen": ([r"\bRüstungs(export|geschäft|konzern|industrie|deal|firma|unternehmen)\w*", r"\bWaffen(handel|geschäft|export|deal|lieferung)\w*", r"\bLeopard\b", r"\bPanzer\w*", r"\bKriegswaffen\w*"], 8),
    "Goldanlage": ([r"\bGold(händler|anlage|barren|kauf|raffinerie|sparplan|depot)\w*", r"\bEdelmetall\w*", r"\bTonnen Gold\b"], 6),
    "Volkswagen": ([r"\bVolkswagen\b(?![- ]?Stiftung)", r"\bVolkswagens\b", r"\bVW\b", r"\bWinterkorn\w*"], 6),
    "Porsche": ([r"\bPorsche (AG|SE|Holding|Automobil|Konzern|Museum)\b", r"\bZuffenhausen\w*", r"\bPorsche\b(?=.{0,80}(Konzern|Vorstand|Werk|Rennsport|Le Mans))"], 3),
    "Tesla": (None, 8),
    "Aldi": ([r"\bAldi\b", r"\bAldi[- ](Nord|Süd)\b", r"\bAlbrecht[- ]Brüder\b"], 6),
    "Handelsblatt": ([r"\bHandelsblatt Media Group\b", r"\bChefredakt(eur|ion) (des|vom) Handelsblatt\w*", r"\bHoltzbrinck\w*", r"\bJustiziar des Handelsblatt\w*"], 2),
    # zweite Runde (Befunde 116–131)
    "Audi-Dieselskandal": ([r"\bAudi[- ]Diesel\w*", r"\bRupert Stadler\b", r"\bStadlers?\b(?=.{0,120}(Audi|Diesel|Prozess|Urteil))", r"\bHatz\b", r"\bPamio\b"], 4),
    "Audi": ([r"\bAudi\b(?! A\d)", r"\bIngolstadt\w*", r"\bRupert Stadler\b"], 6),
    "Untersuchungshaft": ([r"\bUntersuchungshaft\b", r"\bU-Haft\b", r"\bFluchtgefahr\b", r"\bVerdunkelungsgefahr\b", r"\bHaftverschonung\w*"], 4),
    "Compliance": ([r"\bCompliance\w*", r"\binterne[nr]? Untersuchung\w*", r"\bSonderuntersuchung\w*"], 6),
    "Fraunhofer-Gesellschaft": ([r"\bFraunhofer\w*", r"\bNeugebauer\b"], 4),
    "Untreue": (None, 6),
    # vierte Runde (Befunde 028–035)
    "Cum-Ex-Geschäfte": ([r"\bCum[- ]?Ex\b", r"\bKapitalertrag(s)?steuer\w*", r"\bAktienkreisgeschäft\w*", r"\bDividendenstichtag\w*"], 6),
    "Fall Daniel Starr": ([r"\bDaniel Starrs?\b", r"\b(?-i:Starrs?)\b(?=.{0,120}(Daniel|Unternehmer|Flughafen|Haftbefehl|Auslieferung))"], 4),
    "Fall Edward Snowden": ([r"\bSnowdens?\b", r"\bSchutzengel\b", r"\bTibbo\b"], 4),
    "Fraunhofer-Spesenaffäre": ([r"\bFraunhofer[- ]Spesen\w*", r"\bNeugebauer\b", r"\bSpesenaffäre\b", r"\bSpesenskandal\b", r"\bFraunhofer\b(?=.{0,120}(Spesen|Reisen|Dienstwagen|Rechnungshof|Neugebauer))"], 4),
    "Knorr-Bremse": (None, 4),
    "Windkraft-Projektentwicklung": ([r"\bWindpark\w*", r"\bWindkraft\w*", r"\bWindenergie\w*", r"\bProjektrecht\w*"], 6),
    "Falschaussage": ([r"\bFalschaussage\w*", r"\buneidlich\w*", r"\bMeineid\w*", r"\bwider besseres Wissen\b"], 3),
    "Insolvenzverschleppung": ([r"\bInsolvenzverschleppung\w*", r"\bVerschleppung von Insolvenz\w*", r"\bInsolvenzantragspflicht\w*", r"\bInsolvenz\w* verschleppt\w*"], 3),
    # dritte Runde (Befunde 106–110)
    "Immobilienkrise": ([r"\bImmobilienkrise\b", r"\bBaukrise\b", r"\bZinswende\b", r"\bImmobilienpleite\w*", r"\bKrise am Immobilienmarkt\b"], 4),
    "Tesla-Betriebsratswahl Grünheide": ([r"\bBetriebsratswahl\w*", r"\bMichaela Schmitz\b", r"\bKool Savas\b", r"\bWahlvorstand\b"], 3),
    "Betriebsrat und Mitbestimmung": ([r"\bBetriebsr[aä]t\w*", r"\bBetriebsratswahl\w*", r"\bMitbestimmung\w*", r"\bWahlanfechtung\w*"], 6),
}


def main() -> None:
    seen = set()
    for f in sorted((ROOT / "data" / "topics").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for t in d:
            if t["name"] in FIX:
                pats, mn = FIX[t["name"]]
                if pats:
                    t["patterns"] = pats
                if mn:
                    t["min"] = mn
                seen.add(t["name"])
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    missing = set(FIX) - seen
    print(f"{len(seen)} Einträge angepasst" + (f", nicht gefunden: {sorted(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
