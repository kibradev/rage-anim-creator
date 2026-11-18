"""Volleyball animation set, authored as key poses (see lib/posekeys.py for the parameter meanings).
All clips are in place (the game script moves the ped) and start/end in the READY stance so they chain.

make_clip:  -- <ped> volleyball:all            every clip
            -- <ped> volleyball:vb_spike       one clip
"""
from lib import posekeys as pk

J = 0.035  # half distance between joined wrists (forearm pass platform)

READY = {
    "root": (0, 0, -0.14), "pelvis": (8, 0, 0), "spine": (16, 0, 0), "chest": (6, 0, 0), "head": (-16, 0, 0),
    "foot_L": (-0.12, 0, 0), "foot_R": (0.12, 0, 0), "pitch_L": 0, "pitch_R": 0,
    "hand_L": (-0.25, 0.38, 1.02), "hand_R": (0.25, 0.38, 1.02),
    "elbow_L": (-0.35, -0.8, -0.7), "elbow_R": (0.35, -0.8, -0.7),
    "neck": (0, 0, 0), "clav_L": (0, 0, 0), "clav_R": (0, 0, 0), "wrist_L": (0, 0, 0), "wrist_R": (0, 0, 0),
}


def mirror(keys):
    """Left/right mirrored copy of a key list."""
    out = []
    for f, p in keys:
        q = {}
        for k, v in p.items():
            nk = k[:-2] + ("_R" if k.endswith("_L") else "_L") if k.endswith(("_L", "_R")) else k
            if k == "ease" or isinstance(v, (int, float)):
                q[nk] = v
            elif k.split("_")[0] in ("root", "hand", "elbow", "foot"):
                q[nk] = (-v[0], v[1], v[2])
            else:  # rotations: forward lean stays, side bend and turn flip
                q[nk] = (v[0], -v[1], -v[2])
        out.append((f, q))
    return out


def ready_idle():
    a = {**READY}
    b = {"root": (0.02, 0, -0.17), "hand_L": (-0.22, 0.37, 0.93), "hand_R": (0.22, 0.37, 0.93), "spine": (17, 0, 0)}
    c = {"root": (-0.02, 0, -0.17), "hand_L": (-0.22, 0.37, 0.93), "hand_R": (0.22, 0.37, 0.93), "spine": (17, 0, 0)}
    return 60, True, [(0, a), (15, b), (30, {"root": (0, 0, -0.14), "spine": (16, 0, 0), "hand_L": READY["hand_L"], "hand_R": READY["hand_R"]}),
                      (45, c), (60, a)]


def bump():
    """Forearm pass (manşet): hands join low, legs and platform lift through the ball."""
    low = {"root": (0, 0.02, -0.27), "spine": (22, 0, 0), "hand_L": (-J, 0.42, 0.70), "hand_R": (J, 0.42, 0.70),
           "elbow_L": (-0.6, -0.2, -1), "elbow_R": (0.6, -0.2, -1), "head": (-18, 0, 0)}
    hit = {"root": (0, 0.05, -0.12), "spine": (14, 0, 0), "hand_L": (-J, 0.52, 0.98), "hand_R": (J, 0.52, 0.98), "ease": "in"}
    follow = {"root": (0, 0.05, -0.06), "spine": (10, 0, 0), "hand_L": (-J, 0.52, 1.10), "hand_R": (J, 0.52, 1.10), "ease": "out"}
    return 40, False, [(0, READY), (10, low), (16, hit), (21, follow), (40, READY)]


