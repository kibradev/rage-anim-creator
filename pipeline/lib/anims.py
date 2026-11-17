"""Clip dictionary import, retarget to a ped armature and glTF export (run inside Blender with Sollumz).

Parametric functions: import_dict(), bake_clips_to_nla(), export_armature_glb().
"""
import importlib
import json
import os
import bpy

PKG = "bl_ext.user_default.sollumz"


def _mod(name):
    return importlib.import_module(f"{PKG}.{name}")


def import_dict(xml_path: str):
    """Import a .ycd.xml and return (dict_obj, [animation_objs], [clip_objs])."""
    from_ycd = _mod("ycd.ycdimport")
    dict_obj = from_ycd.import_ycd(xml_path)
    anims, clips = [], []
    stack = [dict_obj]
    while stack:
        o = stack.pop()
        stack.extend(o.children)
        st = getattr(o, "sollum_type", "")
        if st == "sollumz_animation":
            anims.append(o)
        elif st == "sollumz_clip":
            clips.append(o)
    return dict_obj, anims, clips


def retarget_to(armature_obj, anims):
    helper = _mod("tools.animationhelper")
    for a in anims:
        helper.retarget_animation(a, None, armature_obj.data)


def merged_action(clip_obj):
    """Return (action, start_frame, end_frame) for a clip. Multi-animation clips (parallel layers) are merged
    into one action, keeping skeleton/mover curves only and the first curve for any duplicate path."""
    cp = clip_obj.clip_properties
    if len(cp.animations) == 1:
        ca = cp.animations[0]
        return ca.animation.animation_properties.action, ca.start_frame, ca.end_frame
    new = bpy.data.actions.new(f"{cp.name or clip_obj.name}_merged")
    seen = set()
    first = cp.animations[0]
    for ca in cp.animations:
        src = ca.animation.animation_properties.action
        if src is None:
            continue
        for fc in src.fcurves:
            if not (fc.data_path.startswith("pose.bones[") or fc.data_path.startswith("delta_")):
                continue
            key = (fc.data_path, fc.array_index)
            if key in seen:
                continue
            seen.add(key)
            nf = new.fcurves.new(fc.data_path, index=fc.array_index, action_group=fc.group.name if fc.group else "")
            nf.keyframe_points.add(len(fc.keyframe_points))
            for i, kp in enumerate(fc.keyframe_points):
                nf.keyframe_points[i].co = kp.co
                nf.keyframe_points[i].interpolation = kp.interpolation
            nf.update()
    return new, first.start_frame, first.end_frame


def bake_clips_to_nla(armature_obj, clips):
    """One NLA track per single-animation clip; returns metadata list."""
    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    if armature_obj.animation_data is None:
        armature_obj.animation_data_create()
    ad = armature_obj.animation_data
    ad.action = None
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    meta, skipped = [], 0
    for c in clips:
        cp = c.clip_properties
        if len(cp.animations) == 0:
            skipped += 1
            continue
        action, a_start, a_end = merged_action(c)
        if action is None or len(action.fcurves) == 0:
            skipped += 1
            continue
        name = cp.name or c.name
        track = ad.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 1, action)
        strip.action_frame_start = a_start
        strip.action_frame_end = max(a_end, a_start + 1)
        strip.use_sync_length = False
        meta.append({"name": name, "duration": float(cp.duration), "fps": fps,
                     "frames": float(strip.action_frame_end - strip.action_frame_start)})
    return meta, skipped


def export_armature_glb(armature_obj, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True,
        export_animations=True, export_animation_mode="NLA_TRACKS",
        export_yup=True, export_skins=True, export_image_format="NONE",
    )


def clear_dict(dict_obj, anims):
    for a in anims:
        act = a.animation_properties.action
        if act:
            bpy.data.actions.remove(act)
    stack = [dict_obj]
    objs = []
    while stack:
        o = stack.pop()
        objs.append(o)
        stack.extend(o.children)
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
