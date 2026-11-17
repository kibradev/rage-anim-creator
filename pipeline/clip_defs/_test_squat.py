"""Test clip: hips go down/up and sway with planted feet, hands reach forward. Exercises set_root + IK."""
import math

FRAMES = 60


def build(arm, cl):
    c = cl.Clip(arm, "test_squat", FRAMES, fps=30, loop=True)
    for f in range(0, FRAMES + 1, 2):
        t = f / FRAMES
        down = 0.5 - 0.5 * math.cos(2 * math.pi * t)  # 0..1..0
        c.set_root(f, (0.08 * math.sin(2 * math.pi * t), 0, -0.30 * down))
        c.set(f, {"SKEL_Spine1": [("x", -20 * down)]})
    worst = c.plant_feet(range(0, FRAMES + 1))
    for f in range(0, FRAMES + 1, 2):
        t = f / FRAMES
        down = 0.5 - 0.5 * math.cos(2 * math.pi * t)
        for side in "LR":
            c.eval(f)
            sh = c.pos(c.ARMS[side][0])
            fw = c.forward()
            c.reach(f, side, sh + fw * (0.15 + 0.4 * down) + cl.Vector((0, 0, -0.45 + 0.4 * down)))
    print("TEST plant worst unreachable m", round(worst, 4))
    return c
