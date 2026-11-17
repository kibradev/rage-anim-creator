"""FastAPI: serves generated GLB files from cache/ and output/, lists peds/clips."""
import json
import subprocess
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
OUTPUT = ROOT / "output"
for d in (CACHE, OUTPUT):
    d.mkdir(exist_ok=True)

app = FastAPI(title="animCreator")
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
JOBS: dict[str, dict] = {}
JOB_LOCK = threading.Lock()  # Blender + ped import is ~2 GB; one job at a time


def _meta_path(name: str) -> Path:
    if "/" in name or "\\" in name or name.startswith("."):
        raise HTTPException(400, "bad name")
    return OUTPUT / name / "meta.json"


class StatusBody(BaseModel):
    status: str


class ExportBody(BaseModel):
    name: str
    version: int


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
                "status": v.get("status", "pending"),
                "report": {
                    "frames": v["frames"], "duration": v["duration"], "fps": v["fps"], "loop": v.get("loop", False),
                    "bones": len(v.get("bones", [])), **v.get("report", {}),
                },
                "exportUrl": (
                    f"/files/output/export/{meta['name']}/v{v['v']}/{meta['name']}.ycd"
                    if (OUTPUT / "export" / meta["name"] / f"v{v['v']}" / f"{meta['name']}.ycd").exists() else None
                ),
            })
    return out


@app.post("/api/mine/{name}/{version}/status")
def set_status(name: str, version: int, body: StatusBody):
    if body.status not in {"pending", "approved", "rejected"}:
        raise HTTPException(400, "bad status")
    path = _meta_path(name)
    if not path.exists():
        raise HTTPException(404, "clip not found")
    meta = json.loads(path.read_text(encoding="utf-8"))
    for v in meta["versions"]:
        if v["v"] == version:
            v["status"] = body.status
            path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
            return {"ok": True}
    raise HTTPException(404, "version not found")


@app.post("/api/export")
def start_export(body: ExportBody):
    """Approval gate: only an approved version can be exported to .ycd."""
    path = _meta_path(body.name)
    if not path.exists():
        raise HTTPException(404, "clip not found")
    meta = json.loads(path.read_text(encoding="utf-8"))
    ver = next((v for v in meta["versions"] if v["v"] == body.version), None)
    if ver is None:
        raise HTTPException(404, "version not found")
    if ver.get("status") != "approved":
        raise HTTPException(409, "version is not approved")
    if any(j["state"] == "running" for j in JOBS.values()):
        raise HTTPException(409, "another job is running")
    job_id = f"export-{body.name}-v{body.version}-{int(time.time())}"
    JOBS[job_id] = {"id": job_id, "state": "running", "log": [], "title": f"{body.name} v{body.version} → .ycd"}

    def run():
        with JOB_LOCK:
            cmd = [CFG["blender"], "-b", "--python", str(ROOT / "pipeline" / "export_ycd.py"), "--",
                   "player_zero", body.name, str(body.version)]
            proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout:
                if line.startswith("EXPORT"):
                    JOBS[job_id]["log"].append(line.strip())
            JOBS[job_id]["state"] = "done" if proc.wait() == 0 and JOBS[job_id]["log"] else "failed"

    threading.Thread(target=run, daemon=True).start()
    return {"id": job_id}


@app.get("/api/jobs")
def jobs():
    return list(JOBS.values())


app.mount("/files/cache", StaticFiles(directory=CACHE), name="cache")
app.mount("/files/output", StaticFiles(directory=OUTPUT), name="output")
