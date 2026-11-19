# vb_dive: doğal plonjon görevi

Mevcut onaylı v4'ü koruyarak vb_dive için yeni, onay bekleyen bir sürüm üret.
Hazırlıkta ağırlık aktarımı ve ayakla itiş; uçuşta topa uzanan birleşik önkol
platformu, yataya yaklaşan gövde ve hafif bükülü dizler kullan. Temas sonrası
elleri açıp avuçları zemine yerleştir; dirsekler inişi yumuşatsın. Eller destek
olurken dizler gövdenin altına gelsin, ağırlık ayaklara geçsin ve karakter
hazır duruşa dönsün. İki kolu aynı anda yukarı çekerek gövdeyi havaya kaldırma.

Klip tanımını pipeline/clip_defs/volleyball.py ve mevcut pipeline/lib araçlarıyla
uygula. GTA iskeletinde pelvis ile omurga ayrı dalları etkiler; gövde eğimini
yalnız kalça açısından varsayma. Erişilemeyen IK hedefleri, aniden değişen
diz/dirsek yönleri, parmak/avuç yönü ve yer temasları gerçek pozlardan ölçülsün.
İsteğe bağlı çözücü ayarları mevcut diğer klipleri etkilemesin.

Ön, yan ve ara kareleri incele. Ayak kaymasını, kare başına dönüşü, el ve ayak
IK erişimini, diz/dirsek sınırlarını ve başlangıç/bitiş uyumunu ölç. Yalnız ayak
kemiklerini kontrol etmekle yetinme: dizleri ve deforme edilmiş modelin zemine
girişini de kontrol et. Mesh zeminini hazır duruştaki gerçek ayakkabı tabanına
göre ölç; kemik başının yüksekliği ayakkabı tabanıyla aynı değildir.

İnceleme için video ve kontak sayfası kaydet. Yeni sürümü kendiliğinden
onaylama, .ycd export etme veya sunucuya gönderme. Görsel doğallığı kullanıcı
değerlendirecek; oyun içi doğrulama ayrı yapılacak.

## 19 Kasım 2026 sonucu

- İncelenecek aday: **v16**, 78 kare / 30 fps = 2,6 saniye, pending.
- Dalışta öne uzanma, avuç desteği, dizleri altına alma ve kademeli kalkış.
- Ayak kayması L/R: v4 0,124/0,163 m → v16 0,027/0,001 m.
- En büyük kare dönüşü: 66,31° → 23,91° (sağ baldır, kare 52).
- Hareket raporunda uyarı ve 1 cm üzeri erişilemeyen IK hedefi yok.
- Kare 27–40: bilek konumları sabit, avuç normalleri aşağı yönle aynı.
- Kontrol edilen diz, pelvis, baş, omurga ve dirsek merkezleri zeminin üstünde.
- 79 karenin bütün deforme meshlerinde, ilk hazır duruşun ayakkabı tabanına
  kıyasla ek zemine girme < 0,001 mm (sayısal yuvarlama düzeyi).
- Hazır duruş, smaç ve tutuş klipleri eski çözücüyle karşılaştırıldı:
  en büyük konum farkı < 0,017 mm, dönüş farkı < 0,08°.
- Video: cache/preview/video/vb_dive_v16_side.mp4
- Kareler: cache/preview/vb_dive_v16.png
- Ölçüm: cache/preview/vb_dive_v16_review.json; cache/dive_mesh.log.
- v4 onayı ve mevcut oyun paketi korunur. v16 henüz oyun içinde denenmedi.
