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
    "vbs_spike": ("TEST Smaç (script)", "Test (script)"), "vbs_block": ("TEST Blok (script)", "Test (script)"),
    "vbs_dig_side_R": ("TEST Sağa defans (script)", "Test (script)"),
    "vbm_spike": ("TEST Smaç (mover)", "Test (mover)"), "vbm_block": ("TEST Blok (mover)", "Test (mover)"),
    "vbm_celebrate": ("TEST Sayı sevinci (mover)", "Test (mover)"), "vbm_bump": ("TEST Manşet (mover)", "Test (mover)"),
    "vbm_dig_side_R": ("TEST Sağa defans (mover)", "Test (mover)"),
})
ORDER = ["Duruş", "Top kontrolü", "Servis", "Hücum / blok", "Defans", "Diğer", "Test (mover)", "Test (script)"]

HIP = {}
clips = {}
for d in sorted(EXPORT.iterdir()) if EXPORT.exists() else []:
    vers = sorted((int(v.name[1:]), v) for v in d.iterdir() if v.is_dir() and (v / f"{d.name}.ycd").exists())
    if vers:
        mp = ROOT / "output" / d.name / "meta.json"
        if mp.exists():
            meta = json.loads(mp.read_text("utf-8"))
            info = next((v for v in meta["versions"] if v["v"] == vers[-1][0]), {})
        elif (ROOT / "output" / d.name / "mover.json").exists():  # Rockstar-split variants (pipeline/export_mover.py)
            info = json.loads((ROOT / "output" / d.name / "mover.json").read_text("utf-8"))
        else:  # script-root variants (pipeline/export_script.py) carry hip.json instead
            info = json.loads((ROOT / "output" / d.name / "hip.json").read_text("utf-8"))
            HIP[d.name] = {k: info[k] for k in ("n", "duration", "x", "y", "z")}
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
def _arr(v):
    return "{" + ",".join(str(x) for x in v) + "}"


lua_hip = ",\n".join(
    f"    ['{n}'] = {{ n = {h['n']}, x = {_arr(h['x'])}, y = {_arr(h['y'])}, z = {_arr(h['z'])} }}" for n, h in HIP.items())
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

-- Kalca (root) hareketi script ile: oyun kemik/mover uzerinden zıplama-comelmeyi uygulamiyor. Clip'ten cikarilan kalca egrisi
-- (karakter uzayi: x sag, y ileri, z yukari, metre) animasyonun anlik fazina gore ped'in konumuna uygulanir.
local HIP = {{
{lua_hip}
}}
local hipRun = 0
local hipBase = nil

local function hipEnd(ped)
    hipRun = hipRun + 1
    if hipBase then  -- yarim kalan hareket (Durdur / yeniden oynat): ped'i baslangic konumuna geri koy, kayma birikmesin
        SetEntityCoordsNoOffset(ped, hipBase.x, hipBase.y, hipBase.z, false, false, false)
        hipBase = nil
    end
    SetEntityCollision(ped, true, true)
    SetPedGravity(ped, true)
end

