# FS2026 Alt Sistemler ve Ar-Ge Reposu 🏎️💨

Bu repository, ana araç beyni (VCU) dışındaki alt modüllerin, göstergelerin, arayüzlerin ve araştırma algoritmalarının geliştirildiği alandır. 

Ana koda (Core VCU) entegre edilmeden önce tüm denemeler, testler ve UI çalışmaları bu repo içerisinde yapılacaktır. Aşağıda yazılım ekibimiz için açılmış **5 Bağımsız Görev** detaylıca açıklanmıştır. Herkes bir görev seçip kendi klasörünü oluşturarak çalışmalara başlayabilir.

---

## 🖥️ Görev 1: Sürücü Ekranı Tasarımı (Dashboard)
Sürücünün kokpitte göreceği verileri görselleştiren arayüzün tasarlanması ve haberleşme kodunun yazılmasıdır.

**Beklentiler:**
1. **Nextion Editor** programı indirilip kullanılacak.
2. Ekranda bulunması gerekenler:
   - Araç Hızı (Gauge / İbreli gösterge veya büyük dijital font)
   - Batarya Sıcaklığı ve Yüzdesi (Progress Bar)
   - Hata Durumu (Büyük Kırmızı Uyarı kutusu - Örn: "Fren-Gaz Çakışması")
3. **Araştırma Konusu:** STM32 ile Nextion Ekranı arasında UART (Seri Haberleşme) protokolü nasıl kurulur? Ekrandaki hız değeri C kodundan gönderilen veriyle nasıl güncellenir?

**Başlangıç Klasörü Önerisi:** `/Dashboard_Nextion/`

---

## 📡 Görev 2: Yer İstasyonu (Telemetri) Arayüzü
Pit alanındaki mühendislerin pistteki aracı canlı olarak takip edeceği bilgisayar programının (Yer İstasyonu) kodlanmasıdır.

**Beklentiler:**
1. Tercihen **Python** (PyQt5 / Tkinter) veya **C#** ile bir masaüstü uygulaması geliştirilecek.
2. Programın yapması gerekenler:
   - Bilgisayarın Seri Portuna (COM) bağlanma arayüzü.
   - Seri porttan "Hız: 65, Sicaklik: 42" gibi gelen String veya Byte verilerini ayrıştırma (Parsing).
   - Bu verileri anlık (Real-time) olarak çizgi grafiklere (Plot) dökme (Örn: Matplotlib veya PyQtGraph kullanarak).
3. **Araştırma Konusu:** Python `pyserial` kütüphanesi nasıl kullanılır? Saniyede 10 kere gelen veri ekranda takılma (freeze) yaratmadan nasıl çizdirilir?

**Başlangıç Klasörü Önerisi:** `/Telemetry_GUI/`

---

## 🧮 Görev 3: Sensör Gürültü Filtreleme Algoritmaları
Gerçek dünyada sensörlerden okunan voltajlar her zaman titrek ve parazitlidir (Noise). Bu görevin amacı ham verileri pürüzsüzleştirmektir.

**Beklentiler:**
1. C dili kullanılarak, dışarıdan kütüphane almadan matematiksel filtre fonksiyonları yazılacak.
2. İki farklı filtre türü koda dökülecek:
   - **Moving Average (Hareketli Ortalama):** Son 10 sensör verisini bir dizide (Array) tutup ortalamasını alan algoritma.
   - **Low-Pass Filter (Alçak Geçiren Filtre):** `Y_yeni = (A * X_yeni) + ((1-A) * Y_eski)` formülü ile çalışan dijital sinyal işleme fonksiyonu.
3. **Araştırma Konusu:** C dilinde Pointer'lar nasıl çalışır? Sabit boyutlu dizilerde veriler nasıl kaydırılır (Circular Buffer mantığı)?

**Başlangıç Klasörü Önerisi:** `/Sensor_Filters/`

---

## 🚥 Görev 4: Durum Göstergeleri (Non-Blocking LED/Buzzer)
Aracın durumunu pilot ve dışarıdaki hakemlere bildiren uyarı ışıklarının kontrol algoritmalarıdır.

**Beklentiler:**
1. C dilinde `delay()` veya `HAL_Delay()` FONKSİYONU KESİNLİKLE KULLANILMADAN yanıp sönme animasyonları yazılacak.
2. Örnek Senaryo:
   - Eğer `hata_var == 1` ise LED saniyede 5 kere yanıp sönsün.
   - Eğer `hata_var == 0` ise LED saniyede 1 kere (kalp atışı gibi) yanıp sönsün.
3. **Araştırma Konusu:** `millis()` (Timer / SysTick) kullanarak zaman hesaplama nasıl yapılır? State Machine (Durum Makinesi) kullanılarak eşzamanlı (Concurrency) işlemler C dilinde nasıl koda dökülür?

**Başlangıç Klasörü Önerisi:** `/Status_Indicators/`

---

## 💾 Görev 5: CAN Bus Veri Kaydedici (SD Card Datalogger)
Ağ üzerinde dönen araç hız, sıcaklık ve hata verilerinin test sonrası analiz edilebilmesi için bir SD karta yazdırılmasıdır.

**Beklentiler:**
1. CAN Bus'tan okunan (Sanal olarak C'de tanımlanmış) verileri, Excel tablosu olacak şekilde virgüllerle ayırarak String formatına çevirmek (CSV Formatı).
2. Bu veriyi FATFS dosya sistemi kullanarak SD karta `.csv` uzantısıyla yazma fonksiyonları oluşturmak.
3. **Araştırma Konusu:** SPI haberleşme protokolü nedir? Gömülü sistemlerde dosya açma `f_open`, dosya yazma `f_write` fonksiyonları nasıl kullanılır? Sürekli SD karta yazmak kartı bozup yavaşlatır mı? (Buffer mantığı araştırması).

**Başlangıç Klasörü Önerisi:** `/SD_Datalogger/`

---

### Katkıda Bulunma Rehberi
1. Bu repoyu bilgisayarınıza indirin (`git clone`).
2. Çalışacağınız görev için bir klasör oluşturun.
3. Kodlarınızı yazıp çalıştırdıktan sonra `git add`, `git commit` ve `git push` ile bu repoya gönderin.
4. Takıldığınız yerlerde birbirinize veya VCU Core ekibine danışmaktan çekinmeyin!
