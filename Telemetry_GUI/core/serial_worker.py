# -*- coding: utf-8 -*-
"""
core/serial_worker.py — SERİ PORT İLETİŞİMİ VE ARKA PLAN İŞ PARÇACIĞI (WORKER THREAD)
========================================================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 1 (Seri Port İletişimi & Backend)
------------------------------------------------------------------
Bu dosya, bilgisayara bağlı COM portlarının taraması, portun seçilen Baudrate (115200)
ile açılması/kapatılması ve seri porttan veri okuma işleminin arayüzü kilitlemeden
arka planda çalışmasını sağlar.

Ham binary ve XOR checksum doğrulaması yapacak şekilde güncellenmiştir.
"""

import serial
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal


def list_available_ports() -> list:
    """Bilgisayara bağlı mevcut tüm COM portlarını listeler."""
    return [(port.device, port.description) for port in serial.tools.list_ports.comports()]


def find_vehicle_port() -> str:
    """
    Bilgisayara bağlı seri portları tarar ve yaygın USB-UART dönüştürücü
    çiplerini arayarak LoRa alıcısını otomatik tespit etmeye çalışır.
    """
    LORA_PORT_HINTS = [
        "ftdi", "ft232",             # FTDI entegreleri
        "cp210", "silicon labs",     # Silicon Labs CP210x entegreleri
        "ch340", "ch341", "wch",     # WCH CH340 entegreleri (ucuz klonlar)
        "usb to uart", "usb serial", # Genel dönüştürücüler
        "usbmodem", "uart"           # macOS / Linux isimlendirmeleri
    ]
    
    for port in serial.tools.list_ports.comports():
        device_info = " ".join([
            str(port.description).lower(),
            str(port.manufacturer).lower(),
            str(port.hwid).lower()
        ])
        
        if any(hint in device_info for hint in LORA_PORT_HINTS):
            return port.device
            
    return None


def calculate_xor_checksum(data_bytes: bytes) -> int:
    """Verilen byte dizisinin tüm elemanlarını XOR'layarak tek bir checksum üretir."""
    checksum = 0
    for b in data_bytes:
        checksum ^= b
    return checksum


class SerialWorker(QThread):
    """
    Seri porttan arka planda okuma yapan QThread sınıfı.

    SİNYALLER:
        - raw_line_received(str)   : Doğrulanmış ham payload byte'larını hex string olarak fırlatır.
        - connection_status(bool, str) : Bağlantı durumunu bildirir.
        - error_occurred(str)      : Hata durumlarını arayüze bildirir.
    """

    raw_line_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port_name: str, baudrate: int = 115200, parent=None):
        super().__init__(parent)
        self.port_name = port_name
        self.baudrate = baudrate
        self.is_running = False
        self.serial_port = None

    def run(self):
        """Arka planda (ayrı iş parçacığında) seri porttan veri okur."""
        self.is_running = True
        try:
            self.serial_port = serial.Serial(self.port_name, self.baudrate, timeout=0.1)
            self.connection_status.emit(True, f"BAĞLI: {self.port_name}")
            
            while self.is_running and self.serial_port.is_open:
                # 1. İlk header byte'ını (0xAA) ara
                b1 = self.serial_port.read(1)
                if not b1 or b1[0] != 0xAA:
                    continue
                
                # 2. İkinci header byte'ını (0x55) doğrula
                b2 = self.serial_port.read(1)
                if not b2 or b2[0] != 0x55:
                    continue
                
                # 3. Length (data uzunluğu) byte'ını oku
                len_byte = self.serial_port.read(1)
                if not len_byte or len_byte[0] == 0:
                    continue
                payload_size = len_byte[0]
                
                # 4. Dinamik uzunluğa göre payload oku
                payload = self.serial_port.read(payload_size)
                if len(payload) != payload_size:
                    continue
                
                # 5. Checksum byte'ını oku (1 byte)
                checksum_byte = self.serial_port.read(1)
                if not checksum_byte or len(checksum_byte) != 1:
                    continue
                
                # 6. Checksum kontrolü yap
                if calculate_xor_checksum(payload) == checksum_byte[0]:
                    # Paket geçerli! Hex formatında sinyali fırlat.
                    self.raw_line_received.emit(payload.hex())
                else:
                    # Bozuk paket, yoksay
                    pass
                    
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.stop()

    def stop(self):
        """Arka plan döngüsünü durdurmak ve portu kapatmak için çağrılır."""
        self.is_running = False
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.connection_status.emit(False, "Bağlantı Kesildi")