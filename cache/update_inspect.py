from pathlib import Path
p=Path('cache/inspect_dive.py');s=p.read_text(encoding='utf-8').replace('v6.action','v8.action').replace('[12,13,18,22,27,32,40,44,48,54,58,62,66]','[0,7,12,18,22,27,32,40,44,48,54,58,60,62,66]');p.write_text(s,encoding='utf-8')