def set_pass():
    """Jump set (parmak pas): hands above the forehead, small jump, the ball is pushed up at the apex, soft landing.
    Hip +0.20 m (air ~0.4 s), knees come up in front (see _air)."""
    load = {"root": (0, 0, -0.24), "spine": (6, 0, 0), "chest": (-6, 0, 0), "head": (-28, 0, 0),
            "hand_L": (-0.10, 0.22, 1.65), "hand_R": (0.10, 0.22, 1.65), "elbow_L": (-1, 0.3, -0.4), "elbow_R": (1, 0.3, -0.4),
            "wrist_L": (-35, 0, 0), "wrist_R": (-35, 0, 0)}
    takeoff = {"root": (0, 0.02, 0.05), "pitch_L": 40, "pitch_R": 40, "foot_L": (-0.12, 0, 0.09), "foot_R": (0.12, 0, 0.09),
               "hand_L": (-0.10, 0.22, 1.86), "hand_R": (0.10, 0.22, 1.86), "ease": "in"}
    apex = {"root": (0, 0.04, 0.20), **_air(0.40, 0.12, 35),
            "hand_L": (-0.12, 0.28, 2.07), "hand_R": (0.12, 0.28, 2.07), "wrist_L": (10, 0, 0), "wrist_R": (10, 0, 0), "ease": "out"}
    down = {"root": (0, 0.04, 0.10), **_air(0.20, 0.06, 30), "hand_L": (-0.14, 0.28, 2.00), "hand_R": (0.14, 0.28, 2.00), "ease": "in"}
    touch = {"root": (0, 0.04, -0.02), **_GROUND, "hand_L": (-0.16, 0.26, 1.80), "hand_R": (0.16, 0.26, 1.80), "ease": "in"}
    land = {"root": (0, 0.02, -0.18), "spine": (12, 0, 0), "chest": (0, 0, 0), "head": (-18, 0, 0), "wrist_L": (0, 0, 0), "wrist_R": (0, 0, 0),
            "hand_L": (-0.22, 0.32, 1.30), "hand_R": (0.22, 0.32, 1.30), "ease": "out"}
    return 46, False, [(0, READY), (9, load), (13, takeoff), (18, apex), (21, down), (24, touch), (28, land), (46, READY)]


def serve_under():
    """Underhand serve: left foot forward, ball held in the left hand, right arm swings from behind."""
    stance = {"root": (0, 0.08, -0.10), "foot_L": (-0.10, 0.28, 0), "foot_R": (0.12, -0.10, 0), "spine": (14, 0, 0),
              "hand_L": (-0.02, 0.42, 0.92), "elbow_L": (-0.7, -0.5, -0.6), "hand_R": (0.26, 0.05, 0.84)}
    back = {"root": (0, 0.04, -0.16), "spine": (24, 0, 0), "chest": (6, 0, -18), "hand_R": (0.28, -0.30, 0.95),
            "elbow_R": (0.4, -1, 0.3)}
    hit = {"root": (0, 0.16, -0.10), "spine": (16, 0, 0), "chest": (6, 0, 10), "hand_R": (0.08, 0.46, 0.90), "ease": "in",
           "elbow_R": (0.6, -0.6, -0.6), "hand_L": (-0.20, 0.30, 0.92)}
    follow = {"root": (0, 0.18, -0.04), "spine": (8, 0, 0), "chest": (2, 0, 16), "hand_R": (0.06, 0.50, 1.36), "ease": "out",
              "hand_L": (-0.26, 0.10, 0.88)}
    return 54, False, [(0, READY), (10, stance), (22, back), (29, hit), (35, follow), (54, READY)]


