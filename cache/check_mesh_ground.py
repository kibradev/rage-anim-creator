import sys,json
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'pipeline'))
import bpy,numpy as np
from mathutils import Vector
from lib import ped,clips,render
cfg=json.loads((ROOT/'config.json').read_text());ped.import_ped_parts(cfg['game_dir'],'mp_m_freemode_01');ped.clean_scene_extras();arm=ped.merge_armatures();ped.simplify_materials();arm.animation_data_create()
data=json.loads((ROOT/'output/vb_dive/v16.action.json').read_text());c=clips.LoadedClip(arm,'review',data['frames'],data['fps'],data['curves']);arm.animation_data.action=c.action
floor=min(b.head_local.z for b in arm.data.bones if b.name.startswith('SKEL_'));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];worst=(10,'',0);permesh={};baseline=10
for f in range(data['frames']+1):
 bpy.context.scene.frame_set(f);dg=bpy.context.evaluated_depsgraph_get()
 for o in meshes:
  ob=o.evaluated_get(dg);me=ob.to_mesh();co=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',co);co=co.reshape(-1,3);z=co @ np.array(ob.matrix_world[2][:3])+ob.matrix_world[2][3]-floor;lo=float(z.min())
  if lo<worst[0]:worst=(lo,o.name,f)
  if f==0:baseline=min(baseline,lo)
  if o.name not in permesh or lo<permesh[o.name][0]:permesh[o.name]=(lo,f)
  ob.to_mesh_clear()
print('MESH_GROUND',worst,flush=True)
print('PER_MESH',permesh)
print('ACTUAL_FLOOR_QA',dict(baseline=baseline,worst=worst[0],extra_penetration=baseline-worst[0]))
assert baseline-worst[0]<.005
