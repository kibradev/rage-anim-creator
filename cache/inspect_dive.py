import sys,json
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'pipeline'))
import bpy
from lib import ped,clips,posekeys
from clip_defs import volleyball
cfg=json.loads((ROOT/'config.json').read_text());ped.import_ped_parts(cfg['game_dir'],'mp_m_freemode_01');ped.clean_scene_extras();arm=ped.merge_armatures()
data=json.loads((ROOT/'output/vb_dive/v8.action.json').read_text());c=clips.LoadedClip(arm,'inspect',data['frames'],data['fps'],data['curves']);arm.animation_data_create();arm.animation_data.action=c.action
floor=min(b.head_local.z for b in arm.data.bones if b.name.startswith('SKEL_'));keys=posekeys._filled(volleyball.dive()[2]);out=[]
for f in [0,7,12,18,22,27,32,40,44,48,54,58,60,62,66]:
 bpy.context.scene.frame_set(f);p=posekeys.pose_at(keys,f);pos={b: [round(v,3) for v in arm.pose.bones[b].head] for b in ['SKEL_L_UpperArm','SKEL_L_Hand','SKEL_L_Calf','SKEL_L_Foot','SKEL_Head']};out.append(dict(f=f,floor=floor,pos=pos,target=p['hand_L']))
print('POSES',json.dumps(out))