def serve_over():
    """Jump float serve: toss with the left hand, crouch with the right arm cocked, jump, contact high in front at the
    apex, land on both feet. Hip +0.28 m (air ~0.48 s), knees come up in front (see _air)."""
    stance = {"root": (0, 0.06, -0.05), "foot_L": (-0.10, 0.26, 0), "foot_R": (0.12, -0.10, 0), "spine": (6, 0, 0), "head": (-8, 0, 0),
              "hand_L": (-0.06, 0.40, 1.15), "elbow_L": (-0.7, -0.5, -0.6), "hand_R": (0.20, 0.22, 1.20)}
    toss = {"root": (0, 0.04, -0.06), "spine": (-4, 0, 0), "chest": (-8, 0, -28), "head": (-30, 0, 0),
            "hand_L": (-0.12, 0.30, 1.84), "elbow_L": (-1, 0, -0.5),
            "hand_R": (0.36, -0.14, 1.72), "elbow_R": (1, -0.6, 0.1), "wrist_R": (-20, 0, 0)}
    crouch = {"root": (0, 0.04, -0.26), "spine": (14, 0, 0), "chest": (-4, 0, -24), "head": (-34, 0, 0),
              "hand_L": (-0.16, 0.34, 1.40), "hand_R": (0.34, -0.16, 1.40), "ease": "out"}
    takeoff = {"root": (0, 0.08, 0.05), "spine": (0, 0, 0), "chest": (-8, 0, -28), "pitch_L": 40, "pitch_R": 40,
               "foot_L": (-0.10, 0.26, 0.09), "foot_R": (0.12, -0.10, 0.09),
               "hand_L": (-0.14, 0.32, 1.78), "hand_R": (0.36, -0.14, 1.70), "ease": "in"}
    cock = {"root": (0, 0.10, 0.24), **_air(0.48, 0.20, 35), "spine": (-6, 0, 0), "chest": (-8, 0, -30), "head": (-28, 0, 0),
            "hand_L": (-0.14, 0.34, 2.04), "hand_R": (0.38, -0.16, 1.98), "elbow_R": (1, -0.6, 0.2), "wrist_R": (-20, 0, 0), "ease": "out"}
    hit = {"root": (0, 0.14, 0.28), **_air(0.52, 0.24, 35), "spine": (8, 0, 0), "chest": (6, 0, 18), "head": (-18, 0, 0), "ease": "out",
           "hand_R": (0.14, 0.34, 2.22), "elbow_R": (1, -0.3, -0.2), "wrist_R": (0, 0, 0),
           "hand_L": (-0.20, 0.32, 1.46), "elbow_L": (-0.3, -0.8, -0.7)}
    follow = {"root": (0, 0.16, 0.14), **_air(0.24, 0.18, 30), "spine": (16, 0, 0), "chest": (8, 0, 26), "head": (-10, 0, 0), "ease": "in",
              "hand_R": (-0.02, 0.56, 1.30), "hand_L": (-0.26, 0.22, 1.10)}
    touch = {"root": (0, 0.16, -0.02), **_GROUND, "spine": (18, 0, 0), "ease": "in"}
    land = {"root": (0, 0.16, -0.24), **_GROUND, "spine": (22, 0, 0), "chest": (4, 0, 10), "head": (-16, 0, 0),
            "hand_R": (-0.02, 0.54, 1.00), "hand_L": (-0.26, 0.24, 0.98), "ease": "out"}
    return 72, False, [(0, READY), (12, stance), (22, toss), (27, crouch), (31, takeoff), (35, cock), (38, hit), (42, follow),
                       (45, touch), (50, land), (72, READY)]


def _air(h, fwd=0.0, pitch=40):
    """Airborne feet: ankles h above their standing spot and `fwd` metres in FRONT of it. Measured in game (/vbspace): GTA's
    own jump lifts the hip only ~0.25 m but the feet ~0.7 m -- the leg tuck is what reads as a jump. The tuck must be a
    HIP flexion (thigh swings forward/up, knee in front, foot under or ahead of the hip), as in Rockstar's jumps
    (legprobe: thigh 50-120 deg forward, foot +0.1..+0.5 m ahead of the hip). Feet folded BEHIND a vertical thigh
    (heels to the backside) is not a pose GTA peds make."""
    return {"foot_L": (-0.12, fwd, h), "foot_R": (0.12, fwd, h), "pitch_L": pitch, "pitch_R": pitch}


_GROUND = {"foot_L": (-0.12, 0, 0), "foot_R": (0.12, 0, 0), "pitch_L": 0, "pitch_R": 0}


