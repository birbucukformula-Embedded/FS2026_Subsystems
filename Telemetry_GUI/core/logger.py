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

    def __init__(self, log_dir: str = "logs", flush_interval: int = 10):
        self.log_dir = log_dir
        self.filepath = None
        self.file_handle = None
        self.writer = None
        self.flush_interval = max(1, int(flush_interval))
        self._pending_flush_count = 0

    def open(self):
        """Yeni bir log oturumu başlatır ve CSV başlıklarını yazar.

        Bu metod, Mühendis 2'nin yaptığı veri pipeline'ın ilk adımıdır.
        Her yarış/test oturumu için ayrı bir CSV dosyası açılır; böylece
        Mühendis 3'ün UI verileriyle, analiz için saklanan kayıtlar aynı yapıda tutulur.
        """
        os.makedirs(self.log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filepath = os.path.join(self.log_dir, f"telemetry_{timestamp}.csv")
        self.file_handle = open(self.filepath, "w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.file_handle, fieldnames=CSV_FIELDNAMES, restval="")
        self.writer.writeheader()
        self.file_handle.flush()
        self._pending_flush_count = 0

    def log_packet(self, packet: dict):
        """
        Gelen telemetri paketini CSV satırı olarak diske yazar.

        Bu yöntem, parser.py'den gelen işlenmiş paketi zaman damgası ile birlikte
        kayıt altına alır. Amaç, daha sonra analiz veya raporlama yapılabilmesi için
        ham veri akışını bozmadan kaydı korumaktır.
        """
        if not self.writer or not self.file_handle:
            self.open()

        row = dict(packet)
        row["timestamp_local"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        for field in CSV_FIELDNAMES:
            row.setdefault(field, "")
        self.writer.writerow(row)
        self._pending_flush_count += 1
        if self._pending_flush_count >= self.flush_interval:
            self.file_handle.flush()
            self._pending_flush_count = 0

    def close(self):
        """
        Dosya tutucusunu kapatır ve tüm arabelleklerin (buffer) diske yazılmasını sağlar.

        Bu adım, loglama işleminin güvenli şekilde tamamlanması için gereklidir.
        Böylece yarış sonunda veya bağlantı kesildiğinde CSV dosyası bozulmadan kapanır.
        """
        try:
            if self.file_handle and not self.file_handle.closed:
                self.file_handle.flush()
                self.file_handle.close()
        except Exception:
            pass
        finally:
            self.file_handle = None
            self.writer = None

