import { useEffect, useState } from 'react'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Sidebar } from '@/components/Sidebar'
import { Viewport } from '@/components/Viewport'
import type { Ped } from '@/lib/types'

export default function App() {
  const [peds, setPeds] = useState<Ped[]>([])
  const [ped, setPed] = useState<string | null>(null)
  const [skeleton, setSkeleton] = useState(false)

  useEffect(() => {
    fetch('/api/peds')
      .then((r) => r.json())
      .then((list: Ped[]) => {
        setPeds(list)
        setPed((cur) => cur ?? list[0]?.name ?? null)
      })
      .catch(() => setPeds([]))
  }, [])

  const current = peds.find((p) => p.name === ped) ?? null

  return (
    <TooltipProvider>
      <div className="dark flex h-screen w-screen overflow-hidden bg-background text-foreground">
        <Sidebar peds={peds} ped={ped} onPed={setPed} skeleton={skeleton} onSkeleton={setSkeleton} />
        <main className="relative min-w-0 flex-1">
          <Viewport url={current?.url ?? null} skeleton={skeleton} />
        </main>
      </div>
      <Toaster />
    </TooltipProvider>
  )
}
