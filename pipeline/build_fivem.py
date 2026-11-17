"""python pipeline/build_fivem.py
Builds ONE FiveM resource, output/fivem/voleybol_anims/, from every exported .ycd (output/export/<clip>/v<N>, newest
version per clip). Contents: fxmanifest.lua, client.lua (all logic + clip table), ui.html (small menu), stream/*.ycd.

In game: put the folder in resources, `ensure voleybol_anims`, then F6 or /vb opens the menu
(click a clip to play it, Durdur stops, Esc closes). /animtest <clip> and /animstop also work from chat.
Each clip is its own dictionary: dict name = clip name, animation name = clip name.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "output" / "export"
RES = ROOT / "output" / "fivem" / "voleybol_anims"

TITLES = {
    "vb_ready_idle": ("Hazır bekleme", "Duruş"), "vb_shuffle_R": ("Sağa yan adım", "Duruş"), "vb_shuffle_L": ("Sola yan adım", "Duruş"),
    "vb_bump": ("Manşet pas", "Top kontrolü"), "vb_set": ("Parmak pas", "Top kontrolü"),
    "vb_serve_under": ("Alttan servis", "Servis"), "vb_serve_over": ("Üstten servis", "Servis"),
    "vb_spike": ("Smaç", "Hücum / blok"), "vb_block": ("Blok", "Hücum / blok"),
    "vb_dig_low": ("Alçak defans", "Defans"), "vb_dig_side_R": ("Sağa defans", "Defans"), "vb_dig_side_L": ("Sola defans", "Defans"),
    "vb_celebrate": ("Sayı sevinci", "Diğer"), "wave_hand": ("El sallama", "Diğer"),
}
TITLES.update({
    "vbx_spike": ("TEST Smaç (mover)", "Test (mover)"), "vbx_block": ("TEST Blok (mover)", "Test (mover)"),
    "vbx_dig_side_R": ("TEST Sağa defans (mover)", "Test (mover)"),
})
ORDER = ["Duruş", "Top kontrolü", "Servis", "Hücum / blok", "Defans", "Diğer", "Test (mover)"]

clips = {}
for d in sorted(EXPORT.iterdir()) if EXPORT.exists() else []:
    vers = sorted((int(v.name[1:]), v) for v in d.iterdir() if v.is_dir() and (v / f"{d.name}.ycd").exists())
    if vers:
        mp = ROOT / "output" / d.name / "meta.json"
        if mp.exists():
            meta = json.loads(mp.read_text("utf-8"))
            info = next((v for v in meta["versions"] if v["v"] == vers[-1][0]), {})
        else:  # test variants (pipeline/export_mover.py) carry mover.json instead
            info = json.loads((ROOT / "output" / d.name / "mover.json").read_text("utf-8"))
        title, group = TITLES.get(d.name, (d.name, "Diğer"))
        clips[d.name] = {"file": vers[-1][1] / f"{d.name}.ycd", "v": vers[-1][0], "loop": bool(info.get("loop")),
                         "sec": round(info.get("duration", 0), 1), "title": title, "group": group}

for old in (ROOT / "output" / "fivem").glob("*"):
    shutil.rmtree(old)
(RES / "stream").mkdir(parents=True)
for name, c in clips.items():
    shutil.copy(c["file"], RES / "stream" / f"{name}.ycd")

(RES / "fxmanifest.lua").write_text("""fx_version 'cerulean'
game 'gta5'

description 'Voleybol animasyonlari (animCreator) - F6 veya /vb'

