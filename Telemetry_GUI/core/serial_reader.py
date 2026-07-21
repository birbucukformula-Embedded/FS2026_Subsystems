# -*- coding: utf-8 -*-
"""
core/serial_reader.py — GERÇEK SERİ PORT VERİ KAYNAĞI
======================================================

Bu dosya "core" katmanına aittir ve içinde PyQt YOKTUR. Görevi:
  1. Bilgisayara bağlı seri portları taramak.
  2. Raspberry Pi / USB-UART köprüsü benzeri bir portu otomatik bulmak.
  3. Bir porta bağlanıp gelen telemetri satırlarını okumak.

EN ÖNEMLİ TASARIM NOKTASI — AYNI ARAYÜZ:
  SerialReader sınıfı, FakeDataSource ile TAM AYNI arayüzü sunar:
  bir `next_packet()` metodu vardır ve README alan adlarıyla bir sözlük
  (dict) döndürür. Böylece arayüz (main_window) kodu, verinin sahte mi
  gerçek mi olduğunu bilmek zorunda kalmaz; ikisini de aynı şekilde kullanır.
  Fark: FakeDataSource her çağrıda dolu paket döndürür; SerialReader ise
  o an okunacak veri yoksa None döndürür (arayüz o kareyi atlar).

⚠️ PAKET FORMATI HENÜZ KESİN DEĞİL:
  VCU/Raspberry Pi tarafının seri porttan tam olarak NE gönderdiği (binary
  paket mi, "anahtar: değer" metni mi, JSON mu) proje ilerledikçe
  kesinleşecek. Bu yüzden ayrıştırma (parsing) işini TEK bir fonksiyona
  (`parse_line`) topladık. Format belli olunca sadece o fonksiyon
  güncellenecek; gerisi olduğu gibi kalacak.
"""

import json   # satır JSON ise ayrıştırmak için

import serial                       # pyserial: seri port haberleşmesi
from serial.tools import list_ports # bağlı portları listelemek için


# Raspberry Pi ya da yaygın USB-UART köprü çiplerini (aracın bilgisayara
# bağlandığı adaptörler) tanımak için aranan anahtar kelimeler. Portun
# açıklaması/üreticisi/donanım kimliğinde bunlardan biri geçiyorsa, o portu
# "araç bağlantısı adayı" kabul ediyoruz.
VEHICLE_PORT_HINTS = (
    "raspberry", "pi",              # doğrudan Raspberry Pi
    "cp210", "slab",                # Silicon Labs CP210x USB-UART
    "ftdi", "ft232",                # FTDI USB-UART
    "ch340", "ch910",               # WCH CH340 USB-UART
    "usb serial", "usbserial",      # genel "USB Serial" adaptörler
    "usbmodem", "uart",             # macOS usbmodem / genel UART
)

# VCU ile aynı olması gereken haberleşme hızı (bit/saniye). VCU tarafı
# hangi baud ile gönderiyorsa bu da o olmalı; yaygın varsayılan 115200.
DEFAULT_BAUDRATE = 115200


def list_serial_ports():
    """
    Bilgisayara bağlı tüm seri portları döndürür.

    Dönüş: [(device, description), ...] listesi.
      device      -> porta bağlanmak için kullanılan ad (COM3, /dev/cu.usbserial-x)
      description -> insana okunur açıklama (adaptör adı vb.)
    """
    return [(port.device, port.description) for port in list_ports.comports()]


def find_vehicle_port():
    """
    Raspberry Pi / USB-UART köprüsü benzeri İLK portu bulur.
    Bulursa port adını (device), bulamazsa None döndürür.

    Portun açıklaması, üreticisi ve donanım kimliğini tek bir metinde
    birleştirip VEHICLE_PORT_HINTS anahtar kelimelerinden herhangi biriyle
    eşleşiyor mu diye bakıyoruz. (Bluetooth, debug-console gibi sistem
    portları bu anahtarlarla eşleşmediği için elenir.)
    """
    for port in list_ports.comports():
        # None olabilecek alanları boş metne çevirip küçük harfe indiriyoruz.
        haystack = " ".join(
            str(x).lower() for x in (port.description, port.manufacturer, port.hwid)
            if x
        )
        if any(hint in haystack for hint in VEHICLE_PORT_HINTS):
            return port.device
    return None


