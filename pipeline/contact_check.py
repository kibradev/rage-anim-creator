"""blender -b --python pipeline/contact_check.py
Voleybol klipleri için GERÇEK el konumlarını temas karesinde ölçer ve volleyballScript'teki animtable.lua tahminleriyle karşılaştırır.
Karakter uzayı: x sağ, y ileri, z zeminden yükseklik (m). Çıktı: output/contact_check.json + konsol tablosu."""
import importlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from lib import ped as pedlib, clips as cliplib

cfg = json.loads((ROOT / "config.json").read_text())
bpy.context.scene.render.fps = 30
pedlib.import_ped_parts(cfg["game_dir"], "mp_m_freemode_01"); pedlib.clean_scene_extras(); arm = pedlib.merge_armatures()
V = importlib.import_module("clip_defs.volleyball")

lua = Path(r"C:\Users\kibra\Desktop\volleyballScript\resource\0r-volleyball\modules\shared\animtable.lua").read_text(encoding="utf-8")
table = {}
for m in re.finditer(r"(vb_\w+) = \{ kind = '(\w+)'.*?contactFrame = (\d+).*?point = \{ x = ([-\d.]+), y = ([-\d.]+), z = ([-\d.]+) \}", lua):
    table[m.group(1)] = dict(kind=m.group(2), frame=int(m.group(3)), x=float(m.group(4)), y=float(m.group(5)), z=float(m.group(6)))

sc = bpy.context.scene
ad = arm.animation_data or arm.animation_data_create()
out = {}
print("KLIP            kare  tablo(x,y,z)            ölçülen sağ el          sol el                  orta nokta              fark(orta-tablo)")
for name, t in table.items():
    c = V.build(arm, cliplib, name)
    c.finish()
    ad.action = c.action
    sc.frame_set(t["frame"])
    bpy.context.view_layer.update()
    floor = getattr(c, "floor", 0.0)
    def hp(b):
        w = arm.matrix_world @ arm.pose.bones[b].head
        return (w.x, w.y, w.z - floor)
    r, l = hp("SKEL_R_Hand"), hp("SKEL_L_Hand")
    mid = tuple((a + b) / 2 for a, b in zip(r, l))
    ref = r if t["kind"] in ("spike", "serve_over", "serve_under") else mid
    d = tuple(round(ref[i] - (t["x"], t["y"], t["z"])[i], 3) for i in range(3))
    out[name] = dict(table=[t["x"], t["y"], t["z"]], R=[round(v, 3) for v in r], L=[round(v, 3) for v in l], mid=[round(v, 3) for v in mid], diff=d, floor=floor)
    f = lambda v: "(%.2f,%.2f,%.2f)" % v
    print("%-15s %3d  %-22s %-22s %-22s %-22s %s" % (name, t["frame"], f((t["x"], t["y"], t["z"])), f(r), f(l), f(mid), d))
(ROOT / "output").mkdir(exist_ok=True)
(ROOT / "output" / "contact_check.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