local function hipStart(name, ped)
    local h = HIP[name]
    if not h then return end
    hipRun = hipRun + 1
    local my = hipRun
    CreateThread(function()
      local ok, err = pcall(function()
        local base = GetEntityCoords(ped)
        hipBase = base
        local head = math.rad(GetEntityHeading(ped))
        local fx, fy, rx, ry = -math.sin(head), math.cos(head), math.cos(head), math.sin(head)
        SetEntityCollision(ped, false, false)
        SetPedGravity(ped, false)
        local t0 = GetGameTimer()
        local aborted = false
        local o = {{ 0.0, 0.0, 0.0 }}
        local function put(k)
            SetEntityCoordsNoOffset(ped, base.x + rx * o[1] * k + fx * o[2] * k, base.y + ry * o[1] * k + fy * o[2] * k, base.z + o[3] * k, false, false, false)
            SetEntityVelocity(ped, 0.0, 0.0, 0.0)
        end
        while hipRun == my do
            if not IsEntityPlayingAnim(ped, name, name, 3) and GetGameTimer() - t0 > 600 then break end
            if IsPedRagdoll(ped) or IsEntityDead(ped) or IsPedInAnyVehicle(ped, false) then aborted = true break end
            local ph = GetEntityAnimCurrentTime(ped, name, name)
            local f = ph * (h.n - 1) + 1
            local i = math.max(1, math.min(h.n - 1, math.floor(f)))
            local u = math.max(0.0, math.min(1.0, f - i))
            o[1] = h.x[i] + (h.x[i + 1] - h.x[i]) * u
            o[2] = h.y[i] + (h.y[i + 1] - h.y[i]) * u
            o[3] = h.z[i] + (h.z[i + 1] - h.z[i]) * u
            put(math.min(1.0, (GetGameTimer() - t0) / 150.0))
            Wait(0)
        end
        if aborted and hipRun == my then
            hipEnd(ped)
        elseif hipRun == my then  -- dogal bitis: kalcayi yumusakca eski yere indir
            local t1 = GetGameTimer()
            while hipRun == my and GetGameTimer() - t1 < 150 do put(1.0 - (GetGameTimer() - t1) / 150.0); Wait(0) end
            hipEnd(ped)
        end
      end)
      if not ok then
        hipEnd(ped)
        print('voleybol HATA (kalca): ' .. tostring(err))
        TriggerEvent('chat:addMessage', {{ args = {{ 'voleybol', 'HATA (kalca): ' .. tostring(err) }} }})
      end
    end)
end

AddEventHandler('onResourceStop', function(res)
    if res == GetCurrentResourceName() then
        local ped = PlayerPedId()
        hipEnd(ped)
        SetPedLegIkMode(ped, 2)
    end
end)

-- Clip oynarken oyuncu girdisi animasyonu kesmesin (bayrak 0 = kesilebilir). Dongu clip'leri ve ust vucut modu serbest.
local LOCK = {{ 30, 31, 32, 33, 34, 35, 21, 22, 23, 24, 25, 36, 37, 44, 140, 141, 142, 257, 263, 264 }}
local function lockControls(name, ped)
    CreateThread(function()
        local t0 = GetGameTimer()
        while current == name and (IsEntityPlayingAnim(ped, name, name, 3) or GetGameTimer() - t0 < 700) do
            for _, c in ipairs(LOCK) do DisableControlAction(0, c, true) end
            Wait(0)
        end
    end)
end

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
    if opts.upper then flag = flag + 48 else flag = flag + 8 end  -- 8 = AF_NOT_INTERRUPTABLE
    local speed = opts.speed or 1.0
    -- ayak IK'si kalcayi zemine geri ceker (ziplama/comelme/yana kayma yutulur): oynarken kapat, stop()'ta geri ac
    hipEnd(ped)
    if not opts.keepIk then SetPedLegIkMode(ped, 0) end
    TaskPlayAnim(ped, name, name, 8.0 * speed, -8.0 * speed, -1, flag, 0.0, false, false, false)
    current = name
    if not opts.upper then hipStart(name, ped) end  -- hemen basla: ilk comelme atlanmasin
    Wait(250)
    if not IsEntityPlayingAnim(ped, name, name, 3) then
        hipEnd(ped)
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
    if not LOOP[name] and not opts.upper then lockControls(name, ped) end
    return true
end