def spike():
    """Spike (smaç): fast deep crouch with arms back, explosive takeoff, knees tuck up behind while the body bows, hit at
    the apex, legs reach down, land soft. Air time ~0.57 s (hip +0.38 m, free fall), knees come up in front, feet ~0.6 m."""
    crouch = {"root": (0, -0.02, -0.38), "spine": (36, 0, 0), "head": (-28, 0, 0),
              "hand_L": (-0.30, -0.26, 0.92), "hand_R": (0.30, -0.26, 0.92), "elbow_L": (-0.6, -0.4, 1), "elbow_R": (0.6, -0.4, 1)}
    takeoff = {"root": (0, 0.04, 0.06), "spine": (6, 0, 0), "pitch_L": 42, "pitch_R": 42, "foot_L": (-0.12, 0, 0.10), "foot_R": (0.12, 0, 0.10),
               "hand_L": (-0.30, 0.46, 1.50), "hand_R": (0.30, 0.46, 1.48), "elbow_L": (-0.5, -0.7, -0.6), "elbow_R": (0.5, -0.7, -0.6), "ease": "in"}
    bow = {"root": (0, 0.10, 0.30), **_air(0.50, 0.20, 40), "spine": (-14, 0, 0), "chest": (-10, 0, -30), "head": (-22, 0, 0),
           "hand_L": (-0.14, 0.34, 2.16), "elbow_L": (-1, 0, -0.5),
           "hand_R": (0.38, -0.20, 2.06), "elbow_R": (1, -0.6, 0.2), "wrist_R": (-25, 0, 0), "ease": "out"}
    hit = {"root": (0, 0.14, 0.38), **_air(0.60, 0.26, 35), "spine": (12, 0, 0), "chest": (8, 0, 22), "head": (-14, 0, 0), "ease": "out",
           "hand_R": (0.14, 0.36, 2.30), "elbow_R": (1, -0.3, -0.2), "wrist_R": (20, 0, 0),
           "hand_L": (-0.22, 0.30, 1.58), "elbow_L": (-0.3, -0.8, -0.7)}
    follow = {"root": (0, 0.16, 0.24), **_air(0.30, 0.20, 30), "spine": (22, 0, 0), "chest": (10, 0, 30), "ease": "in",
              "hand_R": (-0.06, 0.56, 1.30), "wrist_R": (0, 0, 0), "hand_L": (-0.30, 0.16, 1.20)}
    touch = {"root": (0, 0.16, -0.02), **_GROUND, "spine": (20, 0, 0), "ease": "in"}
    land = {"root": (0, 0.16, -0.32), **_GROUND, "spine": (28, 0, 0), "chest": (6, 0, 0), "head": (-20, 0, 0),
            "hand_L": (-0.26, 0.36, 0.95), "hand_R": (0.26, 0.36, 0.95), "elbow_R": (0.35, -0.8, -0.7), "elbow_L": (-0.35, -0.8, -0.7), "ease": "out"}
    return 72, False, [(0, READY), (10, crouch), (16, takeoff), (21, bow), (25, hit), (29, follow), (33, touch), (38, land), (72, READY)]


def block():
    """Block: quick crouch, jump with both arms pressing over the net, knees come up in front in the air, soft
    landing. Air time ~0.5 s (hip +0.32 m), feet up to ~0.6 m."""
    hands_up = {"hand_L": (-0.20, 0.24, 1.45), "hand_R": (0.20, 0.24, 1.45), "elbow_L": (-1, -0.2, -0.6), "elbow_R": (1, -0.2, -0.6)}
    crouch = {"root": (0, 0, -0.30), "spine": (14, 0, 0), **hands_up}
    takeoff = {"root": (0, 0, 0.05), "spine": (2, 0, 0), "pitch_L": 42, "pitch_R": 42, "foot_L": (-0.12, 0, 0.10), "foot_R": (0.12, 0, 0.10),
               "hand_L": (-0.18, 0.22, 1.86), "hand_R": (0.18, 0.22, 1.86), "ease": "in"}
    apex = {"root": (0, 0.02, 0.32), **_air(0.54, 0.16, 35), "spine": (4, 0, 0), "chest": (4, 0, 0), "head": (-6, 0, 0),
            "hand_L": (-0.16, 0.28, 2.18), "hand_R": (0.16, 0.28, 2.18), "wrist_L": (25, 0, 0), "wrist_R": (25, 0, 0), "ease": "out"}
    down = {"root": (0, 0.02, 0.20), **_air(0.28, 0.08, 30), "hand_L": (-0.17, 0.27, 2.02), "hand_R": (0.17, 0.27, 2.02), "ease": "in"}
    touch = {"root": (0, 0, -0.02), **_GROUND, "hand_L": (-0.18, 0.26, 1.72), "hand_R": (0.18, 0.26, 1.72), "wrist_L": (10, 0, 0), "wrist_R": (10, 0, 0), "ease": "in"}
    land = {"root": (0, 0, -0.26), **_GROUND, "spine": (16, 0, 0),
            **hands_up, "wrist_L": (0, 0, 0), "wrist_R": (0, 0, 0), "ease": "out"}
    return 56, False, [(0, READY), (8, crouch), (12, takeoff), (19, apex), (23, down), (27, touch), (32, land), (56, READY)]


