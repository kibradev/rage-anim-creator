import json,tempfile
from pathlib import Path
import server.main as api
with tempfile.TemporaryDirectory() as d:
 api.OUTPUT=Path(d);p=api.OUTPUT/'test';p.mkdir()
 versions=[dict(v=v,file=f'v{v}.glb',duration=1,fps=30,frames=30) for v in [1,4,16]]
 (p/'meta.json').write_text(json.dumps(dict(name='test',versions=versions)))
 assert [x['version'] for x in api.mine() if x['latest']]==[16]
print('VERSION_GAP_API_OK')
