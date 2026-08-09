# -*- coding: utf-8 -*-
"""
core/simulator.py — SİMÜLATÖR / SAHTE TELEMETRİ VERİ MODÜLÜ
===========================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 1 (Seri Port, Arka Plan İletişimi & Simülatör)
-------------------------------------------------------------------------------
Bu dosya, araç veya LoRa / RF alıcı donanımı elimizde olmadığında bile arayüzün (GUI)
ve veri ayrıştırıcının (`parser.py`) tam bağımsız test edilebilmesi için sahte telemetri
paketleri üreten simülatör modülüdür.

Yeni ham binary paket yapısına uygun olarak struct.pack ile 21 byte veri paketi üretir.
"""

import struct
import random
import time
from PyQt5.QtCore import QThread, pyqtSignal

from core.serial_worker import calculate_xor_checksum


def _drift(current: float, low: float, high: float, step: float) -> float:
    """Yumuşak veri geçişleri için rastgele yürüyüş (random walk) algoritması."""
    current += random.uniform(-step, step)
    return max(low, min(high, current))


class TelemetrySimulator(QThread):
    """
    Donanım olmadan testi sağlayan sahte telemetri veri üreticisi QThread sınıfı.

    SİNYALLER:
        - raw_line_received(str)   : Üretilen sahte payload'u hex string formatında fırlatır.
        - connection_status(bool, str) : Simülasyon durumunu arayüze bildirir.
        - error_occurred(str)      : Hata durumunda tetiklenir.
    """

    raw_line_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, interval_ms: int = 100, parent=None):
        super().__init__(parent)
        self.interval_ms = interval_ms
        self.is_running = False

        # Başlangıç sahte sensör değerleri
        self.seq_num = 0
        self._apps = 20.0
        self._brake = 5.0
        self._torque = 40.0
        self._rpm = 3000.0
        self._voltage = 395.0
        self._current = 50.0
        self._soc = 85.0
        self._motor_temp = 45.0
        self._inverter_temp = 40.0
        self._cell_temp = 35.0

    def run(self):
        """QThread başlatıldığında periyodik olarak sahte veri üretir."""
        self.is_running = True
        self.connection_status.emit(True, "SİMÜLASYON BAĞLI")
        
        try:
            while self.is_running:
                self.seq_num += 1

                # Değerleri rastgele yürüyüşle (drift) güncelle
                self._apps          = _drift(self._apps,          0,    100,  step=6)
                self._brake         = _drift(self._brake,         0,    50,   step=4)
                self._torque        = _drift(self._torque,        0,    200,  step=12)
                self._rpm           = _drift(self._rpm,           0,    6000, step=200)
                self._voltage       = _drift(self._voltage,       380,  400,  step=1.2)
                self._current       = _drift(self._current,       -20,  180,  step=8)
                self._soc           = _drift(self._soc,           0,    100,  step=0.3)
                self._motor_temp    = _drift(self._motor_temp,    20,   90,   step=0.8)
                self._inverter_temp = _drift(self._inverter_temp, 20,   80,   step=0.7)
                self._cell_temp     = _drift(self._cell_temp,     20,   60,   step=0.5)

                # Rastgele hata durumları oluştur (100 pakette 1 ihtimal)
                fault_code = 0
                if random.random() < 0.01:
                    fault_code = random.choice([1, 2, 3, 4, 5])

                # System flags (Bit field)
                system_flags = 0
                if self.seq_num > 5:
                    system_flags |= (1 << 0)  # Negative contactor
                if self.seq_num > 10:
                    system_flags |= (1 << 1)  # Positive contactor
                if self.seq_num > 8:
                    system_flags |= (1 << 2)  # Precharge
                if fault_code == 0:
                    system_flags |= (1 << 3)  # SDC closed
                if self.seq_num > 12:
                    system_flags |= (1 << 4)  # Inverter enable

                # struct.pack ile 21 byte veri paketi üret (Format: <BBBBhhHhBBBBBI)
                payload = struct.pack(
                    "<BBBBhhHhBBBBBI",
                    2 if self._apps > 25 else 1,   # vehicleState (uint8_t)
                    fault_code,                    # faultCode (uint8_t)
                    int(self._apps),               # appsPercent (uint8_t)
                    int(self._brake),              # brakePressure (uint8_t)
                    int(self._torque),             # torqueCommand (int16_t)
                    int(self._rpm),                # motorRPM (int16_t)
                    int(self._voltage * 10),       # batteryVoltage (uint16_t - V * 10, örn: 3950 = 395.0V)
                    int(self._current),            # batteryCurrent (int16_t)
                    int(self._soc),                # batterySOC (uint8_t)
                    int(self._motor_temp),         # motorTemp (uint8_t)
                    int(self._inverter_temp),      # inverterTemp (uint8_t)
                    int(self._cell_temp),          # maxCellTemp (uint8_t)
                    system_flags,                  # systemFlags (uint8_t)
                    self.seq_num * 100             # uptimeMs (uint32_t - 10 Hz'de her paket +100ms)
                )

                # Paketi hex formatında sinyal ile yayınla
                self.raw_line_received.emit(payload.hex())

                # 10 Hz frekansı sağlamak için bekle
                time.sleep(self.interval_ms / 1000.0)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.stop()

    def stop(self):
        """Simülasyonu durdurmak için çağrılır."""
        self.is_running = False
        self.connection_status.emit(False, "SİMÜLASYON DURDURULDU")