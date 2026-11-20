import sys,json,importlib.util,math
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'pipeline'))
import bpy
from mathutils import Vector,Quaternion
from lib import ped,clips,posekeys
from clip_defs import volleyball
cfg=json.loads((ROOT/'config.json').read_text());ped.import_ped_parts(cfg['game_dir'],'mp_m_freemode_01');ped.clean_scene_extras();arm=ped.merge_armatures();arm.animation_data_create()
data=json.loads((ROOT/'output/vb_dive/v16.action.json').read_text());c=clips.LoadedClip(arm,'review',data['frames'],data['fps'],data['curves']);arm.animation_data.action=c.action
floor=min(b.head_local.z for b in arm.data.bones if b.name.startswith('SKEL_'))
watched=['SKEL_L_Calf','SKEL_R_Calf','SKEL_Pelvis','SKEL_Head','SKEL_Spine3','SKEL_L_Forearm','SKEL_R_Forearm']
minimum=(10,'',0);hands={};orientation={};yaw=arm.data.bones['SKEL_ROOT'].matrix_local @ Quaternion((0,0,0,1)).to_matrix().to_4x4() @ arm.data.bones['SKEL_ROOT'].matrix_local.inverted();frames=posekeys.rest_hand_frames(arm,yaw)
for f in range(data['frames']+1):
 bpy.context.scene.frame_set(f)
 for b in watched:
  z=arm.pose.bones[b].head.z-floor
  if z<minimum[0]:minimum=(z,b,f)
 if 27<=f<=40:
  hands[f]={}
  for side in 'LR':
   pb=arm.pose.bones[f'SKEL_{side}_Hand'];lf,bone,*_=frames[side];n=pb.matrix.to_3x3() @ bone.inverted() @ lf.col[2];hands[f][side]=[round(v,5) for v in (pb.head.x,pb.head.y,pb.head.z-floor)]
   orientation[f'{side}@{f}']=round(n.dot(Vector((0,0,-1))),6)
print('GROUND_QA',json.dumps(dict(min_joint_height=minimum,grounded_hands=hands,palm_down_dot_min=min(orientation.values()))))
assert minimum[0]>-0.02,minimum
assert min(orientation.values())>.999
for side in 'LR':
 vals=[Vector(hands[f][side]) for f in hands]
 assert max((v-vals[0]).length for v in vals)<.001
# Validate the opt-in solver controls against the original solver on existing clip families.
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
oldclips=module('lib.oldclips',ROOT/'cache/original_clips.py')
oldpk=module('oldpk',ROOT/'cache/original_posekeys.py');oldvb=module('oldvb',ROOT/'cache/original_volleyball.py')
reg={}
for name in ['vb_ready_idle','vb_spike','vb_hold']:
 oldvb.pk=oldpk;old=oldvb.build(arm,oldclips,name);old.finish();a={(fc.data_path,fc.array_index):[k.co.y for k in fc.keyframe_points] for fc in old.action.fcurves}
 new=volleyball.build(arm,clips,name);new.finish();b={(fc.data_path,fc.array_index):[k.co.y for k in fc.keyframe_points] for fc in new.action.fcurves}
 assert a.keys()==b.keys(),name
 delta=max(abs(x-y) for k in a for x,y in zip(a[k],b[k]))
 maxpos=0.0;maxangle=0.0
 for f in range(new.frames+1):
  arm.animation_data.action=old.action;bpy.context.scene.frame_set(f);bpy.context.view_layer.update();snapshot={pb.name:pb.matrix.copy() for pb in arm.pose.bones if pb.name.startswith('SKEL_')}
  arm.animation_data.action=new.action;bpy.context.scene.frame_set(f);bpy.context.view_layer.update()
  for bn,m in snapshot.items():
   n=arm.pose.bones[bn].matrix;maxpos=max(maxpos,(n.translation-m.translation).length);dot=abs(n.to_quaternion().normalized().dot(m.to_quaternion().normalized()));maxangle=max(maxangle,math.degrees(2*math.acos(min(1,dot))))
 assert maxpos<.001 and maxangle<.1,(name,maxpos,maxangle)
 reg[name]=dict(max_curve_component_delta=delta,max_position_m=maxpos,max_rotation_deg=maxangle)
print('REGRESSION_QA',json.dumps(reg))
(ROOT/'cache/preview/vb_dive_v16_review.json').write_text(json.dumps(dict(min_joint_height=minimum,palm_down_dot_min=min(orientation.values()),grounded_hands=hands,regression=reg),indent=2))


