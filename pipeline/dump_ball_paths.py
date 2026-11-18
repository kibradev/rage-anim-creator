"""blender -b --python pipeline/dump_ball_paths.py
Topu elde tutma klipleri için top merkezi yolunu (kare başına, ARMATÜR uzayı = glTF bone uzayı: x sağ, y ileri, z yukarı, zemin dahil) ve
oyundaki top konumu ofsetlerinin varsayılanını yazar: output/ball_paths.json. Web arayüzü bunu klibin oynatma zamanına göre canlı çizer.
Yol, önizleme topuyla ve oyun tablosuyla (HoldPath) aynı `ball_path` fonksiyonundan gelir."""
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
out = {"offset": {"hold": [0.0, 0.0, 0.0], "carry": [0.0, 0.0, 0.0]}, "radius": V.BALL_R, "clips": {}}
for name in V.HOLD_PROP:
    frames, loop, keys = V.CLIPS[name]()
    c = V.build(arm, cliplib, name)
    path = V.ball_path(name, keys, frames)
    out["clips"][name] = {"fps": 30, "frames": frames, "loop": loop, "floor": round(c.floor, 4), "style": "carry" if "carry" in name else "hold",
                          "p": [[round(p[0], 4), round(p[1], 4), round(c.floor + p[2], 4)] for p in path]}
# TASARIM EL KONUMLARI: topun merkezi ile el kemikleri arasındaki ilişki (karakter uzayı, zeminden) + bilek konumları. Oyunda top bu ilişkiyle
# gerçek el kemiklerini izler (VB.HandCal); /vbeller oyundaki gerçek konumları bununla karşılaştırır.
arm.animation_data_create()
cal = {}
for style, name in (("hold", "vb_hold"), ("carry", "vb_carry_L")):
    frames, loop, keys = V.CLIPS[name]()
    c = V.build(arm, cliplib, name)
    c.finish()
    arm.animation_data.action = c.action
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    P, W = arm.pose.bones, arm.matrix_world
    fl = c.floor
    def ch(v):
        return [round(v.x, 4), round(v.y, 4), round(v.z - fl, 4)]
    L, R = ch(W @ P["SKEL_L_Hand"].head), ch(W @ P["SKEL_R_Hand"].head)
    ref = [(L[i] + R[i]) / 2 for i in range(3)] if style == "hold" else L
    ball = list(V.ball_path(name, keys, frames)[0])
    cal[style] = {"cal": [round(ball[i] - ref[i], 4) for i in range(3)], "L": L, "R": R, "ball": [round(x, 4) for x in ball]}
out["hands"] = cal
(ROOT / "output" / "ball_paths.json").write_text(json.dumps(out), encoding="utf-8")
print("BALLPATHS", list(out["clips"]), {k: v["floor"] for k, v in out["clips"].items()})
