# -*- coding: utf-8 -*-
"""
core/logger.py — VERİ KAYDI (CSV LOGGING) MODÜLÜ
=================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 2 (Veri İşleme, Loglama & Data Pipeline)
----------------------------------------------------------------------
Bu dosya, yarış/test esnasında seri porttan gelen ve doğrulanmış telemetri verilerinin
daha sonra analiz edilebilmesi için zaman damgasıyla (timestamp) birlikte `logs/` altındaki
`.csv` dosyalarına yazılmasından sorumlu İSKELET / ŞABLON dosyadır.

GÖREV TANIMI VE ADIMLAR (MÜHENDİS 2 İÇİN TODO REHBERİ):
  1. `TelemetryCSVLogger` Sınıfı:
     - Program açıldığında veya oturum başladığında `logs/` klasörü içinde
       `telemetry_20260728_153000.csv` formatında otomatik bir dosya adı üretin.
     - `csv.DictWriter` veya standart dosya yazma yöntemleri kullanarak README'de tanımlı
       tüm sütun başlıklarını (header) ilk satır olarak dosyaya yazın.
     - `log_packet(packet: dict)` metodu her çağrıldığında sözlüğü CSV satırına dönüştürüp
       dosyaya append (`"a"`) edin.
     - Performans ipucu: Her satırda `file.flush()` yapmak yerine belirli aralıklarla
       veya kapatırken (`close()`) disk yazmasını tamamlayın.
"""

import csv
import os
import time
from datetime import datetime

# Standart CSV Sütun Sıralaması (README Bölüm 1 & 2'deki Alanlar):
CSV_FIELDNAMES = [
    "timestamp_local",   # Pit istasyonu yerel zaman damgası (örn. 2026-07-28 15:30:12.123)
    "seqNumber",
    "uptimeMs",
    "vehicleState",
    "faultCode",
    "appsPercent",
    "brakePressure",
    "torqueCommand",
    "batteryVoltage",
    "batteryCurrent",
    "batterySOC",
    "motorRPM",
    "motorTemp",
    "inverterTemp",
    "maxCellTemp",
    "lossPercent",
    "latencyMs",
    "rssiDbm",
]


class TelemetryCSVLogger:
    """
    Doğrulanmış telemetri sözlüklerini (dict) CSV dosyasına kaydeden loglayıcı sınıf.

    KULLANIM (Arayüz / Ana Döngü Tarafında):
        logger = TelemetryCSVLogger(log_dir="logs")
        ...
        logger.log_packet(packet)
        ...
        logger.close()
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.filepath = None
        self.file_handle = None
        self.writer = None
        # TODO (MÜHENDİS 2):
        # 1) os.makedirs(self.log_dir, exist_ok=True) ile logs klasörünün varlığından emin olun.
        # 2) datetime.now().strftime("%Y%m%d_%H%M%S") kullanarak benzersiz bir dosya adı oluşturun.
        # 3) Dosyayı yazma modunda ("w", newline="", encoding="utf-8") açın.
        # 4) csv.DictWriter(self.file_handle, fieldnames=CSV_FIELDNAMES) oluşturup writeheader() çağırın.

    def open(self):
        """Yeni bir log oturumu başlatır ve CSV başlıklarını yazar."""
        # --- MÜHENDİS 2 KOD ALANI BAŞLANGICI ---
        pass
        # --- MÜHENDİS 2 KOD ALANI BİTİŞİ ---

    def log_packet(self, packet: dict):
        """
        Gelen telemetri paketini CSV satırı olarak diske yazar.

        TODO (MÜHENDİS 2):
            - Sözlüğe "timestamp_local" anahtarıyla anlık tarih/saat etiketini ekleyin
              (örn. datetime.now().isoformat()).
            - self.writer.writerow(row) metodu ile satırı yazın.
            - Eksik alan gelirse DictWriter'ın hata vermemesi için `restval=""` veya
              `packet.get(col, "")` mantığı kullanın.
        """
        # --- MÜHENDİS 2 KOD ALANI BAŞLANGICI ---
        pass
        # --- MÜHENDİS 2 KOD ALANI BİTİŞİ ---

    def close(self):
        """
        Dosya tutucusunu kapatır ve tüm arabelleklerin (buffer) diske yazılmasını sağlar.
        """
        # --- MÜHENDİS 2 KOD ALANI BAŞLANGICI ---
        # try:
        #     if self.file_handle and not self.file_handle.closed:
        #         self.file_handle.close()
        # except Exception:
        #     pass
        pass
        # --- MÜHENDİS 2 KOD ALANI BİTİŞİ ---
