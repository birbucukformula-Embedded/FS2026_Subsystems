# -*- coding: utf-8 -*-
"""
gui/main_window.py — ANA PENCERE
=================================

Bütün bölümleri birleştiren ana pencere sınıfı. Yerleşim:

    ┌───────────────────────────────────────────────────────┐
    │  LOGO  PIT TELEMETRİ            [● BAĞLANTI CHIP]     │  üst şerit
    ├───────────────────────────────────────────────────────┤
    │  ARAÇ DURUMU: READY             ARIZA: YOK            │  durum satırı
    ├───────────────────────────────────────────────────────┤
    │  ▍SÜRÜŞ                                               │
    │  [GAZ] [FREN] [TORK] [MOTOR RPM —]                    │
    │  ▍BATARYA (HV)                                        │
    │  [GERİLİM] [AKIM —] [SOC —] [MAX HÜCRE °C —]          │
    │  ▍SICAKLIKLAR                                         │
    │  [MOTOR °C —] [İNVERTER °C —]                         │
    ├───────────────────────────────────────────────────────┤
    │  ▍SİSTEM    [●AIR-] [●AIR+] [●PRECHARGE] [●SDC] [●INV]│  rozetler
    ├───────────────────────────────────────────────────────┤
    │  Paket#  Kayıp  Gecikme  RSSI                         │  alt şerit
    └───────────────────────────────────────────────────────┘

"—" işaretli kartlar README Bölüm 2'deki placeholder alanlardır: pakette
var ama CAN entegrasyonu bitene kadar sabit 0 geliyor; gri gösterilirler.

Bu dosya SADECE görsel dizilim ve güncelleme ile ilgilenir; veri üretimi
core katmanındadır (core/fake_data.py). Küçük parçalar (kart, chip,
bölüm başlığı) gui/widgets.py içindedir.
"""

import os   # logo dosyasının tam yolunu bulmak için

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QGridLayout,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap

# Kendi modüllerimiz: theme (renkler), widgets (parçalar), fake_data (veri).
from gui import theme
from gui.widgets import ValueCard, StatusChip, SectionTitle
from core import fake_data

# Logo dosyasının yolu. __file__ = bu dosyanın konumu; oradan bir üst
# klasöre çıkıp assets/logo.png'ye ulaşıyoruz. Böylece program hangi
# klasörden çalıştırılırsa çalıştırılsın logo bulunur.
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")


