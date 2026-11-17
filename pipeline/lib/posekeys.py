"""Key-pose authoring on top of Clip: describe a few key poses in CHARACTER SPACE, every frame in between is
interpolated and solved with IK (feet first, then hands). Run inside Blender.

Character space (game_facing clip): origin on the floor under the rest pelvis, x = character's RIGHT, y = FORWARD,
z = UP, metres. A key is (frame, {param: value}); a param missing in a key keeps its previous value.

  root            (x, y, z)   pelvis offset from standing (z<0 crouch, z>0 jump)
  pelvis/spine/chest/neck/head   (x, y, z) degrees: x>0 lean forward, y>0 bend to the left, z>0 turn to the left
  hand_L/hand_R   (x, y, z)   wrist position in character space (z measured from the floor)
  elbow_L/elbow_R (x, y, z)   direction the elbow points to (optional; default back/down/out)
  wrist_L/wrist_R (x, y, z) degrees, extra hand rotation
  clav_L/clav_R   (x, y, z) degrees, shoulder shrug etc.
  foot_L/foot_R   (dx, dy, dz) ankle offset from its standing spot
  pitch_L/pitch_R degrees, >0 = toes point down (tiptoe / airborne)
  glide           1 = feet may slide on the ground toward this key (treadmill loops); default: they step
  ease            'smooth' (default) | 'lin' | 'in' | 'out'  -- how this key is approached
"""
import math

from mathutils import Matrix, Quaternion, Vector

BONES = {"pelvis": "SKEL_Pelvis", "spine": "SKEL_Spine1", "chest": "SKEL_Spine3", "neck": "SKEL_Neck_1", "head": "SKEL_Head",
         "clav_L": "SKEL_L_Clavicle", "clav_R": "SKEL_R_Clavicle"}
STAND = {
    "root": (0, 0, 0), "pelvis": (0, 0, 0), "spine": (0, 0, 0), "chest": (0, 0, 0), "neck": (0, 0, 0), "head": (0, 0, 0),
    "clav_L": (0, 0, 0), "clav_R": (0, 0, 0),
    "hand_L": (-0.27, 0.04, 0.84), "hand_R": (0.27, 0.04, 0.84),
    "elbow_L": (-0.5, -1.0, -0.6), "elbow_R": (0.5, -1.0, -0.6),
    "wrist_L": (0, 0, 0), "wrist_R": (0, 0, 0),
    "foot_L": (0, 0, 0), "foot_R": (0, 0, 0), "pitch_L": 0.0, "pitch_R": 0.0, "glide": 0,
}
EASE = {
    "smooth": lambda t: t * t * (3 - 2 * t), "lin": lambda t: t,
    "in": lambda t: t * t, "out": lambda t: 1 - (1 - t) * (1 - t),
}


def _lerp(a, b, t):
    if isinstance(a, (int, float)):
        return a + (b - a) * t
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _filled(keys):
    cur = dict(STAND)
    out = []
    for frame, pose in sorted(keys, key=lambda k: k[0]):
        cur = {**cur, "glide": 0, **{k: v for k, v in pose.items() if k != "ease"}}
        out.append((frame, dict(cur), pose.get("ease", "smooth")))
    return out


def pose_at(filled, f):
    if f <= filled[0][0]:
        return filled[0][1]
    for (f0, p0, _), (f1, p1, ease) in zip(filled, filled[1:]):
        if f0 <= f <= f1:
            t = EASE[ease]((f - f0) / max(1e-9, f1 - f0))
            out = {k: _lerp(p0[k], p1[k], t) for k in p0}
            for side in "LR":  # a grounded foot that changes spot steps (small arc) instead of sliding
                a, b = p0[f"foot_{side}"], p1[f"foot_{side}"]
                moved = math.hypot(b[0] - a[0], b[1] - a[1])
                if moved > 0.03 and abs(a[2]) < 0.01 and abs(b[2]) < 0.01 and not p1.get("glide"):
                    x, y, z = out[f"foot_{side}"]
                    out[f"foot_{side}"] = (x, y, z + (0.05 + 0.1 * moved) * math.sin(math.pi * t))
            return out
    return filled[-1][1]


def animate(clip, keys):
    """Bake key poses into `clip` for every frame 0..clip.frames. Returns the worst unreachable IK distance (m)."""
    arm = clip.arm
    filled = _filled(keys)
    rm = arm.data.bones["SKEL_ROOT"].matrix_local
    yaw = rm @ Quaternion((0, 0, 0, 1) if clip.game_facing else (1, 0, 0, 0)).to_matrix().to_4x4() @ rm.inverted()
    floor = min((yaw @ b.head_local).z for b in arm.data.bones if b.name.startswith("SKEL_"))
    feet = {}
    for side, chain in zip("LR", clip.LEGS):
        m = yaw @ arm.data.bones[chain[2]].matrix_local
        feet[side] = (chain, m.translation.copy(), m.to_3x3().copy())
    # character x = right. After the yaw the R limbs sit on +X.
    worst, worst_at = 0.0, (0.0, '', 0)
    for f in range(0, clip.frames + 1):
        p = pose_at(filled, f)
        clip.set_root(f, p["root"], interp="LINEAR")
        clip.set(f, {bone: [("x", p[k][0]), ("y", p[k][1]), ("z", p[k][2])] for k, bone in BONES.items()}, interp="LINEAR")
        for side, (chain, tpos, trot) in feet.items():
            rot = Matrix.Rotation(math.radians(-p[f"pitch_{side}"]), 3, "X") @ trot
            clip.eval(f)
            knee = clip.forward() + Vector((0.25 if side == "R" else -0.25, 0, 0.2))
            worst = max(worst, clip.ik(f, *chain, tpos + Vector(p[f"foot_{side}"]), knee, end_rot=rot))
        for side in "LR":
            h = p[f"hand_{side}"]
            clip.eval(f)
            miss = clip.ik(f, *clip.ARMS[side], Vector((h[0], h[1], floor + h[2])), Vector(p[f"elbow_{side}"]))
            if miss > worst_at[0]:
                worst_at = (miss, f"hand_{side}", f)
            worst = max(worst, miss)
            w = p[f"wrist_{side}"]
            clip.set(f, {clip.ARMS[side][2]: [("x", w[0]), ("y", w[1]), ("z", w[2])]}, interp="LINEAR")
    clip.ik_worst_at = worst_at
    return worst
