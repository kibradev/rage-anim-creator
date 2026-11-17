import { useEffect, useRef, useState } from 'react'
import { Pause, Play } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import type { Player } from '@/lib/player'

const SPEEDS = ['0.25', '0.5', '1', '2']

export function Timeline({ player, label }: { player: Player; label: string }) {
  const [time, setTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [paused, setPaused] = useState(false)
  const [loop, setLoop] = useState(true)
  const [speed, setSpeed] = useState('1')
  const scrubbing = useRef(false)

  useEffect(() => {
    let raf = 0
    const tick = () => {
      if (!scrubbing.current) setTime(player.time)
      setDuration(player.duration)
      setPaused(player.paused)
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [player])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !(e.target instanceof HTMLInputElement)) {
        e.preventDefault()
        player.toggle()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [player])

  const disabled = duration === 0

  return (
    <div className="flex items-center gap-4 border-t border-border px-4 py-3">
      <Button size="icon" variant="ghost" disabled={disabled} onClick={() => player.toggle()}>
        {paused ? <Play /> : <Pause />}
      </Button>
      <Slider
        className="flex-1"
        min={0}
        max={Math.max(duration, 0.001)}
        step={0.001}
        value={[Math.min(time, duration)]}
        disabled={disabled}
        onValueChange={(v) => {
          scrubbing.current = true
          const t = Array.isArray(v) ? v[0] : v
          setTime(t)
          player.paused = true
          player.seek(t)
        }}
        onValueCommitted={() => {
          scrubbing.current = false
        }}
      />
      <span className="w-28 text-right text-xs tabular-nums text-muted-foreground">
        {time.toFixed(2)} / {duration.toFixed(2)} s
      </span>
      <ToggleGroup
        value={[speed]}
        onValueChange={(v) => {
          const s = v[0]
          if (!s) return
          setSpeed(s)
          player.setSpeed(Number(s))
        }}
        variant="outline"
        size="sm"
      >
        {SPEEDS.map((s) => (
          <ToggleGroupItem key={s} value={s}>
            {s}x
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
      <label className="flex items-center gap-2 text-xs text-muted-foreground">
        Döngü
        <Switch
          checked={loop}
          onCheckedChange={(v) => {
            setLoop(v)
            player.setLoop(v)
          }}
        />
      </label>
      <span className="hidden max-w-48 truncate text-xs text-muted-foreground xl:block">{label}</span>
    </div>
  )
}
