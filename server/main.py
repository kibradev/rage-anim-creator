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


@app.get("/api/mine")
def mine():
    """Clips authored with pipeline/make_clip.py, latest version first-class; all versions listed."""
    out = []
    for meta_path in sorted(OUTPUT.glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        for v in meta["versions"]:
            out.append({
                "dict": "output", "name": meta["name"], "duration": v["duration"], "fps": v["fps"],
                "version": v["v"], "label": v.get("label", ""), "latest": v["v"] == len(meta["versions"]),
                "url": f"/files/output/{meta['name']}/{v['file']}",
            })
    return out


app.mount("/files/cache", StaticFiles(directory=CACHE), name="cache")
app.mount("/files/output", StaticFiles(directory=OUTPUT), name="output")
