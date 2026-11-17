"""Export an authored Clip as a GTA V clip dictionary (.ycd.xml via Sollumz, binary .ycd via converter) and verify it.

Sollumz exports XML; the converter (CodeWalker.Core) turns it into the binary resource. verify_roundtrip() re-imports
the written binary and compares bone rotations frame by frame with the authored action.
"""
import importlib
import math
import subprocess
from pathlib import Path

import bpy
from mathutils import Quaternion

PKG = "bl_ext.user_default.sollumz"


def _m(name):
    return importlib.import_module(f"{PKG}.{name}")


def complete_action(arm, clip):
    """Copy of the clip's action where every pose bone has rotation keys (rest = identity), like game clips."""
    src = clip.action
    new = bpy.data.actions.new(clip.name + "_export")
    keyed = set()
    for fc in src.fcurves:
        nf = new.fcurves.new(fc.data_path, index=fc.array_index, action_group=fc.group.name if fc.group else "")
        nf.keyframe_points.add(len(fc.keyframe_points))
        for i, kp in enumerate(fc.keyframe_points):
            nf.keyframe_points[i].co = kp.co
            nf.keyframe_points[i].interpolation = kp.interpolation
            nf.keyframe_points[i].handle_left = kp.handle_left
            nf.keyframe_points[i].handle_right = kp.handle_right
        nf.update()
        if fc.data_path.endswith("rotation_quaternion"):
            keyed.add(fc.data_path.split('"')[1])
    ident = (1, 0, 0, 0)
    for pb in arm.pose.bones:
        if pb.name in keyed:
            continue
        for i in range(4):
            nf = new.fcurves.new(f'pose.bones["{pb.name}"].rotation_quaternion', index=i, action_group=pb.name)
            nf.keyframe_points.add(2)
            nf.keyframe_points[0].co = (0, ident[i])
            nf.keyframe_points[1].co = (clip.frames, ident[i])
            nf.update()
    new.frame_range = (0, clip.frames)
    return new


def build_dict_objects(arm, clip, action):
    ycdi = _m("ycd.ycdimport")
    dict_obj, clips_obj, anims_obj = ycdi.create_clip_dictionary_template(clip.name)
    anim_obj = ycdi.create_anim_obj(_m("sollumz_properties").SollumType.ANIMATION)
    anim_obj.name = clip.name
    anim_obj.parent = anims_obj
    ap = anim_obj.animation_properties
    ap.hash = clip.name
    ap.target_id_type = "ARMATURE"
    ap.target_id = arm.data  # set before the action so Sollumz does not try to retarget
    ap.action = action

    clip_obj = ycdi.create_anim_obj(_m("sollumz_properties").SollumType.CLIP)
    clip_obj.name = clip.name + "_clip"
    clip_obj.parent = clips_obj
    cp = clip_obj.clip_properties
    cp.hash = clip.name + "_clip"
    cp.name = f"{clip.name}.clip"
    cp.duration = clip.frames / clip.fps
    ca = cp.animations.add()
    ca.animation = anim_obj
    ca.start_frame = 0
    ca.end_frame = clip.frames
    return dict_obj


def export_xml_and_binary(dict_obj, out_dir: Path, name: str, converter_dll: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    xml = out_dir / f"{name}.ycd.xml"
    ycd = out_dir / f"{name}.ycd"
    if not _m("ycd.ycdexport").export_ycd(dict_obj, str(xml)):
        raise RuntimeError("Sollumz YCD export failed")
    subprocess.run(["dotnet", str(converter_dll), "xml2ycd", str(xml), str(ycd)], check=True)
    return xml, ycd


def verify_roundtrip(arm, clip, ycd: Path, converter_dll: Path, tmp_xml: Path, bones, sample_frames=None):
    """Binary -> XML -> Sollumz import -> retarget -> compare rotations with the authored action."""
    from . import anims as animlib

    subprocess.run(["dotnet", str(converter_dll), "ycd2xmlfile", str(ycd), str(tmp_xml)], check=True)
    d, anims, clips = animlib.import_dict(str(tmp_xml))
    animlib.retarget_to(arm, anims)
    act = clips[0].clip_properties.animations[0].animation.animation_properties.action
    frames = sample_frames or sorted({0, clip.frames // 4, clip.frames // 2, (3 * clip.frames) // 4, clip.frames})
    worst = 0.0
    detail = {}
    for b in bones:
        path = f'pose.bones["{b}"].rotation_quaternion'
        for f in frames:
            q_ref = Quaternion([clip.action.fcurves.find(path, index=i).evaluate(f) for i in range(4)]).normalized()
            q_new = Quaternion([act.fcurves.find(path, index=i).evaluate(f) for i in range(4)]).normalized()
            ang = math.degrees(2 * math.acos(min(1.0, abs(q_ref.dot(q_new)))))
            worst = max(worst, ang)
            if ang > detail.get(b, (0, 0))[0]:
                detail[b] = (round(ang, 3), f)
    print('EXPORT per-bone worst (deg, frame):', detail)
    return worst, len(anims), len(clips)
