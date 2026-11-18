import { useCallback, useEffect, useRef, useState } from 'react'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { ReviewSheet } from '@/components/ReviewSheet'
import { Button } from '@/components/ui/button'
import { Sidebar } from '@/components/Sidebar'
import { Timeline } from '@/components/Timeline'
import { Viewport } from '@/components/Viewport'
import { Player } from '@/lib/player'
import type { Clip, Ped } from '@/lib/types'
import type { BallOffsets, BallPaths } from '@/lib/ball'

export default function App() {
  const [peds, setPeds] = useState<Ped[]>([])
  const [ped, setPed] = useState<string | null>(null)
  const [clips, setClips] = useState<Clip[]>([])
  const [mine, setMine] = useState<Clip[]>([])
  const [tab, setTab] = useState<'orig' | 'mine'>('orig')
  const [clip, setClip] = useState<Clip | null>(null)
  const [review, setReview] = useState(false)
  const [skeleton, setSkeleton] = useState(false)
  const [inPlace, setInPlace] = useState(true)
  const [game, setGame] = useState(false)
  const player = useRef(new Player()).current
  const [ballOn, setBallOn] = useState(true)
  const [ballPaths, setBallPaths] = useState<BallPaths | null>(null)
  const [useOffset, setUseOffset] = useState(true)
  const [offsets, setOffsets] = useState<BallOffsets>({ hold: [0, 0, 7], carry: [0, 0, 0] })

  useEffect(() => {
    fetch('/files/output/ball_paths.json')
      .then((r) => r.json())
      .then((j: BallPaths) => {
        setBallPaths(j)
        setOffsets({
          hold: j.offset.hold.map((v) => Math.round(v * 100)) as BallOffsets['hold'],
          carry: j.offset.carry.map((v) => Math.round(v * 100)) as BallOffsets['carry'],
        })
      })
      .catch(() => setBallPaths(null))
  }, [])

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
  const loadMine = useCallback(
    () =>
      fetch('/api/mine')
        .then((r) => r.json())
        .then((list: Clip[]) => setMine((prev) => (JSON.stringify(prev) === JSON.stringify(list) ? prev : list)))
        .catch(() => {}),
    [],
  )
  useEffect(() => {
    loadMine()
    const id = setInterval(loadMine, 3000)
    return () => clearInterval(id)
  }, [loadMine])

  // keep the selected authored clip in sync with status/export changes
  const liveClip = clip?.version ? (mine.find((m) => m.url === clip.url) ?? clip) : clip

  // "game" view: the clip decoded back from the exported .ycd (what FiveM actually loads)
  const shown = game && liveClip?.gameUrl ? { ...liveClip, url: liveClip.gameUrl } : clip

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
          game={game}
          onGame={setGame}
          ballOn={ballOn}
          onBallOn={setBallOn}
          useOffset={useOffset}
          onUseOffset={setUseOffset}
          offsets={offsets}
          onOffsets={setOffsets}
          ballAvailable={!!ballPaths}
          onInPlace={(v) => {
            setInPlace(v)
            player.setInPlace(v)
          }}
        />
        <div className="flex min-w-0 flex-1 flex-col">
          <main className="relative min-h-0 flex-1">
            <Viewport url={current?.url ?? null} skeleton={skeleton} player={player} clip={shown} ball={{ on: ballOn, paths: ballPaths, offsets, useOffset }} />
            {liveClip?.version && (
              <Button className="absolute top-4 right-4" variant="secondary" size="sm" onClick={() => setReview(true)}>
                İncele
              </Button>
            )}
          </main>
          <Timeline player={player} label={clip ? clip.name.replace(/\.clip$/, '') + (game && liveClip?.gameUrl ? '  [oyun verisi]' : game && clip.version ? '  [export yok]' : '') : ''} />
        </div>
      </div>
      {liveClip?.version && (
        <ReviewSheet clip={liveClip} open={review} onOpenChange={setReview} onChanged={loadMine} />
      )}
      <Toaster />
    </TooltipProvider>
  )
}
