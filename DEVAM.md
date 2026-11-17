# DEVAM NOTU (limit/token biterse buradan devam et)

Bu dosyayı okuyan AI (Claude/Codex) için: proje bağlamı `PLAN.md` içinde. Aşağısı o an yürütülen iş listesi.
Her madde bitince işaretlenir ve commit atılır. Kurallar: `PLAN.md` > "Kurallar". Kullanıcıyla Türkçe konuş.

## Hedef
Animasyon üretiminin tamamını AI yapacak. Bunun için AI'nin kendi ürettiğini görebilmesi, IK ile poz verebilmesi,
GTA clip'lerini referans alabilmesi ve otomatik kalite denetimi gerekiyor.

## İş listesi (sırayla)
- [x] 1. Görme aracı: `pipeline/render_frames.py` — bir clip sürümünün seçili karelerini önden/yandan PNG kontak sayfası olarak çıkarır.
- [x] 2. Playwright: `web/` içine `npm i -D playwright` + `npx playwright install chromium` (arayüz ekran görüntüsü için).
- [x] 3. `Clip` kütüphanesine konum desteği (`SKEL_ROOT` kalça konumu) + IK yardımcıları (el/ayak hedefe, ayak yerde sabit).
- [x] 4. Otomatik kalite denetimi: ayak kayması, yere girme, eklem sınırı, döngü kapanışı (konum dahil).
- [ ] 5. Referans poz kütüphanesi: GTA clip'inden poz/hareket alıp üzerine değişiklik yapma.
- [ ] 6. Hepsini kullanan kısa bir dans döngüsü üret (`pipeline/clip_defs/`), kareleri render edip gözle kontrol et.
- [ ] 7. (Kullanıcıda) `output/export/wave_hand/v4/wave_hand.ycd` oyun içi testi; sonra FiveM test resource'u.

## Komutlar
- Blender: `"C:/Program Files/Blender Foundation/Blender 4.2/blender.exe" -b --python pipeline/<script>.py -- <argümanlar>`
- Clip üret: `pipeline/make_clip.py -- player_zero <modul> "<etiket>"` -> `output/<ad>/vN.*`
- Export testi: `pipeline/rt_dance.py -- player_zero "special_ped@mountain_dancer@monologue_3@monologue_3a" mnt_dnc_buttwag`
- Sunucular: FastAPI `:8000`, Vite `:5173` (kullanıcı çalıştırıyor).

## Durum günlüğü
- 17 Kas: Freemode pedleri eklendi. Export gidiş-dönüş testi geçti (0,079°). `complete_action` yalnızca 61 gövde kemiğini dolduruyor.
- 17 Kas: Codex remote-control bu makinede açık (`codex remote-control stop` ile kapanır).
- 17 Kas: Adım 1–4 bitti. Kullanım:
  - Görme: `pipeline/render_frames.py -- <ped> mine <clip> <v> 0,15,30 front,side` veya `... gta <dict> <clip> 8` -> `cache/preview/*.png` (Read ile bak).
  - `Clip.set_root(frame,(x,y,z))` kalça konumu; `Clip.plant_feet(frames)` ayakları yerde tutar (kalça/omurga anahtarlarından SONRA çağır);
    `Clip.reach(frame,'L'|'R',hedef)` el IK; `Clip.ik(...)` genel; `Clip.add(...)` mevcut hareketin üstüne; `Clip.copy_from(action,...)` GTA hareketi kopyalar.
  - Yön: game_facing clip'lerde ped +Y'ye bakar (`c.forward()`); kök yaw'ı artık `__init__`'te anahtarlanıyor (IK'dan önce olmalı, yoksa ayak kayar).
  - `set` eksenleri kemik yerel/rest tabanlı: omurgada öne eğilme = +x (‑x geriye yatırır).
  - Denetim: `lib/checks.py::motion_report`; `make_clip` çıktısında `CLIP UYARI` satırları. meta.json `report.warnings`.
  - Michael'ın ceketi çömelmede bozuk görünür (ceket eteği bacak kemiklerine bağlı); önizlemede freemode ped tercih et.
  - Test clip'i: `pipeline/clip_defs/_test_squat.py` (çıktısı silindi, yeniden üretilebilir).
