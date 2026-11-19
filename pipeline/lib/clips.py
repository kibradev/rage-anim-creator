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
        if game_facing:
            # yaw first, so world-space work (IK targets, hip offsets, renders) already sees the final facing (+Y)
            root = armature.pose.bones["SKEL_ROOT"]
            root.rotation_quaternion = (0, 0, 0, 1)
            for f in (0, frames):
                root.keyframe_insert("rotation_quaternion", frame=f)

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

    def add(self, frame: int, rotations: dict):
        """Like set(), but layered on top of whatever the bone already does at `frame` (e.g. a copied GTA motion)."""
        self.eval(frame)
        for bone, ops in rotations.items():
            pb = self.arm.pose.bones[bone]
            q = pb.rotation_quaternion.copy()
            for axis, deg in ops:
                q = self.delta(bone, axis, deg) @ q
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=frame)

    # -- position / IK -----------------------------------------------------------------------------
    def eval(self, frame: float):
        """Evaluate the action at `frame` so pose matrices are the real interpolated pose."""
        bpy.context.scene.frame_set(int(frame), subframe=frame - int(frame))

    def pos(self, bone: str) -> Vector:
        """Armature-space head position of a bone in the currently evaluated pose."""
        return self.arm.pose.bones[bone].matrix.translation.copy()

    def rest_pos(self, bone: str) -> Vector:
        return self.arm.data.bones[bone].head_local.copy()

    def set_root(self, frame: int, offset, interp: str = "BEZIER"):
        """Hip translation: move SKEL_ROOT by `offset` metres (armature axes, relative to rest). z<0 = crouch."""
        pb = self.arm.pose.bones["SKEL_ROOT"]
        pb.location = self._rest_rot("SKEL_ROOT").inverted() @ Vector(offset)
        pb.keyframe_insert("location", frame=frame)
        for fc in self.action.fcurves:
            if fc.data_path.endswith('["SKEL_ROOT"].location'):
                for kp in fc.keyframe_points:
                    if kp.co[0] == frame:
                        kp.interpolation = interp

    def _aim(self, bone: str, child: str, new_dir: Vector):
        """Rotate `bone` about its head (shortest arc) so the head->child direction becomes new_dir."""
        pb = self.arm.pose.bones[bone]
        head = pb.matrix.translation.copy()
        cur = (self.arm.pose.bones[child].matrix.translation - head).normalized()
        q = cur.rotation_difference(new_dir.normalized()).to_matrix().to_4x4()
        pb.matrix = Matrix.Translation(head) @ q @ Matrix.Translation(-head) @ pb.matrix
        bpy.context.view_layer.update()

    def ik(self, frame: int, upper: str, lower: str, end: str, target, pole, end_rot: Matrix = None, min_mid_z: float = None):
        """Two-bone IK at `frame`: put the head of `end` (hand/foot) at `target` (armature space); the middle joint
        (elbow/knee) bends toward `pole` (a direction). end_rot: optional armature-space 3x3 orientation for `end`.
        min_mid_z optionally constrains the elbow/knee centre above a floor while preserving segment lengths.
        Keys upper/lower (and end if end_rot). Returns the distance left to the target (0 if reachable)."""
        self.eval(frame)
        P = self.arm.pose.bones
        for b in (upper, lower):  # start from rest so the result does not depend on the previous pose (stable twist)
            P[b].rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()
        p0 = P[upper].matrix.translation.copy()
        l1 = (self.rest_pos(lower) - self.rest_pos(upper)).length
        l2 = (self.rest_pos(end) - self.rest_pos(lower)).length
        t = Vector(target)
        d_full = (t - p0).length
        d = max(abs(l1 - l2) + 1e-4, min(d_full, (l1 + l2) * 0.999))
        direction = (t - p0).normalized()
        a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
        h = math.sqrt(max(0.0, l1 * l1 - a * a))
        pv = Vector(pole)
        perp = pv - direction * pv.dot(direction)
        perp = perp.normalized() if perp.length > 1e-6 else direction.orthogonal().normalized()
        center = p0 + direction * a
        mid = center + perp * h
        if min_mid_z is not None and mid.z < min_mid_z and h > 1e-6:
            # The joint lies on a circle perpendicular to the hip->ankle axis.
            # Choose the closest bend direction on that circle above the floor.
            up = Vector((0, 0, 1)) - direction * direction.z
            span = up.length
            if span > 1e-6:
                up.normalize()
                tangent = direction.cross(up).normalized()
                height = max(-1.0, min(1.0, (min_mid_z - center.z) / (h * span)))
                sign = 1.0 if perp.dot(tangent) >= 0 else -1.0
                perp = up * height + tangent * (sign * math.sqrt(max(0.0, 1 - height * height)))
                mid = center + perp * h
        self._aim(upper, lower, mid - p0)
        self._aim(lower, end, (p0 + direction * d) - mid)
        keyed = [upper, lower]
        if end_rot is not None:
            pe = P[end]
            m = end_rot.to_4x4()
            m.translation = pe.matrix.translation
            pe.matrix = m
            bpy.context.view_layer.update()
            keyed.append(end)
        for b in keyed:
            P[b].keyframe_insert("rotation_quaternion", frame=frame)
        return max(0.0, d_full - d)

    LEGS = (("SKEL_L_Thigh", "SKEL_L_Calf", "SKEL_L_Foot"), ("SKEL_R_Thigh", "SKEL_R_Calf", "SKEL_R_Foot"))
    ARMS = {"L": ("SKEL_L_UpperArm", "SKEL_L_Forearm", "SKEL_L_Hand"), "R": ("SKEL_R_UpperArm", "SKEL_R_Forearm", "SKEL_R_Hand")}

    def forward(self) -> Vector:
        """Direction the pelvis currently faces (armature space, horizontal). Rest faces -Y; game_facing clips +Y."""
        m = self.arm.pose.bones["SKEL_Pelvis"].matrix.to_3x3() @ self._rest_rot("SKEL_Pelvis").inverted()
        f = m @ Vector((0, -1, 0))
        f.z = 0
        return f.normalized()

    def plant_feet(self, frames, ref_frame: int = None, offsets=None, sides="LR"):
        """Keep feet fixed on the ground for every frame in `frames` (call after hips/spine are keyed).
        Targets: foot position+orientation at ref_frame (or rest pose if None), plus optional per-side offsets
        {'L': (x,y,z) or callable(frame)->(x,y,z)} to lift/step a foot. Returns the worst unreachable distance."""
        targets = {}
        if ref_frame is not None:
            self.eval(ref_frame)
        for side, chain in zip("LR", self.LEGS):
            if side not in sides:
                continue
            foot = chain[2]
            if ref_frame is None:  # rest pose, carried along by the root yaw
                rm = self.arm.data.bones["SKEL_ROOT"].matrix_local
                yaw = Quaternion((0, 0, 0, 1) if self.game_facing else (1, 0, 0, 0)).to_matrix().to_4x4()
                m = rm @ yaw @ rm.inverted() @ self.arm.data.bones[foot].matrix_local
            else:
                m = self.arm.pose.bones[foot].matrix
            targets[side] = (chain, m.translation.copy(), m.to_3x3().copy())
        worst = 0.0
        for f in frames:
            for side, (chain, tpos, trot) in targets.items():
                off = (offsets or {}).get(side, (0, 0, 0))
                off = Vector(off(f) if callable(off) else off)
                self.eval(f)
                worst = max(worst, self.ik(f, *chain, tpos + off, self.forward() + Vector((0, 0, 0.2)), end_rot=trot))
        return worst

    def reach(self, frame: int, side: str, target, pole=None):
        """Put the hand of `side` ('L'/'R') at an armature-space target. Elbow points back/down/outward by default."""
        self.eval(frame)
        if pole is None:
            out = Vector((1, 0, 0)) if self.rest_pos(self.ARMS[side][0]).x > 0 else Vector((-1, 0, 0))
            pole = -self.forward() + Vector((0, 0, -0.6)) + out * 0.5
        return self.ik(frame, *self.ARMS[side], target, pole)

    def copy_from(self, action, src_start: int, src_end: int, dst_start: int = 0, bones=None, root_location=True):
        """Copy a (GTA) action range into this clip, frame by frame: rotations of `bones` (default: all keyed) and
        optionally SKEL_ROOT location. Use add()/reach()/plant_feet() afterwards to change it."""
        paths = {}
        for fc in action.fcurves:
            if not fc.data_path.startswith("pose.bones["):
                continue
            b = fc.data_path.split('"')[1]
            kind = fc.data_path.rsplit(".", 1)[-1]
            if kind == "rotation_quaternion" and (bones is None or b in bones) and b in self.arm.pose.bones:
                paths.setdefault((b, kind), {})[fc.array_index] = fc
            elif kind == "location" and b == "SKEL_ROOT" and root_location:
                paths.setdefault((b, kind), {})[fc.array_index] = fc
        for (b, kind), fcs in paths.items():
            n = 4 if kind == "rotation_quaternion" else 3
            default = (1, 0, 0, 0) if n == 4 else (0, 0, 0)
            for i in range(n):
                path = f'pose.bones["{b}"].{kind}'
                nf = self.action.fcurves.find(path, index=i) or self.action.fcurves.new(path, index=i, action_group=b)
                for f in range(src_start, src_end + 1):
                    v = fcs[i].evaluate(f) if i in fcs else default[i]
                    nf.keyframe_points.insert(dst_start + f - src_start, v, options={"FAST"}).interpolation = "LINEAR"
                nf.update()
        self.game_facing = False  # GTA motion already carries the root yaw

    def close_loop(self):
        """Copy the first key of every curve to the last frame so the loop has no pop."""
        for fc in self.action.fcurves:
            if fc.keyframe_points:
                fc.keyframe_points.insert(self.frames, fc.evaluate(0), options={"FAST"})
        self.action.use_cyclic = True

    # -- finishing ---------------------------------------------------------------------------------
    def finish(self):
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


def export_version(arm, clip: Clip, out_root: Path, label: str = "", module: str = "", ped: str = "") -> dict:
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
    n = max((v["v"] for v in meta["versions"]), default=0) + 1
    glb = d / f"v{n}.glb"
    animlib.export_armature_glb(arm, str(glb))
    (d / f"v{n}.action.json").write_text(json.dumps({"frames": clip.frames, "fps": clip.fps, "curves": dump_action(clip.action)}), "utf-8")
    report = quality_report(arm, clip)
    from . import checks
    report["motion"] = checks.motion_report(arm, clip.action, 0, clip.frames, clip.loop)
    report["warnings"] = report["motion"].pop("warnings")
    ad.action = None
    meta["versions"].append({
        "v": n, "label": label, "frames": clip.frames, "fps": clip.fps,
        "duration": clip.frames / clip.fps, "loop": clip.loop, "file": glb.name, "module": module,
        "status": "pending", "report": report, "ped": ped,
        "bones": sorted({fc.data_path.split('"')[1] for fc in clip.action.fcurves if fc.data_path.startswith("pose.bones")}),
    })
    meta_path.write_text(json.dumps(meta, indent=1), "utf-8")
    return meta
