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
from string import hexdigits

# README'de Tanımlı Örnek Alan Adları (Arayüz bu anahtarları bekler):
# "seqNumber", "uptimeMs", "vehicleState", "faultCode", "appsPercent",
# "brakePressure", "torqueCommand", "batteryVoltage", "airMinus", "airPlus", ...


def _coerce_value(value):
    """String değerleri sayıya çevirmeye çalışır; mümkün değilse olduğu gibi döndürür.

    Bu yardımcı fonksiyon, Mühendis 1'den gelen metin verisini GUI, grafik ve CSV loglama
    tarafında güvenli biçimde kullanabilmek için tip dönüşümü yapar.
    """
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return ""
        lowered = value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value
    return value


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
    # Bu bölüm, Mühendis 1'in serial_worker/simulator'dan verdiği ham veriyi
    # GUI'nin anlayacağı ortak telemetri sözlüğüne dönüştürür.
    # Amaç: JSON, anahtar-değer metni ve hex payload'ları aynı arayüzle işleyebilmek.
    if raw_line is None:
        return {}

    if isinstance(raw_line, bytes):
        return parse_binary_packet(raw_line)

    line = str(raw_line).strip()
    if not line:
        return {}

    try:
        parsed = json.loads(line)
        if isinstance(parsed, dict):
            return {key: _coerce_value(value) for key, value in parsed.items()}
    except (TypeError, ValueError):
        pass

    compact = "".join(line.split())
    if len(compact) % 2 == 0 and all(ch in hexdigits for ch in compact):
        try:
            return parse_binary_packet(bytes.fromhex(compact))
        except ValueError:
            pass

    packet = {}
    for part in line.split(","):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        packet[key.strip()] = _coerce_value(value.strip())

    return packet
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
    # Bu bölüm, araçtan gelen binary telemetri paketini C struct yapısına uygun biçimde
    # çözerek UI tarafında kullanılacak alanlara dönüştürür.
    # Amaç: grafikler, rozetler ve sayısal kartlar için doğru değerleri hazırlamak.
    if isinstance(raw_bytes, str):
        raw_bytes = bytes.fromhex(raw_bytes)

    if not isinstance(raw_bytes, (bytes, bytearray)):
        return {}

    packet_bytes = bytes(raw_bytes)
    fmt = "<BBBBhhHhBBBBBI"
    expected_size = struct.calcsize(fmt)
    if len(packet_bytes) < expected_size:
        return {}

    (
        vehicle_state_code,
        fault_code,
        apps_percent,
        brake_pressure,
        torque_command,
        motor_rpm,
        battery_voltage,
        battery_current,
        battery_soc,
        motor_temp,
        inverter_temp,
        max_cell_temp,
        system_flags,
        uptime_ms,
    ) = struct.unpack(fmt, packet_bytes[:expected_size])

    vehicle_state_map = {
        1: "READY",
        2: "DRIVING",
        3: "FAULT",
    }

    return {
        "vehicleState": vehicle_state_map.get(vehicle_state_code, str(vehicle_state_code)),
        "faultCode": fault_code,
        "appsPercent": float(apps_percent),
        "brakePressure": float(brake_pressure),
        "torqueCommand": float(torque_command),
        "motorRPM": motor_rpm,
        "batteryVoltage": battery_voltage / 10.0,
        "batteryCurrent": float(battery_current),
        "batterySOC": battery_soc,
        "motorTemp": motor_temp,
        "inverterTemp": inverter_temp,
        "maxCellTemp": max_cell_temp,
        "systemFlags": {
            "AIR-": bool(system_flags & 0x01),
            "AIR+": bool(system_flags & 0x02),
            "Precharge": bool(system_flags & 0x04),
            "SDC Closed": bool(system_flags & 0x08),
            "Inverter Enable": bool(system_flags & 0x10),
        },
        "uptimeMs": uptime_ms,
    }
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
        # Bu bölüm, paket kaybı ve gecikmeyi hesaplayarak arayüzde alt şeritte gösterilecek
        # metrikleri hazırlar. Böylece Mühendis 3'ün UI tarafı doğrudan bu değerleri kullanabilir.
        packet = dict(packet)
        seq = packet.get("seqNumber")

        if seq is not None:
            try:
                seq = int(seq)
            except (TypeError, ValueError):
                seq = None

            if seq is not None:
                if self.last_seq is not None and seq > self.last_seq + 1:
                    self.total_lost += (seq - self.last_seq - 1)
                self.last_seq = seq

        self.total_received += 1
        total_packets = max(self.total_received, 1)
        if self.total_lost > 0:
            packet["lossPercent"] = round((self.total_lost / total_packets) * 100.0, 2)
        else:
            packet["lossPercent"] = 0.0

        uptime_ms = packet.get("uptimeMs")
        try:
            uptime_ms = int(uptime_ms)
        except (TypeError, ValueError):
            uptime_ms = None

        if uptime_ms is not None:
            packet["latencyMs"] = max(0, int((time.time() * 1000) - uptime_ms))
        else:
            packet["latencyMs"] = 0

        return packet
        # --- MÜHENDİS 2 KOD ALANI BİTİŞİ ---
