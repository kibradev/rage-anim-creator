# animCreator — GTA V Ped Animasyon Stüdyosu

## Amaç
1. GTA V ped'ini tarayıcıda (three.js) görüntülemek.
2. GTA'nın varsayılan animasyonlarını (`.ycd`) tarayıcıda oynatmak.
3. Blender'da kodla (bpy) yeni animasyon üretmek, tarayıcıda önizlemek, onaylanırsa `.ycd` olarak export etmek.

Çalışma biçimi: Kullanıcı terminalde Claude'a ne yapılacağını söyler, Claude kodu/script'i yazar ve çalıştırır;
kullanıcı sonucu tarayıcıdaki arayüzde görür (canlı yenilenir) ve onaylar/reddeder.

## Temel teknik fikir
Tarayıcı GTA formatlarını (`.ydd`, `.ycd`, `.ytd`) okuyamaz. Bu yüzden bir **dönüşüm hattı** kurulur
ve tarayıcı yalnızca standart **glTF/GLB** görür:

```
GTA V kurulumu ──CodeWalker──▶ .ydd/.ytd/.ycd (ham)
                                 │ Sollumz (Blender, arayüzsüz)
                                 ▼
                    Armature + mesh + Action'lar (.blend)
                                 │ glTF export
                                 ▼
          ped.glb  +  anims/<dict>/<clip>.glb  (yalnızca animasyon)
                                 │
                                 ▼
          Tarayıcı: three.js + AnimationMixer (shadcn arayüzü)
```
Ters yön (kendi animasyonumuz): `bpy keyframe → Action → GLB önizleme → onay → Sollumz ile .ycd export`.

## Mimari
```
animCreator/
├── PLAN.md
├── .gitignore               # assets/ ve cache/ ASLA commit edilmez (telifli GTA içeriği)
├── tools/                   # CodeWalker, Sollumz kaynakları (referans, salt okunur)
├── pipeline/                # Python; Blender arayüzsüz çalıştırır
│   ├── extract_ped.py       # ped .ydd/.ytd → ped.glb
│   ├── extract_anims.py     # .ycd → clip başına .glb + index.json
│   └── lib/                 # parametreli bpy fonksiyonları (serbest script yok)
│       ├── skeleton.py      # kemik adı/tag eşlemesi, rest pose
│       ├── poses.py         # pose_set(bone, rot) yardımcıları
│       ├── clips.py         # make_clip(name, keys, fps, loop)
│       ├── procedural.py    # sinüs/IK tabanlı döngüler (idle, nefes, sallanma)
│       └── export_ycd.py    # Sollumz ile .ycd export
├── server/                  # FastAPI + WebSocket
│   ├── main.py              # /api/peds, /api/clips, /ws
│   ├── jobs.py              # Blender job kuyruğu, log akışı
│   └── watch.py             # output/ değişince tarayıcıya "yenile" olayı
├── web/                     # Vite + React + TS + Tailwind + shadcn/ui + react-three-fiber
├── assets/                  # (gitignore) ham GTA dosyaları — salt okunur
├── cache/                   # (gitignore) üretilmiş GLB'ler
└── output/                  # üretilen yeni animasyonlar (.blend, .glb, .ycd) + versiyonlar
```
Gerekçe: Python backend, Blender/Sollumz ile aynı dilde; WebSocket canlı log + "yenile" olayı için.
Three.js gerçek bir `AnimationMixer` ve skinning sağladığı için kendi renderer yazmaya gerek yok.

## Arayüz (sade ve akıcı)
Tek ekran, üç bölge, koyu tema, shadcn/ui:

