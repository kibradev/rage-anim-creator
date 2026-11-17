import { useMemo } from 'react'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import type { Clip } from '@/lib/types'

type Props = { clips: Clip[]; selected: Clip | null; onSelect: (c: Clip) => void }

export function ClipList({ clips, selected, onSelect }: Props) {
  const groups = useMemo(() => {
    const m = new Map<string, Clip[]>()
    for (const c of clips) m.set(c.dict, [...(m.get(c.dict) ?? []), c])
    return [...m.entries()]
  }, [clips])

  return (
    <Command className="min-h-0 flex-1 rounded-lg border border-border bg-transparent">
      <CommandInput placeholder="Animasyon ara…" />
      <CommandList className="max-h-none flex-1">
        <CommandEmpty>Sonuç yok</CommandEmpty>
        {groups.map(([dict, list]) => (
          <CommandGroup key={dict} heading={dict}>
            {list.map((c) => (
              <CommandItem
                key={c.url + c.name}
                value={`${c.dict} ${c.name} ${c.version ?? ''}`}
                data-checked={selected?.url === c.url && selected.name === c.name}
                onSelect={() => onSelect(c)}
              >
                <span className="truncate">{c.name.replace(/\.clip$/, '')}</span>
                {c.version && (
                  <span className="ml-auto text-xs text-muted-foreground">
                    v{c.version}
                    {c.label ? ` · ${c.label}` : ''}
                  </span>
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        ))}
      </CommandList>
    </Command>
  )
}
