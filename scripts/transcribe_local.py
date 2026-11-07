#!/usr/bin/env python3
"""Transkribiert Handelsblatt-Crime-Folgen kostenlos auf dem eigenen PC (faster-whisper).

Einmalig installieren:
    pip install faster-whisper
    (NVIDIA-GPU: pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 – das Skript findet die DLLs selbst)
    ffmpeg muss im PATH liegen.

Aufruf (im Repo-Ordner):
    python scripts/transcribe_local.py                 # alle Folgen ohne Transkript, neueste zuerst
    python scripts/transcribe_local.py 162 161         # nur diese Folgen (Folgennummer, auch ohne führende Nullen)
    python scripts/transcribe_local.py --model small   # schneller, ungenauer (Standard: large-v3-turbo)
    python scripts/transcribe_local.py --cpu           # CPU erzwingen
    python scripts/transcribe_local.py --push          # nach jeder Folge Wiki bauen, committen, pushen

Danach:  python scripts/build_wiki.py   -> Wiki wird mit Minuten-Links neu gebaut.

Auf einer RTX 3070 läuft das Standardmodell mit etwa 15× Echtzeit; auf einer CPU rechnet man mit `small` grob in
Echtzeit. Der Zwischenstand wird alle 15 Segmente gesichert (data/transcripts/partial/), ein abgebrochener Lauf
macht dort weiter, wo er aufgehört hat. Fortschritt steht in data/transcripts/progress.log.
"""
import argparse
import glob
import json
import os
import site
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):  # Windows-Konsole: ▶ ✓ ↻ erlauben
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_wiki import DATA, load_episodes  # noqa: E402

UA = "Mozilla/5.0 (handelsblatt-crime-fanwiki)"
LOG = DATA / "transcripts" / "progress.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def save_json(path: Path, data: dict) -> None:
    """Schreibt erst eine Temp-Datei und tauscht sie dann aus; bei kurzzeitigen Sperren (Virenscanner, Git)
    wird einige Male neu versucht, statt den ganzen Lauf abzubrechen."""
    tmp = path.with_suffix(".tmp")
    for attempt in range(6):
        try:
            tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, path)
            return
        except OSError as err:
            if attempt == 5:
                raise
            log(f"   ! Schreiben von {path.name} fehlgeschlagen ({err}), neuer Versuch")
            time.sleep(2 + attempt)


def add_cuda_dlls() -> None:
    """Macht die per pip installierten CUDA-Bibliotheken (cublas, cudnn) unter Windows sichtbar."""
    for s in site.getsitepackages() + [site.getusersitepackages()]:
        for d in glob.glob(os.path.join(s, "nvidia", "*", "bin")):
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="Folgennummern wie 162 (leer = alle fehlenden)")
    ap.add_argument("--model", default="large-v3-turbo", help="tiny | base | small | medium | large-v3 | large-v3-turbo")
    ap.add_argument("--cpu", action="store_true", help="CPU erzwingen")
    ap.add_argument("--push", action="store_true", help="nach jeder Folge Wiki neu bauen, committen und pushen")
    args = ap.parse_args()
    wanted = {f"{int(x):03d}" for x in args.ids}

    add_cuda_dlls()
    from faster_whisper import WhisperModel

    try:
        if args.cpu:
            raise RuntimeError("CPU gewünscht")
        model = WhisperModel(args.model, device="cuda", compute_type="float16")
        log(f"Modell {args.model} auf der GPU")
    except Exception as err:  # noqa: BLE001
        log(f"GPU nicht verfügbar ({err}); CPU")
        model = WhisperModel(args.model, device="cpu", compute_type="int8")
    out_dir = DATA / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    # neueste Folgen zuerst
    for ep in sorted(load_episodes(), key=lambda e: e["date"], reverse=True):
        target = out_dir / f"{ep['id']}.json"
        if wanted and ep["id"] not in wanted:
            continue
        if not wanted and target.exists():
            continue
        if not ep["audio"]:
            log(f"   ! {ep['id']} ohne Audio, übersprungen")
            continue
        log(f"▶ {ep['id']}  {ep['title']}  ({ep['duration'] // 60} min)")
        t0 = time.time()
        partial = out_dir / "partial" / f"{ep['id']}.json"
        partial.parent.mkdir(exist_ok=True)
        words = json.loads(partial.read_text(encoding="utf-8"))["words"] if partial.exists() else []
        offset = words[-1]["end"] if words else 0.0
        if offset:
            log(f"   ↻ fortsetzen ab {offset:.0f}s")
        with tempfile.TemporaryDirectory() as tmp:
            mp3 = Path(tmp) / "audio.mp3"
            req = urllib.request.Request(ep["audio"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r, open(mp3, "wb") as f:
                f.write(r.read())
            raw = subprocess.run(
                ["ffmpeg", "-loglevel", "error", "-ss", str(offset), "-i", str(mp3), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                capture_output=True, check=True,
            ).stdout
            audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
            segs, _ = model.transcribe(audio, language="de", word_timestamps=True, vad_filter=True)
            for n, seg in enumerate(segs):
                for w in seg.words or []:
                    words.append({"text": w.word.strip(), "type": "word",
                                  "start": round(w.start + offset, 2), "end": round(w.end + offset, 2)})
                print(f"   {seg.start + offset:7.0f}s  {seg.text[:70]}", flush=True)
                if n % 15 == 0:
                    save_json(partial, {"words": words})
        save_json(target, {"words": words})
        partial.unlink(missing_ok=True)
        log(f"   ✓ {len(words)} Wörter in {time.time() - t0:.0f}s -> {target.name}")
        if args.push:
            root = Path(__file__).resolve().parent.parent
            subprocess.run([sys.executable, str(root / "scripts" / "build_wiki.py")], check=True)
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", f"Transkript {ep['id']}: {ep['title']}\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"], check=False)
            for _ in range(4):
                if subprocess.run(["git", "-C", str(root), "push", "-q", "origin", "HEAD"]).returncode == 0:
                    break
    log("fertig: keine offenen Folgen mehr")


if __name__ == "__main__":
    main()