def _to_number(text: str):
    """
    Metni sayıya çevirmeye çalışır: önce tam sayı (int), olmazsa ondalık
    (float), o da olmazsa metni olduğu gibi bırakır. Örn "42" -> 42,
    "3.7" -> 3.7, "READY" -> "READY".
    """
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def parse_line(line: str):
    """
    Seri porttan gelen TEK bir metin satırını telemetri sözlüğüne çevirir.
    Ayrıştıramazsa None döndürür.

    ⚠️ Bu fonksiyon GEÇİCİDİR — gerçek VCU paket formatı kesinleşince
    burası güncellenecek. Şimdilik iki yaygın biçimi destekliyor:

      1) JSON  : {"appsPercent": 45, "batteryVoltage": 396}
      2) Metin : "appsPercent: 45, batteryVoltage: 396"

    İkisi de anahtarları README'deki alan adlarıyla eşleştirir; böylece
    arayüz paketi olduğu gibi kullanabilir.
    """
    line = line.strip()
    if not line:
        return None

    # 1) Önce JSON dene (VCU JSON gönderiyorsa en temiz yol budur).
    try:
        data = json.loads(line)
        if isinstance(data, dict):
            return data
    except ValueError:
        pass   # JSON değilmiş, aşağıdaki metin biçimini dene

    # 2) "anahtar: değer, anahtar: değer" biçimini dene.
    packet = {}
    for part in line.split(","):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        packet[key.strip()] = _to_number(value.strip())

    # Hiçbir alan çıkaramadıysak satır tanınmıyor demektir -> None.
    return packet if packet else None


class SerialReader:
    """
    Bir seri porta bağlanıp gelen telemetri satırlarını okuyan veri kaynağı.
    FakeDataSource ile aynı arayüzü sunar: next_packet() ve (ek olarak) close().

    Kullanımı:
        reader = SerialReader("/dev/cu.usbserial-x")
        packet = reader.next_packet()   # dict veya None
        ...
        reader.close()
    """

    def __init__(self, port: str, baudrate: int = DEFAULT_BAUDRATE):
        self.port = port
        # timeout=0: okuma İŞLEMİ BEKLEMEZ (non-blocking). Böylece veri
        # yokken arayüz donmaz; QTimer her tetiklendiğinde anında döner.
        self.ser = serial.Serial(port, baudrate, timeout=0)
        # Yarım gelen satırları biriktirmek için tampon (buffer). Seri veri
        # parça parça gelebilir; satır sonu (\n) görene kadar burada tutarız.
        self._buffer = ""

    def next_packet(self):
        """
        O an okunabilen veriyi alır. Tam bir satır (\\n ile biten) oluştuysa
        onu ayrıştırıp sözlük döndürür; henüz tam satır yoksa None döndürür.
        """
        # Bekleyen baytları oku (yoksa boş döner, beklemez).
        try:
            waiting = self.ser.in_waiting
            if waiting:
                self._buffer += self.ser.read(waiting).decode("utf-8", errors="ignore")
        except (OSError, serial.SerialException):
            # Kablo çekilmiş / port kaybolmuş olabilir. Çökmek yerine None.
            return None

        # Tampon içinde tam bir satır (\n) var mı?
        if "\n" not in self._buffer:
            return None

        # İlk tam satırı ayır; kalanı tamponda bırak (bir sonraki tur için).
        line, self._buffer = self._buffer.split("\n", 1)
        return parse_line(line)

    def close(self):
        """Portu kapatır. Program kapanırken veya bağlantı kesilirken çağrılır."""
        try:
            self.ser.close()
        except (OSError, serial.SerialException):
            pass   # zaten kapalıysa/kaybolduysa sorun değil