def dig_low():
    """Low dig: deep squat, platform close to the floor in front, lift through the ball."""
    low = {"root": (0, 0.10, -0.46), "foot_L": (-0.24, 0, 0), "foot_R": (0.24, 0.10, 0), "spine": (36, 0, 0), "head": (-30, 0, 0),
           "hand_L": (-J, 0.54, 0.50), "hand_R": (J, 0.54, 0.50), "elbow_L": (-0.6, -0.2, -1), "elbow_R": (0.6, -0.2, -1)}
    lift = {"root": (0, 0.10, -0.38), "spine": (30, 0, 0), "hand_L": (-J, 0.60, 0.72), "hand_R": (J, 0.60, 0.72), "ease": "in"}
    return 46, False, [(0, READY), (12, low), (18, lift), (24, {**lift, "ease": "smooth"}), (46, READY)]


def dig_side_R():
    """Side dig to the right. The hip never moves sideways (root x = 0): sideways hip travel is the one thing no other
    clip does; the lunge comes from a wide step + lean (pelvis/spine roll) instead."""
    step = {"root": (0, 0, -0.20), "foot_R": (0.40, 0.06, 0.09), "pitch_R": -10, "pelvis": (8, -6, 0)}
    low = {"root": (0, 0.04, -0.36), "foot_R": (0.46, 0.06, 0), "pitch_R": 0, "pelvis": (8, -12, 0), "spine": (26, -8, 0), "chest": (6, -16, -10), "head": (-22, 0, 0),
           "hand_L": (0.30 - J, 0.36, 0.58), "hand_R": (0.30 + J, 0.36, 0.58), "elbow_L": (-0.4, -0.3, -1), "elbow_R": (0.8, -0.3, -1), "ease": "out"}
    lift = {"root": (0, 0.04, -0.32), "hand_L": (0.32 - J, 0.38, 0.80), "hand_R": (0.32 + J, 0.38, 0.80), "ease": "in"}
    up = {"root": (0, 0.02, -0.28), "foot_R": (0.46, 0.06, 0.07), "ease": "in"}
    back = {"root": (0, 0, -0.18), "foot_R": (0.14, 0, 0.08), "pelvis": (8, 0, 0), "chest": (6, 0, 0), "spine": (18, 0, 0),
            "hand_L": (-0.10, 0.36, 0.92), "hand_R": (0.30, 0.36, 0.92)}
    return 52, False, [(0, READY), (6, step), (13, low), (19, lift), (24, {**lift, "ease": "smooth"}), (28, up), (40, back), (52, READY)]


def dig_side_L():
    f, loop, keys = dig_side_R()
    return f, loop, mirror(keys)


def shuffle_R():
    """Side shuffle to the right, in place (treadmill): right foot reaches out in the air while the left pushes."""
    a = {**READY, "root": (0, 0, -0.16), "foot_L": (-0.12, 0, 0), "foot_R": (0.12, 0, 0)}
    b = {"root": (0, 0, -0.12), "foot_R": (0.22, 0, 0.07), "foot_L": (-0.22, 0, 0), "ease": "lin", "glide": 1}
    c = {"root": (0, 0, -0.18), "foot_R": (0.32, 0, 0), "foot_L": (-0.32, 0, 0), "ease": "lin", "glide": 1}
    d = {"root": (0, 0, -0.12), "foot_R": (0.22, 0, 0), "foot_L": (-0.22, 0, 0.07), "ease": "lin", "glide": 1}
    return 20, True, [(0, a), (5, b), (10, c), (15, d), (20, {**a, "ease": "lin", "glide": 1})]


def shuffle_L():
    f, loop, keys = shuffle_R()
    return f, loop, mirror(keys)


