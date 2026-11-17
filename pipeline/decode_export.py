"""blender -b --python pipeline/decode_export.py -- <clip_prefix_or_name>[,<name>...]
For every exported clip (output/export/<clip>/v<N>/<clip>.ycd): decode the BINARY .ycd back (what the game loads),
retarget it onto the ped, bake it to output/export/<clip>/v<N>/game.glb (shown as "Oyun (export)" in the web UI) and
write game.json: frame-by-frame difference between the authored action and the decoded one (rotation deg, root m).
Uses the ped recorded in meta.json (default mp_m_freemode_01)."""
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from mathutils import Quaternion, Vector
from lib import ped as pedlib, clips as cliplib, anims as animlib

cfg = json.loads((ROOT / "config.json").read_text())
sel = sys.argv[sys.argv.index("--") + 1:][0].split(",")
bpy.context.scene.render.fps = 30
dll = ROOT / "cache" / "converter" / "ycd2xml.dll"

todo = []  # (ped, name, version)
for meta_path in sorted((ROOT / "output").glob("*/meta.json")):
    meta = json.loads(meta_path.read_text("utf-8"))
    for v in meta["versions"]:
        ycd = ROOT / "output" / "export" / meta["name"] / f"v{v['v']}" / f"{meta['name']}.ycd"
        if ycd.exists() and any(meta["name"].startswith(s) for s in sel):
            todo.append((v.get("ped") or "player_zero", meta["name"], v["v"], v))
print("DECODE", len(todo), "clips")

loaded = None
arm = None
for ped, name, ver, v in todo:
    if loaded is not None and loaded != ped:
        print("DECODE atlandi (farkli ped, ayri calistir):", name, ped)
        continue
    if loaded is None:
        pedlib.import_ped_parts(cfg["game_dir"], ped)
        pedlib.clean_scene_extras()
        arm = pedlib.merge_armatures()
        loaded = ped
    out = ROOT / "output" / "export" / name / f"v{ver}"
    data = json.loads((ROOT / "output" / name / f"v{ver}.action.json").read_text("utf-8"))
    ref = cliplib.LoadedClip(arm, name, data["frames"], data["fps"], data["curves"]).action

    tmp = ROOT / "cache" / "rt" / f"decode_{name}.ycd.xml"
    subprocess.run(["dotnet", str(dll), "ycd2xmlfile", str(out / f"{name}.ycd"), str(tmp)], check=True)
    d, anims, clips = animlib.import_dict(str(tmp))
    animlib.retarget_to(arm, anims)
    act, s, e = animlib.merged_action(clips[0])

    # difference authored vs decoded (what the game receives)
    rot, loc = {}, {}
    worst_rot, worst_loc = (0.0, "", 0), (0.0, "", 0)
    paths = sorted({fc.data_path for fc in ref.fcurves})

    def val(a, p, n, f, dflt):
        out_ = []
        for i in range(n):
            fc = a.fcurves.find(p, index=i)
            out_.append(fc.evaluate(f) if fc else dflt[i])
        return out_

    for p in paths:
        b = p.split('"')[1]
        for f in range(0, data["frames"] + 1):
            if p.endswith("rotation_quaternion"):
                q1 = Quaternion(val(ref, p, 4, f, (1, 0, 0, 0))).normalized()
                q2 = Quaternion(val(act, p, 4, f, (1, 0, 0, 0))).normalized()
                ang = math.degrees(2 * math.acos(min(1.0, abs(q1.dot(q2)))))
                if ang > rot.get(b, 0):
                    rot[b] = round(ang, 3)
                if ang > worst_rot[0]:
                    worst_rot = (round(ang, 3), b, f)
            elif p.endswith("location"):
                dist = (Vector(val(ref, p, 3, f, (0, 0, 0))) - Vector(val(act, p, 3, f, (0, 0, 0)))).length
                if dist > loc.get(b, 0):
                    loc[b] = round(dist, 5)
                if dist > worst_loc[0]:
                    worst_loc = (round(dist, 5), b, f)
    missing = [p for p in paths if act.fcurves.find(p, index=0) is None]

    # bake the decoded action to GLB
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    tr = ad.nla_tracks.new()
    tr.name = name
    st = tr.strips.new(name, 0, act)
    st.action_frame_start, st.action_frame_end = s, max(e, s + 1)
    st.use_sync_length = False
    animlib.export_armature_glb(arm, str(out / "game.glb"))
    ad.action = None

    info = {"frames_authored": data["frames"], "frames_game": round(e - s), "max_rot_deg": worst_rot, "max_root_m": worst_loc,
            "bone_rot_deg": rot, "bone_loc_m": loc, "missing_in_game": missing,
            "game_bones": sorted({fc.data_path.split('"')[1] for fc in act.fcurves if fc.data_path.startswith("pose.bones")})}
    (out / "game.json").write_text(json.dumps(info, indent=1), "utf-8")
    print("DECODE", name, "v", ver, "rot", worst_rot, "root", worst_loc, "missing", len(missing), "frames", data["frames"], round(e - s))
    animlib.clear_dict(d, anims)
