"""blender -b --python pipeline/render_video.py -- <ped> <prefix|clip,clip,...> [view]
Renders the latest version of every authored clip whose name starts with <prefix> (or is listed) to
cache/preview/video/<clip>.mp4 (H.264, 30 fps) so the motion can be watched without the web UI."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import bpy
from mathutils import Vector
from lib import ped as pedlib, clips as cliplib, render

cfg = json.loads((ROOT / "config.json").read_text())
a = sys.argv[sys.argv.index("--") + 1:]
ped, sel = a[0], a[1]
view = a[2] if len(a) > 2 else "34"
bpy.context.scene.render.fps = 30
pedlib.import_ped_parts(cfg["game_dir"], ped)
pedlib.clean_scene_extras()
arm = pedlib.merge_armatures()
pedlib.simplify_materials()

names = sel.split(",") if "," in sel else sorted(d.name for d in (ROOT / "output").iterdir() if d.name.startswith(sel) and (d / "meta.json").exists())
sc, cam = render._setup(400, 520)
fl = bpy.data.objects["preview_floor"]
fl.location = (0, 0, min((arm.matrix_world @ b.head_local).z for b in arm.data.bones if b.name.startswith("SKEL_")) - 0.02)
render._aim(cam, render.VIEWS[view], Vector((0, 0, fl.location.z + 1.25)), 3.0)
sc.render.image_settings.file_format = "FFMPEG"
sc.render.ffmpeg.format = "MPEG4"
sc.render.ffmpeg.codec = "H264"
sc.render.ffmpeg.constant_rate_factor = "MEDIUM"
sc.render.ffmpeg.gopsize = 15
if arm.animation_data is None:
    arm.animation_data_create()
for t in list(arm.animation_data.nla_tracks):
    arm.animation_data.nla_tracks.remove(t)
out_dir = ROOT / "cache" / "preview" / "video"
out_dir.mkdir(parents=True, exist_ok=True)
for name in names:
    meta = json.loads((ROOT / "output" / name / "meta.json").read_text("utf-8"))
    v = meta["versions"][-1]
    data = json.loads((ROOT / "output" / name / f"v{v['v']}.action.json").read_text("utf-8"))
    arm.animation_data.action = cliplib.LoadedClip(arm, f"{name}_vid", data["frames"], data["fps"], data["curves"]).action
    reps = 3 if v.get("loop") else 1
    sc.frame_start, sc.frame_end = 0, data["frames"]
    out = out_dir / f"{name}.mp4"
    sc.render.filepath = str(out)
    sc.render.use_file_extension = False
    bpy.ops.render.render(animation=True)
    print("VIDEO", out, out.stat().st_size, "frames", data["frames"], "loop", bool(v.get("loop")))
