"""blender -b --python pipeline/rt_dance.py -- <ped> <dict> <clip_name>
Round-trip test: original GTA clip -> Blender -> our export path -> binary .ycd -> back, compared with the original.
Writes cache/rt/<clip>/{raw,completed}.ycd(.xml) and prints RT lines."""
import json, math, subprocess, sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from mathutils import Quaternion, Vector
from lib import ped as pedlib, anims as animlib, export_ycd as ex

cfg = json.loads((ROOT / "config.json").read_text())
ped, dname, cname = sys.argv[sys.argv.index("--") + 1:][:3]
bpy.context.scene.render.fps = 30
pedlib.import_ped_parts(cfg["game_dir"], ped)
pedlib.clean_scene_extras()
arm = pedlib.merge_armatures()
dll = ROOT / "cache" / "converter" / "ycd2xml.dll"
out = ROOT / "cache" / "rt" / cname


def load(xml):
    d, anims, clips = animlib.import_dict(str(xml))
    animlib.retarget_to(arm, anims)
    c = next(c for c in clips if cname in (c.clip_properties.name or c.name))
    act, s, e = animlib.merged_action(c)
    return act, s, e


def kinds(act):
    k = {}
    for fc in act.fcurves:
        key = fc.data_path.split(".")[-1] if fc.data_path.startswith("pose") else fc.data_path
        k.setdefault(key, set()).add(fc.data_path)
    return {a: len(b) for a, b in k.items()}


def sample(act, path, n, f, default):
    v = []
    for i in range(n):
        fc = act.fcurves.find(path, index=i)
        v.append(fc.evaluate(f) if fc else default[i])
    return v


def compare(ref, new, f0, f1, tag):
    paths = sorted({fc.data_path for fc in ref.fcurves})
    new_paths = {fc.data_path for fc in new.fcurves}
    missing = [p for p in paths if p not in new_paths]
    worst_rot, worst_loc = (0, "", 0), (0, "", 0)
    for p in paths:
        if p in missing:
            continue
        for f in range(int(f0), int(f1) + 1):
            if p.endswith("rotation_quaternion"):
                a = Quaternion(sample(ref, p, 4, f, (1, 0, 0, 0))).normalized()
                b = Quaternion(sample(new, p, 4, f, (1, 0, 0, 0))).normalized()
                ang = math.degrees(2 * math.acos(min(1.0, abs(a.dot(b)))))
                if ang > worst_rot[0]:
                    worst_rot = (round(ang, 3), p, f)
            elif p.endswith("location"):
                dist = (Vector(sample(ref, p, 3, f, (0, 0, 0))) - Vector(sample(new, p, 3, f, (0, 0, 0)))).length
                if dist > worst_loc[0]:
                    worst_loc = (round(dist, 5), p, f)
    print("RT", tag, "paths", len(paths), "missing_after_roundtrip", len(missing), missing[:8])
    print("RT", tag, "worst rotation deg", worst_rot, "worst location m", worst_loc)


ref, s, e = load(ROOT / "cache" / "ycdxml" / f"{dname}.ycd.xml")
print("RT original action", ref.name, "frames", s, e, "curve kinds", kinds(ref))
clip = SimpleNamespace(name=cname, frames=int(round(e - s)), fps=30, action=ref)

for tag, action in (("raw", ref), ("completed", ex.complete_action(arm, clip))):
    d = ex.build_dict_objects(arm, clip, action)
    xml, ycd = ex.export_xml_and_binary(d, out / tag, cname, dll)
    back = out / tag / "back.ycd.xml"
    subprocess.run(["dotnet", str(dll), "ycd2xmlfile", str(ycd), str(back)], check=True)
    new, s2, e2 = load(back)
    print("RT", tag, "size", ycd.stat().st_size, "frames", s2, e2, "curve kinds", kinds(new))
    compare(ref, new, s, e, tag)
