## İletişim Protokolü ve Veri Akışı

Yer istasyonuna (PC) UART/LoRa alıcısı üzerinden gelen fiziksel frame yapısı **25 Byte** uzunluğundadır:
`[Header 1: 0xAA] [Header 2: 0x55] [Length: 21] [Payload: 21 Byte] [Checksum: 1 Byte]`

### Mühendis 1'in Yaptığı İşlem:
1. `SerialWorker` (veya `TelemetrySimulator`) gelen veriyi yakalar.
2. Sabit başlıkları (`0xAA 0x55`) ve uzunluğu (`21`) doğrular.
3. 21 byte'lık Payload'un XOR checksum'ını kontrol eder.
4. **Yalnızca checksum'ı doğru olan geçerli paketleri** hex string formatına (`payload.hex()`) dönüştürerek yayınlar.

---

## Sunulan Sinyaller ve Fonksiyonlar (Arayüzler)

### `core/serial_worker.py`
Seri port haberleşmesini ve cihaz bulmayı yöneten asenkron iş parçacığıdır.

* **`list_available_ports() -> list`**
  * Bilgisayara bağlı mevcut tüm COM portlarını `[(cihaz_adi, aciklama), ...]` şeklinde döndürür.
* **`find_vehicle_port() -> str`**
  * Bağlı portlar arasında FTDI, CP210, CH340 gibi yaygın LoRa alıcı/USB-UART dönüştürücü çipleri taşıyan ilk portun adını (Örn: `"COM4"` veya `"/dev/ttyUSB0"`) otomatik olarak bulur. Bulamazsa `None` döndürür.
* **`SerialWorker(QThread)` Sinyalleri:**
  * `raw_line_received(str)`: Doğrulanmış 21 byte'lık payload'u **hex string** olarak döndürür (Örn: `"02001405002d0fa00000551e1e1e0f000003e8"`).
  * `connection_status(bool, str)`: Bağlantı açıldığında (`True, "BAĞLI: COM4"`), kapandığında (`False, "Bağlantı Kesildi"`) durum bilgisi döndürür.
  * `error_occurred(str)`: Port okuma hatası oluştuğunda hata mesajı döndürür.

### `core/simulator.py`
Donanım bağlı değilken test yapabilmek için gerçekçi veriler üreten sahte veri kaynağıdır.

* **`TelemetrySimulator(QThread)` Sinyalleri:**
  * `raw_line_received(str)`: Simüle edilen 21 byte'lık veriyi **hex string** formatında döndürür. `SerialWorker` ile tamamen aynı sinyal imzasına sahiptir.
  * `connection_status(bool, str)`: Simülasyon başladığında/bittiğinde durum bilgisi döndürür.
  * `error_occurred(str)`: Hata durumunda tetiklenir.

---

## Payload Veri Formatı

Mühendis 1'den `raw_line_received` sinyaliyle gelen hex string çözüldüğünde (`bytes.fromhex(hex_str)`) elde edilen **21 byte'lık** veri yapısı, VCU (`telemetry.h`) içindeki `TelemetryPacket_t` struct yapısıyla birebir eşleşir.

Bu byte dizisini çözmek için Python'da kullanılacak **struct formatı:** **`"<BBBBhhHhBBBBBI"`**

### Paket Byte Haritası (Struct Çözümleme Sırası):

| Sıra | Değişken Adı | Türü | Python Karşılığı | Boyut | Açıklama |
|---|---|---|---|---|---|
| 0 | `vehicleState` | `uint8_t` | `B` | 1 Byte | Araç durumu (1: READY, 2: DRIVING, 3: FAULT) |
| 1 | `faultCode` | `uint8_t` | `B` | 1 Byte | Aktif hata kodu (0: Yok, 1-5: Kritik Hata) |
| 2 | `appsPercent` | `uint8_t` | `B` | 1 Byte | Gaz pedalı yüzdesi (0-100%) |
| 3 | `brakePressure` | `uint8_t` | `B` | 1 Byte | Fren basıncı (0-255 Bar) |
| 4-5 | `torqueCommand` | `int16_t` | `h` | 2 Byte | Motora gönderilen tork komutu |
| 6-7 | `motorRPM` | `int16_t` | `h` | 2 Byte | Motor devri (RPM) |
| 8-9 | `batteryVoltage` | `uint16_t`| `H` | 2 Byte | HV Batarya Gerilimi (Gerçek voltaj için **10.0'a bölünmelidir**). |
| 10-11| `batteryCurrent` | `int16_t` | `h` | 2 Byte | Batarya akımı (A, negatif = rejeneratif şarj) |
| 12 | `batterySOC` | `uint8_t` | `B` | 1 Byte | Batarya şarj seviyesi (0-100%) |
| 13 | `motorTemp` | `uint8_t` | `B` | 1 Byte | Motor sıcaklığı (°C) |
| 14 | `inverterTemp` | `uint8_t` | `B` | 1 Byte | İnverter sıcaklığı (°C) |
| 15 | `maxCellTemp` | `uint8_t` | `B` | 1 Byte | En sıcak hücre sıcaklığı (°C) |
| 16 | `systemFlags` | `uint8_t` | `B` | 1 Byte | Bit bazlı kontaktör/güvenlik durumları (AIR-, AIR+ vb.) |
| 17-20| `uptimeMs` | `uint32_t`| `I` | 4 Byte | Araç açılışından beri geçen süre (ms) |

#### `systemFlags` Bit Haritası (Byte 16):
* **Bit 0 (0x01):** AIR- (Negatif Kontaktör Kapalı/Aktif)
* **Bit 1 (0x02):** AIR+ (Pozitif Kontaktör Kapalı/Aktif)
* **Bit 2 (0x04):** Precharge Tamamlandı/Aktif
* **Bit 3 (0x08):** SDC Closed (Shutdown devresi kapalı, her şey OK)
* **Bit 4 (0x10):** Inverter Enable (İnverter aktif)

---

## ⚠️ Gelecekteki Değişiklikler ve Esneklik

* **Veri Yapısı Değişirse:** Gönderilen veriler, veri sıralaması ve paket boyutları ileride değişebilir. Bu durumda Mühendis 2'nin `core/parser.py` dosyasındaki struct format dizgisini (`"<BBBBhhHhBBBBBI"`) ve sözlük eşlemelerini güncellemesi gerekecektir.