ui_page 'ui.html'
files { 'ui.html' }
client_script 'client.lua'
""", "utf-8")

ui_clips = [{"name": n, "title": c["title"], "group": c["group"], "loop": c["loop"], "sec": c["sec"]} for n, c in clips.items()]
ui_clips.sort(key=lambda c: (ORDER.index(c["group"]) if c["group"] in ORDER else 99, c["title"]))
def _q(v):
    return json.dumps(v, ensure_ascii=False)  # JSON string literals are valid Lua strings for our content


lua_clips = ",\n".join(
    f"    {{ name = {_q(c['name'])}, title = {_q(c['title'])}, group = {_q(c['group'])}, loop = {'true' if c['loop'] else 'false'}, sec = {c['sec']} }}"
    for c in ui_clips)
lua_loop = ",\n".join(f"    ['{n}'] = {'true' if c['loop'] else 'false'}" for n, c in clips.items())

(RES / "client.lua").write_text(f"""-- Voleybol animasyonlari: tek resource, F6 veya /vb ile menu.
local LOOP = {{
{lua_loop}
}}
local CLIPS = {{
{lua_clips}
}}
local open = false
local current = nil

local function loadDict(name)
    if HasAnimDictLoaded(name) then return true end
    RequestAnimDict(name)
    local t = GetGameTimer()
    while not HasAnimDictLoaded(name) do
        Wait(0)
        if GetGameTimer() - t > 5000 then return false end
    end
    return true
end

