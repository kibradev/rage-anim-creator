import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ClipList } from '@/components/ClipList'
import { Slider } from '@/components/ui/slider'
import type { Clip, Ped } from '@/lib/types'
import type { BallOffsets, Vec3 } from '@/lib/ball'

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
  game: boolean
  onGame: (v: boolean) => void
  ballOn: boolean
  onBallOn: (v: boolean) => void
  useOffset: boolean
  onUseOffset: (v: boolean) => void
  offsets: BallOffsets
  onOffsets: (o: BallOffsets) => void
  ballAvailable: boolean
}

export function Sidebar({ peds, ped, onPed, skeleton, onSkeleton, clips, mine, tab, onTab, clip, onClip, inPlace, onInPlace, game, onGame, ballOn, onBallOn, useOffset, onUseOffset, offsets, onOffsets, ballAvailable }: Props) {
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
      <label className="flex items-center justify-between text-sm" title="Export edilen .ycd dosyasını geri çözüp oynatır: oyunun gördüğü veri">
        Oyun verisi (.ycd'den geri çözülmüş)
        <Switch checked={game} onCheckedChange={onGame} />
      </label>
      <label className="flex items-center justify-between text-sm">
        İskelet
        <Switch checked={skeleton} onCheckedChange={onSkeleton} />
      </label>

      <div className="flex flex-col gap-2 border-t border-border pt-3">
        <label className="flex items-center justify-between text-sm" title="p_vb_volleyball.ydr: topu elde tutma/alma/atma kliplerinde gerçek top modeli">
          Voleybol topu (.ydr)
          <Switch checked={ballOn} onCheckedChange={onBallOn} disabled={!ballAvailable} />
        </label>
        {ballOn && ballAvailable && (
          <>
            <label className="flex items-center justify-between text-xs text-muted-foreground" title="Oyundaki Config.Carry.Offset: animasyonun hesapladığı yere ek">
              Oyundaki top ofseti uygula
              <Switch checked={useOffset} onCheckedChange={onUseOffset} />
            </label>
            {(['hold', 'carry'] as const).map((st) => (
              <div key={st} className="flex flex-col gap-1.5">
                <div className="text-xs font-medium">{st === 'hold' ? 'İki el tutuş' : 'Sol koltuk altı'} (cm)</div>
                {(['x sağ', 'y ileri', 'z yukarı'] as const).map((lbl, i) => (
                  <div key={lbl} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="w-14">{lbl}</span>
                    <Slider
                      className="flex-1"
                      min={-20}
                      max={20}
                      step={1}
                      value={[offsets[st][i]]}
                      onValueChange={(v) => {
                        const n = (Array.isArray(v) ? v[0] : v) as number
                        const arr = [...offsets[st]] as Vec3
                        arr[i] = n
                        onOffsets({ ...offsets, [st]: arr })
                      }}
                    />
                    <span className="w-8 text-right tabular-nums">{offsets[st][i]}</span>
                  </div>
                ))}
                <code className="whitespace-pre rounded bg-muted px-1.5 py-1 text-[10px] leading-4 text-muted-foreground">
                  {(['x', 'y', 'z'] as const).map((ax, i) => `/vbtopayar ${st} ${ax} ${offsets[st][i]}`).join('\n')}
                </code>
              </div>
            ))}
          </>
        )}
      </div>
    </aside>
  )
}
