# -*- coding: utf-8 -*-
"""
core/simulator.py — SİMÜLATÖR / SAHTE TELEMETRİ VERİ MODÜLÜ
===========================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 1 (Seri Port, Arka Plan İletişimi & Simülatör)
-------------------------------------------------------------------------------
Bu dosya, araç veya LoRa / RF alıcı donanımı elimizde olmadığında bile arayüzün (GUI)
ve veri ayrıştırıcının (`parser.py`) tam bağımsız test edilebilmesi için, sanki araç
pistte tur atıyormuş gibi saniyede 10 kez (10 Hz) sahte telemetri satırları/paketleri
üreten İSKELET / ŞABLON dosyadır.

GÖREV TANIMI VE ADIMLAR (MÜHENDİS 1 İÇİN TODO REHBERİ):
  1. `TelemetrySimulator(QThread)` Sınıfı:
     - Gerçek seri port okuyucusu (`SerialWorker`) ile AYNI sinyal arayüzünü sunun
       (`raw_line_received`, `connection_status`).
     - Böylece arayüz tarafı verinin gerçek araçtan mı yoksa simülatörden mi geldiğini
       bilmek zorunda kalmaz; ikisi de aynı parser'dan geçerek işlenir.
     - `run()` metodu içinde `time.sleep(0.1)` (100 ms) aralıklarla sahte sensör
       verilerini üretip `raw_line_received.emit(sahte_satir)` yayınlayın.
     - Sensör verilerinin gerçekçi görünmesi için değerleri her adımda küçük miktarlarda
       değiştirin (random walk / drift).
"""

import random
import time
from PyQt5.QtCore import QThread, pyqtSignal


class TelemetrySimulator(QThread):
    """
    Donanım (araç/COM port) olmadan testi sağlayan sahte telemetri veri üreticisi.

    SİNYALLER (OUTBOUND INTERFACES - SerialWorker ile birebir aynı):
        - raw_line_received(str)   : Üretilen sahte metin satırını fırlatır
                                     (Örn: 'appsPercent: 45.2, batteryVoltage: 395.1').
        - connection_status(bool, str) : Simülasyon başladığında (True, "SİMÜLASYON BAĞLI").
        - error_occurred(str)      : Simülasyon hatası oluşursa arayüze bildirir.
    """

    raw_line_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, interval_ms: int = 100, parent=None):
        super().__init__(parent)
        self.interval_ms = interval_ms
        self.is_running = False

        # Başlangıç sahte sensör değerleri:
        self.seq_num = 0
        self.apps_percent = 20.0
        self.brake_pressure = 5.0
        self.battery_voltage = 395.0
        self.torque_command = 40.0
        self.motor_rpm = 3000.0

    def run(self):
        """
        QThread başladığında periyodik olarak sahte veri üretir.

        TODO (MÜHENDİS 1):
            1. self.connection_status.emit(True, "SİMÜLASYON MODU") çağırın.
            2. while self.is_running: döngüsü içinde self.seq_num değerini 1 artırın.
            3. Sensör değerlerine küçük rastgele değişimler ekleyerek (drift) güncelleyin.
            4. Satırı JSON string veya "key: value, key: value" formatında oluşturun:
               Örn: f"seqNumber: {self.seq_num}, appsPercent: {self.apps_percent:.1f}, batteryVoltage: {self.battery_voltage:.1f}"
            5. self.raw_line_received.emit(fake_line) ile satırı yayınlayın.
            6. time.sleep(self.interval_ms / 1000.0) ile 10 Hz frekansı sağlayın.
        """
        # --- MÜHENDİS 1 KOD ALANI BAŞLANGICI ---
        self.is_running = True
        # Örnek taslak:
        # self.connection_status.emit(True, "SİMÜLASYON MODU BAĞLI")
        # while self.is_running:
        #     self.seq_num += 1
        #     fake_line = f"seqNumber: {self.seq_num}, appsPercent: {self.apps_percent:.1f}, batteryVoltage: {self.battery_voltage:.1f}"
        #     self.raw_line_received.emit(fake_line)
        #     time.sleep(self.interval_ms / 1000.0)
        pass
        # --- MÜHENDİS 1 KOD ALANI BİTİŞİ ---

    def stop(self):
        """Simülasyonu durdurmak için arayüz tarafından çağrılır."""
        # --- MÜHENDİS 1 KOD ALANI BAŞLANGICI ---
        self.is_running = False
        self.connection_status.emit(False, "SİMÜLASYON DURDURULDU")
        # --- MÜHENDİS 1 KOD ALANI BİTİŞİ ---
