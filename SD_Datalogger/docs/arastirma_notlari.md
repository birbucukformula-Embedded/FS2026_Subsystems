# Araştırma Notları

## 1. Kişi: SPI protokolü ve f_open / f_write parametreleri

### 1. SPI Haberleşme Protokolü Nedir?
- **SPI (Serial Peripheral Interface):** MCU ile SD kart arasında senkron, tam çift yönlü (full-duplex) haberleşme sağlayan seri bir protokoldür. 4 hat kullanır:
  - **MOSI (Master Out Slave In):** MCU'dan SD karta giden veri hattı.
  - **MISO (Master In Slave Out):** SD karttan MCU'ya dönen veri hattı.
  - **SCK (Serial Clock):** MCU'nun ürettiği ve veri örneklemesini senkronize eden saat sinyali.
  - **CS (Chip Select):** MCU'nun "şu an seninle konuşuyorum" demesi için LOW'a çektiği pin. Birden fazla SPI cihazı aynı hatta olsa bile, aynı anda sadece CS'i LOW olan cihaz dinler/cevap verir.
- **Nasıl çalışır:** Her clock darbesinde MOSI'den 1 bit gönderilir, MISO'dan 1 bit okunur (aynı anda). SD kart, SPI modunda çalışırken önce CMD0/CMD8/CMD58 gibi komutlarla başlatılır (initialization), sonra CMD17 (tek blok oku) / CMD24 (tek blok yaz) gibi komutlarla 512 baytlık bloklar halinde okuma/yazma yapılır.
- **Neden 512 bayt önemli:** SPI üzerinden SD karta yazma komutu her zaman 512 baytlık (1 sektör) blok bazında çalışır — bu da 2. Kişinin buffer'ı neden 512 bayt seçtiğinin donanımsal sebebi.

### 2. FATFS Kütüphanesinde f_open / f_write / f_sync / f_close
- **`f_mount(&fs, path, opt)`**: Dosya sistemini (FAT12/16/32) bir sürücü numarasına bağlar. `opt=1` verilirse hemen (gecikmesiz) mount dener ve kart takılı değilse burada hata alınır — bizim `SD_Logger_Init()`'in karşılığı.
- **`f_open(&file, filename, mode)`**: Dosyayı açar. Mode bayrakları `|` ile birleştirilir:
  - `FA_READ` / `FA_WRITE`: okuma/yazma izni.
  - `FA_OPEN_ALWAYS`: dosya yoksa oluştur, varsa aç (bizim `fopen(..., "a")` karşılığımız).
  - `FA_CREATE_NEW`: dosya zaten varsa hata döner.
  - Append (sona ekleme) için `f_open` sonrası `f_lseek(&file, f_size(&file))` ile imleç dosya sonuna taşınır.
- **`f_write(&file, buf, len, &bw)`**: `buf` içindeki `len` baytı dosyaya yazar, gerçekte kaç bayt yazıldığını `bw` (bytes written) parametresine yazar. Dönen `bw != len` ise disk dolmuş demektir.
- **`f_sync(&file)`**: FATFS'in RAM'de tuttuğu dosya tablosu (FAT) ve tampon önbelleğini fiziksel olarak SD karta yazdırır, dosyayı kapatmadan veri kaybını önler (örn. ani güç kesilmesine karşı).
- **`f_close(&file)`**: Önce içeride `f_sync` çağırır, sonra dosya tanıtıcısını (handle) serbest bırakır.
- **Hata kodu:** Tüm bu fonksiyonlar `FRESULT` enum'u döner (`FR_OK`, `FR_DISK_ERR`, `FR_NOT_READY`, `FR_DENIED` vb.) — bizim `SD_Logger_Status_t` enum'umuz bu FRESULT kodlarının basitleştirilmiş/projeye özel karşılığıdır.

## 2. Kişi: Neden buffer kullandık?

### 1. Sürekli SD Karta Yazmak Kartı Neden Bozar ve Yavaşlatır? (Flash Wear-Out & Latency)
- **NAND Flash Blok Silme/Yazma Mimarisi:** SD kartlar küçük baytlar halinde (örn. 20-30 baytlık her bir CSV satırı) yazmayı fiziksel olarak desteklemez. Bir hücreye yazmak için öncelikle tüm **Sektörün (512 Byte)** veya **Bloğun** okunup, silinip tekrar yazılması gerekir (Read-Modify-Write çevrimi).
- **Yüksek Yazma Yükü (Write Amplification) & Aşınma (Wear-Out):** Her 30 baytlık veri geldiğinde yazma komutu göndermek, arka planda kart kontrolcüsünün sürekli 512 baytlık hücreleri silip yeniden yazmasına yol açar. Bu durum flash hücrelerinin ömrünü çok hızlı tüketir.
- **Yüksek Gecikme (Latency) & Mikrodenetleyici Bloklanması:** SPI üzerinden SD karta yazma işlemi milisaniyeler (1-10 ms, bazen kart içi temizlikte 50-100 ms) sürebilir. Eğer her CAN mesajında diske yazma yapılırsa MCU kilitlenir, yüksek öncelikli CAN kesmeleri (interrupt) kaçırılır ve telemetri verisi kaybedilir.

### 2. Sektör Buffer (512 Bayt) ve Ring/Double Buffer Mantığı Nasıl Çalışır?
- **Sektör Buffer (512 Bayt / 1 Blok):** Gelen her CSV satırı doğrudan SD karta gönderilmez; RAM üzerinde ayrılan `CAN_BUFFER_SECTOR_SIZE` (512 Byte) boyutundaki bir dizide (`s_sector_buffer`) biriktirilir. Tampon 512 bayta ulaştığında tek bir SPI/FATFS yazma işlemiyle (`SD_Logger_Write`) karta blok halinde aktarılır. Bu sayede hem kart aşınmaz hem de işlem süreleri %95 oranında azalır.
- **Ring (Dairesel) veya Double (Çift) Buffer Stratejisi:** Gömülü sistemlerde daha gelişmiş senaryolar için **Double Buffer** (Ping-Pong Buffer) kullanılır. Birinci tampon dolduğunda yazma işlemi DMA/SPI ile arka planda SD karta yapılırken, yeni gelen CAN mesajları kesintisiz olarak ikinci tampona yazılmaya devam eder.
