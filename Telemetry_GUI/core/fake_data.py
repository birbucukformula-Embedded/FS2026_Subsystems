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
     formatını döndürecek. Arayüz tarafında TEK SATIR bile değişmeyecek;
     sadece veri kaynağı değiştirilecek.

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


def generate_packet(seq_number: int) -> dict:
    """
    Tek bir sahte telemetri paketi üretir ve sözlük (dict) olarak döndürür.

    Parametre:
        seq_number: paket sıra numarası (seqNumber). Çağıran taraf her
                    seferinde 1 artırarak verir; gerçek sistemde kayıp
                    paket hesabı bu numaradan yapılır.

    Dönen sözlüğün anahtarları README'deki alan adlarıyla birebir aynıdır;
    böylece gerçek paket ayrıştırıcı (parser) yazıldığında format uyuşur.
    """
    return {
        # ---------------- Bölüm 1: CANLI ALANLAR ----------------
        "seqNumber": seq_number,
        "uptimeMs": seq_number * 100,   # 10 Hz'de her paket 100 ms arayla

        # Simülasyonda hep READY (1); arıza senaryosunu denemek istersen
        # vehicleState'i 3 ve faultCode'u 0 dışı bir değer yap.
        "vehicleState": 1,
        "faultCode": 0,              # 0 = arıza yok

        "appsPercent":    random.uniform(0, 100),    # gaz pedalı, %
        "brakePressure":  random.uniform(0, 50),     # fren basıncı, bar
        "torqueCommand":  random.uniform(0, 200),    # tork komutu, Nm
        "batteryVoltage": random.uniform(380, 400),  # HV batarya gerilimi, V

        # systemFlags bitleri: gerçekte tek bir sayının bitleri olarak
        # gelir (bit maskeleme ile çözülür); simülasyonda kolaylık olsun
        # diye ayrı ayrı bool tutuyoruz.
        "airMinus": True,        # AIR- kontaktörü kapalı (devrede)
        "airPlus": True,         # AIR+ kontaktörü kapalı (devrede)
        "precharge": True,       # precharge tamamlandı
        "sdcClosed": True,       # shutdown circuit kapalı (OK)
        "inverterEnable": True,  # inverter etkin

        # ---------------- Bölüm 2: PLACEHOLDER ALANLAR ----------------
        # Gerçek sistemde de şu an sabit 0 geliyor; CAN entegrasyonu
        # yapılana kadar arayüz bunları gri "—" olarak gösterecek.
        "motorRPM": 0,          # inverter CAN'ı gelince gerçek olacak
        "batteryCurrent": 0,    # BMS CAN'ı gelince
        "batterySOC": 0,        # BMS CAN'ı gelince
        "motorTemp": 0,         # inverter CAN'ı gelince
        "inverterTemp": 0,      # inverter CAN'ı gelince
        "maxCellTemp": 0,       # BMS CAN'ı gelince

        # ---------------- Bölüm 3: BAĞLANTI SAĞLIĞI ----------------
        # Gerçekte pit tarafında seqNumber/uptimeMs'ten HESAPLANIR,
        # paketin içinde gelmez; simülasyonda temsili üretiyoruz.
        "latencyMs": random.randint(20, 60),   # ms
        "rssiDbm": random.randint(-90, -60),   # dBm (LoRa sinyal gücü)
    }


def state_text(state_code: int) -> str:
    """
    vehicleState sayısını okunur metne çevirir.
    Bilinmeyen kod gelirse çökmek yerine "? (kod)" döndürür — telemetri
    arayüzü asla çökmemeli, bilinmeyen veriyi de göstermeli.
    """
    return VEHICLE_STATES.get(state_code, f"? ({state_code})")
