# animCreator

Kullanıcıyla Türkçe konuş. Kullanıcı informal yazar ("kanka"). Oyun içi testi kullanıcı yapar; oyunda denenmemiş şey için "çalışıyor" deme.

## Ne bu
GTA V (FiveM) için AI ile yazılan animasyonlar: Blender 4.2 + Sollumz, CodeWalker dönüştürücüsü ile `.ycd`. Önce `PLAN.md` (kurallar, bilinen tuzaklar), sonra `DEVAM.md` (güncel iş listesi ve günlük) oku.

## Onay kapısı (en önemli kural)
Yalnızca kullanıcının onayladığı sürüm export edilir. Kullanıcı açıkça "onayla/export et" demeden hiçbir klibi onaylama, export etme, sunucuya kopyalama. Yeni animasyon istenmediyse üretme.

## Yapı
- `pipeline/`: Blender betikleri (`make_clip.py`, `render_frames.py`, `contact_check.py`, `export_ycd.py`), `clip_defs/` klip tanımları, `lib/` (posekeys, IK, kalite denetimi).
- `output/<klip>/vN.*`: üretilen sürümler + `meta.json` (durum: pending/approved).
- `server/` FastAPI :8000, `web/` Vite :5173 (onay arayüzü), `converter/` CodeWalker aracı.
- Blender: `"C:/Program Files/Blender Foundation/Blender 4.2/blender.exe" -b --python pipeline/<script>.py -- <arg>`.

## Kurallar
- Klip üretimini serbest betik yerine `pipeline/lib` yardımcıları ve `clip_defs` ile yap. Üretimden sonra kontak sayfasını (`cache/preview/`) Read ile kendin gözden geçir.
- GTA'ya özgü: freemode ped (`mp_m_freemode_01`), kalça `SKEL_ROOT`, havada dizler önde. Bkz. memory notları (zıplama tarifi).
- Oyuna dağıtım: `voleybol_anims` kaynağını `Z:\Desktop\LegacyQBOX\...\resources\[volleyball]\` altına robocopy ile kopyala (yalnızca onaylı klipler).
- Voleybol animtable verisi `volleyballScript` tarafında `tools/gen_animtable.py` ile bu klip anahtar pozlarından üretilir; klip değişirse yeniden üret ve `pipeline/contact_check.py` ile doğrula.
- Her adımı commit et; commit sonuna `Co-Authored-By` satırı ekle.

## Kardeş projeler (Desktop)
- `volleyballScript` (FiveM scripti, klipleri kullanır), `mapCreator` (saha/top modelleri).
