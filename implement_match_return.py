from pathlib import Path

ROOT = Path(r'C:\Users\kibra\Desktop\volleyballScript')

def edit(rel, old, new):
    p = ROOT / rel
    raw = p.read_bytes()
    text = raw.decode('utf-8').replace('\r\n', '\n')
    assert old in text, (rel, old[:90])
    text = text.replace(old, new, 1)
    p.write_bytes(text.replace('\n', '\r\n' if b'\r\n' in raw else '\n').encode('utf-8'))

base = 'resource/0r-volleyball/'
edit(base+'config.lua', 'VB.Config.Match = {', '''VB.Config.Match = {
    Rejoin = {
        AfterDisconnect = true, -- bağlantı kopunca/oyundan çıkınca, devam eden maça /vbgeri ile dön
        AfterDeath = true,      -- ölünce kadrodan çıkar; canlandıktan sonra /vbgeri ile dön
    },''')

edit(base+'modules/server/lobby.lua', '''    local ok, kind, evac, newHost
    if fromDrop''', '''    local ok, kind, evac, newHost
    VB.MatchSrv.prepareLeave(lobby.id, src, fromDrop == true and 'disconnect' or (fromDrop == 'death' and 'death' or 'leave'))
    if fromDrop''')
edit(base+'modules/server/lobby.lua', "RegisterNetEvent(EV .. 'server:LeaveLobby'", '''-- Ölüm de aynı kadro/host temizliğinden geçer; istemci beyanıyla oyuncu çıkarılmaz.
VB.MatchUnavailable = function(src, reason)
    local id = store:lobbyOf(src)
    if id then handleLeave(src, id, reason == 'death' and 'death' or true) end
end

RegisterNetEvent(EV .. 'server:LeaveLobby' ''')
# Remove the space introduced before the argument separator.
edit(base+'modules/server/lobby.lua', "'server:LeaveLobby' ,", "'server:LeaveLobby',")

edit(base+'modules/server/match.lua', "local function nameOf(m, id)", '''-- Kalıcı lisans kimliği: yeniden kullanılan server ID geri dönüş hakkı vermez.
local function identity(src)
    for _, id in ipairs(GetPlayerIdentifiers(src) or {}) do
        if id:sub(1, 8) == 'license:' then return id end
    end
end

local function isDead(src)
    local ped = GetPlayerPed(src)
    if not ped or ped == 0 then return true end
    if GetEntityHealth(ped) <= 0 then return true end
    -- Qbox/QB ölüm ekranında ped canı pozitif kalabilir (laststand dahil).
    if GetResourceState and GetResourceState('qbx_core') == 'started' then
        local ok, player = pcall(function() return exports.qbx_core:GetPlayer(src) end)
        local md = ok and player and player.PlayerData and player.PlayerData.metadata
        if md and (md.isdead or md.inlaststand) then return true end
    elseif GetResourceState and GetResourceState('qb-core') == 'started' then
        local ok, player = pcall(function() return exports['qb-core']:GetCoreObject().Functions.GetPlayer(src) end)
        local md = ok and player and player.PlayerData and player.PlayerData.metadata
        if md and (md.isdead or md.inlaststand) then return true end
    end
    return false
end

local function nameOf(m, id)''')

edit(base+'modules/server/match.lua', '''    local players = {}
    for ti = 1, 2 do
        for _, s in ipairs(R.teams[ti].initial) do
            local st = R.stats[s] or {}
            if not isBot(s) then players[#players + 1] = { identifier = VB.Stats.identifier(s), name = GetPlayerName(s) or ('#' .. s), team = ti, setsWon = R.teams[ti].sets,
                points = st.points or 0, aces = st.aces or 0, kills = st.kills or 0, blocks = st.blocks or 0, digs = st.digs or 0,
                assists = st.assists or 0, errors = st.errors or 0 } end
        end
    end''', '''    local players = {}
    for _, rec in ipairs(m.roster) do
        local st = rec.stats or {}
        players[#players + 1] = { identifier = rec.identifier, name = rec.name, team = rec.team, setsWon = R.teams[rec.team].sets,
            points = st.points or 0, aces = st.aces or 0, kills = st.kills or 0, blocks = st.blocks or 0, digs = st.digs or 0,
            assists = st.assists or 0, errors = st.errors or 0 }
    end''')

edit(base+'modules/server/match.lua', '''    if VB.FreePlay and VB.FreePlay.suspend then VB.FreePlay.suspend() end''', '''    active.roster = {}
    for ti = 1, 2 do
        for _, p in ipairs(lobby['team' .. ti].players) do
            active.roster[#active.roster + 1] = { src = p.src, identifier = identity(p.src) or VB.Stats.identifier(p.src),
                name = GetPlayerName(p.src) or ('#' .. p.src), team = ti, jersey = p.jerseyNumber, stats = R_:stat(p.src) }
        end
    end
    if VB.FreePlay and VB.FreePlay.suspend then VB.FreePlay.suspend() end''')

