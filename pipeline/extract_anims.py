"""blender -b --python pipeline/extract_anims.py -- <ped> <dict_name>...
Needs cache/ycdxml/<dict>.ycd.xml (made by converter/ycd2xml). Writes cache/anims/<dict>.glb and updates cache/anims/index.json."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from lib import ped as pedlib, anims as animlib

cfg = json.loads((ROOT / "config.json").read_text())
args = sys.argv[sys.argv.index("--") + 1:]
ped, dicts = args[0], args[1:]
if len(dicts) == 1 and dicts[0].startswith('@'):  # @file: one dict name per line
    dicts = [l.strip() for l in Path(dicts[0][1:]).read_text('utf-8').splitlines() if l.strip()]
bpy.context.scene.render.fps = 30

pedlib.import_ped_parts(cfg["game_dir"], ped)
pedlib.clean_scene_extras()
arm = pedlib.merge_armatures()
print("ANIM armature", arm.name, len(arm.data.bones))

out_dir = ROOT / "cache" / "anims"
out_dir.mkdir(parents=True, exist_ok=True)
index_path = out_dir / "index.json"
index = json.loads(index_path.read_text("utf-8")) if index_path.exists() else []

for d in dicts:
    xml = ROOT / "cache" / "ycdxml" / f"{d}.ycd.xml"
    dict_obj, anims, clips = animlib.import_dict(str(xml))
    animlib.retarget_to(arm, anims)
    meta, skipped = animlib.bake_clips_to_nla(arm, clips)
    print("ANIM", d, "animations", len(anims), "clips", len(clips), "baked", len(meta), "skipped", skipped)
    glb = out_dir / f"{d}.glb"
    animlib.export_armature_glb(arm, str(glb))
    index = [e for e in index if e["dict"] != d]
    for m in meta:
        index.append({"dict": d, "name": m["name"], "duration": m["duration"], "fps": m["fps"],
                      "url": f"/files/cache/anims/{d}.glb"})
    animlib.clear_dict(dict_obj, anims)
index_path.write_text(json.dumps(index, indent=1), "utf-8")
print("ANIM done", len(index))
