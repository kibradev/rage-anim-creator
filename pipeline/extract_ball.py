"""blender -b --python pipeline/extract_ball.py -- [ydr_yolu]
Voleybol topu .ydr (mapCreator çıktısı) -> cache/props/p_vb_volleyball.glb (web arayüzünde canlı önizleme için).
Sollumz ile içe aktarır (dokular ydr içinde / yanındaki ytd'den), çıktıda orijin = top merkezi. Web: /files/cache/props/p_vb_volleyball.glb"""
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
src = Path(a[0]) if a else ROOT.parent / "mapCreator" / "workspace" / "output" / "ball_build" / "export" / "voleybol_topu" / "stream" / "p_vb_volleyball.ydr"
out = ROOT / "cache" / "props" / "p_vb_volleyball.glb"
out.parent.mkdir(parents=True, exist_ok=True)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
res = bpy.ops.sollumz.import_assets(directory=str(src.parent), files=[{"name": src.name}])
meshes = [o for o in bpy.data.objects if o.type == "MESH" and "Bound" not in o.name and "col" not in o.name.lower()]
print("BALL meshes", [(o.name, len(o.data.vertices)) for o in meshes], "result", res)
for o in list(bpy.data.objects):
    if o not in meshes and o.type != "EMPTY" and o.type != "ARMATURE":
        bpy.data.objects.remove(o, do_unlink=True)
# yalnızca topun görsel mesh'ini dışa aktar
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
for o in meshes:
    xs = [v.co for v in o.data.vertices]
    print("BALL bbox", [round(min(c[i] for c in xs), 3) for i in range(3)], [round(max(c[i] for c in xs), 3) for i in range(3)])
bpy.ops.export_scene.gltf(filepath=str(out), use_selection=True, export_format="GLB", export_apply=True)
print("BALL_GLB", out, out.stat().st_size)
