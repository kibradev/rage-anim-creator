"""blender -b --python pipeline/extract_ped.py -- <ped> [out_dir]
Imports a streamed ped from the game RPFs via Sollumz and reports what ended up in the scene."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from lib import ped as pedlib

cfg = json.loads((ROOT / "config.json").read_text())
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ped = args[0] if args else "player_zero"

ytds, ydds, res = pedlib.import_ped_parts(cfg["game_dir"], ped)
print("PED import", res, "ytd", ytds, "ydd", ydds)
for o in bpy.data.objects:
    print("PED obj", o.type, o.name, "parent=", o.parent.name if o.parent else None,
          "verts=", len(o.data.vertices) if o.type == "MESH" else "-")
print("PED images", [i.name for i in bpy.data.images][:20])

pedlib.clean_scene_extras()
master = pedlib.merge_armatures()
print("PED master", master.name, "bones", len(master.data.bones), [b.name for b in master.data.bones][:6])
print("PED mats", pedlib.simplify_materials())
for o in bpy.data.objects:
    if o.type == "MESH":
        print("PED mesh", o.name, "mods", [m.type for m in o.modifiers], "vg", len(o.vertex_groups), "mats", [s.material.name for s in o.material_slots if s.material])
out = ROOT / "cache" / "peds" / ped / "ped.glb"
pedlib.export_glb(str(out))
print("PED exported", out, out.stat().st_size)