def celebrate():
    """Point won: small jump with both fists up, land, right fist pump."""
    crouch = {"root": (0, 0, -0.26), "spine": (20, 0, 0), "hand_L": (-0.24, 0.20, 0.95), "hand_R": (0.24, 0.20, 0.95)}
    takeoff = {"root": (0, 0, 0.04), "pitch_L": 40, "pitch_R": 40, "foot_L": (-0.12, 0, 0.09), "foot_R": (0.12, 0, 0.09), "spine": (6, 0, 0),
               "hand_L": (-0.28, 0.16, 1.60), "hand_R": (0.28, 0.16, 1.60), "ease": "in"}
    up = {"root": (0, 0, 0.24), **_air(0.46, 0.14, 35), "spine": (-6, 0, 0), "chest": (-8, 0, 0), "head": (-20, 0, 0),
          "hand_L": (-0.32, 0.10, 1.96), "hand_R": (0.32, 0.10, 1.96), "elbow_L": (-1, -0.3, -0.3), "elbow_R": (1, -0.3, -0.3), "ease": "out"}
    down = {"root": (0, 0, 0.12), **_air(0.22, 0.06, 30), "ease": "in"}
    land = {"root": (0, 0, -0.20), **_GROUND, "spine": (14, 0, 0), "chest": (0, 0, 0),
            "hand_L": (-0.26, 0.16, 1.05), "hand_R": (0.24, 0.26, 1.55), "elbow_R": (0.35, -0.8, -0.7), "elbow_L": (-0.35, -0.8, -0.7), "ease": "out"}
    pump = {"root": (0, 0, -0.22), "spine": (20, 0, 0), "chest": (4, 0, 12), "hand_R": (0.20, 0.30, 1.18), "ease": "in"}
    hold = {"root": (0, 0, -0.10), "spine": (10, 0, 0), "chest": (0, 0, 0), "hand_R": (0.24, 0.22, 1.50), "ease": "out"}
    return 70, False, [(0, READY), (8, crouch), (12, takeoff), (17, up), (21, down), (26, land), (34, pump), (42, hold), (48, pump), (56, hold), (70, READY)]


# ---------------------------------------------------------------------------------------------------- TOPU ELDE TUTMA
# İki elle tutuş: bilekler topun iki yanında; top merkezi = bileklerin ortası + GRIP (karakter uzayı). Tüm hold klipleri AYNI tutuşu korur
# (oyunda top tek bir kemiğe, aynı ofsetle bağlanır; tutuş değişirse top elden kayar).
BALL_R = 0.105
GRIP = (0.0, 0.06, -0.03)
# Referans el yönleri (armatür uzayı 3x3), `vb_hold` doğal tutuş pozunda ölçüldü (pipeline/hold_attach.py). Tutuş ağırlığı > 0 olan karelerde
# el bu yöne kilitlenir.
GRIP_ROT = {
    "L": [[0.45829, -0.046429, 0.887583], [0.864321, 0.255423, -0.433058], [-0.206547, 0.965818, 0.157192]],
    "R": [[-0.458335, 0.046432, 0.887571], [0.86442, 0.255405, 0.433042], [-0.206577, 0.965725, -0.1572]],
}
REST = {"root": (0, 0, 0), "pelvis": (0, 0, 0), "spine": (0, 0, 0), "chest": (0, 0, 0), "head": (0, 0, 0),
        "hand_L": (-0.25, 0.04, 0.90), "hand_R": (0.25, 0.04, 0.90), "elbow_L": (-0.5, -1.0, -0.6), "elbow_R": (0.5, -1.0, -0.6),
        "wrist_L": (0, 0, 0), "wrist_R": (0, 0, 0), "foot_L": (-0.10, 0, 0), "foot_R": (0.10, 0, 0), "pitch_L": 0, "pitch_R": 0,
        "grip": 0.0}
WRIST_L, WRIST_R = (0, 0, 0), (0, 0, 0)           # avuç içlerini topa çevirmek için (önizlemede ayarlanır)
HOLD_POSE = {**REST, "root": (0, 0, -0.02), "spine": (6, 0, 0), "chest": (2, 0, 0), "head": (-6, 0, 0),
             "hand_L": (-0.12, 0.30, 1.08), "hand_R": (0.12, 0.30, 1.08),
             "elbow_L": (-0.6, -0.5, -1), "elbow_R": (0.6, -0.5, -1), "wrist_L": WRIST_L, "wrist_R": WRIST_R, "grip": 1.0}


def hold():
    """Topu iki elle göğüs önünde tutma: nefes alma kadar hafif hareketli DÖNGÜ (yürürken üst vücut katmanı olarak oynatılır)."""
    breathe = {**HOLD_POSE, "root": (0, 0, -0.035), "chest": (3, 0, 0), "hand_L": (-0.12, 0.30, 1.095), "hand_R": (0.12, 0.30, 1.095)}
    return 60, True, [(0, HOLD_POSE), (30, breathe), (60, HOLD_POSE)]


