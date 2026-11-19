"""Key-pose authoring on top of Clip: describe a few key poses in CHARACTER SPACE, every frame in between is
interpolated and solved with IK (feet first, then hands). Run inside Blender.

Character space (game_facing clip): origin on the floor under the rest pelvis, x = character's RIGHT, y = FORWARD,
z = UP, metres. A key is (frame, {param: value}); a param missing in a key keeps its previous value.

  root            (x, y, z)   pelvis offset from standing (z<0 crouch, z>0 jump)
  pelvis/spine/chest/neck/head   (x, y, z) degrees: x>0 lean forward, y>0 bend to the left, z>0 turn to the left
  hand_L/hand_R   (x, y, z)   wrist position in character space (z measured from the floor)
  elbow_L/elbow_R (x, y, z)   direction the elbow points to (optional; default back/down/out)
  palm_L/palm_R, fingers_L/fingers_R direction vectors: anatomical hand orientation, blended by orient_L/orient_R (0..1)
  wrist_L/wrist_R (x, y, z) degrees, extra hand rotation
  ball (x, y, z)  ball centre in character space, cup 0..1: hands are PLACED from the ball (palm on the surface, fingers wrapping forward-down,
                  see cup_frame) instead of from hand_L/hand_R; the two blend by `cup`
  cup_L/cup_R     0..1 per-hand multiplier of `cup`; cu_*/cd_* (x, y, z) override the palm contact direction (ball centre -> palm) and the finger
                  direction (default: sides of the ball, fingers forward-down), character space, zero vector = default
  fing_L/fing_R   0..1 finger pose weight (rest -> clip.finger_sets[side]); `grip` also drives it (max of the two)
  clav_L/clav_R   (x, y, z) degrees, shoulder shrug etc.
  foot_L/foot_R   (dx, dy, dz) ankle offset from its standing spot
  knee_L/knee_R   (x, y, z) optional knee bend direction; zero uses the default
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
    "palm_L": (0, 0, -1), "palm_R": (0, 0, -1), "fingers_L": (0, 1, 0), "fingers_R": (0, 1, 0),
    "orient_L": 0.0, "orient_R": 0.0, "knee_L": (0, 0, 0), "knee_R": (0, 0, 0),
    "wrist_L": (0, 0, 0), "wrist_R": (0, 0, 0),
    "foot_L": (0, 0, 0), "foot_R": (0, 0, 0), "pitch_L": 0.0, "pitch_R": 0.0, "glide": 0,
    "grip": 0.0, "fing_L": 0.0, "fing_R": 0.0, "ball": (0.0, 0.36, 1.05), "cup": 0.0,
    "cup_L": 1.0, "cup_R": 1.0, "cu_L": (0.0, 0.0, 0.0), "cu_R": (0.0, 0.0, 0.0), "cd_L": (0.0, 0.0, 0.0), "cd_R": (0.0, 0.0, 0.0),
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


# CUP (topu avuçla sarma) geometrisi: avuç içi topun yüzeyine, ekvatorun biraz altında ve hafif önünde; parmaklar küre teğeti boyunca ileri-aşağı
CUP_ELEV, CUP_AZ = math.radians(-12.0), math.radians(12.0)     # avuç temas yönü (yan eksenden aşağı / ileri sapma)
CUP_FINGER_DIR = (0.0, 1.0, -0.6)                               # istenen parmak yönü (karakter uzayı; teğet düzleme izdüşürülür)
PALM_TO_WRIST = 0.055                                           # el kemiği başı (bilek) -> avuç merkezi, parmak yönünde (m)
CUP_MARGIN = 0.004                                              # avuç topun yüzeyinde (içeri/dışarı payı)


def rest_hand_frames(arm, yaw):
    """Her el için KEMİK EKSENİNDEN BAĞIMSIZ anatomik çerçeve (bileğin, orta/işaret/serçe parmak boğumlarının dinlenme konumlarından):
    parmak ekseni a = bilek -> orta boğum; avuç içi normali n = sağ elde a × (işaret->serçe), sol elde bunun tersi (sağ/sol kuralı);
    LF = (a, n × a, n). Dönüş: {side: (LF 3x3, el kemiğinin dinlenme yönelimi 3x3 [yaw çerçevesinde])}. Bilek/parmak kemiklerinin yerel
    eksenleri iki elde aynalı olmadığından yönelim buradan kurulur (kemik eksenine göre sabit B = bone^T LF)."""
    out = {}
    for side in "LR":
        hb = arm.data.bones[f"SKEL_{side}_Hand"]
        w = (yaw @ hb.head_local)
        m = (yaw @ arm.data.bones[f"SKEL_{side}_Finger20"].head_local)
        i = (yaw @ arm.data.bones[f"SKEL_{side}_Finger10"].head_local)
        k = (yaw @ arm.data.bones[f"SKEL_{side}_Finger40"].head_local)
        a = (m - w).normalized()
        lip = (k - i)
        lip = (lip - a * lip.dot(a)).normalized()
        n = a.cross(lip)
        if side == "L":
            n = -n
        n = n.normalized()
        y = n.cross(a)
        lf = Matrix(((a.x, y.x, n.x), (a.y, y.y, n.y), (a.z, y.z, n.z)))
        bone = (yaw.to_3x3() @ hb.matrix_local.to_3x3())
        # parmak kıvrılma ekseni = boğum hattı (işaret -> serçe), armatür dinlenme uzayında (yaw'sız): hemen her kemiğin yerel ekseninden
        # bağımsız; pozitif açı = avuca doğru kıvırma (sol elde +, sağ elde - dönüş), yani aynı sayılar iki elde simetriktir
        w0 = hb.head_local
        a0 = (arm.data.bones[f"SKEL_{side}_Finger20"].head_local - w0).normalized()
        l0 = arm.data.bones[f"SKEL_{side}_Finger40"].head_local - arm.data.bones[f"SKEL_{side}_Finger10"].head_local
        l0 = (l0 - a0 * l0.dot(a0)).normalized()
        out[side] = (lf, bone, (m - w).length, l0)
    return out


def cup_frame(side, ball, floor, radius, frames, u_over=None, d_over=None):
    """Topun merkezinden (karakter uzayı) el hedefi ve el kemiği yönelimi: dönüş (bilek konumu [armatür uzayı, zemin dahil], 3x3 yönelim).
    Hedef çerçeve: parmaklar küre teğeti boyunca ileri-aşağı (f), avuç içi topun merkezine bakar (n = -u). Sol el sağın aynasıdır."""
    sg = 1.0 if side == "R" else -1.0
    u = Vector((sg * math.cos(CUP_ELEV) * math.cos(CUP_AZ), math.cos(CUP_ELEV) * math.sin(CUP_AZ), math.sin(CUP_ELEV)))
    d0 = Vector((sg * CUP_FINGER_DIR[0], CUP_FINGER_DIR[1], CUP_FINGER_DIR[2]))
    if u_over is not None and Vector(u_over).length > 1e-6:
        u = Vector(u_over).normalized()
    if d_over is not None and Vector(d_over).length > 1e-6:
        d0 = Vector(d_over)
    f = (d0 - u * d0.dot(u)).normalized()
    n = -u
    y = n.cross(f)
    target = Matrix(((f.x, y.x, n.x), (f.y, y.y, n.y), (f.z, y.z, n.z)))
    lf, bone, wm, _lat = frames[side]
    rot = target @ lf.transposed() @ bone                       # hedef anatomik çerçeveyi veren kemik yönelimi
    palm = Vector(ball) + u * (radius + CUP_MARGIN)
    wrist = palm - f * (wm * 0.5)                               # bilek -> avuç merkezi = bilek -> orta boğumun yarısı
    return Vector((wrist.x, wrist.y, floor + wrist.z)), rot


def _key_fingers(clip, p, f):
    """Key every finger bone of a hand whose `clip.finger_sets[side]` is defined. Fingers 1..4: (c0, c1, c2) = curl degrees TOWARD THE PALM of
    the three joints, about the knuckle line (same numbers on both hands, see rest_hand_frames). Thumb (key 0): legacy bone-local
    ((z0, x0), z1, z2). Weight = max(grip, fing_<side>) scales rest -> pose."""
    sets = getattr(clip, "finger_sets", None)
    if not sets:
        return
    P = clip.arm.pose.bones
    frames = getattr(clip, "_hand_frames", None)
    for side in "LR":
        tbl = sets.get(side)
        if not tbl:
            continue
        w = max(p.get("grip", 0.0), p.get(f"fing_{side}", 0.0))
        sign = 1.0 if side == "L" else -1.0
        lat = frames[side][3] if frames else None
        for fi, vals in tbl.items():
            for j in range(3):
                name = f"SKEL_{side}_Finger{fi}{j}"
                pb = P[name]
                pb.rotation_mode = "QUATERNION"
                if fi == 0:
                    z, x = (vals[0][0], vals[0][1]) if j == 0 else (vals[j], 0.0)
                    pb.rotation_quaternion = Quaternion((0, 0, 1), math.radians(z * w)) @ Quaternion((1, 0, 0), math.radians(x * w))
                else:
                    pb.rotation_quaternion = clip.delta(name, lat, sign * vals[j] * w)
                pb.keyframe_insert("rotation_quaternion", frame=f)


def animate(clip, keys):
    """Bake key poses into `clip` for every frame 0..clip.frames. Returns the worst unreachable IK distance (m)."""
    arm = clip.arm
    filled = _filled(keys)
    rm = arm.data.bones["SKEL_ROOT"].matrix_local
    yaw = rm @ Quaternion((0, 0, 0, 1) if clip.game_facing else (1, 0, 0, 0)).to_matrix().to_4x4() @ rm.inverted()
    hand_frames = rest_hand_frames(arm, yaw)
    clip._hand_frames = hand_frames
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
            # knee direction: a little outward on the ground (squat), straight ahead once the foot is off the floor (a
            # tucked leg with the knee splayed wider than the foot is not a GTA ped pose)
            out = 0.25 - 0.17 * min(1.0, max(0.0, p[f"foot_{side}"][2]) / 0.3)
            knee = clip.forward() + Vector((out if side == "R" else -out, 0, 0.2))
            if Vector(p[f"knee_{side}"]).length > 1e-6:
                override = Vector(p[f"knee_{side}"])
                knee = knee.normalized().lerp(override.normalized(), min(1.0, override.length)).normalized()
            miss = clip.ik(f, *chain, tpos + Vector(p[f"foot_{side}"]), knee, end_rot=rot,
                           min_mid_z=floor + clip.knee_clearance if hasattr(clip, "knee_clearance") else None)
            if miss > worst_at[0]:
                worst_at = (miss, f"foot_{side}", f)
            worst = max(worst, miss)
        _key_fingers(clip, p, f)
        for side in "LR":
            h = p[f"hand_{side}"]
            clip.eval(f)
            tgt, elb = Vector((h[0], h[1], floor + h[2])), Vector(p[f"elbow_{side}"])
            hand = clip.ARMS[side][2]
            gw = p.get("grip", 0.0)
            gr = getattr(clip, "grip_rot", None)
            cw = min(1.0, p.get("cup", 0.0)) * p.get(f"cup_{side}", 1.0)
            gripping = (bool(gr) and gw > 0.001) or cw > 0.001
            if cw > 0.001:
                tgt_c, rot_c = cup_frame(side, p["ball"], floor, 0.105, hand_frames, p.get(f"cu_{side}"), p.get(f"cd_{side}"))
                tgt = tgt + (tgt_c - tgt) * cw
                gw = cw
                grot = rot_c.to_quaternion()
            elif gripping:
                grot = gr[side].to_quaternion()
            if gripping:
                # TUTUŞ: el yönü, doğal yönden referans tutuş yönüne `grip` ağırlığıyla harmanlanır; böylece top-el ofseti klipler
                # arasında sabit kalır (oyunda top tek kemiğe tek ofsetle bağlanır).
                import bpy
                clip.ik(f, *clip.ARMS[side], tgt, elb)                      # doğal el yönünü ölç
                P = clip.arm.pose.bones
                P[hand].rotation_quaternion = (1, 0, 0, 0)
                bpy.context.view_layer.update()
                nat = P[hand].matrix.to_3x3().to_quaternion()
                q = nat.slerp(grot, min(1.0, gw))
                miss = clip.ik(f, *clip.ARMS[side], tgt, elb, end_rot=q.to_matrix())
            elif p.get(f"orient_{side}", 0.0) > 0.001:
                # Explicit anatomical orientation for ground support; existing clips default to weight zero.
                import bpy
                clip.ik(f, *clip.ARMS[side], tgt, elb)
                P = arm.pose.bones
                P[hand].rotation_quaternion = (1, 0, 0, 0)
                bpy.context.view_layer.update()
                nat = P[hand].matrix.to_quaternion()
                n = Vector(p[f"palm_{side}"]).normalized()
                d = Vector(p[f"fingers_{side}"])
                d = (d - n * d.dot(n)).normalized()
                y = n.cross(d)
                target = Matrix(((d.x, y.x, n.x), (d.y, y.y, n.y), (d.z, y.z, n.z)))
                lf, bone, _, _ = hand_frames[side]
                q = (target @ lf.transposed() @ bone).to_quaternion()
                q = nat.slerp(q, min(1.0, p[f"orient_{side}"]))
                miss = clip.ik(f, *clip.ARMS[side], tgt, elb, end_rot=q.to_matrix())
            else:
                miss = clip.ik(f, *clip.ARMS[side], tgt, elb)
            if miss > worst_at[0]:
                worst_at = (miss, f"hand_{side}", f)
            worst = max(worst, miss)
            if not gripping and p.get(f"orient_{side}", 0.0) <= 0.001:
                w = p[f"wrist_{side}"]
                clip.set(f, {hand: [("x", w[0]), ("y", w[1]), ("z", w[2])]}, interp="LINEAR")
    for fc in clip.action.fcurves:                       # finger tracks: linear between the per-frame bakes
        if "_Finger" in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    clip.ik_worst_at = worst_at
    clip.floor = floor
    return worst
