from pathlib import Path
import subprocess
Path('cache/original_clips.py').write_bytes(subprocess.check_output(['git','show','HEAD:pipeline/lib/clips.py']))
p=Path('cache/verify_dive.py');s=p.read_text(encoding='utf-8');s=s.replace("oldpk=module('oldpk'", "oldclips=module('lib.oldclips',ROOT/'cache/original_clips.py')\noldpk=module('oldpk'");s=s.replace('old=oldvb.build(arm,clips,name)','old=oldvb.build(arm,oldclips,name)');s=s.replace('delta=max(abs(x-y) for k in a for x,y in zip(a[k],b[k]));assert delta<1e-5,(name,delta);reg[name]=delta', '''delta=max(abs(x-y) for k in a for x,y in zip(a[k],b[k]))
 maxpos=0.0;maxangle=0.0
 for f in range(new.frames+1):
  arm.animation_data.action=old.action;bpy.context.scene.frame_set(f);bpy.context.view_layer.update();snapshot={pb.name:pb.matrix.copy() for pb in arm.pose.bones if pb.name.startswith('SKEL_')}
  arm.animation_data.action=new.action;bpy.context.scene.frame_set(f);bpy.context.view_layer.update()
  for bn,m in snapshot.items():
   n=arm.pose.bones[bn].matrix;maxpos=max(maxpos,(n.translation-m.translation).length);dot=abs(n.to_quaternion().normalized().dot(m.to_quaternion().normalized()));maxangle=max(maxangle,math.degrees(2*math.acos(min(1,dot))))
 assert maxpos<.001 and maxangle<.1,(name,maxpos,maxangle)
 reg[name]=dict(max_curve_component_delta=delta,max_position_m=maxpos,max_rotation_deg=maxangle)''');p.write_text(s,encoding='utf-8')
