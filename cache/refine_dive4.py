from pathlib import Path
p=Path('pipeline/clip_defs/volleyball.py');s=p.read_text(encoding='utf-8');a=s.index('def dive():');b=s.index('\n\ndef shuffle_R()',a);d=s[a:b]
for old,new in [('1.23, 0.10','1.15, 0.04'),('0.68, -0.64','0.68, -0.68'),('0.74, -0.72','0.74, -0.76'),('0.68, -0.67','0.68, -0.71'),('0.53, -0.65','0.53, -0.68'),('"hand_R": (0.26, 0.86, 0.42)','"hand_R": (0.26, 0.70, 0.68)'),('"orient_R": 0.4','"orient_R": 0.0'),('(-0.25, 1, 0.2)','(-0.05, 1, 0.2)'),('(0.25, 1, 0.2)','(0.05, 1, 0.2)'),('(-0.12, 0.27, 0.06)','(-0.04, 0.27, 0.02)'),('(-0.12, 0.27, 0.02)','(-0.04, 0.27, 0.02)')]:
 assert old in d,old;d=d.replace(old,new)
s=s[:a]+d+s[b:];p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
