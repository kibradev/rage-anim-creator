"""blender -b --python pipeline/hold_attach.py
Top elde tutma klipleri için topun AVUÇ KEMİĞİNE (SKEL_R_Hand) göre sabit konumunu ölçer: oyunda top bu kemiğe tek bir ofsetle bağlanır
(AttachEntityToEntity). Her klipte/karede ofset aynı çıkmalı; çıkmazsa tutuş klipler arasında tutarsızdır ve top elden kayar.
Çıktı: output/hold_attach.json  { bone, tag, offset[x,y,z] (kemik yerel ekseni, m), samples{...}, max_dev_m }.
Not: ofset Blender kemik yerel ekseninde ölçülür; oyun kemik ekseni farklıysa oyunda /vbholdcal ile ince ayar yapılır."""
import importlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from lib import ped as pedlib, clips as cliplib

cfg = json.loads((ROOT / "config.json").read_text())
bpy.context.scene.render.fps = 30
pedlib.import_ped_parts(cfg["game_dir"], "mp_m_freemode_01"); pedlib.clean_scene_extras(); arm = pedlib.merge_armatures()
V = importlib.import_module("clip_defs.volleyball")
BONE, TAG = "SKEL_R_Hand", 57005
SAMPLES = [("vb_hold", 0), ("vb_hold", 15), ("vb_hold", 30), ("vb_pickup", 14), ("vb_pickup", 24), ("vb_pickup", 36), ("vb_pickup", 48),
           ("vb_hold_pass", 0), ("vb_hold_pass", 6), ("vb_hold_pass", 11)]
sc = bpy.context.scene
ad = arm.animation_data or arm.animation_data_create()
rows, built = {}, {}
for name, f in SAMPLES:
    if name not in built:
        c = V.build(arm, cliplib, name)
        c.finish()
        built[name] = (c, bpy.data.objects["vb_prop_ball"].animation_data.action)
    c, ball_action = built[name]
    ball = bpy.data.objects["vb_prop_ball"]
    ball.animation_data.action = ball_action           # bu klibin top animasyonu
    ad.action = c.action
    sc.frame_set(f)
    bpy.context.view_layer.update()
    m = arm.matrix_world @ arm.pose.bones[BONE].matrix
    local = m.inverted() @ ball.matrix_world.translation
    rows[f"{name}@{f}"] = [round(local.x, 4), round(local.y, 4), round(local.z, 4)]
    if f"{name}@{f}" == "vb_hold@0":
        for side in "LR":
            r = (arm.matrix_world @ arm.pose.bones[f"SKEL_{side}_Hand"].matrix).to_3x3()
            print("HANDROT", side, json.dumps([[round(r[i][j], 6) for j in range(3)] for i in range(3)]))
vals = list(rows.values())
mean = [sum(v[i] for v in vals) / len(vals) for i in range(3)]
dev = max(((v[0] - mean[0]) ** 2 + (v[1] - mean[1]) ** 2 + (v[2] - mean[2]) ** 2) ** 0.5 for v in vals)
out = {"bone": BONE, "tag": TAG, "offset": [round(x, 4) for x in mean], "samples": rows, "max_dev_m": round(dev, 4)}
(ROOT / "output").mkdir(exist_ok=True)
(ROOT / "output" / "hold_attach.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print("ATTACH", json.dumps(out))
