from pathlib import Path
p=Path('pipeline/clip_defs/volleyball.py')
s=p.read_text(encoding='utf-8')
a=s.index('def dive():')
b=s.index('\n\ndef shuffle_R()',a)
s=s[:a]+'''def dive():
    """Forward platform dig, soft hand-supported landing and staggered recovery.
    Local root travel is recovered during airborne/replant phases; grounded hands stay fixed.
    Pelvis and spine pitch ADD: keep the flying torso near horizontal, not folded over.
    """
    load = {"root": (0, 0.02, -0.32), "pelvis": (18, 0, 0), "spine": (20, 0, 0), "chest": (4, 0, 0), "head": (-24, 0, 0),
            "hand_L": (-0.12, 0.54, 0.80), "hand_R": (0.12, 0.54, 0.80),
            "foot_L": READY["foot_L"], "foot_R": READY["foot_R"]}
    drive = {"root": (0, 0.20, -0.22), "pelvis": (38, 0, 0), "spine": (16, 0, 0), "chest": (4, 0, 0), "head": (-24, 0, 0),
             "hand_L": (-J, 0.92, 0.91), "hand_R": (J, 0.92, 0.91),
             "foot_L": (-0.12, 0, 0.04), "foot_R": (0.12, 0, 0.04), "pitch_L": 15, "pitch_R": 15, "ease": "in"}
    fly = {"root": (0, 0.44, -0.35), "pelvis": (70, 0, 0), "spine": (10, 0, 0), "chest": (2, 0, 0), "head": (-24, 0, 0),
           "hand_L": (-J, 1.38, 0.69), "hand_R": (J, 1.38, 0.69),
           "elbow_L": (-0.6, 0, -1), "elbow_R": (0.6, 0, -1),
           "foot_L": (-0.10, -0.27, 0.42), "foot_R": (0.10, -0.31, 0.48), "pitch_L": 30, "pitch_R": 32, "ease": "lin"}
    hit = {"root": (0, 0.58, -0.47), "pelvis": (78, 0, 0), "spine": (8, 0, 0), "chest": (0, 0, 0), "head": (-24, 0, 0),
           "hand_L": (-J, 1.55, 0.48), "hand_R": (J, 1.55, 0.48),
           "foot_L": (-0.10, -0.21, 0.35), "foot_R": (0.10, -0.25, 0.40), "ease": "lin"}
    contact = {"root": (0, 0.68, -0.64), "pelvis": (80, 0, 0), "spine": (6, 0, 0), "head": (-20, 0, 0),
               "hand_L": (-0.25, 1.37, 0.12), "hand_R": (0.25, 1.37, 0.12),
               "elbow_L": (-1, -0.25, 0.25), "elbow_R": (1, -0.25, 0.25),
               "foot_L": (-0.10, -0.15, 0.22), "foot_R": (0.10, -0.18, 0.26),
               "palm_L": (0, 0, -1), "palm_R": (0, 0, -1), "fingers_L": (0, 1, 0), "fingers_R": (0, 1, 0),
               "orient_L": 1.0, "orient_R": 1.0, "ease": "lin"}
    absorb = {"root": (0, 0.74, -0.72), "pelvis": (82, 0, 0), "spine": (4, 0, 0), "head": (-16, 0, 0),
              "foot_L": (-0.10, -0.12, 0.14), "foot_R": (0.10, -0.15, 0.17), "pitch_L": 18, "pitch_R": 20, "ease": "out"}
    support = {"root": (0, 0.68, -0.59), "pelvis": (66, 0, 0), "spine": (6, 0, 0), "head": (-20, 0, 0),
               "foot_L": (-0.10, 0.02, 0.17), "foot_R": (0.10, -0.03, 0.18), "pitch_L": 12, "pitch_R": 15}
    tuck = {"root": (0, 0.53, -0.53), "pelvis": (48, 0, 0), "spine": (12, 0, 0), "head": (-24, 0, 0),
            "foot_L": (-0.12, 0.27, 0.02), "foot_R": (0.12, -0.02, 0.12), "pitch_L": 0, "pitch_R": 18,
            "hand_L": (-0.25, 1.20, 0.14), "hand_R": (0.25, 1.37, 0.12), "orient_L": 0.8}
    squat = {"root": (0, 0.28, -0.42), "pelvis": (24, 0, 0), "spine": (18, 0, 0), "head": (-24, 0, 0),
             "foot_L": (-0.12, 0.27, 0.02), "foot_R": (0.12, 0, 0.02), "pitch_L": 0, "pitch_R": 0,
             "hand_L": (-0.26, 0.76, 0.62), "hand_R": (0.26, 0.86, 0.42), "orient_L": 0.0, "orient_R": 0.4,
             "elbow_L": (-0.6, -0.6, -0.6), "elbow_R": (0.6, -0.6, -0.6)}
    step = {"root": (0, 0.08, -0.24), "pelvis": (12, 0, 0), "spine": (18, 0, 0), "head": (-20, 0, 0),
            "foot_L": (-0.12, 0.12, 0.14), "foot_R": (0.12, 0, 0.02),
            "hand_L": (-0.25, 0.45, 0.94), "hand_R": (0.25, 0.45, 0.94), "orient_R": 0.0}
    reset = {**READY, "foot_R": (0.12, 0, 0.02), "orient_L": 0.0, "orient_R": 0.0}
    return 78, False, [(0, READY), (7, load), (12, drive), (18, fly), (22, hit), (27, contact), (32, absorb),
                       (40, support), (48, tuck), (58, squat), (66, step), (72, reset), (78, READY)]
''' + s[b:]
p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
p=Path('pipeline/lib/posekeys.py')
s=p.read_text(encoding='utf-8')
s=s.replace('  wrist_L/wrist_R', '  palm_L/palm_R, fingers_L/fingers_R direction vectors: anatomical hand orientation, blended by orient_L/orient_R (0..1)\n  wrist_L/wrist_R',1)
s=s.replace('    "wrist_L": (0, 0, 0),', '    "palm_L": (0, 0, -1), "palm_R": (0, 0, -1), "fingers_L": (0, 1, 0), "fingers_R": (0, 1, 0),\n    "orient_L": 0.0, "orient_R": 0.0,\n    "wrist_L": (0, 0, 0),',1)
s=s.replace('            else:\n                miss = clip.ik(f, *clip.ARMS[side], tgt, elb)\n', '''            elif p.get(f"orient_{side}", 0.0) > 0.001:
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
''',1)
s=s.replace('            if not gripping:\n', '            if not gripping and p.get(f"orient_{side}", 0.0) <= 0.001:\n',1)
p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
