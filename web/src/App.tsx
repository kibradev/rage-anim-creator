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
