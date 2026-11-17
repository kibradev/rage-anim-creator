"""Reference motion from the game: load a GTA clip as a Blender action to copy from / build on (run inside Blender).

    act, f0, f1 = ref.gta_action(arm, "special_ped@mountain_dancer@monologue_3@monologue_3a", "mnt_dnc_buttwag")
    clip.copy_from(act, f0, f0 + 60)          # then clip.add(...), clip.reach(...), clip.plant_feet(...)
"""
import json
import subprocess
from pathlib import Path

from . import anims as animlib

ROOT = Path(__file__).resolve().parents[2]


def ensure_xml(dict_name: str) -> Path:
    """cache/ycdxml/<dict>.ycd.xml, converting it from the game archives on first use."""
    xml = ROOT / "cache" / "ycdxml" / f"{dict_name}.ycd.xml"
    if not xml.exists():
        cfg = json.loads((ROOT / "config.json").read_text())
        subprocess.run(["dotnet", str(ROOT / "cache" / "converter" / "ycd2xml.dll"), cfg["game_dir"],
                        str(xml.parent), dict_name], check=True)
    if not xml.exists():
        raise FileNotFoundError(f"clip dictionary not found in the game: {dict_name}")
    return xml


def gta_action(arm, dict_name: str, clip_name: str):
    """Return (action, first_frame, last_frame) of a game clip, retargeted to `arm`."""
    d, anims, clips = animlib.import_dict(str(ensure_xml(dict_name)))
    animlib.retarget_to(arm, anims)
    names = [c.clip_properties.name or c.name for c in clips]
    match = [c for c in clips if clip_name in (c.clip_properties.name or c.name)]
    if not match:
        raise KeyError(f"{clip_name} not in {dict_name}; clips: {names[:20]}")
    act, s, e = animlib.merged_action(match[0])
    return act, int(round(s)), int(round(e))
