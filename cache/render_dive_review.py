import sys,json
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'pipeline'))
import bpy,numpy as np
from mathutils import Vector
from lib import ped,clips,render
cfg=json.loads((ROOT/'config.json').read_text());ped.import_ped_parts(cfg['game_dir'],'mp_m_freemode_01');ped.clean_scene_extras();arm=ped.merge_armatures();ped.simplify_materials();arm.animation_data_create()
data=json.loads((ROOT/'output/vb_dive/v16.action.json').read_text());c=clips.LoadedClip(arm,'review',data['frames'],data['fps'],data['curves']);arm.animation_data.action=c.action
floor=min(b.head_local.z for b in arm.data.bones if b.name.startswith('SKEL_'));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];worst=(10,'',0)
for f in range(data['frames']+1):
 bpy.context.scene.frame_set(f);dg=bpy.context.evaluated_depsgraph_get()
 for o in meshes:
  ob=o.evaluated_get(dg);me=ob.to_mesh();co=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',co);co=co.reshape(-1,3);z=co @ np.array(ob.matrix_world[2][:3])+ob.matrix_world[2][3]-floor;lo=float(z.min())
  if lo<worst[0]:worst=(lo,o.name,f)
  ob.to_mesh_clear()
print('MESH_GROUND',worst,flush=True)
sc,cam=render._setup(640,640);fl=bpy.data.objects['preview_floor'];fl.location=(0,.5,floor-.02);render._aim(cam,render.VIEWS['side'],Vector((0,.5,floor+1.1)),2.6)
sc.render.image_settings.file_format='FFMPEG';sc.render.ffmpeg.format='MPEG4';sc.render.ffmpeg.codec='H264';sc.render.ffmpeg.constant_rate_factor='HIGH';sc.render.ffmpeg.gopsize=15;sc.render.fps=30;sc.frame_start=0;sc.frame_end=data['frames'];sc.render.filepath=str(ROOT/'cache/preview/video/vb_dive_v16_side.mp4');sc.render.use_file_extension=False
Path(sc.render.filepath).parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(animation=True)
print('VIDEO_DONE',sc.render.filepath,flush=True)