class MainWindow(QMainWindow):
    """Uygulamanın ana penceresi: bölümleri kurar ve periyodik günceller."""

    def __init__(self):
        super().__init__()

        # --- Pencere temel ayarları ---
        self.setWindowTitle("FS2026 — 1.5 Adana Formula Student | Pit Telemetri")
        self.resize(1000, 720)
        self.setStyleSheet(theme.STYLE_WINDOW)    # koyu tema (site renkleri)

        # QMainWindow'a doğrudan yerleşim verilemez; önce bir "merkez
        # widget" koyup yerleşimi ona bağlamak gerekir (PyQt kalıbı).
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)  # pencere iç boşluğu
        main_layout.setSpacing(10)                      # bölümler arası boşluk

        # Bölümleri sırayla kur. Her bölüm ayrı metod; __init__ kısa kalsın.
        main_layout.addLayout(self._build_top_bar())
        main_layout.addLayout(self._build_vehicle_status_row())
        main_layout.addWidget(SectionTitle("Sürüş"))
        main_layout.addLayout(self._build_drive_cards())
        main_layout.addWidget(SectionTitle("Batarya (HV)"))
        main_layout.addLayout(self._build_battery_cards())
        main_layout.addWidget(SectionTitle("Sıcaklıklar"))
        main_layout.addLayout(self._build_temperature_cards())
        main_layout.addWidget(SectionTitle("Sistem"))
        main_layout.addLayout(self._build_status_chips())
        main_layout.addStretch()   # kalan boşluğu alta it (kartlar yayılmasın)
        main_layout.addLayout(self._build_bottom_bar())

        # --- VERİ ZAMANLAYICISI ---
        # QTimer: belirli aralıkla bir fonksiyonu çağırır. Qt'nin olay
        # döngüsü (event loop) içinde çalıştığı için arayüzü DONDURMAZ.
        # README'deki "saniyede 10 veri ekranı dondurmadan nasıl çizilir?"
        # sorusunun cevabı budur (while+sleep yerine QTimer).
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(100)   # 100 ms = saniyede 10 kez (10 Hz)

        # Paket sıra numarası (seqNumber). Her pakette 1 artar.
        self.packet_counter = 0

    # ------------------------------------------------------------------
    # BÖLÜM KURULUM METODLARI — her biri bir yerleşim (layout) döndürür
    # ------------------------------------------------------------------

    def _build_top_bar(self):
        """Üst şerit: solda takım logosu + başlık, sağda bağlantı chip'i."""
        bar = QHBoxLayout()

        # --- Takım logosu ---
        # QPixmap resmi yükler; scaledToHeight ile 36 px yüksekliğe
        # küçültürüz (SmoothTransformation = kaliteli küçültme).
        logo_label = QLabel()
        logo_pixmap = QPixmap(LOGO_PATH)
        if not logo_pixmap.isNull():   # dosya yoksa çökme, logosuz devam et
            logo_label.setPixmap(
                logo_pixmap.scaledToHeight(36, Qt.SmoothTransformation)
            )

        # --- Başlık ---
        title = QLabel("1.5 Adana Formula Student | Pit Telemetri")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet(f"color: {theme.COLOR_TEXT}; letter-spacing: 3px;")

        # --- Bağlantı durumu chip'i ---
        # Rozetlerle aynı görünüm: koyu hap + renkli nokta. Seri port
        # gelince nokta yeşil (STABİL) / kırmızı (KOPTU) olacak.
        self.connection_chip = StatusChip("SİMÜLASYON")

        bar.addWidget(logo_label)
        bar.addSpacing(10)          # logo ile başlık arası sabit boşluk
        bar.addWidget(title)
        bar.addStretch()            # esnek boşluk -> chip'i sağa yaslar
        bar.addWidget(self.connection_chip)
        return bar

    def _build_vehicle_status_row(self):
        """
        Araç durumu (vehicleState) ve arıza (faultCode) satırı.
        Yazılar normalde BEYAZ kalır; sadece arıza anında kırmızıya döner.
        (Sürekli yeşil yanmaz — göz yormasın.)
        """
        row = QHBoxLayout()

        self.state_label = QLabel("ARAÇ DURUMU: —")
        self.state_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.state_label.setStyleSheet(f"color: {theme.COLOR_TEXT};")

        self.fault_label = QLabel("ARIZA: —")
        self.fault_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.fault_label.setStyleSheet(f"color: {theme.COLOR_TEXT_MUTED};")

        row.addWidget(self.state_label)
        row.addStretch()
        row.addWidget(self.fault_label)
        return row

    def _build_drive_cards(self):
        """SÜRÜŞ bölümü: gaz, fren, tork (canlı) + motor RPM (placeholder)."""
        grid = QGridLayout()
        grid.setSpacing(10)

        self.card_apps   = ValueCard("GAZ PEDALI", "%")
        self.card_brake  = ValueCard("FREN BASINCI", "bar")
        self.card_torque = ValueCard("TORK KOMUTU", "Nm")
        # README Bölüm 2: motorRPM inverter CAN'ı bağlanınca gerçek olacak.
        self.card_rpm    = ValueCard("MOTOR DEVRİ", "RPM", placeholder=True)

        # addWidget(widget, satır, sütun)
        grid.addWidget(self.card_apps,   0, 0)
        grid.addWidget(self.card_brake,  0, 1)
        grid.addWidget(self.card_torque, 0, 2)
        grid.addWidget(self.card_rpm,    0, 3)
        return grid

    def _build_battery_cards(self):
        """BATARYA bölümü: gerilim (canlı) + akım, SOC, max hücre (placeholder)."""
        grid = QGridLayout()
        grid.setSpacing(10)

        self.card_voltage = ValueCard("GERİLİM", "V")
        # README Bölüm 2: bu üçü BMS CAN'ı bağlanınca gerçek olacak.
        self.card_current   = ValueCard("AKIM", "A", placeholder=True)
        self.card_soc       = ValueCard("ŞARJ DURUMU (SOC)", "%", placeholder=True)
        self.card_cell_temp = ValueCard("MAX HÜCRE SICAKLIĞI", "°C", placeholder=True)

        grid.addWidget(self.card_voltage,   0, 0)
        grid.addWidget(self.card_current,   0, 1)
        grid.addWidget(self.card_soc,       0, 2)
        grid.addWidget(self.card_cell_temp, 0, 3)
        return grid

    def _build_temperature_cards(self):
        """SICAKLIKLAR bölümü: motor ve inverter sıcaklığı (ikisi de placeholder)."""
        grid = QGridLayout()
        grid.setSpacing(10)

        # README Bölüm 2: ikisi de inverter CAN'ı bağlanınca gerçek olacak.
        self.card_motor_temp    = ValueCard("MOTOR", "°C", placeholder=True)
        self.card_inverter_temp = ValueCard("İNVERTER", "°C", placeholder=True)

        grid.addWidget(self.card_motor_temp,    0, 0)
        grid.addWidget(self.card_inverter_temp, 0, 1)
        # Diğer bölümlerle sütun hizası tutsun diye 4 sütunun DA genişliğini
        # eşitliyoruz (stretch=1). Böylece 2 kart, üstteki kartlarla aynı
        # genişlikte olur; kalan 2 sütun boş kalır ama yer kaplar.
        for column in range(4):
            grid.setColumnStretch(column, 1)
        return grid

    def _build_status_chips(self):
        """AIR-, AIR+, PRECHARGE, SDC, INV EN durum chip'leri satırı."""
        row = QHBoxLayout()
        row.setSpacing(8)

        # Eşleme: chip üzerindeki isim -> paketteki alan adı.
        # Güncellerken bu sözlüğü dolaşarak her chip'e kendi verisini vereceğiz.
        self.chip_fields = {
            "AIR-":      "airMinus",
            "AIR+":      "airPlus",
            "PRECHARGE": "precharge",
            "SDC":       "sdcClosed",
            "INV EN":    "inverterEnable",
        }
        self.chips = {}
        for name in self.chip_fields:
            chip = StatusChip(name)
            self.chips[name] = chip
            row.addWidget(chip)

        row.addStretch()   # chip'leri sola yasla
        return row

    def _build_bottom_bar(self):
        """Alt şerit: paket no + bağlantı sağlığı metrikleri."""
        bar = QHBoxLayout()

        # Paket sırası (seqNumber) küçük referans metni olarak gösterilir
        # (README önerisi). Kayıp/gecikme/RSSI pit tarafında hesaplanır.
        self.packet_label  = QLabel("Paket: —")
        self.loss_label    = QLabel("Kayıp: —%")
        self.latency_label = QLabel("Gecikme: — ms")
        self.rssi_label    = QLabel("RSSI: — dBm")

        for label in (self.packet_label, self.loss_label,
                      self.latency_label, self.rssi_label):
            label.setStyleSheet(
                f"color: {theme.COLOR_INACTIVE}; font-size: 11px;"
            )
            bar.addWidget(label)
            bar.addSpacing(20)

        bar.addStretch()
        return bar

    # ------------------------------------------------------------------
    # PERİYODİK GÜNCELLEME
    # ------------------------------------------------------------------

    def update_data(self):
        """
        QTimer tarafından saniyede 10 kez çağrılır.

        Akış: core katmanından bir paket al -> ekrandaki widget'lara işle.
        İleride seri port eklendiğinde SADECE paketin alındığı satır
        değişecek (fake_data yerine serial_reader); gerisi aynı kalacak.
        """
        self.packet_counter += 1
        packet = fake_data.generate_packet(self.packet_counter)

        # --- Canlı sayısal kartlar ---
        self.card_apps.update_value(packet["appsPercent"])
        self.card_brake.update_value(packet["brakePressure"])
        self.card_torque.update_value(packet["torqueCommand"])
        self.card_voltage.update_value(packet["batteryVoltage"])
        # Placeholder kartlar (RPM, akım, SOC, sıcaklıklar) güncellenmez;
        # update_value çağrılsa bile kendileri "—" olarak kalır.

        # --- Bağlantı chip'i ---
        # Simülasyon her zaman "canlı" sayılır -> yeşil nokta.
        self.connection_chip.set_status(True)

        # --- Araç durumu ---
        state = fake_data.state_text(packet["vehicleState"])
        self.state_label.setText(f"ARAÇ DURUMU: {state}")

        # --- Arıza ---
        # README renk kuralı: faultCode != 0 ise KIRMIZI; normalde soluk
        # beyaz (sürekli yeşil yazı göz yorduğu için kullanılmıyor).
        if packet["faultCode"] == 0:
            self.fault_label.setText("ARIZA: YOK")
            self.fault_label.setStyleSheet(f"color: {theme.COLOR_TEXT_MUTED};")
        else:
            self.fault_label.setText(f"ARIZA: KOD {packet['faultCode']}")
            self.fault_label.setStyleSheet(
                f"color: {theme.COLOR_CRITICAL}; font-weight: bold;"
            )

        # --- Durum chip'leri ---
        # Chip adı -> paket alanı eşlemesini dolaşıp her chip'i güncelle.
        for name, field_name in self.chip_fields.items():
            self.chips[name].set_status(packet[field_name])

        # --- Alt şerit ---
        self.packet_label.setText(f"Paket: #{packet['seqNumber']}")
        self.loss_label.setText("Kayıp: %0.0")
        self.latency_label.setText(f"Gecikme: {packet['latencyMs']} ms")
        self.rssi_label.setText(f"RSSI: {packet['rssiDbm']} dBm")
