"""blender -b --python pipeline/export_ycd.py -- <ped> <clip_name> <version> [test]
Rebuilds the clip from output/<clip>/v<N>.action.json (exactly what was previewed), exports output/export/<clip>/<clip>.ycd(.xml) and verifies the round trip."""
import importlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from lib import ped as pedlib, clips as cliplib, export_ycd as ex

cfg = json.loads((ROOT / "config.json").read_text())
args = sys.argv[sys.argv.index("--") + 1:]
ped, name, version = args[0], args[1], int(args[2])
bpy.context.scene.render.fps = 30

pedlib.import_ped_parts(cfg["game_dir"], ped)
pedlib.clean_scene_extras()
arm = pedlib.merge_armatures()
data = json.loads((ROOT / "output" / name / f"v{version}.action.json").read_text("utf-8"))
clip = cliplib.LoadedClip(arm, name, data["frames"], data["fps"], data["curves"])
bones = sorted({fc.data_path.split('"')[1] for fc in clip.action.fcurves if fc.data_path.startswith("pose.bones")})

action = ex.complete_action(arm, clip)
dict_obj = ex.build_dict_objects(arm, clip, action)
dll = ROOT / "cache" / "converter" / "ycd2xml.dll"
out = ROOT / "output" / "export" / clip.name / f"v{version}"
if len(args) > 3 and args[3] == "test":  # file-level check only: does not count as an export (approval gate untouched)
    out = ROOT / "cache" / "rt" / "export_test" / clip.name
xml, ycd = ex.export_xml_and_binary(dict_obj, out, clip.name, dll)
worst, n_anims, n_clips = ex.verify_roundtrip(arm, clip, ycd, dll, ROOT / "cache" / "rt.ycd.xml", bones)
print("EXPORT", ycd, ycd.stat().st_size, "bytes; roundtrip anims", n_anims, "clips", n_clips, "max rotation error deg", round(worst, 4))
