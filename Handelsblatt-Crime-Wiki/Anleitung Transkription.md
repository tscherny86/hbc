# Anleitung: weitere Folgen transkribieren

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

← [[Handelsblatt Crime Wiki|Start]]
