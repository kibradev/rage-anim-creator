import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import type { Ped } from '@/lib/types'

type Props = {
  peds: Ped[]
  ped: string | null
  onPed: (name: string) => void
  skeleton: boolean
  onSkeleton: (v: boolean) => void
}

export function Sidebar({ peds, ped, onPed, skeleton, onSkeleton }: Props) {
  return (
    <aside className="flex w-72 shrink-0 flex-col gap-4 border-r border-border p-4">
      <div className="text-sm font-medium tracking-tight">animCreator</div>

      <div className="flex flex-col gap-2">
        <span className="text-xs text-muted-foreground">Ped</span>
        <Select items={peds.map((p) => ({ value: p.name, label: p.name }))} value={ped ?? undefined} onValueChange={(v) => v && onPed(v)} disabled={peds.length === 0}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder={peds.length ? 'Seç' : 'Ped bulunamadı'} />
          </SelectTrigger>
          <SelectContent>
            {peds.map((p) => (
              <SelectItem key={p.name} value={p.name}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Separator />

      <label className="flex items-center justify-between text-sm">
        İskelet
        <Switch checked={skeleton} onCheckedChange={onSkeleton} />
      </label>
    </aside>
  )
}