```
┌──────────────┬─────────────────────────────────┬─────────────┐
│ Ped seçici   │                                 │  Çıktı      │
│ (Select)     │        3D görüntüleme           │  (Sheet,    │
│              │   orbit kamera, zemin, ışık     │  gizlenir)  │
│ Arama        │                                 │  - Job log  │
│ (Command)    │                                 │  - Ölçü     │
│ Anim listesi │                                 │  - Versiyon │
│ (ScrollArea) │                                 │             │
├──────────────┴─────────────────────────────────┴─────────────┤
│ ▶/⏸  ──────●──────────  0.00 / 2.30 s   Hız 1x   Döngü ☐    │
└──────────────────────────────────────────────────────────────┘
```
- Sol: ped seçimi + arama kutusu (Command) + animasyon listesi, `Orijinal | Benim` sekmeleri (Tabs).
- Orta: viewport; tıklayınca animasyon anında değişir, çapraz geçiş (crossFade) 0.2 s.
- Alt: oynat/duraklat, zaman çubuğu (Slider), hız (ToggleGroup), döngü (Switch). Boşluk tuşu = oynat/duraklat.
- Sağ panel (Sheet): job log, kemik sayısı/süre/kare bilgisi, "Onayla / Reddet / Export (.ycd)" butonları, versiyon geçmişi.
- Ek gösterim (kapalı gelir): iskelet (SkeletonHelper), kemik adı etiketi, wireframe.
- Kullanılacak bileşenler: Command, ScrollArea, Tabs, Slider, ToggleGroup, Switch, Button, Sheet, Badge, Tooltip, Sonner (toast). Başka bir şey eklenmez.

## Aşamalar ve çıkış kriterleri

### Aşama 0 — Ortam ve kaynaklar
- Kaynakları `tools/` altına indir: Sollumz (`Sollumz/Sollumz`), CodeWalker (`dexyfex/CodeWalker`) — kod okuyup `.ydd`, `.ycd`, iskelet/kemik tag ve animasyon sıkıştırma formatlarının nasıl çözüldüğünü öğrenmek için.
- Blender sürümü: **4.2 LTS** önerilir (Sollumz uyumu); 5.1 yüklü ama Sollumz henüz uyumlu olmayabilir.
- Sollumz'u arayüzsüz Blender'a kur, `blender -b --python-expr "import bpy; print(bpy.context.preferences.addons.keys())"` ile doğrula.
- Çıkış: Blender komut satırından Sollumz yüklü açılıyor.

### Aşama 1 — Ped'i çıkar ve göster
- CodeWalker ile ped dosyalarını al (başlangıç: `player_zero` veya `mp_m_freemode_01`; freemode çok parçalı ve karmaşık, ilk hedef değil).
- `extract_ped.py`: ydd + ytd'yi Sollumz ile içe aktar, `ped.glb` export (skinned mesh + armature + dokular).
- `web/`: Vite iskeleti, shadcn kurulumu, viewport'ta `ped.glb`, orbit kamera, T-pose/idle.
- Çıkış: tarayıcıda ped dokulu ve iskeletli görünüyor.

### Aşama 2 — GTA animasyonlarını oynat
- `extract_anims.py`: `.ycd` içe aktar (Sollumz) → her clip bir Action → glTF animasyonu. `index.json` (dict, clip adı, süre, fps, döngü).
- Bilinen zorluklar: root/mover hareketi (`mover` kemiği), kemik tag eşlemesi, ölçek/ofset track'leri, ped'in rest pose'u ile animasyon rest pose'u uyumu, yüz animasyonları (ilk etapta kapsam dışı).
- Arayüz: liste, arama, oynat/duraklat, hız, döngü.
- Çıkış: `anim@...` / `move_...` clip'leri tarayıcıda doğru oynuyor (yürüme, idle, el sallama); 20+ clip taranmış.

