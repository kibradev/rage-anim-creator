"""blender -b --python pipeline/render_frames.py -- <ped> mine <clip> <version> [n_frames|f1,f2,...] [views]
   blender -b --python pipeline/render_frames.py -- <ped> gta <dict> <clip_name> [n_frames|f1,f2,...] [views]
Writes a contact sheet PNG (rows = views, columns = frames) to cache/preview/ and prints its path (RENDER ...)."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from lib import ped as pedlib, clips as cliplib, anims as animlib, render

cfg = json.loads((ROOT / "config.json").read_text())
a = sys.argv[sys.argv.index("--") + 1:]
ped, kind = a[0], a[1]
bpy.context.scene.render.fps = 30
pedlib.import_ped_parts(cfg["game_dir"], ped)
pedlib.clean_scene_extras()
arm = pedlib.merge_armatures()
pedlib.simplify_materials()

if kind == "mine":
    name, version = a[2], int(a[3])
    data = json.loads((ROOT / "output" / name / f"v{version}.action.json").read_text("utf-8"))
    action, f0, f1 = cliplib.LoadedClip(arm, name, data["frames"], data["fps"], data["curves"]).action, 0, data["frames"]
    tag = f"{name}_v{version}"
else:
    dname, cname = a[2], a[3]
    d, anims, clips = animlib.import_dict(str(ROOT / "cache" / "ycdxml" / f"{dname}.ycd.xml"))
    animlib.retarget_to(arm, anims)
    c = next(c for c in clips if cname in (c.clip_properties.name or c.name))
    action, f0, f1 = animlib.merged_action(c)
    tag = f"gta_{cname}"
spec = a[4] if len(a) > 4 else "8"
frames = [float(x) for x in spec.split(",")] if "," in spec else [f0 + (f1 - f0) * i / (int(spec) - 1) for i in range(int(spec))]
frames = [round(f) for f in frames]
views = a[5].split(",") if len(a) > 5 else ["front", "side"]
out = render.render_sheet(arm, action, frames, ROOT / "cache" / "preview" / f"{tag}.png", views)
print("RENDER", out, "frames", frames, "views", views)
