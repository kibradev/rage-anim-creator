import * as THREE from 'three'

/** Thin wrapper around AnimationMixer: one active clip, crossfade, speed, loop, scrubbing. */
export class Player {
  private mixer: THREE.AnimationMixer | null = null
  private action: THREE.AnimationAction | null = null
  speed = 1
  loop = true
  paused = false
  inPlace = true
  private rootName = ''
  private source: THREE.AnimationClip | null = null

  attach(root: THREE.Object3D) {
    this.mixer?.stopAllAction()
    this.mixer = new THREE.AnimationMixer(root)
    this.action = null
    this.rootName = root.children[0]?.name ?? ''
  }

  detach() {
    this.mixer?.stopAllAction()
    this.mixer = null
    this.action = null
  }

  /** Root motion = translation of the armature node (the game's mover). In-place drops it. */
  private prepare(clip: THREE.AnimationClip) {
    if (!this.inPlace || !this.rootName) return clip
    const c = clip.clone()
    c.name = clip.name + (this.inPlace ? '#inplace' : '')
    c.tracks = c.tracks.filter((t) => t.name !== `${this.rootName}.position`)
    return c
  }

  setInPlace(v: boolean) {
    this.inPlace = v
    if (this.source) {
      const t = this.time
      this.play(this.source, 0)
      this.seek(t)
    }
  }

  play(source: THREE.AnimationClip, fade = 0.2) {
    if (!this.mixer) return
    this.source = source
    const clip = this.prepare(source)
    const next = this.mixer.clipAction(clip)
    next.reset()
    next.enabled = true
    next.setLoop(this.loop ? THREE.LoopRepeat : THREE.LoopOnce, Infinity)
    next.clampWhenFinished = true
    next.timeScale = this.speed
    next.play()
    if (this.action && this.action !== next) this.action.crossFadeTo(next, fade, false)
    this.action = next
    this.paused = false
  }

  stop() {
    this.mixer?.stopAllAction()
    this.action = null
  }

  update(dt: number) {
    if (!this.mixer) return
    this.mixer.update(this.paused ? 0 : dt)
  }

  get duration() {
    return this.action?.getClip().duration ?? 0
  }

  get time() {
    return this.action ? this.action.time : 0
  }

  get hasClip() {
    return this.action !== null
  }

  seek(t: number) {
    if (!this.action || !this.mixer) return
    this.action.time = Math.max(0, Math.min(t, this.duration))
    this.mixer.update(0)
  }

  setSpeed(v: number) {
    this.speed = v
    if (this.action) this.action.timeScale = v
  }

  setLoop(v: boolean) {
    this.loop = v
    if (this.action) this.action.setLoop(v ? THREE.LoopRepeat : THREE.LoopOnce, Infinity)
  }

  toggle() {
    if (!this.action) return
    if (!this.paused && !this.loop && this.time >= this.duration - 1e-3) {
      this.action.reset().play()
    }
    this.paused = !this.paused
  }
}
