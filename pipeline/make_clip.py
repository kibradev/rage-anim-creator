"""blender -b --python pipeline/make_clip.py -- <ped> <clip_module> [label]
Runs pipeline/clip_defs/<clip_module>.py: build(arm, Clip) -> Clip. Exports output/<clip>/vN.glb (+ meta.json)."""
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from lib import ped as pedlib, clips as cliplib

cfg = json.loads((ROOT / "config.json").read_text())
args = sys.argv[sys.argv.index("--") + 1:]
ped, module = args[0], args[1]
label = args[2] if len(args) > 2 else ""
bpy.context.scene.render.fps = 30

pedlib.import_ped_parts(cfg["game_dir"], ped)
pedlib.clean_scene_extras()
arm = pedlib.merge_armatures()

mod = importlib.import_module(f"clip_defs.{module}")
clip = mod.build(arm, cliplib)
clip.finish()
meta = cliplib.export_version(arm, clip, ROOT / "output", label)
print("CLIP done", clip.name, "v", meta["versions"][-1]["v"], "frames", clip.frames, "bones", len(meta["versions"][-1]["bones"]))
