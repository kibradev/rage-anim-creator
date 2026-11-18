import type { Player } from '@/lib/player'

/** output/ball_paths.json (pipeline/dump_ball_paths.py): top merkezi yolu, armatür/glTF bone uzayında (x sağ, y ileri, z yukarı, zemin dahil). */
export type BallClip = { fps: number; frames: number; loop: boolean; floor: number; style: 'hold' | 'carry'; p: [number, number, number][] }
export type BallPaths = { offset: { hold: number[]; carry: number[] }; radius: number; clips: Record<string, BallClip> }
export type Vec3 = [number, number, number]
/** Oyundaki top konumu ek ofseti, santimetre (karakter uzayı: x sağ, y ileri, z yukarı) */
export type BallOffsets = { hold: Vec3; carry: Vec3 }

const GRAB_FRAME = 14 // vb_pickup: kavrama karesi; ofset kavramadan sonra yumuşakça devreye girer (oyundaki C.pathOff ile aynı)

const smooth = (t: number) => t * t * (3 - 2 * t)

/** Klibin şimdiki zamanında top konumu (bone uzayı, m) + oyundaki ofset. null: bu klip için top yok. */
export function ballAt(paths: BallPaths | null, clipName: string, player: Player, off: BallOffsets, useOffset: boolean): Vec3 | null {
  const c = paths?.clips[clipName]
  if (!c) return null
  const t = player.time
  const f = Math.min(Math.max(t * c.fps, 0), c.frames)
  const i = Math.min(Math.floor(f), c.frames - 1)
  const k = f - i
  const a = c.p[i]
  const b = c.p[i + 1] ?? a
  const p: Vec3 = [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k]
  if (!useOffset) return p
  let w = 1
  if (clipName === 'vb_pickup') {
    const ev = GRAB_FRAME / c.fps
    const dur = c.frames / c.fps
    w = smooth(Math.min(Math.max((t - ev) / (dur - ev), 0), 1))
  }
  const o = c.style === 'carry' ? off.carry : off.hold
  return [p[0] + (o[0] / 100) * w, p[1] + (o[1] / 100) * w, p[2] + (o[2] / 100) * w]
}
