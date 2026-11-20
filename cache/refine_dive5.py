from pathlib import Path
p=Path('pipeline/clip_defs/volleyball.py');s=p.read_text(encoding='utf-8');a=s.index('def dive():');b=s.index('\n\ndef shuffle_R()',a);d=s[a:b]
d=d.replace('"foot_L": (-0.10, -0.12, 0.14), "foot_R": (0.10, -0.15, 0.17)', '"foot_L": (-0.10, 0.02, 0.18), "foot_R": (0.10, 0, 0.21)')
d=d.replace('"knee_L": (-0.05, 1, 0.2), "knee_R": (0.05, 1, 0.2),\n            "foot_L"','"knee_L": (-0.05, 1, -0.15), "knee_R": (0.05, 1, -0.15),\n            "foot_L"',1)
d=d.replace('"elbow_L": (-0.6, 0, -1), "elbow_R": (0.6, 0, -1),','"elbow_L": (-0.6, 0, -1), "elbow_R": (0.6, 0, -1),\n           "orient_L": 0.25, "orient_R": 0.25,',1)
d=d.replace('"hand_L": (-J, 1.32, 0.50), "hand_R": (J, 1.32, 0.50),','"hand_L": (-J, 1.32, 0.50), "hand_R": (J, 1.32, 0.50), "orient_L": 0.6, "orient_R": 0.6,',1)
s=s[:a]+d+s[b:];p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
