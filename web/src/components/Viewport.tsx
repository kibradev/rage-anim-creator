import { Suspense, useEffect, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Grid, OrbitControls, useGLTF } from '@react-three/drei'
import * as THREE from 'three'
import type { Player } from '@/lib/player'
import type { Clip } from '@/lib/types'

function ClipLoader({ clip, player }: { clip: Clip; player: Player }) {
  const { animations } = useGLTF(clip.url)
  useEffect(() => {
    const a = animations.find((x) => x.name === clip.name)
    if (a) player.play(a)
  }, [animations, clip, player])
  return null
}

function PedModel({ url, skeleton, player, clip }: { url: string; skeleton: boolean; player: Player; clip: Clip | null }) {
  const { scene } = useGLTF(url)
  const helper = useMemo(() => {
    const h = new THREE.SkeletonHelper(scene)
    h.visible = false
    return h
  }, [scene])

  useEffect(() => {
    helper.visible = skeleton
  }, [helper, skeleton])

  // peds have their origin at the pelvis: lift the model so the feet stand on the grid
  const lift = useMemo(() => {
    scene.updateMatrixWorld(true)
    const box = new THREE.Box3()
    scene.traverse((o) => {
      const m = o as THREE.Mesh
      if (m.isMesh) {
        m.geometry.computeBoundingBox()
        box.union(m.geometry.boundingBox!.clone().applyMatrix4(m.matrixWorld))
      }
    })
    return box.isEmpty() ? 0 : -box.min.y
  }, [scene])

  useEffect(() => {
    scene.traverse((o) => {
      if ((o as THREE.SkinnedMesh).isSkinnedMesh) o.frustumCulled = false
    })
    player.attach(scene)
    return () => player.detach()
  }, [scene, player])

  useFrame((_, dt) => player.update(dt))

  return (
    <>
      {/* GTA clips face the opposite way of the rest pose in glTF space */}
      <group rotation-y={Math.PI} position-y={lift}>
        <primitive object={scene} />
        <primitive object={helper} />
      </group>
      {clip && (
        <Suspense fallback={null}>
          <ClipLoader key={clip.dict} clip={clip} player={player} />
        </Suspense>
      )}
    </>
  )
}

type Props = { url: string | null; skeleton: boolean; player: Player; clip: Clip | null }

export function Viewport({ url, skeleton, player, clip }: Props) {
  return (
    <Canvas camera={{ position: [0, 1.15, 4.2], fov: 40 }} gl={{ antialias: true }}>
      <color attach="background" args={['#0b0b0d']} />
      <hemisphereLight args={['#ffffff', '#303040', 1.1]} />
      <directionalLight position={[3, 5, 4]} intensity={2} />
      <Grid args={[20, 20]} cellColor="#2a2a30" sectionColor="#3a3a44" fadeDistance={14} infiniteGrid />
      <Suspense fallback={null}>
        {url && <PedModel key={url} url={url} skeleton={skeleton} player={player} clip={clip} />}
      </Suspense>
      <OrbitControls target={[0, 0.95, 0]} makeDefault />
    </Canvas>
  )
}
