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
    ['vbs_block'] = false,
    ['vbs_dig_side_R'] = false,
    ['vbs_spike'] = false,
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
    { name = "vb_celebrate", title = "Sayı sevinci", group = "Diğer", loop = false, sec = 2.3 },
    { name = "vbs_block", title = "TEST Blok (script)", group = "Test (script)", loop = false, sec = 1.9 },
    { name = "vbs_dig_side_R", title = "TEST Sağa defans (script)", group = "Test (script)", loop = false, sec = 1.7 },
    { name = "vbs_spike", title = "TEST Smaç (script)", group = "Test (script)", loop = false, sec = 2.4 }
}
local open = false
local current = nil

-- Kalca (root) hareketi script ile: oyun kemik/mover uzerinden zıplama-comelmeyi uygulamiyor. Clip'ten cikarilan kalca egrisi
-- (karakter uzayi: x sag, y ileri, z yukari, metre) animasyonun anlik fazina gore ped'in konumuna uygulanir.
local HIP = {
    ['vbs_block'] = { n = 57, x = {0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0}, y = {0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0047,0.0088,0.0122,0.015,0.0172,0.0188,0.0197,0.02,0.02,0.02,0.02,0.0198,0.019,0.0178,0.016,0.0138,0.0111,0.0079,0.0042,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0}, z = {-0.14,-0.146,-0.1619,-0.1843,-0.21,-0.2357,-0.2581,-0.274,-0.28,-0.2672,-0.2288,-0.1648,-0.0752,0.04,0.1244,0.1975,0.2594,0.31,0.3494,0.3775,0.3944,0.4,0.4,0.4,0.4,0.3923,0.3694,0.3311,0.2775,0.2086,0.1244,0.0249,-0.0899,-0.22,-0.2196,-0.2183,-0.2163,-0.2136,-0.2103,-0.2065,-0.2023,-0.1977,-0.1928,-0.1878,-0.1826,-0.1774,-0.1722,-0.1672,-0.1623,-0.1577,-0.1535,-0.1497,-0.1464,-0.1437,-0.1417,-0.1404,-0.14} },
    ['vbs_dig_side_R'] = { n = 53, x = {0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0}, y = {0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0106,0.0196,0.0269,0.0327,0.0367,0.0392,0.04,0.04,0.04,0.04,0.04,0.04,0.04,0.04,0.04,0.04,0.04,0.04,0.0388,0.035,0.0288,0.02,0.0196,0.0185,0.0169,0.0148,0.0125,0.01,0.0075,0.0052,0.0031,0.0015,0.0004,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0}, z = {-0.14,-0.1444,-0.1556,-0.17,-0.1844,-0.1956,-0.2,-0.2424,-0.2784,-0.3078,-0.3306,-0.3469,-0.3567,-0.36,-0.3589,-0.3556,-0.35,-0.3422,-0.3322,-0.32,-0.32,-0.32,-0.32,-0.32,-0.32,-0.3175,-0.31,-0.2975,-0.28,-0.278,-0.2726,-0.2644,-0.2541,-0.2424,-0.23,-0.2176,-0.2059,-0.1956,-0.1874,-0.182,-0.18,-0.1792,-0.177,-0.1737,-0.1696,-0.165,-0.16,-0.155,-0.1504,-0.1462,-0.143,-0.1408,-0.14} },
    ['vbs_spike'] = { n = 73, x = {0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0}, y = {0.0,-0.0004,-0.0015,-0.0031,-0.0052,-0.0075,-0.01,-0.0125,-0.0148,-0.0169,-0.0185,-0.0196,-0.02,-0.0183,-0.0133,-0.005,0.0067,0.0217,0.04,0.0541,0.0662,0.0766,0.085,0.0916,0.0962,0.0991,0.1,0.1025,0.11,0.1225,0.14,0.1472,0.1528,0.1568,0.1592,0.16,0.16,0.16,0.16,0.16,0.16,0.16,0.1595,0.1581,0.1558,0.1527,0.1489,0.1443,0.1392,0.1335,0.1274,0.1208,0.1139,0.1066,0.0992,0.0916,0.0839,0.0761,0.0684,0.0608,0.0534,0.0461,0.0392,0.0326,0.0265,0.0208,0.0157,0.0111,0.0073,0.0042,0.0019,0.0005,0.0}, z = {-0.14,-0.1439,-0.1548,-0.1713,-0.1919,-0.2152,-0.24,-0.2648,-0.2881,-0.3088,-0.3252,-0.3361,-0.34,-0.3294,-0.2978,-0.245,-0.1711,-0.0761,0.04,0.1384,0.2237,0.2959,0.355,0.4009,0.4338,0.4534,0.46,0.4625,0.47,0.4825,0.5,0.428,0.372,0.332,0.308,0.3,0.2844,0.2378,0.16,0.0511,-0.0889,-0.26,-0.2596,-0.2586,-0.2568,-0.2545,-0.2516,-0.2483,-0.2444,-0.2401,-0.2355,-0.2306,-0.2254,-0.22,-0.2144,-0.2087,-0.2029,-0.1971,-0.1913,-0.1856,-0.18,-0.1746,-0.1694,-0.1645,-0.1599,-0.1556,-0.1517,-0.1484,-0.1455,-0.1432,-0.1414,-0.1404,-0.14} }
}
local hipRun = 0

local function hipEnd(ped)
    hipRun = hipRun + 1
    SetEntityCollision(ped, true, true)
    SetPedGravity(ped, true)
end

local function hipStart(name, ped)
    local h = HIP[name]
    if not h then return end
    hipRun = hipRun + 1
    local my = hipRun
    CreateThread(function()
        local base = GetEntityCoords(ped)
        local head = math.rad(GetEntityHeading(ped))
        local fx, fy, rx, ry = -math.sin(head), math.cos(head), math.cos(head), math.sin(head)
        SetEntityCollision(ped, false, false)
        SetPedGravity(ped, false)
        local t0 = GetGameTimer()
        local o = { 0.0, 0.0, 0.0 }
        local function put(k)
            SetEntityCoordsNoOffset(ped, base.x + rx * o[1] * k + fx * o[2] * k, base.y + ry * o[1] * k + fy * o[2] * k, base.z + o[3] * k, false, false, false)
            SetEntityVelocity(ped, 0.0, 0.0, 0.0)
        end
        while hipRun == my do
            if not IsEntityPlayingAnim(ped, name, name, 3) and GetGameTimer() - t0 > 600 then break end
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
        if hipRun == my then  -- dogal bitis: kalcayi yumusakca eski yere indir
            local t1 = GetGameTimer()
            while hipRun == my and GetGameTimer() - t1 < 150 do put(1.0 - (GetGameTimer() - t1) / 150.0); Wait(0) end
            hipEnd(ped)
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
    hipEnd(ped)
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
        hipStart(name, ped)
        return true
    end
    SetEntityAnimSpeed(ped, name, name, speed)
    current = name
    hipStart(name, ped)
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