-- opts: speed (1.0 = normal), upper (hareket edebilir, ust vucut)
local function play(name, opts)
    if LOOP[name] == nil then return false end
    opts = opts or {{}}
    if not loadDict(name) then
        TriggerEvent('chat:addMessage', {{ args = {{ 'voleybol', 'Animasyon yuklenemedi: ' .. name .. ' (stream klasoru dogru mu?)' }} }})
        return false
    end
    local ped = PlayerPedId()
    local flag = LOOP[name] and 1 or 0
    if opts.upper then flag = flag + 48 end
    local speed = opts.speed or 1.0
    -- ayak IK'si kalcayi zemine geri ceker (ziplama/comelme/yana kayma yutulur): oynarken kapat, stop()'ta geri ac
    if not opts.keepIk then SetPedLegIkMode(ped, 0) end
    TaskPlayAnim(ped, name, name, 8.0 * speed, -8.0 * speed, -1, flag, 0.0, false, false, false)
    Wait(250)
    if not IsEntityPlayingAnim(ped, name, name, 3) then
        -- tanilama: dict yuklendi ama clip oynamadi; "_clip" son ekli ad da dene (eski export hash'i)
        TaskPlayAnim(ped, name, name .. '_clip', 8.0 * speed, -8.0 * speed, -1, flag, 0.0, false, false, false)
        Wait(250)
        if not IsEntityPlayingAnim(ped, name, name .. '_clip', 3) then
            TriggerEvent('chat:addMessage', {{ args = {{ 'voleybol', 'Oynamadi: ' .. name .. ' (dict yuklendi ama clip bulunamadi/oynatilamadi)' }} }})
            print('voleybol: oynamadi ' .. name)
            return false
        end
        SetEntityAnimSpeed(ped, name, name .. '_clip', speed)
        current = name
        return true
    end
    SetEntityAnimSpeed(ped, name, name, speed)
    current = name
    return true
end

local function stop()
    ClearPedTasks(PlayerPedId())
    SetPedLegIkMode(PlayerPedId(), 2)
    current = nil
end

local function setOpen(v)
    open = v
    SetNuiFocus(v, v)
    SendNUIMessage({{ type = v and 'open' or 'close', clips = CLIPS, current = current }})
end

RegisterCommand('vb', function() setOpen(not open) end, false)
RegisterKeyMapping('vb', 'Voleybol animasyon menusu', 'keyboard', 'F6')

RegisterCommand('animtest', function(_, args)
    if args[1] and play(args[1]) then return end
    local names = {{}}
    for k in pairs(LOOP) do names[#names + 1] = k end
    table.sort(names)
    TriggerEvent('chat:addMessage', {{ args = {{ 'animtest', table.concat(names, ', ') }} }})
end, false)
RegisterCommand('animstop', stop, false)

-- /vbtest: butun clip'leri sirayla dener, her biri icin dict yuklendi mi / oynadi mi yazar (F8 konsoluna ve sohbete)
RegisterCommand('vbtest', function()
    CreateThread(function()
        local report = {{}}
        for _, c in ipairs(CLIPS) do
            local name = c.name
            RequestAnimDict(name)
            local t = GetGameTimer()
            while not HasAnimDictLoaded(name) and GetGameTimer() - t < 4000 do Wait(0) end
            local dict = HasAnimDictLoaded(name)
            local plays = false
            if dict then
                local ped = PlayerPedId()
                TaskPlayAnim(ped, name, name, 8.0, -8.0, -1, 0, 0.0, false, false, false)
                Wait(300)
                plays = IsEntityPlayingAnim(ped, name, name, 3)
                ClearPedTasks(ped)
            end
            local line = ('%s  dict=%s  oynuyor=%s'):format(name, dict and 'EVET' or 'HAYIR', plays and 'EVET' or 'HAYIR')
            print('vbtest: ' .. line)
            report[#report + 1] = line
            Wait(200)
        end
        for _, l in ipairs(report) do
            TriggerEvent('chat:addMessage', {{ args = {{ 'vbtest', l }} }})
        end
    end)
end, false)

-- /vbhip <clip> [ik]: clip'i oynatir, kalca (SKEL_Pelvis) ve bas yuksekligini olcer. "ik" yazarsan ayak IK'si acik kalir (kiyas icin).
-- Sonuc: baslangictan en yuksek / en alcak kalca farki (m). Ziplama clip'i icin "yuksek" ~ +0.3..0.5 olmali.
RegisterCommand('vbhip', function(_, args)
    local name = args[1]
    if not name or LOOP[name] == nil then
        TriggerEvent('chat:addMessage', {{ args = {{ 'vbhip', 'kullanim: /vbhip vb_spike [ik]' }} }})
        return
    end
    CreateThread(function()
        local ped = PlayerPedId()
        ClearPedTasks(ped)
        Wait(600)
        local base = GetPedBoneCoords(ped, 11816, 0.0, 0.0, 0.0)
        local ground = GetEntityCoords(ped)
        if not play(name, {{ keepIk = args[2] == 'ik' }}) then return end
        local hi, lo, side = -9, 9, 0
        local ox, oy = base.x, base.y
        local t0 = GetGameTimer()
        local dur = 3000
        for _, c in ipairs(CLIPS) do if c.name == name then dur = math.floor(c.sec * 1000) + 300 end end
        while GetGameTimer() - t0 < dur do
            local b = GetPedBoneCoords(ped, 11816, 0.0, 0.0, 0.0)
            local dz = b.z - base.z
            if dz > hi then hi = dz end
            if dz < lo then lo = dz end
            local dx = math.sqrt((b.x - ox) ^ 2 + (b.y - oy) ^ 2)
            if dx > side then side = dx end
            Wait(33)
        end
        local line = string.format('%s legIK=%s: kalca yukari %+.2f m, asagi %+.2f m, yatay %.2f m', name, args[2] == 'ik' and 'ACIK' or 'kapali', hi, lo, side)
        print('vbhip: ' .. line)
        TriggerEvent('chat:addMessage', {{ args = {{ 'vbhip', line }} }})
    end)
end, false)

RegisterNUICallback('play', function(data, cb)
    if play(data.name, {{ speed = tonumber(data.speed) or 1.0, upper = data.upper == true }}) then
        SendNUIMessage({{ type = 'playing', name = data.name }})
    end
    cb('ok')
end)
RegisterNUICallback('stop', function(_, cb) stop(); SendNUIMessage({{ type = 'playing', name = nil }}); cb('ok') end)
RegisterNUICallback('close', function(_, cb) setOpen(false); cb('ok') end)
""", "utf-8")

(RES / "ui.html").write_text("""<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: transparent; font-family: 'Segoe UI', Arial, sans-serif; color: #eef3f0; user-select: none; }
  #panel { display: none; position: absolute; right: 24px; top: 50%; transform: translateY(-50%); width: 300px; max-height: 86vh;
    background: rgba(14, 20, 17, .94); border: 1px solid #2c3a32; border-radius: 6px; flex-direction: column; overflow: hidden; }
  #panel.on { display: flex; }
  header { padding: 12px 14px; border-bottom: 3px solid #2fbf8a; display: flex; align-items: baseline; justify-content: space-between; }
  header b { font-size: 17px; letter-spacing: .06em; text-transform: uppercase; }
  header span { font-size: 11px; color: #8da096; }
  #list { overflow-y: auto; padding: 6px 10px 10px; }
  h3 { margin: 12px 2px 4px; font-size: 11px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: #8da096; }
  button.clip { width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 8px; margin: 3px 0; padding: 9px 11px;
    background: #1b2620; color: inherit; border: 1px solid #2c3a32; border-radius: 4px; font: inherit; font-size: 14px; cursor: pointer; text-align: left; }
  button.clip:hover { border-color: #2fbf8a; background: #22312a; }
  button.clip.on { background: #2fbf8a; border-color: #2fbf8a; color: #08140e; font-weight: 600; }
  button.clip small { font-size: 11px; opacity: .7; white-space: nowrap; }
  footer { padding: 10px 12px; border-top: 1px solid #2c3a32; display: flex; flex-direction: column; gap: 8px; font-size: 13px; }
  .row { display: flex; align-items: center; gap: 8px; }
  input[type=range] { flex: 1; accent-color: #2fbf8a; }
  .btns { display: flex; gap: 8px; }
  .btns button { flex: 1; padding: 9px; border-radius: 4px; border: 1px solid #2c3a32; background: #1b2620; color: inherit; font: inherit; cursor: pointer; }
  .btns button.stop { background: #8f2f2f; border-color: #8f2f2f; }
  .btns button:hover { filter: brightness(1.2); }
</style></head>
<body>
<div id="panel">
  <header><b>Voleybol</b><span>Esc: kapat</span></header>
  <div id="list"></div>
  <footer>
    <label class="row"><input type="checkbox" id="upper"> Hareket edebileyim (üst vücut)</label>
    <label class="row">Hız <input type="range" id="speed" min="0.5" max="1.5" step="0.05" value="1"><span id="sv">1.0x</span></label>
    <div class="btns"><button class="stop" id="stop">Durdur</button><button id="close">Kapat</button></div>
  </footer>
</div>
<script>
const $ = (id) => document.getElementById(id);
const post = (name, data) => fetch(`https://${GetParentResourceName()}/${name}`, { method: 'POST', body: JSON.stringify(data || {}) });
let playing = null;
function mark() { document.querySelectorAll('button.clip').forEach(b => b.classList.toggle('on', b.dataset.name === playing)); }
function build(clips) {
  const list = $('list'); list.innerHTML = '';
  let group = null;
  for (const c of clips) {
    if (c.group !== group) { group = c.group; const h = document.createElement('h3'); h.textContent = group; list.appendChild(h); }
    const b = document.createElement('button');
    b.className = 'clip'; b.dataset.name = c.name;
    b.innerHTML = `<span>${c.title}</span><small>${c.loop ? 'döngü' : c.sec + ' sn'}</small>`;
    b.onclick = () => { playing = c.name; mark(); post('play', { name: c.name, speed: parseFloat($('speed').value), upper: $('upper').checked }); };
    list.appendChild(b);
  }
}
$('speed').oninput = () => { $('sv').textContent = parseFloat($('speed').value).toFixed(1) + 'x'; };
$('stop').onclick = () => { playing = null; mark(); post('stop'); };
$('close').onclick = () => post('close');
window.addEventListener('keydown', (e) => { if (e.key === 'Escape') post('close'); });
window.addEventListener('message', (e) => {
  const m = e.data;
  if (m.type === 'open') { build(m.clips); playing = m.current; mark(); $('panel').classList.add('on'); }
  else if (m.type === 'close') $('panel').classList.remove('on');
  else if (m.type === 'playing') { playing = m.name; mark(); }
});
</script>
</body></html>
""", "utf-8")
print("FIVEM", RES, "clips", len(clips), sorted(clips))
