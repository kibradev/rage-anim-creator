"""Ped import helpers (run inside Blender with Sollumz enabled).

Parametric functions only: import_ped_parts(), bake_simple_materials(), export_glb().
"""
import re
import bpy
from szio import VPath

DEFAULT_COMPONENTS = ("head", "uppr", "lowr", "hand", "feet", "teef", "hair")


def find_ped_dir(game_dir: str, ped: str) -> VPath:
    """Locate the streamed ped folder (<rpf>/<ped>/) inside the game archives."""
    for rpf in (
        "x64v.rpf/models/cdimages/streamedpeds_players.rpf",
        "x64v.rpf/models/cdimages/streamedpeds_mp.rpf",
        "x64v.rpf/models/cdimages/streamedpeds.rpf",
    ):
        d = VPath(f"{game_dir}/{rpf}/{ped}")
        if d.is_dir():
            return d
    raise FileNotFoundError(f"ped folder not found: {ped}")


def pick_parts(ped_dir: VPath, components=DEFAULT_COMPONENTS, drawable_index="000", tex_variant="a"):
    """Return (ytd_names, ydd_names) for the given components, base variant."""
    names = [f.name for f in ped_dir.iterdir() if f.is_file()]
    ydds, ytds = [], []
    for comp in components:
        ydd = [n for n in names if re.fullmatch(rf"{comp}_{drawable_index}_[a-z]\.ydd", n)]
        ytd = [n for n in names if re.fullmatch(rf"{comp}_diff_{drawable_index}_{tex_variant}_[a-z]+\.ytd", n)]
        ydds += ydd[:1]
        ytds += ytd[:1]
    return ytds, ydds


def import_ped_parts(game_dir: str, ped: str, components=DEFAULT_COMPONENTS, drawable_index="000", tex_variant="a"):
    ped_dir = find_ped_dir(game_dir, ped)
    ytds, ydds = pick_parts(ped_dir, components, drawable_index, tex_variant)
    files = [{"name": n} for n in ytds + ydds]
    res = bpy.ops.sollumz.import_assets(directory=str(ped_dir), files=files)
    return ytds, ydds, res


def clean_scene_extras():
    """Remove default/helper objects (camera, light, cube, cloth bounds, cloth meshes)."""
    for o in list(bpy.data.objects):
        junk = o.type in {"CAMERA", "LIGHT"} or o.name == "Cube" or "Bound" in o.name or ".cloth" in o.name
        if junk:
            bpy.data.objects.remove(o, do_unlink=True)


def merge_armatures():
    """Parts are imported with one armature each (same skeleton). Keep one, repoint all skinned meshes to it."""
    arms = sorted([o for o in bpy.data.objects if o.type == "ARMATURE"], key=lambda o: -len(o.data.bones))
    if not arms:
        raise RuntimeError("no armature imported")
    master = arms[0]
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for m in o.modifiers:
            if m.type == "ARMATURE":
                m.object = master
        if o.parent is not None and o.parent.type == "ARMATURE":
            mw = o.matrix_world.copy()
            o.parent = master
            o.matrix_world = mw
    for a in arms[1:]:
        bpy.data.objects.remove(a, do_unlink=True)
    return master


def simplify_materials():
    """Replace Sollumz shader trees with a Principled BSDF using the diffuse image, so glTF can export textures."""
    done = {}
    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        for slot in o.material_slots:
            mat = slot.material
            if mat is None:
                continue
            if mat.name in done:
                slot.material = done[mat.name]
                continue
            img = None
            for n in mat.node_tree.nodes if mat.node_tree else []:
                if n.type == "TEX_IMAGE" and n.image and ("diff" in n.image.name.lower() or n.name == "DiffuseSampler"):
                    img = n.image
                    break
            new = bpy.data.materials.new(mat.name + "_web")
            new.use_nodes = True
            bsdf = new.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Roughness"].default_value = 0.8
            if img:
                tex = new.node_tree.nodes.new("ShaderNodeTexImage")
                tex.image = img
                new.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
                if "hair" in img.name.lower():
                    new.node_tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
                    new.blend_method = "HASHED"
            done[mat.name] = new
            slot.material = new
    return list(done)


def export_glb(path: str, animations: bool = False):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", export_animations=animations,
        export_yup=True, export_apply=False, export_image_format="AUTO",
    )
