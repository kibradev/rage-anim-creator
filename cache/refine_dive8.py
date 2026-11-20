from pathlib import Path
p=Path('pipeline/clip_defs/volleyball.py');s=p.read_text(encoding='utf-8');a=s.index('def dive():');b=s.index('\n\ndef shuffle_R()',a);d=s[a:b]
for old,new in [('(-0.12, 0, 0.04), "foot_R": (0.12, 0, 0.04)','(-0.12, 0, 0.12), "foot_R": (0.12, 0, 0.12)'),('0.68, -0.68','0.68, -0.62'),('0.74, -0.76','0.74, -0.70'),('0.68, -0.71','0.68, -0.65'),('0.53, -0.68','0.53, -0.62'),('"pelvis": (45, 0, 0), "spine": (65, 0, 0), "chest": (18, 0, 0)','"pelvis": (45, 0, 0), "spine": (70, 0, 0), "chest": (14, 0, 0)'),('"pelvis": (16, 0, 0), "spine": (68, 0, 0), "chest": (16, 0, 0)','"pelvis": (16, 0, 0), "spine": (76, 0, 0), "chest": (10, 0, 0)')]:
 assert old in d,old;d=d.replace(old,new)
s=s[:a]+d+s[b:];s=s.replace('c.knee_clearance = 0.065','c.knee_clearance = 0.10');p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
for f in ['cache/verify_dive.py','cache/check_mesh_ground.py','cache/render_dive_review.py']:
 p=Path(f);s=p.read_text(encoding='utf-8').replace('v14','v15');p.write_text(s,encoding='utf-8')