### Aşama 3 — Blender'da kodla animasyon üretimi
- `lib/` altında parametreli fonksiyonlar: `make_clip(name, fps, loop)`, `key_pose(frame, {bone: euler})`, `procedural.breathing(amplitude, rate)`, `procedural.wave(arm="R")`, kolay IK (`reach(target)`).
- Üretilen clip `output/<isim>/v1.glb` olarak yazılır, server değişikliği fark eder, tarayıcıda `Benim` sekmesinde otomatik belirir.
- Pose'ları doğrulama: kemik açı sınırları (ör. dirsek ters bükülmesin), döngü sürekliliği (ilk kare = son kare), kare başına hız limiti.
- Çıkış: "el sallama" gibi basit bir clip kodla üretilip tarayıcıda oynuyor ve versiyonlanıyor (v1, v2…).

### Aşama 4 — Onay kapısı ve `.ycd` export
- Kural: export'tan önce önizleme + ölçü raporu (süre, kare, kemik sayısı, ilk/son kare farkı) gösterilir, kullanıcı onaylar.
- `export_ycd.py`: Sollumz'un clip dictionary export'u ile `.ycd` üret (`output/export/`), orijinal dosyalar asla değiştirilmez.
- Oyun içi test kullanıcıda; sonuç sorulmadan "çalışıyor" denmez. Bilinen tuzaklar `PLAN.md`'nin sonuna eklenir.

### Aşama 5 — Genişletme (sonra)
- Animasyon karıştırma/katmanlama (üst vücut + alt vücut), kopyalama/ayna (sol↔sağ), hız/kırpma düzeltme.
- Doğal dil → clip parametreleri akışı, prop (nesne) tutma, birden fazla ped.
- Doğrudan XML→glTF dönüştürücü (Blender'a bağımlılığı azaltmak için), isteğe bağlı.

## Aşama 0 sonuçları (tamamlandı)
- Blender 4.2.22 LTS + Sollumz 2.9.1 kuruldu ve arayüzsüz modda etkin; `szio` bağımlılığı hazır.
- `tools/Sollumz` ve `tools/CodeWalker` kaynakları referans için indirildi (gitignore'da).
- **OpenIV/CodeWalker export'una gerek yok:** Sollumz'un `szio` katmanı RPF arşivlerini doğrudan okuyor
  (`GameFiles(game_dir).read_asset_filelist(...)`). Oyun klasörü `config.json`'da. OpenIV yalnızca yedek yol.
- Bulundu: 20.343 `.ycd` clip dictionary, 10.604 `.ydd`. `player_zero` -> `x64v.rpf/models/cdimages/streamedpeds_players.rpf/`
  (`.yft` + `.ydd` + `.ytd`); yürüyüş `move_m@generic` -> `clip_move_.rpf`; el sallama `anim@mp_player_intcelebrationmale@wave`.
- Sollumz hem `import_ycd` hem `export_ycd` içeriyor: Aşama 2 ve 4 için ek bir format çözücü yazmak gerekmiyor.

## Kurallar
- `assets/` salt okunur; tüm çıktı `output/` ve `cache/` içine.
- Blender işleri `pipeline/lib/` içindeki parametreli fonksiyonlarla; serbest script yok.
- Her adım git commit'i; ham GTA dosyaları ve türetilmiş GLB'ler `.gitignore`'da (telifli, yalnızca yerel kullanım — yeniden dağıtılmaz).
- Arayüz sade kalır: yeni özellik eklemeden önce mevcut üç bölgeye sığıp sığmadığına bakılır.

## Riskler
| Risk | Önlem |
|---|---|
| `.ycd` sıkıştırma/kemik eşleme hataları | Sollumz kaynak kodunu referans al; önce tek clip ile doğrula |
| Ped rest pose farkı → bozuk poz | İlk gün T-pose karşılaştırma testi |
| Sollumz Blender sürüm uyumu | Blender 4.2 LTS kullan |
| Büyük GLB'ler | Dokuları küçült, clip'leri ayrı dosyada lazy-load et |
| `.ycd` export oyun içinde çalışmama | Aşama 4'te küçük clip ile test, hata "Bilinen tuzaklar"a |

## Bilinen tuzaklar
(Aşama 4 testinden sonra doldurulacak.)
