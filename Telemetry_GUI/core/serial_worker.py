# -*- coding: utf-8 -*-
"""
core/serial_worker.py — SERİ PORT İLETİŞİMİ VE ARKA PLAN İŞ PARÇACIĞI (WORKER THREAD)
========================================================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 1 (Seri Port İletişimi & Backend)
------------------------------------------------------------------
Bu dosya, bilgisayara bağlı COM portlarının taraması, portun seçilen Baudrate (örn. 115200)
ile açılması/kapatılması ve seri porttan veri okuma işleminin arayüzü KİLİTLEMEDEN (freeze olmadan)
arka planda çalışmasını sağlamak için oluşturulmuş bir İSKELET / ŞABLON dosyadır.

GÖREV TANIMI VE ADIMLAR (MÜHENDİS 1 İÇİN TODO REHBERİ):
  1. `list_available_ports()`:
     - `serial.tools.list_ports.comports()` kullanarak bilgisayara takılı tüm COM portlarını bul ve
       `[("COM3", "CP2102 USB to UART Bridge"), ...]` formatında liste döndür.
  2. `SerialWorker(QThread)` Sınıfı:
     - `ser.readline()` bloklayıcı (blocking) bir işlem olduğu için bu okuma KESİNLİKLE ana
       arayüz (GUI) thread'inde yapılmamalıdır; `QThread` içindeki `run()` metodunda yapılmalıdır.
     - Okunan ham satırı (`str` veya `bytes`) `raw_line_received` sinyaliyle ilet (Mühendis 2'nin
       parser katmanı bu sinyali dinleyecek).
     - Port açma/kapama durumlarında `connection_status` sinyali, hatalarda `error_occurred` sinyali fırlat.
"""

from PyQt5.QtCore import QThread, pyqtSignal

# TODO (MÜHENDİS 1): pyserial kütüphanesini import edin
# import serial
# import serial.tools.list_ports


def list_available_ports() -> list:
    """
    Bilgisayara bağlı mevcut tüm COM portlarını listeler.

    Dönüş Formatı (Örnek):
        [
            ("COM3", "CP2102 USB to UART Bridge Controller"),
            ("COM4", "USB Serial Port (FTDI)")
        ]

    TODO (MÜHENDİS 1):
        - serial.tools.list_ports.comports() metodunu çağırın.
        - Her portun device (COM port adı) ve description (açıklama) alanlarını çift (tuple)
          olarak listeye ekleyip döndürün.
    """
    # --- MÜHENDİS 1 KOD ALANI BAŞLANGICI ---
    # Örnek taslak:
    # return [(port.device, port.description) for port in serial.tools.list_ports.comports()]
    return []
    # --- MÜHENDİS 1 KOD ALANI BİTİŞİ ---


class SerialWorker(QThread):
    """
    Seri porttan arka planda okuma yapan QThread sınıfı.

    SİNYALLER (OUTBOUND INTERFACES):
        - raw_line_received(str)   : Seri porttan \n ile biten ham bir satır okunduğunda fırlatılır.
        - connection_status(bool, str) : Bağlantı açıldığında (True, "COM3 Bağlı"), kapandığında (False, "Bağlantı Kesildi").
        - error_occurred(str)      : Okuma/bağlantı hatası oluştuğunda arayüzü bilgilendirmek için fırlatılır.
    """

    # --- SİNYAL TANIMLARI ---
    raw_line_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port_name: str, baudrate: int = 115200, parent=None):
        super().__init__(parent)
        self.port_name = port_name
        self.baudrate = baudrate
        self.is_running = False
        # TODO (MÜHENDİS 1): serial.Serial nesnesi tutmak için bir nitelik (self.serial_port = None) tanımlayın.

    def run(self):
        """
        QThread başlatıldığında (worker.start()) otomatik çağıran metot.
        Arka planda (ayrı iş parçacığında) sonsuz döngüde seri port okur.

        TODO (MÜHENDİS 1):
            1. serial.Serial ile self.port_name portunu belirtilen self.baudrate hızında açın.
            2. Başarılıysa self.connection_status.emit(True, f"BAĞLI: {self.port_name}") çağırın.
            3. while self.is_running: döngüsü oluşturarak ser.readline() ile satır okuyun.
            4. Okunan satırı .decode('utf-8', errors='ignore').strip() ile temizleyip
               self.raw_line_received.emit(line) sinyaliyle yayınlayın.
            5. Bağlantı koptuğunda veya SerialException olduğunda self.error_occurred sinyali verin.
            6. Döngü bittiğinde (stop() çağrıldığında) portu güvenlice kapatıp
               self.connection_status.emit(False, "KESİLDİ") verin.
        """
        # --- MÜHENDİS 1 KOD ALANI BAŞLANGICI ---
        self.is_running = True
        # YÖNERGE ÖRNEĞİ:
        # try:
        #     self.serial_port = serial.Serial(self.port_name, self.baudrate, timeout=1)
        #     self.connection_status.emit(True, f"BAĞLI: {self.port_name}")
        #     while self.is_running and self.serial_port.is_open:
        #         line = self.serial_port.readline().decode("utf-8", errors="ignore").strip()
        #         if line:
        #             self.raw_line_received.emit(line)
        # except Exception as e:
        #     self.error_occurred.emit(str(e))
        # finally:
        #     self.stop()
        pass
        # --- MÜHENDİS 1 KOD ALANI BİTİŞİ ---

    def stop(self):
        """
        Arka plan döngüsünü durdurmak ve portu kapatmak için arayüz tarafından çağrılır.

        TODO (MÜHENDİS 1):
            - self.is_running bayrağını False yapın.
            - Açık seri port varsa ve isOpen() ise close() metodunu çağırın.
            - self.wait() veya pyqtSignal ile kapanışı arayüze bildirin.
        """
        # --- MÜHENDİS 1 KOD ALANI BAŞLANGICI ---
        self.is_running = False
        # --- MÜHENDİS 1 KOD ALANI BİTİŞİ ---
