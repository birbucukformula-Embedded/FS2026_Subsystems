# -*- coding: utf-8 -*-
"""
core/fake_data.py — SİMÜLASYON VERİ KAYNAĞI
============================================

Bu dosya "core" (çekirdek/veri) katmanına aittir ve ARAYÜZDEN TAMAMEN
BAĞIMSIZDIR: içinde hiçbir PyQt kodu yoktur. Görevi sadece, araçtan
gelecek telemetri paketinin AYNI FORMATTA sahtesini üretmektir.

Neden böyle yapıyoruz?
  1. Seri port (gerçek araç) olmadan da arayüzü test edebiliyoruz.
  2. İleride `core/serial_reader.py` yazıldığında, o da AYNI sözlük (dict)
     formatını döndüren bir sınıf olacak (ör. SerialReader.next_packet()).
     Arayüz tarafında neredeyse hiçbir şey değişmeyecek; sadece veri
     kaynağı nesnesi değiştirilecek.

NEDEN SINIF? (önceki sürümde düz fonksiyondu)
  Grafiklerin gerçekçi görünmesi için değerlerin YUMUŞAK değişmesi gerekir
  (gerçek sensör verisi ani zıplamaz). Bunu yapmak için "önceki değeri"
  hatırlamak lazım — yani state (durum) tutmak gerekir. Fonksiyonlar state
  tutamaz; sınıflar tutar. Bu yüzden veri kaynağını bir sınıfa aldık.

Paket alanları README'deki "FST-26 Pit Telemetri Veri Rehberi"nden
BİREBİR alınmıştır — rehberde ne varsa pakette de o var:
  Bölüm 1 (canlı):       seqNumber, vehicleState, faultCode, appsPercent,
                         brakePressure, torqueCommand, batteryVoltage,
                         systemFlags bitleri, uptimeMs
  Bölüm 2 (placeholder): motorRPM, batteryCurrent, batterySOC, motorTemp,
                         inverterTemp, maxCellTemp   (şu an sabit 0)
  Bölüm 3 (bağlantı):    gecikme, RSSI (pit tarafında hesaplanır/okunur)
"""

import random   # rastgele ama makul aralıkta sahte değerler üretmek için


# Araç durumları: gerçek sistemde vehicleState bir SAYI olarak gelir ve
# state machine'deki duruma karşılık gelir. Bu sözlük sayıyı okunur metne
# çevirir. (Kodlar temsilidir; gerçek değerler VCU koduyla eşleştirilecek.)
VEHICLE_STATES = {
    0: "INIT",       # açılış / kendini test
    1: "READY",      # sürüşe hazır
    2: "DRIVING",    # sürüş modu
    3: "FAULT",      # arıza durumu
}


def state_text(state_code: int) -> str:
    """
    vehicleState sayısını okunur metne çevirir.
    Bilinmeyen kod gelirse çökmek yerine "? (kod)" döndürür — telemetri
    arayüzü asla çökmemeli, bilinmeyen veriyi de göstermeli.
    """
    return VEHICLE_STATES.get(state_code, f"? ({state_code})")


def _drift(current: float, low: float, high: float, step: float) -> float:
    """
    "Random walk" (rastgele yürüyüş): bir değeri, önceki değerine yakın
    kalacak şekilde küçük bir miktar rastgele değiştirir. Böylece grafik
    testere dişi gibi zıplamak yerine gerçek sensör gibi yumuşak akar.

    - current: mevcut (önceki) değer
    - low, high: değerin çıkabileceği alt/üst sınır
    - step: bir adımda en fazla ne kadar değişebileceği

    max(low, min(high, ...)) kalıbı "clamp"tir: değeri sınırların içinde
    tutar (sınırı aşarsa sınırda sabitler).
    """
    current += random.uniform(-step, step)
    return max(low, min(high, current))


