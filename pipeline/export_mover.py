"""blender -b --python pipeline/export_mover.py -- <clip>[,<clip>...]
TEST VARIANT "Rockstar split" (vbm_<clip>): hip motion is divided the way GTA's own jump clips carry it
(anim@arena@celeb@flat@solo@no_props@ jump_a/b/c/d, analysed with the converter):
  - SKEL_ROOT position keeps x/y and everything at or BELOW standing height (crouch, landing dip): legs bend;
  - the part ABOVE standing height goes to the MOVER (track 5, base z = 1.0 like every standalone GTA clip): the
    whole ped entity rises, the hip never goes above standing height in the bone track;
  - mover rotation identity (track 6), clip flag RootMotion (16).
Uses the newest exported version of each clip and its ped. Writes output/export/vbm_<clip>/v1 + output/vbm_<clip>/mover.json."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from mathutils import Vector
from lib import ped as pedlib, clips as cliplib, export_ycd as ex

BASE_Z = 1.0
cfg = json.loads((ROOT / "config.json").read_text())
names = sys.argv[sys.argv.index("--") + 1:][0].split(",")
bpy.context.scene.render.fps = 30
dll = ROOT / "cache" / "converter" / "ycd2xml.dll"
P = 'pose.bones["SKEL_ROOT"].location'

arm, loaded = None, None
for name in names:
    meta = json.loads((ROOT / "output" / name / "meta.json").read_text("utf-8"))
    version = max(int(p.name[1:]) for p in (ROOT / "output" / "export" / name).iterdir() if (p / f"{name}.ycd").exists())
    v = next(v for v in meta["versions"] if v["v"] == version)
    ped = v.get("ped") or "mp_m_freemode_01"
    if loaded is None:
        pedlib.import_ped_parts(cfg["game_dir"], ped)
        pedlib.clean_scene_extras()
        arm, loaded = pedlib.merge_armatures(), ped
    elif ped != loaded:
        print("MOVER atlandi (farkli ped):", name, ped)
        continue
    data = json.loads((ROOT / "output" / name / f"v{version}.action.json").read_text("utf-8"))
    vname = "vbm_" + name.removeprefix("vb_")
    clip = cliplib.LoadedClip(arm, vname, data["frames"], data["fps"], data["curves"])
    rest = arm.data.bones["SKEL_ROOT"].matrix_local.to_3x3()
    src = clip.action
    n = data["frames"] + 1

    def loc(f):
        c = [src.fcurves.find(P, index=i) for i in range(3)]
        return rest @ Vector([x.evaluate(f) if x else 0.0 for x in c])

    offs = [loc(f) for f in range(n)]  # character space: x right, y forward, z up
    action = ex.complete_action(arm, clip)
    for fc in list(action.fcurves):
        if fc.data_path == P:
            action.fcurves.remove(fc)
    bone = [rest.inverted() @ Vector((o.x, o.y, min(o.z, 0.0))) for o in offs]
    for i in range(3):  # bone track: crouch only
        fc = action.fcurves.new(P, index=i, action_group="SKEL_ROOT")
        fc.keyframe_points.add(n)
        for f in range(n):
            fc.keyframe_points[f].co = (f, bone[f][i])
            fc.keyframe_points[f].interpolation = "LINEAR"
        fc.update()
    for i in range(3):  # mover: lift only
        fc = action.fcurves.new("delta_location", index=i)
        fc.keyframe_points.add(n)
        for f in range(n):
            fc.keyframe_points[f].co = (f, BASE_Z + max(offs[f].z, 0.0) if i == 2 else 0.0)
            fc.keyframe_points[f].interpolation = "LINEAR"
        fc.update()
    for i, val in enumerate((1, 0, 0, 0)):
        fc = action.fcurves.new("delta_rotation_quaternion", index=i)
        fc.keyframe_points.add(2)
        fc.keyframe_points[0].co = (0, val)
        fc.keyframe_points[1].co = (data["frames"], val)
        fc.update()

    dict_obj = ex.build_dict_objects(arm, clip, action)
    out = ROOT / "output" / "export" / vname / "v1"
    xml, ycd = ex.export_xml_and_binary(dict_obj, out, vname, dll)
    s = xml.read_text(encoding="utf-8")
    lift = max(o.z for o in offs)
    print("MOVER", vname, "from", name, f"v{version}", "lift", round(max(lift, 0), 3), "crouch", round(min(o.z for o in offs), 3),
          "track5", s.count('<Track value="5" />'), "track6", s.count('<Track value="6" />'), "flag", s.split("<Unknown10 value=")[1][:4])
    (ROOT / "output" / vname).mkdir(exist_ok=True)
    (ROOT / "output" / vname / "mover.json").write_text(json.dumps(
        {"loop": v.get("loop", False), "duration": v["duration"], "source": f"{name} v{version}", "lift": round(lift, 3)}), "utf-8")
