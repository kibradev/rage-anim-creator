export type Ped = { name: string; url: string }
export type Clip = {
  dict: string
  name: string
  duration: number
  fps: number
  url: string
  version?: number
  label?: string
  latest?: boolean
  status?: 'pending' | 'approved' | 'rejected'
  report?: Report
  exportUrl?: string | null
}
export type Report = {
  frames: number
  duration: number
  fps: number
  loop: boolean
  bones: number
  loop_gap_deg?: number
  max_step_deg?: number
  max_step_at?: string
}
export type Job = { id: string; state: 'running' | 'done' | 'failed'; log: string[]; title: string }
