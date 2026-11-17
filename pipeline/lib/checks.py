"""Automatic motion checks on an action (run inside Blender). motion_report() returns numbers + human warnings.

Everything is measured in armature space on the evaluated pose, frame by frame:
- foot slide: horizontal travel of a foot while it is on the ground
- ground: how far a foot/toe goes below the rest-pose floor
- knees/elbows: bend angle and bending the wrong way (hyperextension)
- hands inside the torso
- loop seam: pose difference between first and last frame (rotation and root position)
"""
import math

import bpy
from mathutils import Vector

FEET = {"L": ("SKEL_L_Thigh", "SKEL_L_Calf", "SKEL_L_Foot", "SKEL_L_Toe0"), "R": ("SKEL_R_Thigh", "SKEL_R_Calf", "SKEL_R_Foot", "SKEL_R_Toe0")}
ARMS = {"L": ("SKEL_L_UpperArm", "SKEL_L_Forearm", "SKEL_L_Hand"), "R": ("SKEL_R_UpperArm", "SKEL_R_Forearm", "SKEL_R_Hand")}
GROUND_BAND = 0.03  # a foot within 3 cm of its rest height counts as planted


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length


def motion_report(arm, action, f0: int, f1: int, loop: bool = False) -> dict:
    sc = bpy.context.scene
    if arm.animation_data is None:
        arm.animation_data_create()
    prev_action = arm.animation_data.action
    arm.animation_data.action = action
    P, R = arm.pose.bones, arm.data.bones
    rest_z = {s: R[c[2]].head_local.z for s, c in FEET.items()}
    toe_rest_z = {s: R[c[3]].head_local.z for s, c in FEET.items()}

    slide = {"L": 0.0, "R": 0.0}
    slide_worst = (0.0, "", 0)
    below = (0.0, "", 0)
    bend_max = {}
    hyper = (0.0, "", 0)
    hand_in = (1e9, "", 0)
    last = {}
    first_pose, last_pose = None, None
    for f in range(int(f0), int(f1) + 1):
        sc.frame_set(f)
        pos = {b: P[b].matrix.translation.copy() for c in list(FEET.values()) + list(ARMS.values()) for b in c}
        pelvis_m = P["SKEL_Pelvis"].matrix.to_3x3() @ R["SKEL_Pelvis"].matrix_local.to_3x3().inverted()
        fwd = pelvis_m @ Vector((0, -1, 0))
        for s, (thigh, calf, foot, toe) in FEET.items():
            planted = pos[foot].z - rest_z[s] < GROUND_BAND
            if planted and last.get(s) is not None:
                step = (pos[foot].xy - last[s].xy).length
                slide[s] += step
                if step > slide_worst[0]:
                    slide_worst = (step, foot, f)
            last[s] = pos[foot].copy() if planted else None
            for b, rz in ((foot, rest_z[s]), (toe, toe_rest_z[s])):
                d = rz - pos[b].z
                if d > below[0]:
                    below = (d, b, f)
            # knee: bend angle, and knee must stay in front of the hip-ankle line
            u, l = pos[calf] - pos[thigh], pos[foot] - pos[calf]
            ang = math.degrees(u.angle(l, 0.0))
            bend_max[calf] = max(bend_max.get(calf, 0.0), ang)
            line = (pos[foot] - pos[thigh]).normalized()
            off = (pos[calf] - pos[thigh]) - line * (pos[calf] - pos[thigh]).dot(line)
            back = -off.dot(fwd)
            if ang > 12 and back > hyper[0]:
                hyper = (back, calf, f)
        spine_a, spine_b = P["SKEL_Spine0"].matrix.translation, P["SKEL_Spine3"].matrix.translation
        for s, (up, fore, hand) in ARMS.items():
            ang = math.degrees((pos[fore] - pos[up]).angle(pos[hand] - pos[fore], 0.0))
            bend_max[fore] = max(bend_max.get(fore, 0.0), ang)
            d = _seg_dist(pos[hand], spine_a, spine_b)
            if d < hand_in[0]:
                hand_in = (d, hand, f)
        if f == int(f0) or f == int(f1):
            snap = ({b.name: b.matrix.to_quaternion() for b in P if b.name.startswith("SKEL_")}, P["SKEL_ROOT"].matrix.translation.copy())
            if f == int(f0):
                first_pose = snap
            else:
                last_pose = snap
    arm.animation_data.action = prev_action

    seam_rot, seam_bone = 0.0, ""
    for b, q in first_pose[0].items():
        a = math.degrees(2 * math.acos(min(1.0, abs(q.dot(last_pose[0][b])))))
        if a > seam_rot:
            seam_rot, seam_bone = a, b
    seam_pos = (first_pose[1] - last_pose[1]).length

    rep = {
        "foot_slide_m": {s: round(v, 3) for s, v in slide.items()},
        "foot_slide_worst_step": (round(slide_worst[0], 4), slide_worst[1], slide_worst[2]),
        "below_ground_m": (round(below[0], 3), below[1], below[2]),
        "max_bend_deg": {b: round(v, 1) for b, v in bend_max.items()},
        "knee_backward_m": (round(hyper[0], 3), hyper[1], hyper[2]),
        "hand_to_spine_min_m": (round(hand_in[0], 3), hand_in[1], hand_in[2]),
        "seam_rot_deg": (round(seam_rot, 2), seam_bone), "seam_root_m": round(seam_pos, 4),
    }
    w = []
    for s, v in slide.items():
        if v > 0.05:
            w.append(f"ayak kayması {s}: yerdeyken toplam {v:.2f} m kaydı (en büyük adım kare {slide_worst[2]})")
    if below[0] > 0.02:
        w.append(f"yere girme: {below[1]} zeminin {below[0]*100:.0f} cm altında (kare {below[2]})")
    if hyper[0] > 0.03:
        w.append(f"diz ters bükülüyor: {hyper[1]} (kare {hyper[2]})")
    for b, v in bend_max.items():
        if v > 155:
            w.append(f"aşırı bükülme: {b} {v:.0f}° (sınır ~155°)")
    if hand_in[0] < 0.09:
        w.append(f"el gövdenin içinde: {hand_in[1]} omurgaya {hand_in[0]*100:.0f} cm (kare {hand_in[2]})")
    if loop and (seam_rot > 2 or seam_pos > 0.01):
        w.append(f"döngü kapanmıyor: {seam_bone} {seam_rot:.1f}°, kök {seam_pos*100:.1f} cm")
    rep["warnings"] = w
    return rep