edit(base+'modules/server/match.lua', '''-- Oyuncu lobiden ayrıldı / düştü (store:leave sonrası çağrılır)''', '''-- Store oyuncuyu silmeden önce dönüş hakkını ve bahis sahipliğini sakla.
function M.prepareLeave(lobbyId, src, reason)
    local m = active
    if not m or m.ending or m.lobbyId ~= lobbyId then return end
    for _, rec in ipairs(m.roster) do
        if rec.src == src then
            rec.src = nil
            rec.reason = reason
            local opts = CFG.Rejoin or {}
            rec.canReturn = (reason == 'disconnect' and opts.AfterDisconnect == true) or (reason == 'death' and opts.AfterDeath == true)
            local paid = m.lobby.paidBySrc
            local key = 'absent:' .. rec.identifier
            paid[key], paid[tostring(src)] = paid[tostring(src)] or 0, nil
            rec.paidKey = key
            break
        end
    end
end

-- /vbgeri: yalnızca sunucunun tuttuğu eski katılımcı, sağken, devam eden maçına dönebilir.
function M.rejoin(src)
    local m = active
    if not m or m.ending or isDead(src) or lobbyStore():lobbyOf(src) then return false end
    local id = identity(src)
    if not id then return false end
    local lobby = lobbyStore().lobbies[m.lobbyId]
    if not lobby then return false end
    for _, rec in ipairs(m.roster) do
        local opts = CFG.Rejoin or {}
        local enabled = (rec.reason == 'disconnect' and opts.AfterDisconnect == true) or (rec.reason == 'death' and opts.AfterDeath == true)
        if rec.identifier == id and not rec.src and rec.canReturn and enabled then
            local team = m.R.teams[rec.team]
            team.order[#team.order + 1], team.initial[#team.initial + 1] = src, src
            -- Eski source başka bir oyuncuya verilmiş olabilir: istatistikler kayıttan taşınır.
            m.R.stats[src] = rec.stats
            rec.src, rec.canReturn, rec.reason = src, false, nil
            local paid = lobby.paidBySrc
            paid[tostring(src)], paid[rec.paidKey] = paid[rec.paidKey] or 0, nil
            lobby['team' .. rec.team].players[#lobby['team' .. rec.team].players + 1] = lobbyStore():playerEntry(src, rec.jersey)
            TriggerClientEvent(EV .. 'match:enter', src, { lobbyId = m.lobbyId, names = names(m),
                teamNames = { lobby.team1.name, lobby.team2.name }, serveClip = CFG.ServeClip })
            local x, y, _, h = VB.Rules.formation(court, m.R.sideOf[rec.team], #team.order)
            place(src, x, y, h)
            sendState(m)
            sendBall(m, src)
            syncLobbyScores(m)
            return true
        end
    end
    return false
end

RegisterCommand('vbgeri', function(src)
    if src == 0 then return end
    if not M.rejoin(src) then TriggerClientEvent(EV .. 'match:msg', src, { ok = false, sebep = 'rejoin_unavailable' }) end
end, false)

CreateThread(function()
    while true do
        Wait(500)
        local m = active
        if m and not m.ending then
            local dead = {}
            for _, rec in ipairs(m.roster) do
                if rec.src and isDead(rec.src) then dead[#dead + 1] = rec.src end
            end
            for _, src in ipairs(dead) do VB.MatchUnavailable(src, 'death') end
        end
    end
end)

-- Oyuncu lobiden ayrıldı / düştü (store:leave sonrası çağrılır)''')

edit(base+'modules/server/match.lua', '''    m.R:removePlayer(src, now())
    handleEvents(m)''', '''    m.R:removePlayer(src, now())
    -- Host ayrılınca NPC yönetimi kalan host'a geçer.
    local lobby = lobbyStore().lobbies[lobbyId]
    if lobby and m.hostSrc ~= lobby.host then
        m.hostSrc = lobby.host
        TriggerClientEvent(EV .. 'match:enter', m.hostSrc, { lobbyId = m.lobbyId, names = names(m),
            teamNames = { lobby.team1.name, lobby.team2.name }, serveClip = CFG.ServeClip, bots = m.bots })
        for _, b in ipairs(m.bots) do
            local p = m.botState[b.id]
            if p then place(b.id, p.x, p.y, p.heading) end
        end
    end
    if not lobby then m.R:forceEnd(now(), 0, 'empty') end
    handleEvents(m)
    if not m.ending then sendState(m) end''')

edit(base+'modules/client/match.lua', "    uzak = 'top erişim dışı'", "    rejoin_unavailable = 'Devam eden maça dönüş hakkın yok veya henüz hayatta değilsin.',\n    uzak = 'top erişim dışı'")

# Existing test harness overwrote same-name event handlers, hiding real playerDropped ordering.
edit('tests/smoke_match.lua', 'function AddEventHandler(name, fn) handlers[name] = fn end', '''function AddEventHandler(name, fn)
    local prev = handlers[name]
    handlers[name] = function(...) if prev then prev(...) end; fn(...) end
end
function GetEntityHealth(ped) return players[ped - 1000] and (players[ped - 1000].health or 200) or 0 end''')
edit('tests/smoke_match.lua', "function GetPlayerIdentifiers(src) return { 'license:abc' .. src } end", "function GetPlayerIdentifiers(src) return { players[src] and players[src].license or ('license:abc' .. src) } end")

print('Match return implementation applied')
