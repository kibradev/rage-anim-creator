import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ClipList } from '@/components/ClipList'
import type { Clip, Ped } from '@/lib/types'

type Props = {
  peds: Ped[]
  ped: string | null
  onPed: (name: string) => void
  skeleton: boolean
  onSkeleton: (v: boolean) => void
  clips: Clip[]
  mine: Clip[]
  tab: 'orig' | 'mine'
  onTab: (t: 'orig' | 'mine') => void
  clip: Clip | null
  onClip: (c: Clip) => void
  inPlace: boolean
  onInPlace: (v: boolean) => void
}

export function Sidebar({ peds, ped, onPed, skeleton, onSkeleton, clips, mine, tab, onTab, clip, onClip, inPlace, onInPlace }: Props) {
  return (
    <aside className="flex w-72 shrink-0 flex-col gap-4 border-r border-border p-4">
      <div className="text-sm font-medium tracking-tight">animCreator</div>

      <Select
        items={peds.map((p) => ({ value: p.name, label: p.name }))}
        value={ped ?? null}
        onValueChange={(v) => v && onPed(v)}
        disabled={peds.length === 0}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder={peds.length ? 'Ped seç' : 'Ped bulunamadı'} />
        </SelectTrigger>
        <SelectContent>
          {peds.map((p) => (
            <SelectItem key={p.name} value={p.name}>
              {p.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Tabs value={tab} onValueChange={(v) => onTab(v as 'orig' | 'mine')}>
        <TabsList className="w-full">
          <TabsTrigger value="orig">Orijinal</TabsTrigger>
          <TabsTrigger value="mine">Benim{mine.length ? ` (${mine.length})` : ''}</TabsTrigger>
        </TabsList>
      </Tabs>
      <ClipList key={tab} clips={tab === 'orig' ? clips : mine} selected={clip} onSelect={onClip} />

      <label className="flex items-center justify-between text-sm">
        Yerinde (root motion kapalı)
        <Switch checked={inPlace} onCheckedChange={onInPlace} />
      </label>
      <label className="flex items-center justify-between text-sm">
        İskelet
        <Switch checked={skeleton} onCheckedChange={onSkeleton} />
      </label>
    </aside>
  )
}
