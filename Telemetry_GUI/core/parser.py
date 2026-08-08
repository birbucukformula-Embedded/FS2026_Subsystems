# -*- coding: utf-8 -*-
"""
core/parser.py — VERİ AYRIŞTIRMA (PARSING), DOĞRULAMA VE BAĞLANTI SAĞLIĞI
========================================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 2 (Veri İşleme, Doğrulama & Data Pipeline)
--------------------------------------------------------------------------
Bu dosya, Mühendis 1'in seri porttan (`SerialWorker`) aldığı ham metin veya bayt dizilerini
anlamlı Python sözlüklerine (dictionary) çeviren, CRC / sıra numarası (`seqNumber`) denetimi
yapan ve paket kayıp oranı (`lossPercent`), gecikme (`latencyMs`) hesaplayan İSKELET / ŞABLON dosyadır.

GÖREV TANIMI VE ADIMLAR (MÜHENDİS 2 İÇİN TODO REHBERİ):
  1. `parse_text_line(raw_line: str) -> dict`:
     - Gelen satır `"appsPercent: 45, batteryVoltage: 396"` veya JSON string ise ayrıştır.
     - README alan adlarıyla uyuşan bir Python dict döndür.
  2. `parse_binary_packet(raw_bytes: bytes) -> dict`:
     - VCU / LoRa binary paket gönderiyorsa `struct.unpack()` ile float/int/bit bayraklarını ayrıştır.
  3. `validate_packet(packet: dict, state_tracker: dict) -> bool`:
     - `seqNumber` (paket sıra numarası) takibiyle kayıp paket sayısını tespit et.
     - Checksum / CRC kontrolü ile bozuk paketleri ele.
"""

import json
import struct
import time

# README'de Tanımlı Örnek Alan Adları (Arayüz bu anahtarları bekler):
# "seqNumber", "uptimeMs", "vehicleState", "faultCode", "appsPercent",
# "brakePressure", "torqueCommand", "batteryVoltage", "airMinus", "airPlus", ...


def parse_text_line(raw_line: str) -> dict:
    """
    Seri porttan gelen tek bir metin satırını telemetri sözlüğüne çevirir.
    Ayrıştıramazsa None döndürür.

    GİRDİ (Input):
        raw_line -> Örnek 1: '{"appsPercent": 45, "batteryVoltage": 396}'
                    Örnek 2: "appsPercent: 45, batteryVoltage: 396, seqNumber: 104"

    ÇIKTI (Output):
        {"appsPercent": 45.0, "batteryVoltage": 396.0, "seqNumber": 104}

    TODO (MÜHENDİS 2):
        - Önce json.loads() ile satırın geçerli bir JSON olup olmadığını deneyin.
        - JSON değilse satırı virgül (",") ve iki nokta (":") karakterlerinden parçalayarak
          anahtar-değer (key-value) sözlüğü oluşturun.
        - Değerleri sayıya (int/float) çevirecek bir yardımcı fonksiyon kullanın.
    """
    # --- MÜHENDİS 2 KOD ALANI BAŞLANGICI ---
    # Taslak yönerge:
    # 1) Try json.loads(raw_line)
    # 2) If ValueError -> parse as "key: value, key: value"
    return None
    # --- MÜHENDİS 2 KOD ALANI BİTİŞİ ---


def parse_binary_packet(raw_bytes: bytes) -> dict:
    """
    VCU / STM32 / Raspberry Pi tarafından gönderilen sıkıştırılmış ikili (binary) verileri ayrıştırır.

    GİRDİ (Input):
        raw_bytes -> Örn: b'\\x01\\x00\\x00\\x00\\x14\\x00\\x00\\x00...'

    TODO (MÜHENDİS 2):
        - struct.unpack() fonksiyonunu ve araç verici paketiyle (C struct) eşleşen
          format dizgesini (örn: "<IHff") kullanarak baytları çözün.
        - Ayrıştırılan alanları README dokümanındaki standart isimlerle bir dict içinde döndürün.
    """
    # --- MÜHENDİS 2 KOD ALANI BAŞLANGICI ---
    return {}
    # --- MÜHENDİS 2 KOD ALANI BİTİŞİ ---


class ConnectionHealthTracker:
    """
    Bağlantı sağlığı metriklerini (Paket kayıp oranı %, Latency ms) tutan yardımcı sınıf.

    TODO (MÜHENDİS 2):
        - `last_seq_number`: Son gelen paket sıra numarasını tutun.
        - `update_health(packet)`:
          * `seqNumber` ile `last_seq_number` arasındaki fark 1'den büyükse aradaki kayıpları sayın.
          * `lossPercent = (toplam_kayip / toplam_paket) * 100` formülünü hesaplayıp pakete
            `lossPercent` anahtarıyla ekleyin.
          * `uptimeMs` ile pit yerel saatini (`time.time() * 1000`) karşılaştırarak
            `latencyMs` gecikme süresini hesaplayın ve pakete ekleyin.
    """

    def __init__(self):
        self.last_seq = None
        self.total_received = 0
        self.total_lost = 0

    def process_health_metrics(self, packet: dict) -> dict:
        """
        Pakete 'lossPercent' ve 'latencyMs' alanlarını ekleyip/güncelleyerek geri döndürür.
        """
        # --- MÜHENDİS 2 KOD ALANI BAŞLANGICI ---
        # Örnek mantık:
        # seq = packet.get("seqNumber")
        # if seq is not None and self.last_seq is not None:
        #     if seq > self.last_seq + 1:
        #         self.total_lost += (seq - self.last_seq - 1)
        # ...
        return packet
        # --- MÜHENDİS 2 KOD ALANI BİTİŞİ ---
