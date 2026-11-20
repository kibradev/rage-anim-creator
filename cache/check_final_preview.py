import json,urllib.request
with urllib.request.urlopen('http://localhost:8000/api/mine',timeout=3) as r:
 data=json.load(r)
v=next(x for x in data if x['name']=='vb_dive' and x.get('latest'))
assert v['version']==16 and v['status']=='pending'
with urllib.request.urlopen('http://localhost:8000'+v['url'],timeout=3) as r:assert r.status==200 and r.read(4)==b'glTF'
print('PREVIEW_OK vb_dive v16 pending, GLB served')
