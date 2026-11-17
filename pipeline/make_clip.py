"""blender -b --python pipeline/make_clip.py -- <ped> <clip_module>[:variant|:all] [label]
Runs pipeline/clip_defs/<clip_module>.py: build(arm, cliplib[, variant]) -> Clip. Exports output/<clip>/vN.glb (+ meta.json)
and a contact sheet cache/preview/<clip>_vN.png. Modules with several clips expose CLIPS = {variant: ...}."""
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from lib import ped as pedlib, clips as cliplib, render

cfg = json.loads((ROOT / "config.json").read_text())
args = sys.argv[sys.argv.index("--") + 1:]
ped, module = args[0], args[1]
label = args[2] if len(args) > 2 else ""
module, _, variant = module.partition(":")
bpy.context.scene.render.fps = 30

pedlib.import_ped_parts(cfg["game_dir"], ped)
pedlib.clean_scene_extras()
arm = pedlib.merge_armatures()
pedlib.simplify_materials()

mod = importlib.import_module(f"clip_defs.{module}")
variants = list(mod.CLIPS) if variant == "all" else [variant] if variant else [None]
for var in variants:
    clip = mod.build(arm, cliplib, var) if var else mod.build(arm, cliplib)
    clip.finish()
    meta = cliplib.export_version(arm, clip, ROOT / "output", label, f"{module}:{var}" if var else module, ped)
    ver = meta["versions"][-1]
    for w in ver["report"]["warnings"]:
        print("CLIP UYARI", clip.name, w)
    if getattr(clip, "ik_unreachable", 0) > 0.01:
        print("CLIP UYARI", clip.name, f"IK hedefine ulaşılamadı: {clip.ik_unreachable:.2f} m", getattr(clip, "ik_worst_at", ""))
    frames = sorted(set(getattr(clip, "key_frames", None) or [round(clip.frames * i / 7) for i in range(8)]))
    sheet = render.render_sheet(arm, clip.action, frames, ROOT / "cache" / "preview" / f"{clip.name}_v{ver['v']}.png", ("front", "side"))
    print("CLIP rapor", clip.name, json.dumps(ver["report"], ensure_ascii=False))
    print("CLIP done", clip.name, "v", ver["v"], "frames", clip.frames, "bones", len(ver["bones"]), "sheet", sheet, "kareler", frames)
