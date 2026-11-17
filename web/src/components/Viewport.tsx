import { Suspense, useEffect, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { Grid, OrbitControls, useGLTF } from '@react-three/drei'
import * as THREE from 'three'

function PedModel({ url, skeleton }: { url: string; skeleton: boolean }) {
  const { scene } = useGLTF(url)
  const helper = useMemo(() => {
    const h = new THREE.SkeletonHelper(scene)
    h.visible = false
    return h
  }, [scene])

  useEffect(() => {
    helper.visible = skeleton
  }, [helper, skeleton])

  useEffect(() => {
    scene.traverse((o) => {
      if ((o as THREE.SkinnedMesh).isSkinnedMesh) o.frustumCulled = false
    })
  }, [scene])

  return (
    <>
      <primitive object={scene} />
      <primitive object={helper} />
    </>
  )
}

export function Viewport({ url, skeleton }: { url: string | null; skeleton: boolean }) {
  return (
    <Canvas camera={{ position: [0, 1.2, 3.2], fov: 40 }} gl={{ antialias: true }}>
      <color attach="background" args={['#0b0b0d']} />
      <hemisphereLight args={['#ffffff', '#303040', 1.1]} />
      <directionalLight position={[3, 5, 4]} intensity={2} />
      <Grid args={[20, 20]} cellColor="#2a2a30" sectionColor="#3a3a44" fadeDistance={14} infiniteGrid />
      <Suspense fallback={null}>{url && <PedModel key={url} url={url} skeleton={skeleton} />}</Suspense>
      <OrbitControls target={[0, 0.9, 0]} makeDefault />
    </Canvas>
  )
}
