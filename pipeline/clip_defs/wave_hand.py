"""Right-hand wave: arm lifts, forearm raised, hand sweeps side to side, arm lowers. Loops back to rest pose."""
import math

FRAMES = 90  # 3 s at 30 fps


def build(arm, cl, upper_deg=75, forearm_deg=85, sweep_deg=22, cycles=3):
    c = cl.Clip(arm, "wave_hand", FRAMES, fps=30, loop=False)
    bones = ["SKEL_R_Clavicle", "SKEL_R_UpperArm", "SKEL_R_Forearm", "SKEL_R_Hand", "SKEL_Head"]
    c.key_rest(0, bones)
    raise_end, lower_start = 18, FRAMES - 18

    def pose(ramp, sweep=0.0):
        return {
            "SKEL_R_Clavicle": [("y", 8 * ramp)],
            "SKEL_R_UpperArm": [("y", upper_deg * ramp)],
            "SKEL_R_Forearm": [("y", forearm_deg * ramp + sweep * 0.6)],
            "SKEL_R_Hand": [("y", sweep)],
            "SKEL_Head": [("z", 8 * ramp)],
        }

    c.set(raise_end, pose(1.0))
    n = int((lower_start - raise_end))
    for i in range(1, n):
        f = raise_end + i
        t = i / n
        c.set(f, pose(1.0, sweep_deg * math.sin(2 * math.pi * cycles * t)), interp="LINEAR" if False else "BEZIER")
    c.set(lower_start, pose(1.0))
    c.key_rest(FRAMES, bones)
    return c
