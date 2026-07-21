# Telemetry GUI — Yer İstasyonu Arayüzü

Pit alanındaki mühendislerin pistteki aracı canlı olarak takip etmesi için geliştirilen masaüstü telemetri programı. Raspberry Pi üzerinden LoRa ile gelen araç verisini (hız, sıcaklık vb.) seri port üzerinden okuyup gerçek zamanlı çizgi grafiklere döker.

## Proje yapısı

```
Telemetry_GUI/
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── logs/
└── assets/
```

## Bölümler

**`main.py`**
Uygulamanın tek giriş noktası. PyQt5 penceresini oluşturur, seri port bağlantısını yönetir, pyqtgraph ile gelen veriyi canlı grafiğe çizer. Proje şu an tek dosyalık (monolitik) bir yapıda; ileride büyürse `gui/` ve `core/` gibi ayrı modüllere bölünebilir.

**`requirements.txt`**
Projenin çalışması için gereken Python kütüphaneleri (PyQt5, pyqtgraph, pyserial, numpy). Kurulum: `pip install -r requirements.txt`

**`logs/`**
Yarış/test sırasında kaydedilen telemetri verilerinin (CSV) tutulduğu klasör. Sonradan analiz için kullanılır.

**`assets/`**
Arayüzde kullanılan ikon, logo veya stil dosyaları.

**`.gitignore`**
Sürüm kontrolüne dahil edilmeyecek dosyalar: sanal ortam (`venv/`), derlenmiş Python dosyaları (`__pycache__/`), ve `logs/` altındaki kayıt verileri.


# FST-26 Pit Telemetri Veri Rehberi
 
Bu doküman, `telemetry.c` / `telemetry.h` kodunda **şu an gerçekten
gönderilen** veya gönderilmeye hazırlanan alanları listeler. Kod tarafında
karşılığı olmayan sensörler (lastik, IMU, GPS, IMD, TSAL vb.) bu sürümde
listeden çıkarılmıştır — CAN entegrasyonları ilerledikçe geri eklenebilir.
 
---
 
## 1. Şu An Canlı Gönderilen Veriler
 
State Machine'den doğrudan doldurulan, gerçek değer taşıyan alanlar:
 
| Alan | Kaynak | Anlamı | Önerilen UI Elemanı |
|---|---|---|---|
| `seqNumber` | Telemetri sayaç | Paket sıra no (kayıp/latency hesabı için) | Küçük referans metni |
| `vehicleState` | `sm->outputs.currentState` | Araç durumu (state machine state'i) | Metin etiketi |
| `faultCode` | `sm->outputs.activeFault` | Aktif arıza kodu | Durum rozeti (kod → açıklama eşlemesi ile) |
| `appsPercent` | `sm->inputs.appsPercent` | Gaz pedalı pozisyonu | Yarım daire gauge (iğneli) |
| `brakePressure` | `sm->inputs.brakePressure` | Fren basıncı | Yarım daire gauge (iğneli) |
| `torqueCommand` | `sm->outputs.torqueCommand` | Motora giden tork komutu | Sayısal kart |
| `batteryVoltage` | `sm->inputs.bmsVoltage` | Batarya gerilimi | Sayısal kart |
| `systemFlags` (bit: AIR-) | Kontaktör durumu | Negatif kontaktör açık/kapalı | Durum rozeti |
| `systemFlags` (bit: AIR+) | Kontaktör durumu | Pozitif kontaktör açık/kapalı | Durum rozeti |
| `systemFlags` (bit: Precharge) | Kontaktör durumu | Precharge aktif mi | Durum rozeti |
| `systemFlags` (bit: SDC Closed) | `sm->inputs.sdcClosed` | Shutdown circuit kapalı mı | Durum rozeti (OK / AÇIK) |
| `systemFlags` (bit: Inverter Enable) | İnverter durumu | İnverter etkin mi | Durum rozeti |
| `uptimeMs` | Sistem zamanlayıcı | Zaman damgası (latency hesabı) | Ekranda gösterilmez, arka planda kullanılır |
 
---
 
## 2. Şu An Placeholder (0) — Henüz CAN Entegrasyonu Yok
 
Bu alanlar pakette yer alıyor ama şu an sabit 0 gönderiliyor:
 
| Alan | Beklenen Kaynak | Ne zaman gerçek olur |
|---|---|---|
| `motorRPM` | İnverter (CAN) | İnverter CAN entegrasyonu yapılınca |
| `batteryCurrent` | BMS (CAN) | BMS CAN entegrasyonu yapılınca |
| `batterySOC` | BMS (CAN) | BMS CAN entegrasyonu yapılınca |
| `motorTemp` | İnverter (CAN) | İnverter CAN entegrasyonu yapılınca |
| `inverterTemp` | İnverter (CAN) | İnverter CAN entegrasyonu yapılınca |
| `maxCellTemp` | BMS (CAN) | BMS CAN entegrasyonu yapılınca |
 
**UI kuralı:** Bu alanlar için pit ekranında gerçek 0 değeriyle
placeholder 0'ı karıştırmamak adına "—" veya soluk/gri renk kullanılmalı.
 
---
 
## 3. Bağlantı Sağlığı Metrikleri
 
Sensör verisi değil, `seqNumber` ve `uptimeMs` üzerinden pit tarafında
hesaplanır:
 
| Metrik | Nasıl hesaplanır | Önerilen UI Elemanı |
|---|---|---|
| Paket kayıp oranı (%) | `seqNumber` takibiyle | Yüzde etiketi |
| Gecikme / Latency (ms) | `uptimeMs` + tek seferlik senkronizasyon | Sayısal etiket |
| RSSI (dBm) | LoRa modülünden doğrudan okunur | Sinyal çubuğu ikonu |
 
---
 
## 4. Sadeleştirilmiş Ekran Yerleşimi
 
```
┌─────────────────────────────────────────────┐
│  TAKIM LOGOSU          BAĞLANTI: STABİL      │  ← üst şerit
├─────────────────────────────────────────────┤
│  ARAÇ DURUMU: vehicleState                   │
│  ARIZA KODU:  faultCode                      │
├───────────────┬───────────────┬─────────────┤
│  GAZ PEDALI    │  FREN BASINCI │  TORK       │
│    (gauge)     │    (gauge)    │  (sayısal)  │
├───────────────┴───────────────┴─────────────┤
│  BATARYA GERİLİMİ  │  AKIM(—)  │  SOC(—)     │  ← (—) = henüz gerçek değil
├───────────────────────────────────────────────┤
│  [AIR-] [AIR+] [PRECHARGE] [SDC] [INV EN]     │  ← durum rozetleri
├───────────────────────────────────────────────┤
│  Kayıp: %  Gecikme: ms  RSSI: dBm             │  ← alt şerit
└─────────────────────────────────────────────┘
```
 
---
 
## 5. Renk Kuralları
 
| Durum | Renk | Uygulama |
|---|---|---|
| Normal | Yeşil | SDC kapalı, arıza kodu yok |
| Kritik | Kırmızı | SDC açık veya `faultCode != 0` |
| Bilinmiyor / veri yok | Gri, "—" | Placeholder alanlar (CAN entegrasyonu bekleyen) |
 
Placeholder alanlar CAN entegrasyonu tamamlandıkça bu dokümana ve UI
koduna geri eklenmelidir; o zamana kadar pit ekibinin bunları "aracın
gerçek durumu" sanmaması için görsel olarak ayırt edilmesi önemlidir.


## Kurulum ve çalıştırma

```bash
pip install -r requirements.txt
python main.py
```
