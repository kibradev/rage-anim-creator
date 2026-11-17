"""Club groove: 4-beat in-place dance loop. Hips bounce on every beat and sway side to side over two beats,
feet stay planted, torso counter-twists, bent arms pump alternately in front of the chest, head nods."""
import math

FRAMES = 60  # 4 beats at 120 BPM, 30 fps
BEAT = 15


def build(arm, cl, bounce=0.07, sway=0.07, twist=10, arm_pump=0.10):
    c = cl.Clip(arm, "club_groove", FRAMES, fps=30, loop=True)
    V = cl.Vector
    fr = range(0, FRAMES + 1)

    def phase(f):
        t = f / FRAMES
        beat = 0.5 - 0.5 * math.cos(2 * math.pi * 4 * t)       # 0 on the beat-top, 1 at the dip (each beat)
        side = math.sin(2 * math.pi * 2 * t)                   # left/right, one full sway per 2 beats
        return beat, side

    # 1) hips and torso
    for f in fr:
        beat, side = phase(f)
        c.set_root(f, (sway * side, 0, -0.03 - bounce * beat), interp="LINEAR")
        c.set(f, {
            "SKEL_Pelvis": [("z", twist * side), ("y", 5 * side)],
            "SKEL_Spine1": [("x", 6 + 4 * beat), ("z", -twist * 0.8 * side)],
            "SKEL_Spine3": [("z", -twist * 0.6 * side), ("y", -4 * side)],
            "SKEL_Neck_1": [("z", twist * 0.5 * side)],
            "SKEL_Head": [("x", 7 * beat - 2)],
            "SKEL_L_Clavicle": [("y", 0)], "SKEL_R_Clavicle": [("y", 0)],
        }, interp="LINEAR")

    # 2) feet stay where they are in the rest pose
    c.plant_feet(fr)

    # 3) arms: hands in front of the chest, pumping up/down in opposite phase
    for f in fr:
        beat, side = phase(f)
        c.eval(f)
        fw = c.forward()
        right = V((fw.y, -fw.x, 0))
        chest = c.pos("SKEL_Spine3")
        for s, sign in (("L", -1), ("R", 1)):
            sh = c.pos(c.ARMS[s][0])
            out = 1 if (sh - chest).dot(right) > 0 else -1
            pump = arm_pump * sign * side + 0.03 * beat
            c.reach(f, s, sh + right * out * 0.06 + fw * 0.30 + V((0, 0, -0.20 + pump)))
            c.set(f, {c.ARMS[s][2]: [("x", 0)]}, interp="LINEAR")
    return c
