# Araştırma Notları

## 1. Kişi: SPI protokolü ve f_open / f_write parametreleri
(Buraya notlarınızı ekleyebilirsiniz...)

## 2. Kişi: Neden buffer kullandık?

### 1. Sürekli SD Karta Yazmak Kartı Neden Bozar ve Yavaşlatır? (Flash Wear-Out & Latency)
- **NAND Flash Blok Silme/Yazma Mimarisi:** SD kartlar küçük baytlar halinde (örn. 20-30 baytlık her bir CSV satırı) yazmayı fiziksel olarak desteklemez. Bir hücreye yazmak için öncelikle tüm **Sektörün (512 Byte)** veya **Bloğun** okunup, silinip tekrar yazılması gerekir (Read-Modify-Write çevrimi).
- **Yüksek Yazma Yükü (Write Amplification) & Aşınma (Wear-Out):** Her 30 baytlık veri geldiğinde yazma komutu göndermek, arka planda kart kontrolcüsünün sürekli 512 baytlık hücreleri silip yeniden yazmasına yol açar. Bu durum flash hücrelerinin ömrünü çok hızlı tüketir.
- **Yüksek Gecikme (Latency) & Mikrodenetleyici Bloklanması:** SPI üzerinden SD karta yazma işlemi milisaniyeler (1-10 ms, bazen kart içi temizlikte 50-100 ms) sürebilir. Eğer her CAN mesajında diske yazma yapılırsa MCU kilitlenir, yüksek öncelikli CAN kesmeleri (interrupt) kaçırılır ve telemetri verisi kaybedilir.

### 2. Sektör Buffer (512 Bayt) ve Ring/Double Buffer Mantığı Nasıl Çalışır?
- **Sektör Buffer (512 Bayt / 1 Blok):** Gelen her CSV satırı doğrudan SD karta gönderilmez; RAM üzerinde ayrılan `CAN_BUFFER_SECTOR_SIZE` (512 Byte) boyutundaki bir dizide (`s_sector_buffer`) biriktirilir. Tampon 512 bayta ulaştığında tek bir SPI/FATFS yazma işlemiyle (`SD_Logger_Write`) karta blok halinde aktarılır. Bu sayede hem kart aşınmaz hem de işlem süreleri %95 oranında azalır.
- **Ring (Dairesel) veya Double (Çift) Buffer Stratejisi:** Gömülü sistemlerde daha gelişmiş senaryolar için **Double Buffer** (Ping-Pong Buffer) kullanılır. Birinci tampon dolduğunda yazma işlemi DMA/SPI ile arka planda SD karta yapılırken, yeni gelen CAN mesajları kesintisiz olarak ikinci tampona yazılmaya devam eder.
