"""FastAPI: serves generated GLB files from cache/ and output/, lists peds/clips."""
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
OUTPUT = ROOT / "output"
for d in (CACHE, OUTPUT):
    d.mkdir(exist_ok=True)

app = FastAPI(title="animCreator")


@app.get("/api/peds")
def peds():
    base = CACHE / "peds"
    if not base.exists():
        return []
    return [{"name": p.name, "url": f"/files/cache/peds/{p.name}/ped.glb"} for p in sorted(base.iterdir()) if (p / "ped.glb").exists()]


@app.get("/api/clips")
def clips():
    idx = CACHE / "anims" / "index.json"
    return json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []


app.mount("/files/cache", StaticFiles(directory=CACHE), name="cache")
app.mount("/files/output", StaticFiles(directory=OUTPUT), name="output")
