import { useEffect, useRef, useState } from 'react'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Sidebar } from '@/components/Sidebar'
import { Timeline } from '@/components/Timeline'
import { Viewport } from '@/components/Viewport'
import { Player } from '@/lib/player'
import type { Clip, Ped } from '@/lib/types'

export default function App() {
  const [peds, setPeds] = useState<Ped[]>([])
  const [ped, setPed] = useState<string | null>(null)
  const [clips, setClips] = useState<Clip[]>([])
  const [mine, setMine] = useState<Clip[]>([])
  const [tab, setTab] = useState<'orig' | 'mine'>('orig')
  const [clip, setClip] = useState<Clip | null>(null)
  const [skeleton, setSkeleton] = useState(false)
  const [inPlace, setInPlace] = useState(true)
  const player = useRef(new Player()).current

  useEffect(() => {
    fetch('/api/peds')
      .then((r) => r.json())
      .then((list: Ped[]) => {
        setPeds(list)
        setPed((cur) => cur ?? list[0]?.name ?? null)
      })
      .catch(() => setPeds([]))
    fetch('/api/clips')
      .then((r) => r.json())
      .then((list: Clip[]) => {
        setClips(list)
        setClip((cur) => cur ?? list.find((c) => c.name === 'idle.clip') ?? null)
      })
      .catch(() => setClips([]))
  }, [])

  // authored clips: poll so a newly generated version shows up without reloading
  useEffect(() => {
    let alive = true
    const load = () =>
      fetch('/api/mine')
        .then((r) => r.json())
        .then((list: Clip[]) => {
          if (!alive) return
          setMine((prev) => (JSON.stringify(prev) === JSON.stringify(list) ? prev : list))
        })
        .catch(() => {})
    load()
    const id = setInterval(load, 3000)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [])

  const current = peds.find((p) => p.name === ped) ?? null

  return (
    <TooltipProvider>
      <div className="dark flex h-screen w-screen overflow-hidden bg-background text-foreground">
        <Sidebar
          peds={peds}
          ped={ped}
          onPed={setPed}
          skeleton={skeleton}
          onSkeleton={setSkeleton}
          clips={clips}
          mine={mine}
          tab={tab}
          onTab={setTab}
          clip={clip}
          onClip={setClip}
          inPlace={inPlace}
          onInPlace={(v) => {
            setInPlace(v)
            player.setInPlace(v)
          }}
        />
        <div className="flex min-w-0 flex-1 flex-col">
          <main className="relative min-h-0 flex-1">
            <Viewport url={current?.url ?? null} skeleton={skeleton} player={player} clip={clip} />
          </main>
          <Timeline player={player} label={clip ? clip.name.replace(/\.clip$/, '') : ''} />
        </div>
      </div>
      <Toaster />
    </TooltipProvider>
  )
}
