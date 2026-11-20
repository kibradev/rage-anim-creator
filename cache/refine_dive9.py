from pathlib import Path
p=Path('pipeline/clip_defs/volleyball.py');s=p.read_text(encoding='utf-8');a=s.index('def dive():');b=s.index('\n\ndef shuffle_R()',a);d=s[a:b]
for old,new in [('0.68, -0.62','0.68, -0.68'),('0.74, -0.70','0.74, -0.76'),('0.68, -0.65','0.68, -0.71'),('0.53, -0.62','0.53, -0.68'),('"pelvis": (45, 0, 0), "spine": (70, 0, 0), "chest": (14, 0, 0)','"pelvis": (45, 0, 0), "spine": (65, 0, 0), "chest": (18, 0, 0)'),('"pelvis": (16, 0, 0), "spine": (76, 0, 0), "chest": (10, 0, 0)','"pelvis": (16, 0, 0), "spine": (68, 0, 0), "chest": (16, 0, 0)')]:
 assert old in d,old;d=d.replace(old,new)
s=s[:a]+d+s[b:];s=s.replace('c.knee_clearance = 0.10','c.knee_clearance = 0.065');p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
for f in ['cache/verify_dive.py','cache/check_mesh_ground.py','cache/render_dive_review.py']:
 p=Path(f);s=p.read_text(encoding='utf-8').replace('v15','v16');p.write_text(s,encoding='utf-8')
p=Path('cache/check_mesh_ground.py');s=p.read_text(encoding='utf-8').replace("permesh={}","permesh={};baseline=10").replace("if lo<worst[0]:worst=(lo,o.name,f)","if lo<worst[0]:worst=(lo,o.name,f)\n  if f==0:baseline=min(baseline,lo)");s+="print('ACTUAL_FLOOR_QA',dict(baseline=baseline,worst=worst[0],extra_penetration=baseline-worst[0]))\nassert baseline-worst[0]<.005\n";p.write_text(s,encoding='utf-8')
