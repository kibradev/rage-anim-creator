"""python pipeline/build_fivem.py
Collects every exported .ycd (output/export/<clip>/v<N>/<clip>.ycd, newest version per clip) into a FiveM test
resource at output/fivem/animcreator_anims/. Plain Python, no Blender. Only approved+exported clips end up here.

In game:  ensure animcreator_anims   then   /animtest vb_spike   (/animtest alone lists clips, /animstop stops)
Each clip is its own dictionary: dict name = clip name, animation name = clip name.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "output" / "export"
RES = ROOT / "output" / "fivem" / "animcreator_anims"

clips = {}
for d in sorted(EXPORT.iterdir()) if EXPORT.exists() else []:
    vers = sorted((int(v.name[1:]), v) for v in d.iterdir() if v.is_dir() and (v / f"{d.name}.ycd").exists())
    if vers:
        meta = json.loads((ROOT / "output" / d.name / "meta.json").read_text("utf-8"))
        info = next((v for v in meta["versions"] if v["v"] == vers[-1][0]), {})
        clips[d.name] = (vers[-1][1] / f"{d.name}.ycd", vers[-1][0], bool(info.get("loop")))

if RES.exists():
    shutil.rmtree(RES)
(RES / "stream").mkdir(parents=True)
for name, (ycd, v, loop) in clips.items():
    shutil.copy(ycd, RES / "stream" / f"{name}.ycd")

(RES / "fxmanifest.lua").write_text(
    "fx_version 'cerulean'\ngame 'gta5'\n\ndescription 'animCreator test animations'\n\nclient_script 'client.lua'\n", "utf-8")

table = ",\n".join(f"    ['{n}'] = {{ loop = {'true' if loop else 'false'} }}" for n, (_, _, loop) in clips.items())
(RES / "client.lua").write_text(f"""local CLIPS = {{
{table}
}}

RegisterCommand('animtest', function(_, args)
    local name = args[1]
    if not name or not CLIPS[name] then
        local names = {{}}
        for k in pairs(CLIPS) do names[#names + 1] = k end
        table.sort(names)
        print('animtest: ' .. table.concat(names, ', '))
        TriggerEvent('chat:addMessage', {{ args = {{ 'animtest', table.concat(names, ', ') }} }})
        return
    end
    RequestAnimDict(name)
    local t = GetGameTimer()
    while not HasAnimDictLoaded(name) do
        Wait(0)
        if GetGameTimer() - t > 5000 then
            print('animtest: dict yuklenemedi: ' .. name)
            return
        end
    end
    local ped = PlayerPedId()
    local flag = CLIPS[name].loop and 1 or 0
    TaskPlayAnim(ped, name, name, 8.0, -8.0, -1, flag, 0.0, false, false, false)
end, false)

RegisterCommand('animstop', function()
    ClearPedTasks(PlayerPedId())
end, false)
""", "utf-8")
print("FIVEM", RES, "clips", {n: f"v{v}" for n, (_, v, _) in clips.items()})
