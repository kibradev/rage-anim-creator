from pathlib import Path
p=Path('pipeline/clip_defs/volleyball.py');s=p.read_text(encoding='utf-8');a=s.index('def dive():');b=s.index('\n\ndef shuffle_R()',a);d=s[a:b]
for old,new in [
('1.38, 0.69','1.22, 0.69'),('1.55, 0.48','1.36, 0.48'),
('1.37, 0.12','1.23, 0.10'),
('"root": (0, 0.68, -0.59), "pelvis": (66, 0, 0), "spine": (48, 0, 0), "chest": (16, 0, 0)','"root": (0, 0.68, -0.67), "pelvis": (66, 0, 0), "spine": (65, 0, 0), "chest": (18, 0, 0)'),
('"root": (0, 0.53, -0.53), "pelvis": (48, 0, 0), "spine": (36, 0, 0), "chest": (12, 0, 0)','"root": (0, 0.53, -0.65), "pelvis": (48, 0, 0), "spine": (68, 0, 0), "chest": (16, 0, 0)'),
('"foot_L": (-0.10, 0.02, 0.17)','"knee_L": (-0.12, 1, -0.15), "knee_R": (0.12, 1, -0.15),\n               "foot_L": (-0.10, 0.02, 0.17)'),
('"foot_L": (-0.12, 0.27, 0.02), "foot_R": (0.12, -0.02, 0.12)','"knee_L": (-0.25, 1, 0.2), "knee_R": (0.25, 1, 0.2),\n            "foot_L": (-0.12, 0.27, 0.06), "foot_R": (0.12, -0.02, 0.15)'),
('"hand_L": (-0.25, 1.00, 0.20), "hand_R": (0.25, 1.18, 0.12)','"hand_L": (-0.25, 1.08, 0.26), "hand_R": (0.25, 1.23, 0.10)')]:
 assert old in d,old;d=d.replace(old,new)
s=s[:a]+d+s[b:];p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