local function stop()
    hipEnd(PlayerPedId())
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
    local REF_DICT, REF_CLIP = 'anim@arena@celeb@flat@solo@no_props@', 'jump_b_player_a'
    if not name or (LOOP[name] == nil and name ~= 'ref') then
        TriggerEvent('chat:addMessage', {{ args = {{ 'vbhip', 'kullanim: /vbhip vbm_spike [ik]   |   /vbhip ref (oyunun ziplamasi)' }} }})
        return
    end
    CreateThread(function()
        local ped = PlayerPedId()
        ClearPedTasks(ped)
        Wait(600)
        local base = GetPedBoneCoords(ped, 11816, 0.0, 0.0, 0.0)
        local ground = GetEntityCoords(ped)
        local footR0 = GetPedBoneCoords(ped, 52301, 0.0, 0.0, 0.0).z   -- SKEL_R_Foot
        local footL0 = GetPedBoneCoords(ped, 14201, 0.0, 0.0, 0.0).z   -- SKEL_L_Foot
        local eHi, eLo, fHi, fLo = -9, 9, -9, 9
        if name == 'ref' then
            RequestAnimDict(REF_DICT)
            local tw = GetGameTimer()
            while not HasAnimDictLoaded(REF_DICT) and GetGameTimer() - tw < 5000 do Wait(0) end
            TaskPlayAnim(ped, REF_DICT, REF_CLIP, 8.0, -8.0, -1, 0, 0.0, false, false, false)
        elseif not play(name, {{ keepIk = args[2] == 'ik' }}) then return end
        -- yon tanilamasi: entity heading ile iskeletin (sag-sol uyluk) bakis yonu; fark ~0 olmali, ~180 = iskelet ters
        local function skelYawDiff()
            local r = GetPedBoneCoords(ped, 51826, 0.0, 0.0, 0.0)   -- SKEL_R_Thigh
            local l = GetPedBoneCoords(ped, 58271, 0.0, 0.0, 0.0)   -- SKEL_L_Thigh
            local d = math.deg(math.atan2(r.y - l.y, r.x - l.x)) - GetEntityHeading(ped)
            while d > 180 do d = d - 360 end
            while d < -180 do d = d + 360 end
            return d
        end
        local yaw0, h0 = skelYawDiff(), GetEntityHeading(ped)
        local yawMid, yawEnd, hMax = yaw0, yaw0, 0.0
        local hi, lo, side = -9, 9, 0
        local ox, oy = base.x, base.y
        local t0 = GetGameTimer()
        local dur = 3000
        for _, c in ipairs(CLIPS) do if c.name == name then dur = math.floor(c.sec * 1000) + 300 end end
        if name == 'ref' then dur = 6300 end
        while GetGameTimer() - t0 < dur do
            local ez = GetEntityCoords(ped).z - ground.z
            if ez > eHi then eHi = ez end
            if ez < eLo then eLo = ez end
            local fz = math.min(GetPedBoneCoords(ped, 52301, 0.0, 0.0, 0.0).z - footR0, GetPedBoneCoords(ped, 14201, 0.0, 0.0, 0.0).z - footL0)
            if fz > fHi then fHi = fz end   -- alttaki ayagin en yuksek yeri: >0.2 ise ped havada
            if fz < fLo then fLo = fz end
            local b = GetPedBoneCoords(ped, 11816, 0.0, 0.0, 0.0)
            local dz = b.z - base.z
            if dz > hi then hi = dz end
            if dz < lo then lo = dz end
            local dx = math.sqrt((b.x - ox) ^ 2 + (b.y - oy) ^ 2)
            if dx > side then side = dx end
            local el = GetGameTimer() - t0
            if el > dur * 0.4 and el < dur * 0.6 then yawMid = skelYawDiff() end
            local dh = math.abs(GetEntityHeading(ped) - h0)
            if dh > 180 then dh = 360 - dh end
            if dh > hMax then hMax = dh end
            yawEnd = skelYawDiff()
            Wait(33)
        end
        local line = string.format('%s legIK=%s: kalca yukari %+.2f m, asagi %+.2f m, yatay %.2f m', name, args[2] == 'ik' and 'ACIK' or 'kapali', hi, lo, side)
        print('vbhip: ' .. line)
        TriggerEvent('chat:addMessage', {{ args = {{ 'vbhip', line }} }})
        local el2 = string.format('PED(entity) yukari %+.2f asagi %+.2f m | ALT AYAK yerden en fazla %+.2f, en az %+.2f m', eHi, eLo, fHi, fLo)
        print('vbhip: ' .. el2)
        TriggerEvent('chat:addMessage', {{ args = {{ 'vbhip', el2 }} }})
        local yl = string.format('YON: iskelet-entity farki baslangic %.0f, orta %.0f, son %.0f derece; entity heading en fazla %.0f derece degisti', yaw0, yawMid, yawEnd, hMax)
        print('vbhip: ' .. yl)
        TriggerEvent('chat:addMessage', {{ args = {{ 'vbhip', yl }} }})
    end)
