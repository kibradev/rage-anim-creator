from pathlib import Path
import json
root=Path.cwd().resolve();out=(root/'output/vb_dive').resolve();preview=(root/'cache/preview').resolve()
assert out.is_relative_to(root) and preview.is_relative_to(root)
p=out/'meta.json';meta=json.loads(p.read_text(encoding='utf-8'));meta['versions']=[v for v in meta['versions'] if v['v']<=4 or v['v']==16];p.write_bytes((json.dumps(meta,ensure_ascii=True,indent=1)+'\n').encode('utf-8'))
# Only intermediate versions created during this turn are removed.
for v in range(5,16):
 for p in [out/f'v{v}.glb',out/f'v{v}.action.json',preview/f'vb_dive_v{v}.png']:
  assert p.parent in (out,preview)
  if p.exists():p.unlink()
p=root/'DEVAM.md';s=p.read_text(encoding='utf-8');s+='''\n## 19 Kasım — doğal plonjon revizyonu\n- Kullanıcı talebiyle vb_dive yeniden işlendi; son aday **v16**, 78 kare / 2,6 sn, **pending**. v4 approved/export durumu korundu.\n- Görev promptu ve ölçümler: `pipeline/prompts/vb_dive.md`. Ara denemeler (v5–v15) temizlendi.\n- Uzanma, sabit aşağı bakan avuç desteği, zemin sınırına uyan dizler, kademeli kalkış.\n- Kayma L/R 2,7 cm / 1 mm; en büyük kare dönüşü 23,91°; hareket raporu uyarısız, IK kaçırma >1 cm yok.\n- Tüm deforme mesh kareleri gerçek ayakkabı tabanına göre kontrol edildi; ek zemin ihlali yok. Hazır duruş/smaç/tutuş eski çözücüyle karşılaştırıldı (<0,017 mm / <0,08°).\n- İnceleme: `cache/preview/video/vb_dive_v16_side.mp4`, `cache/preview/vb_dive_v16.png`.\n- Sonraki adım: kullanıcının görsel değerlendirmesi. Yeni aday onaylanmadı, YCD export veya sunucuya kopyalama yapılmadı.\n''';p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))