def pickup():
    """Yerdeki topu al: eğil, iki elle yanlardan kavra (kare 14 = KAVRAMA, top eve bağlanır), doğrul, tutuş pozuna gel."""
    reach = {**REST, "root": (0, 0.12, -0.54), "pelvis": (12, 0, 0), "spine": (60, 0, 0), "chest": (6, 0, 0), "head": (-32, 0, 0),
             "hand_L": (-0.115, 0.40, 0.17), "hand_R": (0.115, 0.40, 0.17),
             "elbow_L": (-0.5, -0.3, -1), "elbow_R": (0.5, -0.3, -1), "wrist_L": WRIST_L, "wrist_R": WRIST_R,
             "foot_L": (-0.10, 0, 0), "foot_R": (0.10, 0, 0), "grip": 1.0}
    rise = {**reach, "root": (0, 0.06, -0.22), "spine": (22, 0, 0), "pelvis": (4, 0, 0), "head": (-14, 0, 0),
            "hand_L": (-0.12, 0.38, 0.72), "hand_R": (0.12, 0.38, 0.72), "ease": "out"}
    down = {**reach, "root": (0, 0.08, -0.28), "spine": (28, 0, 0), "pelvis": (5, 0, 0), "head": (-16, 0, 0),
            "hand_L": (-0.12, 0.34, 0.55), "hand_R": (0.12, 0.34, 0.55), "grip": 0.35}
    return 48, False, [(0, REST), (5, down), (10, {**reach, "ease": "out"}), (14, reach), (28, rise), (42, {**HOLD_POSE, "ease": "out"}), (48, HOLD_POSE)]


def hold_pass():
    """Tutarken pas (alttan itiş): hafif çömel, kollar ileri-yukarı uzanırken BIRAKMA (kare 11), kollar gevşeyerek dinlenir."""
    wind = {**HOLD_POSE, "root": (0, 0, -0.16), "spine": (14, 0, 0), "hand_L": (-0.12, 0.26, 0.80), "hand_R": (0.12, 0.26, 0.80)}
    rel = {**HOLD_POSE, "root": (0, 0.10, -0.04), "spine": (9, 0, 0), "chest": (0, 0, 0),
           "hand_L": (-0.12, 0.50, 1.06), "hand_R": (0.12, 0.50, 1.06), "ease": "in"}
    follow = {**rel, "root": (0, 0.12, -0.04), "hand_L": (-0.14, 0.55, 1.10), "hand_R": (0.14, 0.55, 1.10), "head": (-2, 0, 0), "grip": 0.4, "ease": "out"}
    return 32, False, [(0, HOLD_POSE), (6, wind), (11, rel), (16, follow), (32, REST)]


# Topu SOL KOLTUK ALTINDA taşıma: top gövdenin solunda kaburga hizasında, sol önkol ve el topun önünden sarar, sağ kol serbest.
# Top merkezi karakter uzayında sabit (oyunda top gövdeye/ele bu ofsetle bağlanır).
CARRY_BALL = (-0.20, 0.02, 1.10)
CARRY_POSE = {**REST, "root": (0, 0, -0.02), "spine": (3, 0, 0), "chest": (1, 5, 0), "head": (-4, 0, 0),
              "hand_L": (-0.27, 0.13, 1.12), "elbow_L": (-0.45, -1.0, -0.35), "clav_L": (0, 0, 0),
              "hand_R": (0.26, 0.03, 0.88), "elbow_R": (0.5, -1.0, -0.6), "grip": 0.0}


def carry_L():
    """Top sol koltuk altında, ayakta duruş: nefes kadar hafif hareketli DÖNGÜ (yürürken üst vücut katmanı)."""
    breathe = {**CARRY_POSE, "root": (0, 0, -0.035), "chest": (2, 5, 0), "hand_R": (0.26, 0.05, 0.89)}
    return 60, True, [(0, CARRY_POSE), (30, breathe), (60, CARRY_POSE)]


def carry_tuck_L():
    """İki elle göğüs önünde tutuştan topu çabucak sol koltuk altına sıkıştır (kare 12 = sıkıştı), sağ kol serbest kalır."""
    pull = {**HOLD_POSE, "root": (0, 0, -0.04), "chest": (2, 3, 0),
            "hand_L": (-0.19, 0.24, 1.12), "hand_R": (0.06, 0.32, 1.05), "grip": 0.0, "ease": "in"}
    tuck = {**CARRY_POSE, "root": (0, 0, -0.05), "ease": "out"}
    return 18, False, [(0, {**HOLD_POSE, "grip": 0.0}), (5, pull), (12, tuck), (18, CARRY_POSE)]