end, false)

-- /vbjump [a|b]: ANIMASYONSUZ ziplama testi. a = her kare SetEntityCoordsNoOffset (script'imizin yaptigi), b = SetEntityVelocity (fizik).
-- Hangisi ped'i gercekten kaldiriyor? Sohbete "oyunun bildigi" en yuksek yukseklik yazilir.
RegisterCommand('vbjump', function(_, args)
    local mode = args[1] or 'a'
    CreateThread(function()
        local ped = PlayerPedId()
        ClearPedTasks(ped)
        Wait(300)
        local base = GetEntityCoords(ped)
        local peak = -9.0
        local t0 = GetGameTimer()
        if mode == 'b' then
            SetEntityVelocity(ped, 0.0, 0.0, 4.5)
            while GetGameTimer() - t0 < 1000 do
                local z = GetEntityCoords(ped).z - base.z
                if z > peak then peak = z end
                Wait(0)
            end
        else
            SetEntityCollision(ped, false, false)
            SetPedGravity(ped, false)
            while GetGameTimer() - t0 < 700 do
                local k = (GetGameTimer() - t0) / 700.0
                SetEntityCoordsNoOffset(ped, base.x, base.y, base.z + 0.5 * math.sin(math.pi * k), false, false, false)
                SetEntityVelocity(ped, 0.0, 0.0, 0.0)
                local z = GetEntityCoords(ped).z - base.z
                if z > peak then peak = z end
                Wait(0)
            end
            SetEntityCoordsNoOffset(ped, base.x, base.y, base.z, false, false, false)
            SetEntityCollision(ped, true, true)
            SetPedGravity(ped, true)
        end
        local line = string.format('vbjump %s: en yuksek %.2f m (beklenen: a=0.50, b=~1.0)', mode, peak)
        print(line)
        TriggerEvent('chat:addMessage', {{ args = {{ 'vbjump', line }} }})
    end)
end, false)

-- /vbref [clip] [dict]: OYUNUN KENDI ziplama kutlamasini oynatir (arena celeb jump_b_player_a: comelme kalcada, havaya
-- kalkis mover'da; vbm_ test varyantlari ayni duzende). /vbref jump_a_player_a, jump_c_player_a, flip_a_player_a da var.
RegisterCommand('vbref', function(_, args)
    local clip = args[1] or 'jump_b_player_a'
    local dict = args[2] or 'anim@arena@celeb@flat@solo@no_props@'
    RequestAnimDict(dict)
    local t = GetGameTimer()
    while not HasAnimDictLoaded(dict) and GetGameTimer() - t < 5000 do Wait(0) end
    if not HasAnimDictLoaded(dict) then
        TriggerEvent('chat:addMessage', {{ args = {{ 'vbref', 'dict yuklenemedi: ' .. dict }} }})
        return
    end
    TaskPlayAnim(PlayerPedId(), dict, clip, 8.0, -8.0, -1, 0, 0.0, false, false, false)
    TriggerEvent('chat:addMessage', {{ args = {{ 'vbref', 'oynuyor: ' .. clip .. ' (durdurmak icin /animstop)' }} }})
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
