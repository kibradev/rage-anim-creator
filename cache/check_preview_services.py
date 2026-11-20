import urllib.request,json
for port,path in [(8000,'/api/mine'),(5173,'/')]:
 try:
  with urllib.request.urlopen(f'http://localhost:{port}{path}',timeout=3) as r:
   body=r.read();print('SERVICE',port,r.status)
   if port==8000:
    data=json.loads(body)
    print('DIVE_API',json.dumps([x for x in data if 'vb_dive' in str(x)],ensure_ascii=False)[:1800])
 except Exception as e:print('SERVICE',port,str(e))
