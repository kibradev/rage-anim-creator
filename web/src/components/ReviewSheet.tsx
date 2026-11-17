import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import type { Clip, Job } from '@/lib/types'

const STATUS_LABEL = { pending: 'Onay bekliyor', approved: 'Onaylandı', rejected: 'Reddedildi' } as const

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-4 text-sm">
      <span className="text-muted-foreground">{k}</span>
      <span className="text-right tabular-nums">{v}</span>
    </div>
  )
}

type Props = { clip: Clip; open: boolean; onOpenChange: (o: boolean) => void; onChanged: () => void }

export function ReviewSheet({ clip, open, onOpenChange, onChanged }: Props) {
  const [job, setJob] = useState<Job | null>(null)
  const status = clip.status ?? 'pending'
  const r = clip.report
  const base = `/api/mine/${encodeURIComponent(clip.name)}/${clip.version}`

  // follow the running export job
  useEffect(() => {
    if (!job || job.state !== 'running') return
    const id = setInterval(async () => {
      const list: Job[] = await fetch('/api/jobs').then((x) => x.json())
      const cur = list.find((j) => j.id === job.id)
      if (!cur) return
      setJob(cur)
      if (cur.state === 'done') {
        toast.success('.ycd hazır')
        onChanged()
      } else if (cur.state === 'failed') toast.error('Export başarısız')
    }, 1500)
    return () => clearInterval(id)
  }, [job, onChanged])

  const setStatus = async (s: string) => {
    await fetch(`${base}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: s }),
    })
    onChanged()
  }

  const startExport = async () => {
    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: clip.name, version: clip.version }),
    })
    if (!res.ok) {
      toast.error((await res.json()).detail ?? 'Export başlatılamadı')
      return
    }
    const { id } = await res.json()
    setJob({ id, state: 'running', log: [], title: '' })
  }

  const running = job?.state === 'running'

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex w-96 flex-col gap-4">
        <SheetHeader>
          <SheetTitle>
            {clip.name} · v{clip.version}
          </SheetTitle>
          <SheetDescription>{clip.label || 'Etiket yok'}</SheetDescription>
        </SheetHeader>

        <div className="flex flex-col gap-4 px-4">
          <Badge variant={status === 'approved' ? 'default' : 'secondary'} className="w-fit">
            {STATUS_LABEL[status]}
          </Badge>

          {r && (
            <div className="flex flex-col gap-2">
              <Row k="Süre" v={`${r.duration.toFixed(2)} s`} />
              <Row k="Kare" v={`${r.frames} @ ${r.fps} fps`} />
              <Row k="Animasyonlu kemik" v={String(r.bones)} />
              <Row k="Döngü farkı" v={`${r.loop_gap_deg ?? 0}°`} />
              <Row k="En hızlı adım" v={`${r.max_step_deg ?? 0}°/kare`} />
              {r.max_step_at && <Row k="Nerede" v={r.max_step_at} />}
            </div>
          )}

          <Separator />

          <div className="flex gap-2">
            <Button className="flex-1" disabled={status === 'approved'} onClick={() => setStatus('approved')}>
              Onayla
            </Button>
            <Button className="flex-1" variant="outline" disabled={status === 'rejected'} onClick={() => setStatus('rejected')}>
              Reddet
            </Button>
          </div>

          <Button variant="secondary" disabled={status !== 'approved' || running} onClick={startExport}>
            {running ? 'Export ediliyor…' : '.ycd olarak export et'}
          </Button>

          {job?.state === 'failed' && <p className="text-sm text-destructive">Export başarısız oldu.</p>}
          {clip.gameDiff && (
            <div className="flex flex-col gap-2">
              <Row k="Export → tasarım farkı" v={`${clip.gameDiff.rotDeg}° (${clip.gameDiff.rotBone})`} />
              <Row k="Kalça konum farkı" v={`${(clip.gameDiff.rootM * 1000).toFixed(1)} mm`} />
              <Row k="Kayıp kemik eğrisi" v={String(clip.gameDiff.missing)} />
            </div>
          )}
          {clip.exportUrl && (
            <div className="flex flex-col gap-1 text-sm">
              <a className="underline underline-offset-4" href={clip.exportUrl} download>
                {clip.name}.ycd indir
              </a>
              <span className="text-xs text-muted-foreground">
                Oyun içi test sana ait: sen doğrulayana kadar “çalışıyor” sayılmaz.
              </span>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