class FakeDataSource:
    """
    Sahte telemetri paketleri üreten kaynak.

    Kullanımı:
        source = FakeDataSource()
        packet = source.next_packet()   # her çağrıda bir sonraki paket

    İleride gerçek seri port okuyucusu da AYNI arayüzü sunacak
    (bir next_packet() metodu, aynı sözlük formatı), böylece arayüz kodu
    değişmeden veri kaynağı değiştirilebilecek.
    """

    def __init__(self):
        # Paket sıra numarası (seqNumber). Her pakette 1 artar; gerçek
        # sistemde kayıp paket hesabı bu sayaçtan yapılır.
        self.seq_number = 0

        # Canlı değerlerin BAŞLANGIÇ durumları. next_packet her çağrıldığında
        # bunları _drift ile azıcık değiştirip yeni paketi buradan üretiyoruz.
        # NOT: Simülasyonda ARTIK TÜM alanları üretiyoruz (eskiden RPM, akım,
        # SOC, sıcaklıklar sabit 0 idi). Böylece simülasyon modunda ekrandaki
        # her kart ve grafik gerçekçi veri gösterir. Gerçek araçta bu alanlar
        # CAN entegrasyonu gelene kadar yine gelmeyebilir — o durumu artık
        # "veri geldi mi?" mantığıyla (paket içinde var mı) ayırt ediyoruz.
        self._apps = 20.0            # gaz pedalı, %
        self._brake = 5.0            # fren basıncı, bar
        self._torque = 40.0          # tork komutu, Nm
        self._voltage = 395.0        # HV batarya gerilimi, V
        self._rpm = 3000.0           # motor devri, RPM
        self._current = 50.0         # batarya akımı, A
        self._soc = 85.0             # şarj durumu, %
        self._motor_temp = 45.0      # motor sıcaklığı, °C
        self._inverter_temp = 40.0   # inverter sıcaklığı, °C
        self._cell_temp = 35.0       # en yüksek hücre sıcaklığı, °C

    def next_packet(self) -> dict:
        """
        Bir sonraki sahte telemetri paketini üretir ve sözlük (dict) olarak
        döndürür. Dönen sözlüğün anahtarları README'deki alan adlarıyla
        birebir aynıdır; böylece gerçek paket ayrıştırıcı (parser) yazıldığında
        format uyuşur.
        """
        self.seq_number += 1

        # Canlı değerleri yumuşakça güncelle (random walk).
        self._apps          = _drift(self._apps,          0,    100,  step=6)
        self._brake         = _drift(self._brake,         0,    50,   step=4)
        self._torque        = _drift(self._torque,        0,    200,  step=12)
        self._voltage       = _drift(self._voltage,       380,  400,  step=1.2)
        self._rpm           = _drift(self._rpm,           0,    6000, step=200)
        self._current       = _drift(self._current,       -20,  180,  step=8)
        self._soc           = _drift(self._soc,           0,    100,  step=0.3)
        self._motor_temp    = _drift(self._motor_temp,    20,   90,   step=0.8)
        self._inverter_temp = _drift(self._inverter_temp, 20,   80,   step=0.7)
        self._cell_temp     = _drift(self._cell_temp,     20,   60,   step=0.5)

        return {
            # ---------------- Bölüm 1: CANLI ALANLAR ----------------
            "seqNumber": self.seq_number,
            "uptimeMs": self.seq_number * 100,   # 10 Hz'de her paket 100 ms arayla

            # Simülasyonda hep READY (1); arıza senaryosunu denemek istersen
            # vehicleState'i 3 ve faultCode'u 0 dışı bir değer yap.
            "vehicleState": 1,
            "faultCode": 0,              # 0 = arıza yok

            "appsPercent":    self._apps,
            "brakePressure":  self._brake,
            "torqueCommand":  self._torque,
            "batteryVoltage": self._voltage,

            # systemFlags bitleri: gerçekte tek bir sayının bitleri olarak
            # gelir (bit maskeleme ile çözülür); simülasyonda kolaylık olsun
            # diye ayrı ayrı bool tutuyoruz.
            "airMinus": True,        # AIR- kontaktörü kapalı (devrede)
            "airPlus": True,         # AIR+ kontaktörü kapalı (devrede)
            "precharge": True,       # precharge tamamlandı
            "sdcClosed": True,       # shutdown circuit kapalı (OK)
            "inverterEnable": True,  # inverter etkin

            # ---------------- Bölüm 2: (eskiden placeholder) ----------------
            # Gerçek araçta bu alanlar CAN entegrasyonu gelene kadar
            # gelmeyebilir; ama SİMÜLASYONDA hepsini üretiyoruz ki bütün
            # ekran (kartlar + grafikler) dolu ve test edilebilir olsun.
            "motorRPM": self._rpm,
            "batteryCurrent": self._current,
            "batterySOC": self._soc,
            "motorTemp": self._motor_temp,
            "inverterTemp": self._inverter_temp,
            "maxCellTemp": self._cell_temp,

            # ---------------- Bölüm 3: BAĞLANTI SAĞLIĞI ----------------
            # Gerçekte pit tarafında seqNumber/uptimeMs'ten HESAPLANIR,
            # paketin içinde gelmez; simülasyonda temsili üretiyoruz.
            "lossPercent": 0.0,                    # paket kayıp oranı, %
            "latencyMs": random.randint(20, 60),   # ms
            "rssiDbm": random.randint(-90, -60),   # dBm (LoRa sinyal gücü)
        }
