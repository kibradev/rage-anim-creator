"""blender -b --python pipeline/export_mover.py -- <ped> <clip> <version> [mover_base_z]
TEST VARIANT: same clip, but the hip motion (SKEL_ROOT.location) is written to the MOVER tracks (delta_location, track 5; plus an
identity mover rotation, track 6) instead, the way real GTA clips carry it (their mover z is an absolute ~1.0 hip height).
Writes output/export/vbx_<clip>/v1/vbx_<clip>.ycd (dict/clip name vbx_<clip>). Used to find out why hip jumps/crouches do not show in game."""
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
vname = "vbx_" + name.removeprefix("vb_")
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
for i in range(3):
    fc = action.fcurves.new("delta_location", index=i)
    fc.keyframe_points.add(len(offs))
    for f, o in enumerate(offs):
        fc.keyframe_points[f].co = (f, o[i] + (base_z if i == 2 else 0.0))
        fc.keyframe_points[f].interpolation = "LINEAR"
    fc.update()
for i, v in enumerate((1, 0, 0, 0)):
    fc = action.fcurves.new("delta_rotation_quaternion", index=i)
    fc.keyframe_points.add(2)
    fc.keyframe_points[0].co = (0, v); fc.keyframe_points[1].co = (data["frames"], v)
    fc.update()
print("MOVER hip range z", round(min(o[2] for o in offs), 3), round(max(o[2] for o in offs), 3), "x", round(min(o[0] for o in offs), 3), round(max(o[0] for o in offs), 3))

dict_obj = ex.build_dict_objects(arm, clip, action)
dll = ROOT / "cache" / "converter" / "ycd2xml.dll"
out = ROOT / "output" / "export" / vname / "v1"
xml, ycd = ex.export_xml_and_binary(dict_obj, out, vname, dll)
s = xml.read_text(encoding="utf-8")
print("MOVER xml track5", s.count('<Track value="5" />'), "track6", s.count('<Track value="6" />'), "flag", s.split("<Unknown10 value=")[1][:4], ycd, ycd.stat().st_size)
(ROOT / "output" / vname).mkdir(exist_ok=True)
meta = json.loads((ROOT / "output" / name / "meta.json").read_text("utf-8"))
v = next(v for v in meta["versions"] if v["v"] == version)
(ROOT / "output" / vname / "mover.json").write_text(json.dumps({"loop": v.get("loop", False), "duration": v["duration"], "source": f"{name} v{version}"}), "utf-8")
