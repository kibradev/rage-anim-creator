-- Voleybol animasyonlari: tek resource, F6 veya /vb ile menu.
local LOOP = {
    ['vb_block'] = false,
    ['vb_bump'] = false,
    ['vb_celebrate'] = false,
    ['vb_dig_low'] = false,
    ['vb_dig_side_L'] = false,
    ['vb_dig_side_R'] = false,
    ['vb_ready_idle'] = true,
    ['vb_serve_over'] = false,
    ['vb_serve_under'] = false,
    ['vb_set'] = false,
    ['vb_shuffle_L'] = true,
    ['vb_shuffle_R'] = true,
    ['vb_spike'] = false,
    ['wave_hand'] = false
}
local CLIPS = {
    { name = "vb_ready_idle", title = "Hazır bekleme", group = "Duruş", loop = true, sec = 2.0 },
    { name = "vb_shuffle_R", title = "Sağa yan adım", group = "Duruş", loop = true, sec = 0.7 },
    { name = "vb_shuffle_L", title = "Sola yan adım", group = "Duruş", loop = true, sec = 0.7 },
    { name = "vb_bump", title = "Manşet pas", group = "Top kontrolü", loop = false, sec = 1.3 },
    { name = "vb_set", title = "Parmak pas", group = "Top kontrolü", loop = false, sec = 1.3 },
    { name = "vb_serve_under", title = "Alttan servis", group = "Servis", loop = false, sec = 1.8 },
    { name = "vb_serve_over", title = "Üstten servis", group = "Servis", loop = false, sec = 2.1 },
    { name = "vb_block", title = "Blok", group = "Hücum / blok", loop = false, sec = 1.9 },
    { name = "vb_spike", title = "Smaç", group = "Hücum / blok", loop = false, sec = 2.4 },
    { name = "vb_dig_low", title = "Alçak defans", group = "Defans", loop = false, sec = 1.5 },
    { name = "vb_dig_side_R", title = "Sağa defans", group = "Defans", loop = false, sec = 1.7 },
    { name = "vb_dig_side_L", title = "Sola defans", group = "Defans", loop = false, sec = 1.7 },
    { name = "wave_hand", title = "El sallama", group = "Diğer", loop = false, sec = 3.0 },
    { name = "vb_celebrate", title = "Sayı sevinci", group = "Diğer", loop = false, sec = 2.3 }
}
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
    opts = opts or {}
    if not loadDict(name) then
        TriggerEvent('chat:addMessage', { args = { 'voleybol', 'Animasyon yuklenemedi: ' .. name .. ' (stream klasoru dogru mu?)' } })
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
            TriggerEvent('chat:addMessage', { args = { 'voleybol', 'Oynamadi: ' .. name .. ' (dict yuklendi ama clip bulunamadi/oynatilamadi)' } })
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
    SendNUIMessage({ type = v and 'open' or 'close', clips = CLIPS, current = current })
end

RegisterCommand('vb', function() setOpen(not open) end, false)
RegisterKeyMapping('vb', 'Voleybol animasyon menusu', 'keyboard', 'F6')

RegisterCommand('animtest', function(_, args)
    if args[1] and play(args[1]) then return end
    local names = {}
    for k in pairs(LOOP) do names[#names + 1] = k end
    table.sort(names)
    TriggerEvent('chat:addMessage', { args = { 'animtest', table.concat(names, ', ') } })
end, false)
RegisterCommand('animstop', stop, false)

-- /vbtest: butun clip'leri sirayla dener, her biri icin dict yuklendi mi / oynadi mi yazar (F8 konsoluna ve sohbete)
RegisterCommand('vbtest', function()
    CreateThread(function()
        local report = {}
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
            TriggerEvent('chat:addMessage', { args = { 'vbtest', l } })
        end
    end)
end, false)

-- /vbhip <clip> [ik]: clip'i oynatir, kalca (SKEL_Pelvis) ve bas yuksekligini olcer. "ik" yazarsan ayak IK'si acik kalir (kiyas icin).
-- Sonuc: baslangictan en yuksek / en alcak kalca farki (m). Ziplama clip'i icin "yuksek" ~ +0.3..0.5 olmali.
RegisterCommand('vbhip', function(_, args)
    local name = args[1]
    if not name or LOOP[name] == nil then
        TriggerEvent('chat:addMessage', { args = { 'vbhip', 'kullanim: /vbhip vb_spike [ik]' } })
        return
    end
    CreateThread(function()
        local ped = PlayerPedId()
        ClearPedTasks(ped)
        Wait(600)
        local base = GetPedBoneCoords(ped, 11816, 0.0, 0.0, 0.0)
        local ground = GetEntityCoords(ped)
        if not play(name, { keepIk = args[2] == 'ik' }) then return end
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
        TriggerEvent('chat:addMessage', { args = { 'vbhip', line } })
    end)
end, false)

RegisterNUICallback('play', function(data, cb)
    if play(data.name, { speed = tonumber(data.speed) or 1.0, upper = data.upper == true }) then
        SendNUIMessage({ type = 'playing', name = data.name })
    end
    cb('ok')
end)
RegisterNUICallback('stop', function(_, cb) stop(); SendNUIMessage({ type = 'playing', name = nil }); cb('ok') end)
RegisterNUICallback('close', function(_, cb) setOpen(false); cb('ok') end)