# klip -> (top klibi bırakılan/alınan kare, top eve ne zaman bağlı): önizleme topu için
HOLD_PROP = {"vb_hold": ("all", None), "vb_pickup": ("from", 14), "vb_hold_pass": ("until", 11),
             "vb_carry_L": ("fixed", None), "vb_carry_tuck_L": ("tuck", (4, 12))}


def ball_path(variant, keys, frames):
    """Topun karakter uzayındaki merkezi (x sağ, y ileri, z zeminden), kare 0..frames. Blender gerektirmez (önizleme topu ve
    oyun tablosu `tools/gen_animtable.py` aynı fonksiyonu kullanır)."""
    spec = HOLD_PROP.get(variant)
    if spec is None:
        return []
    mode, at = spec
    filled = pk._filled(keys)

    def center(f):
        pz = pk.pose_at(filled, f)
        hl, hr = pz["hand_L"], pz["hand_R"]
        return tuple((hl[i] + hr[i]) / 2.0 + GRIP[i] for i in range(3))

    out = []
    for f in range(0, frames + 1):
        if mode == "fixed":
            c = CARRY_BALL
        elif mode == "tuck":
            a, b = at
            t = min(max((f - a) / float(b - a), 0.0), 1.0)
            t = t * t * (3 - 2 * t)
            c0 = center(a)
            c = tuple(c0[i] + (CARRY_BALL[i] - c0[i]) * t for i in range(3))
        elif mode == "from" and f < at:
            c = center(at)
            c = (c[0], c[1], BALL_R)                       # grab kareden önce top yerde
        elif mode == "until" and f > at:
            c0, k = center(at), f - at                      # bıraktıktan sonra: ileri/yukarı süzülür (yalnızca görsel)
            c = (c0[0], c0[1] + 0.045 * k, c0[2] + 0.05 * k - 0.0035 * k * k)
        else:
            c = center(f)
        out.append(c)
    return out


def _prop_ball(arm, clip, variant, keys):
    """Önizleme için top küresi: ellerin tuttuğu yerde. Yalnızca bu klipler için görünür; yoksa gizlenir. (GLB ve .ycd'ye girmez.)"""
    import bpy
    ob = bpy.data.objects.get("vb_prop_ball")
    if ob is None:
        me = bpy.data.meshes.new("vb_prop_ball")
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=BALL_R)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("vb_prop_ball", me)
        bpy.context.scene.collection.objects.link(ob)
        mat = bpy.data.materials.new("vb_prop_ball")
        mat.diffuse_color = (0.95, 0.78, 0.12, 1.0)
        me.materials.append(mat)
        ob.color = (0.95, 0.78, 0.12, 1.0)
    if ob.animation_data:
        ob.animation_data_clear()
    spec = HOLD_PROP.get(variant)
    ob.hide_render = ob.hide_viewport = spec is None
    if spec is None:
        return
    mode, at = spec
    floor = clip.floor
    path = ball_path(variant, keys, clip.frames)
    for f, c in enumerate(path):
        ob.location = (c[0], c[1], floor + c[2])
        ob.keyframe_insert("location", frame=f)


CLIPS = {
    "vb_ready_idle": ready_idle, "vb_bump": bump, "vb_set": set_pass, "vb_serve_under": serve_under,
    "vb_serve_over": serve_over, "vb_spike": spike, "vb_block": block, "vb_dig_low": dig_low,
    "vb_dig_side_R": dig_side_R, "vb_dig_side_L": dig_side_L, "vb_shuffle_R": shuffle_R, "vb_shuffle_L": shuffle_L,
    "vb_celebrate": celebrate, "vb_hold": hold, "vb_pickup": pickup, "vb_hold_pass": hold_pass,
    "vb_carry_L": carry_L, "vb_carry_tuck_L": carry_tuck_L,
}


def build(arm, cl, variant):
    frames, loop, keys = CLIPS[variant]()
    c = cl.Clip(arm, variant, frames, fps=30, loop=loop)
    try:
        from mathutils import Matrix
        c.grip_rot = {k: Matrix(v) for k, v in GRIP_ROT.items()}
    except (ImportError, TypeError):
        pass
    worst = pk.animate(c, keys)
    c.key_frames = [k[0] for k in keys]
    c.ik_unreachable = worst
    try:
        _prop_ball(arm, c, variant, keys)      # yalnız Blender içinde (bpy); gen_animtable.py bunu çağırmaz
    except ImportError:
        pass
    return c
