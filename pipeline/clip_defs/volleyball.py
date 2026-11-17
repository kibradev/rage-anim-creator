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
    """Overhead set (parmak pas): hands above the forehead, extend up through legs and arms."""
    load = {"root": (0, 0, -0.20), "spine": (6, 0, 0), "chest": (-6, 0, 0), "head": (-28, 0, 0),
            "hand_L": (-0.10, 0.20, 1.74), "hand_R": (0.10, 0.20, 1.74), "elbow_L": (-1, 0.3, -0.4), "elbow_R": (1, 0.3, -0.4),
            "wrist_L": (-35, 0, 0), "wrist_R": (-35, 0, 0)}
    push = {"root": (0, 0.03, 0.03), "pitch_L": 25, "pitch_R": 25, "foot_L": (-0.12, 0, 0.05), "foot_R": (0.12, 0, 0.05),
            "hand_L": (-0.12, 0.28, 1.94), "hand_R": (0.12, 0.28, 1.94), "wrist_L": (10, 0, 0), "wrist_R": (10, 0, 0), "ease": "in"}
    return 40, False, [(0, READY), (10, load), (16, push), (22, {**push, "ease": "smooth"}), (40, READY)]


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
    """Overhand float serve: toss with the left hand, right arm cocked, contact high in front."""
    stance = {"root": (0, 0.06, -0.05), "foot_L": (-0.10, 0.26, 0), "foot_R": (0.12, -0.10, 0), "spine": (6, 0, 0), "head": (-8, 0, 0),
              "hand_L": (-0.06, 0.40, 1.15), "elbow_L": (-0.7, -0.5, -0.6), "hand_R": (0.20, 0.22, 1.20)}
    toss = {"root": (0, 0.02, -0.03), "spine": (-4, 0, 0), "chest": (-8, 0, -28), "head": (-30, 0, 0),
            "hand_L": (-0.12, 0.30, 1.84), "elbow_L": (-1, 0, -0.5),
            "hand_R": (0.36, -0.14, 1.72), "elbow_R": (1, -0.6, 0.1), "wrist_R": (-20, 0, 0)}
    hit = {"root": (0, 0.14, 0.0), "spine": (8, 0, 0), "chest": (6, 0, 18), "head": (-18, 0, 0), "ease": "in",
           "hand_R": (0.14, 0.32, 1.96), "elbow_R": (1, -0.3, -0.2), "wrist_R": (0, 0, 0),
           "hand_L": (-0.20, 0.32, 1.18), "elbow_L": (-0.3, -0.8, -0.7)}
    follow = {"root": (0, 0.18, -0.06), "spine": (18, 0, 0), "chest": (8, 0, 26), "head": (-10, 0, 0), "ease": "out",
              "hand_R": (-0.04, 0.58, 1.02), "hand_L": (-0.26, 0.22, 0.98)}
    return 64, False, [(0, READY), (12, stance), (26, toss), (33, hit), (40, follow), (64, READY)]


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


CLIPS = {
    "vb_ready_idle": ready_idle, "vb_bump": bump, "vb_set": set_pass, "vb_serve_under": serve_under,
    "vb_serve_over": serve_over, "vb_spike": spike, "vb_block": block, "vb_dig_low": dig_low,
    "vb_dig_side_R": dig_side_R, "vb_dig_side_L": dig_side_L, "vb_shuffle_R": shuffle_R, "vb_shuffle_L": shuffle_L,
    "vb_celebrate": celebrate,
}


def build(arm, cl, variant):
    frames, loop, keys = CLIPS[variant]()
    c = cl.Clip(arm, variant, frames, fps=30, loop=loop)
    worst = pk.animate(c, keys)
    c.key_frames = [k[0] for k in keys]
    c.ik_unreachable = worst
    return c
