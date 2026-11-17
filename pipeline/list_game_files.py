"""Blender icinde calisir: blender -b --python pipeline/list_game_files.py -- <ped_adi> <anim_filtre>
GTA V RPF arsivlerini dogrudan okur (OpenIV/CodeWalker export'u gerekmez) ve ped/animasyon dosyalarini listeler."""
import json, sys
from pathlib import Path

cfg = json.loads((Path(__file__).resolve().parent.parent / "config.json").read_text())
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ped = (args[0] if args else "player_zero").lower()
anim_filter = (args[1] if len(args) > 1 else "").lower()

gf = __import__(cfg["sollumz_pkg"] + ".shared.game_assets.game_files", fromlist=["x"])
idx = gf.GameFiles(cfg["game_dir"]).read_asset_filelist(((".ydd",), (".yft",), (".ytd",), (".ycd",)))
for ext in ((".ydd",), (".yft",), (".ytd",)):
    for name, paths in idx.get(ext, {}).items():
        if name.lower().startswith(ped):
            print("PED", ext[0], name, "|", paths[-1])
for name, paths in idx.get((".ycd",), {}).items():
    if anim_filter and anim_filter in name.lower():
        print("YCD", name, "|", paths[-1])
print("TOTAL ycd", len(idx.get((".ycd",), {})))
