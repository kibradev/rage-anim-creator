"""SCRIPT-DRIVEN ROOT variant. blender -b --python pipeline/export_script.py -- <ped> <clip> <version> [mover_base_z]
TEST VARIANT: hip motion (SKEL_ROOT.location) is REMOVED from the clip and written to output/vbs_<clip>/hip.json
(character space metres per frame: x right, y forward, z up). client.lua moves the ped entity with it, in sync with the
animation phase (game does not apply bone/mover hip travel the way we need). Dict/clip name vbs_<clip>."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from lib import ped as pedlib, clips as cliplib, export_ycd as ex

cfg = json.loads((ROOT / "config.json").read_text())
args = sys.argv[sys.argv.index("--") + 1:]
ped, name, version = args[0], args[1], int(args[2])
base_z = float(args[3]) if len(args) > 3 else 1.002
bpy.context.scene.render.fps = 30
pedlib.import_ped_parts(cfg["game_dir"], ped)
pedlib.clean_scene_extras()
arm = pedlib.merge_armatures()
data = json.loads((ROOT / "output" / name / f"v{version}.action.json").read_text("utf-8"))
vname = "vbs_" + name.removeprefix("vb_")
clip = cliplib.LoadedClip(arm, vname, data["frames"], data["fps"], data["curves"])
rest = arm.data.bones["SKEL_ROOT"].matrix_local.to_3x3()
src = clip.action

def loc(f):
    from mathutils import Vector
    v = [src.fcurves.find('pose.bones["SKEL_ROOT"].location', index=i) for i in range(3)]
    return rest @ Vector([c.evaluate(f) if c else 0.0 for c in v])

action = ex.complete_action(arm, clip)
for fc in list(action.fcurves):  # hip motion leaves the bone track ...
    if fc.data_path == 'pose.bones["SKEL_ROOT"].location':
        action.fcurves.remove(fc)
offs = [loc(f) for f in range(data["frames"] + 1)]  # ... and goes to the mover
print("SCRIPT hip range z", round(min(o[2] for o in offs), 3), round(max(o[2] for o in offs), 3), "x", round(min(o[0] for o in offs), 3), round(max(o[0] for o in offs), 3))

dict_obj = ex.build_dict_objects(arm, clip, action)
dll = ROOT / "cache" / "converter" / "ycd2xml.dll"
out = ROOT / "output" / "export" / vname / "v1"
xml, ycd = ex.export_xml_and_binary(dict_obj, out, vname, dll)
print("SCRIPT", ycd, ycd.stat().st_size)
(ROOT / "output" / vname).mkdir(exist_ok=True)
meta = json.loads((ROOT / "output" / name / "meta.json").read_text("utf-8"))
v = next(v for v in meta["versions"] if v["v"] == version)
hip = {"loop": v.get("loop", False), "duration": v["duration"], "source": f"{name} v{version}", "n": len(offs),
       "x": [round(o[0], 4) for o in offs], "y": [round(o[1], 4) for o in offs], "z": [round(o[2], 4) for o in offs]}
(ROOT / "output" / vname / "hip.json").write_text(json.dumps(hip), "utf-8")
