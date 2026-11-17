local CLIPS = {
    ['vb_block'] = { loop = false },
    ['vb_bump'] = { loop = false },
    ['vb_celebrate'] = { loop = false },
    ['vb_dig_low'] = { loop = false },
    ['vb_dig_side_L'] = { loop = false },
    ['vb_dig_side_R'] = { loop = false },
    ['vb_ready_idle'] = { loop = true },
    ['vb_serve_over'] = { loop = false },
    ['vb_serve_under'] = { loop = false },
    ['vb_set'] = { loop = false },
    ['vb_shuffle_L'] = { loop = true },
    ['vb_shuffle_R'] = { loop = true },
    ['vb_spike'] = { loop = false },
    ['wave_hand'] = { loop = false }
}

RegisterCommand('animtest', function(_, args)
    local name = args[1]
    if not name or not CLIPS[name] then
        local names = {}
        for k in pairs(CLIPS) do names[#names + 1] = k end
        table.sort(names)
        print('animtest: ' .. table.concat(names, ', '))
        TriggerEvent('chat:addMessage', { args = { 'animtest', table.concat(names, ', ') } })
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
