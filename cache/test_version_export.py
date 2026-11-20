import runpy,tempfile,json
from pathlib import Path
qa=runpy.run_path('cache/verify_dive.py');clips=qa['clips'];arm=qa['arm'];c=qa['new']
with tempfile.TemporaryDirectory(dir='cache') as d:
 root=Path(d);out=root/c.name;out.mkdir();(out/'v16.glb').write_bytes(b'preserve')
 (out/'meta.json').write_text(json.dumps(dict(name=c.name,versions=[dict(v=v) for v in [1,4,16]])))
 meta=clips.export_version(arm,c,root,'version gap check')
 assert meta['versions'][-1]['v']==17
 assert (out/'v16.glb').read_bytes()==b'preserve'
 assert (out/'v17.glb').exists()
print('VERSION_GAP_EXPORT_OK: v17 created, v16 preserved')
