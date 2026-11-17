"""Parametric animation authoring for a ped armature (run inside Blender).

Axes are ARMATURE-SPACE axes of the REST pose ('x','y','z' or a Vector), so callers never need to know how
individual bones are rolled. Rotations are applied as local pose deltas, so they chain down the hierarchy.
"""
import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

AXES = {"x": Vector((1, 0, 0)), "y": Vector((0, 1, 0)), "z": Vector((0, 0, 1))}


class Clip:
    def __init__(self, armature, name: str, frames: int, fps: int = 30, loop: bool = False, game_facing: bool = True):
        self.arm = armature
        self.name = name
        self.frames = frames  # last frame index; clip spans frame 0..frames
        self.fps = fps
        self.loop = loop
        self.game_facing = game_facing  # GTA clips key SKEL_ROOT with a 180 deg yaw; match it so the ped faces forward
        self.action = bpy.data.actions.new(name)
        if armature.animation_data is None:
            armature.animation_data_create()
        armature.animation_data.action = self.action
        for pb in armature.pose.bones:
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
        self._pose = {}  # bone -> Quaternion (current local delta)

    # -- low level ---------------------------------------------------------------------------------
    def _rest_rot(self, bone: str) -> Matrix:
        return self.arm.pose.bones[bone].bone.matrix_local.to_3x3()

    def delta(self, bone: str, axis, degrees: float) -> Quaternion:
        """Local pose quaternion equivalent to rotating `bone` by `degrees` about an armature-space axis."""
        a = AXES[axis] if isinstance(axis, str) else Vector(axis).normalized()
        r = self._rest_rot(bone)
        local_axis = r.inverted() @ a
        return Quaternion(local_axis, math.radians(degrees))

    def set(self, frame: int, rotations: dict, interp: str = "BEZIER"):
        """Key a pose. rotations: {bone: [(axis, degrees), ...]} applied in order (extrinsic, armature axes)."""
        for bone, ops in rotations.items():
            pb = self.arm.pose.bones[bone]
            q = Quaternion((1, 0, 0, 0))
            for axis, deg in ops:
                q = self.delta(bone, axis, deg) @ q
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=frame)
        for fc in self.action.fcurves:
            for kp in fc.keyframe_points:
                if kp.co[0] == frame:
                    kp.interpolation = interp

    def key_rest(self, frame: int, bones):
        self.set(frame, {b: [] for b in bones})

    def close_loop(self):
        """Copy the first key of every curve to the last frame so the loop has no pop."""
        for fc in self.action.fcurves:
            if fc.keyframe_points:
                fc.keyframe_points.insert(self.frames, fc.evaluate(0), options={"FAST"})
        self.action.use_cyclic = True

    # -- finishing ---------------------------------------------------------------------------------
    def finish(self):
        if self.game_facing:
            root = self.arm.pose.bones["SKEL_ROOT"]
            root.rotation_quaternion = (0, 0, 0, 1)
            for f in (0, self.frames):
                root.keyframe_insert("rotation_quaternion", frame=f)
        for fc in self.action.fcurves:
            fc.update()
        self.action.frame_range = (0, self.frames)
        return self.action


def sine_ops(bone_axis_amp_phase, t: float, cycles: float = 1.0):
    """Helper: ops list for a bone from [(axis, amplitude_deg, phase_cycles), ...] at normalized time t in [0,1]."""
    return [(ax, amp * math.sin(2 * math.pi * (cycles * t + ph))) for ax, amp, ph in bone_axis_amp_phase]


def dump_action(action) -> list:
    """Serialisable copy of every fcurve (keys, interpolation, handles) so a version can be re-exported later."""
    out = []
    for fc in action.fcurves:
        out.append({
            "path": fc.data_path, "index": fc.array_index, "group": fc.group.name if fc.group else "",
            "keys": [{"co": list(k.co), "interp": k.interpolation, "hl": list(k.handle_left), "hr": list(k.handle_right),
                      "hlt": k.handle_left_type, "hrt": k.handle_right_type} for k in fc.keyframe_points],
        })
    return out


class LoadedClip:
    """Clip rebuilt from a dumped action; enough surface for lib.export_ycd."""

    def __init__(self, arm, name, frames, fps, curves):
        self.arm, self.name, self.frames, self.fps = arm, name, frames, fps
        self.action = bpy.data.actions.new(name)
        for c in curves:
            fc = self.action.fcurves.new(c["path"], index=c["index"], action_group=c["group"])
            fc.keyframe_points.add(len(c["keys"]))
            for kp, k in zip(fc.keyframe_points, c["keys"]):
                kp.co = k["co"]
                kp.interpolation = k["interp"]
                kp.handle_left_type, kp.handle_right_type = k["hlt"], k["hrt"]
                kp.handle_left, kp.handle_right = k["hl"], k["hr"]
            fc.update()
        self.action.frame_range = (0, frames)


def quality_report(arm, clip) -> dict:
    """Numbers shown before export: loop seam gap and the fastest per-frame rotation change (degrees)."""
    bones = sorted({fc.data_path.split('"')[1] for fc in clip.action.fcurves if fc.data_path.startswith("pose.bones")})

    def quat(b, f):
        path = f'pose.bones["{b}"].rotation_quaternion'
        cs = [clip.action.fcurves.find(path, index=i) for i in range(4)]
        return Quaternion([c.evaluate(f) if c else (1.0 if i == 0 else 0.0) for i, c in enumerate(cs)]).normalized()

    def ang(a, b):
        return math.degrees(2 * math.acos(min(1.0, abs(a.dot(b)))))

    gap, fastest, fastest_at = 0.0, 0.0, ""
    for b in bones:
        gap = max(gap, ang(quat(b, 0), quat(b, clip.frames)))
        for f in range(clip.frames):
            d = ang(quat(b, f), quat(b, f + 1))
            if d > fastest:
                fastest, fastest_at = d, f"{b}@{f}"
    return {"loop_gap_deg": round(gap, 2), "max_step_deg": round(fastest, 2), "max_step_at": fastest_at}


def export_version(arm, clip: Clip, out_root: Path, label: str = "", module: str = "") -> dict:
    """Bake the clip into a single NLA track, export output/<name>/vN.glb and update meta.json."""
    from . import anims as animlib

    ad = arm.animation_data
    ad.action = None
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    track = ad.nla_tracks.new()
    track.name = clip.name
    strip = track.strips.new(clip.name, 0, clip.action)
    strip.action_frame_start, strip.action_frame_end = 0, clip.frames

    d = out_root / clip.name
    d.mkdir(parents=True, exist_ok=True)
    meta_path = d / "meta.json"
    meta = json.loads(meta_path.read_text("utf-8")) if meta_path.exists() else {"name": clip.name, "versions": []}
    n = len(meta["versions"]) + 1
    glb = d / f"v{n}.glb"
    animlib.export_armature_glb(arm, str(glb))
    (d / f"v{n}.action.json").write_text(json.dumps({"frames": clip.frames, "fps": clip.fps, "curves": dump_action(clip.action)}), "utf-8")
    report = quality_report(arm, clip)
    meta["versions"].append({
        "v": n, "label": label, "frames": clip.frames, "fps": clip.fps,
        "duration": clip.frames / clip.fps, "loop": clip.loop, "file": glb.name, "module": module,
        "status": "pending", "report": report,
        "bones": sorted({fc.data_path.split('"')[1] for fc in clip.action.fcurves if fc.data_path.startswith("pose.bones")}),
    })
    meta_path.write_text(json.dumps(meta, indent=1), "utf-8")
    return meta
