"""Headless preview renders so the author (AI) can look at a clip: contact sheet of frames x views (run inside Blender)."""
import math
import os
import tempfile

import bpy
import numpy as np
from mathutils import Vector

# camera position direction (armature space) per view; clips face +Y after the game_facing root yaw
VIEWS = {"front": Vector((0, 1, 0)), "side": Vector((1, 0, 0)), "back": Vector((0, -1, 0)), "top": Vector((0, 0.001, 1)),
         "34": Vector((0.7, 0.7, 0.25))}


def _setup(cell_w, cell_h):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = cell_w, cell_h, 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    if sc.world is None:
        sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0.16, 0.17, 0.19)
    cam = bpy.data.objects.get("preview_cam")
    if cam is None:
        cam = bpy.data.objects.new("preview_cam", bpy.data.cameras.new("preview_cam"))
        sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    sc.camera = cam
    if bpy.data.objects.get("preview_floor") is None:  # ground reference at z=0 of the armature
        me = bpy.data.meshes.new("preview_floor")
        s = 1.2
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        fl = bpy.data.objects.new("preview_floor", me)
        sc.collection.objects.link(fl)
    return sc, cam


def _aim(cam, direction: Vector, center: Vector, height: float):
    d = direction.normalized()
    cam.location = center + d * 6.0
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = height


def render_sheet(arm, action, frames, out_png, views=("front", "side"), cell=(300, 420), floor_z=None, follow=True):
    """Rows = views, columns = frames. `follow` keeps the camera centred on the pelvis (in-place look)."""
    sc, cam = _setup(*cell)
    if arm.animation_data is None:
        arm.animation_data_create()
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)
    arm.animation_data.action = action
    fl = bpy.data.objects["preview_floor"]
    rest_low = min((arm.matrix_world @ b.head_local).z for b in arm.data.bones if b.name.startswith("SKEL_"))
    fl.location = (0, 0, rest_low - 0.02 if floor_z is None else floor_z)
    tmp = tempfile.mkdtemp()
    rows = []
    for v in views:
        cells = []
        for f in frames:
            sc.frame_set(int(f), subframe=f - int(f))
            pelvis = arm.matrix_world @ arm.pose.bones["SKEL_Pelvis"].head
            center = Vector((pelvis.x, pelvis.y, fl.location.z + 1.0)) if follow else Vector((0, 0, fl.location.z + 1.0))
            fl.location.x, fl.location.y = (center.x, center.y) if follow else (0, 0)
            _aim(cam, VIEWS[v], center, 2.3 if v != "top" else 2.3)
            sc.render.filepath = os.path.join(tmp, f"{v}_{f}.png")
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(sc.render.filepath)
            px = np.array(img.pixels[:], dtype=np.float32).reshape(cell[1], cell[0], 4)
            bpy.data.images.remove(img)
            px[:3, :, :3] = 1.0  # thin separators
            px[:, :2, :3] = 0.0
            cells.append(px)
        rows.append(np.concatenate(cells, axis=1))
    sheet = np.concatenate(rows[::-1], axis=0)  # image origin is bottom-left; first view on top
    out = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True)
    out.pixels = sheet.ravel()
    out.filepath_raw = str(out_png)
    out.file_format = "PNG"
    os.makedirs(os.path.dirname(str(out_png)), exist_ok=True)
    out.save()
    bpy.data.images.remove(out)
    arm.animation_data.action = None
    return str(out_png)
