# -*- coding: utf-8 -*-
"""
gui/main_window.py — ANA PENCERE
=================================

Bütün bölümleri birleştiren ana pencere. Yerleşim:

    ┌────────────────────────────────────────────────────────────┐
    │ LOGO  PIT TELEMETRİ      [port ▼][↻][Bağlan/Kes] [● durum] │  üst şerit
    │ Paket:#   Kayıp:%   Gecikme:ms   RSSI:dBm                   │  bağlantı bilgisi
    │ ARAÇ DURUMU: READY                       ARIZA: YOK         │
    ├────────────────────────────────────────────────────────────┤
    │ ▍ANA GRAFİK   [x]Gaz [x]Fren [x]Tork                       │
    │ (gaz/fren/tork tek grafikte, kutucuklarla aç/kapa)          │
    ├────────────────────────────────────────────────────────────┤
    │ ▍SÜRÜŞ      [GAZ][FREN][TORK][RPM]        (tıklanabilir)    │
    │ ▍BATARYA    [GERİLİM][AKIM][SOC][MAX HÜCRE]                 │
    │ ▍SICAKLIK   [MOTOR][İNVERTER]                               │
    │ ▍DETAY — <seçili kart>   (bir karta tıklayınca açılır)      │  accordion
    ├────────────────────────────────────────────────────────────┤
    │ ▍SİSTEM    [●AIR-][●AIR+][●PRECHARGE][●SDC][●INV EN]        │
    └────────────────────────────────────────────────────────────┘

Değer kartları TIKLANABİLİR: bir karta basınca o verinin büyük grafiği
"DETAY" panelinde açılır; başka bir karta basınca panel ona geçer, aynı
karta tekrar basınca kapanır (accordion mantığı).

Bu dosya SADECE görsel dizilim ve güncelleme ile ilgilenir; veri üretimi
core katmanındadır. Küçük parçalar gui/widgets.py içindedir.
"""

import os   # logo dosyasının tam yolunu bulmak için

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QComboBox, QPushButton,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap

# Kendi modüllerimiz: theme (renkler), widgets (parçalar), veri kaynakları.
from gui import theme
from gui.widgets import (
    ValueCard, StatusChip, SectionTitle, LiveChart, MultiSeriesChart,
)
from core import fake_data
from core import serial_reader

# Logo dosyasının yolu (bu dosyadan bir üst klasördeki assets/logo.png).
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")


class MainWindow(QMainWindow):
    """Uygulamanın ana penceresi: bölümleri kurar ve periyodik günceller."""

    def __init__(self, start_mode: str = "simulation", start_port: str = None):
        """
        start_mode: "serial" -> start_port'a bağlanmayı dener,
                    "simulation" -> sahte veriyle başlar.
        Bu bilgi açılış ekranından (StartupDialog) gelir.
        """
        super().__init__()

        # --- Pencere temel ayarları ---
        self.setWindowTitle("FS2026 — 1.5 Adana Formula Student | Pit Telemetri")
        self.resize(1100, 1000)
        self.setStyleSheet(theme.STYLE_WINDOW)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(9)

        # Tıklanabilir kartlar burada key -> ValueCard olarak toplanır;
        # detay panelinde hangi kartın grafiği açık olduğunu da takip ediyoruz.
        # Bölüm kurulumları bunları kullandığı için ÖNCE tanımlıyoruz.
        self.cards = {}
        self.active_detail_key = None

        # Bölümleri sırayla kur.
        main_layout.addLayout(self._build_top_bar())
        main_layout.addLayout(self._build_connection_info_row())
        main_layout.addLayout(self._build_vehicle_status_row())
        main_layout.addWidget(SectionTitle("Ana Grafik"))
        main_layout.addWidget(self._build_main_chart(), stretch=1)
        main_layout.addWidget(SectionTitle("Sürüş"))
        main_layout.addLayout(self._build_drive_cards())
        main_layout.addWidget(SectionTitle("Batarya (HV)"))
        main_layout.addLayout(self._build_battery_cards())
        main_layout.addWidget(SectionTitle("Sıcaklıklar"))
        main_layout.addLayout(self._build_temperature_cards())
        main_layout.addWidget(self._build_detail_panel())
        main_layout.addWidget(SectionTitle("Sistem"))
        main_layout.addLayout(self._build_status_chips())

        # --- VERİ ZAMANLAYICISI (10 Hz) ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(100)

        # --- VERİ KAYNAĞI ---
        self.data_source = None

        # Açılış ekranından gelen karara göre başla.
        self._refresh_ports()
        if start_mode == "serial" and start_port and self._connect(start_port):
            pass   # seri porta başarıyla bağlandı
        else:
            self._use_simulation()   # simülasyon ya da bağlanamadıysa yedek

    # ==================================================================
    # BÖLÜM KURULUMLARI
    # ==================================================================

    def _build_top_bar(self):
        """Üst şerit: logo + başlık + port kontrolleri + bağlantı chip'i."""
        bar = QHBoxLayout()

        logo_label = QLabel()
        logo_pixmap = QPixmap(LOGO_PATH)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaledToHeight(36, Qt.SmoothTransformation))

        title = QLabel("PIT TELEMETRİ")
        title.setFont(QFont("Arial", 17, QFont.Bold))
        title.setStyleSheet(f"color: {theme.COLOR_TEXT}; letter-spacing: 3px;")

        # Port seçimi + Yenile + Bağlan/Kes.
        self.port_combo = QComboBox()
        self.port_combo.setStyleSheet(theme.STYLE_COMBOBOX)
        self.port_combo.setMinimumWidth(200)

        self.refresh_button = QPushButton("↻")
        self.refresh_button.setStyleSheet(theme.STYLE_BUTTON)
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self._refresh_ports)

        self.connect_button = QPushButton("Bağlan")
        self.connect_button.setStyleSheet(theme.STYLE_BUTTON)
        self.connect_button.setCursor(Qt.PointingHandCursor)
        self.connect_button.clicked.connect(self._toggle_connection)

        # Bağlantı durumu chip'i: yeşil=bağlı, gri=simülasyon, kırmızı=hata.
        self.connection_chip = StatusChip("SİMÜLASYON")

        bar.addWidget(logo_label)
        bar.addSpacing(10)
        bar.addWidget(title)
        bar.addStretch()
        bar.addWidget(self.port_combo)
        bar.addSpacing(6)
        bar.addWidget(self.refresh_button)
        bar.addSpacing(6)
        bar.addWidget(self.connect_button)
        bar.addSpacing(10)
        bar.addWidget(self.connection_chip)
        return bar

    def _build_connection_info_row(self):
        """Bağlantı sağlığı metrikleri (paket, kayıp, gecikme, RSSI) — ÜSTTE."""
        row = QHBoxLayout()

        self.packet_label  = QLabel("Paket: —")
        self.loss_label    = QLabel("Kayıp: —%")
        self.latency_label = QLabel("Gecikme: — ms")
        self.rssi_label    = QLabel("RSSI: — dBm")

        for label in (self.packet_label, self.loss_label,
                      self.latency_label, self.rssi_label):
            label.setStyleSheet(f"color: {theme.COLOR_INACTIVE}; font-size: 11px;")
            row.addWidget(label)
            row.addSpacing(20)

        row.addStretch()
        return row

    def _build_vehicle_status_row(self):
        """Araç durumu (vehicleState) ve arıza (faultCode) satırı."""
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

    def _build_main_chart(self):
        """
        Ana çoklu-seri grafik: gaz/fren/tork tek grafikte, üstte kutucuklarla
        aç/kapa. İleride başka seriler de series_defs'e eklenebilir.
        """
        # (key, etiket, renk) — renkler temadan, birbirinden ayrışsın diye farklı.
        series_defs = [
            ("appsPercent",   "Gaz %",   theme.COLOR_SERIES_1),
            ("brakePressure", "Fren bar", theme.COLOR_SERIES_2),
            ("torqueCommand", "Tork Nm", theme.COLOR_SERIES_3),
        ]
        self.main_chart = MultiSeriesChart(series_defs)
        self.main_chart.setMinimumHeight(200)
        return self.main_chart

    def _build_drive_cards(self):
        """SÜRÜŞ bölümü kartları (hepsi tıklanabilir -> detay grafiği açar)."""
        grid = QGridLayout()
        grid.setSpacing(10)
        cards = [
            ValueCard("appsPercent",   "GAZ PEDALI",   "%"),
            ValueCard("brakePressure", "FREN BASINCI", "bar"),
            ValueCard("torqueCommand", "TORK KOMUTU",  "Nm"),
            ValueCard("motorRPM",      "MOTOR DEVRİ",  "RPM"),
        ]
        for column, card in enumerate(cards):
            grid.addWidget(card, 0, column)
            self._register_card(card)
        return grid

    def _build_battery_cards(self):
        """BATARYA bölümü kartları."""
        grid = QGridLayout()
        grid.setSpacing(10)
        cards = [
            ValueCard("batteryVoltage", "GERİLİM",            "V"),
            ValueCard("batteryCurrent", "AKIM",               "A"),
            ValueCard("batterySOC",     "ŞARJ DURUMU (SOC)",  "%"),
            ValueCard("maxCellTemp",    "MAX HÜCRE SICAKLIĞI", "°C"),
        ]
        for column, card in enumerate(cards):
            grid.addWidget(card, 0, column)
            self._register_card(card)
        return grid

    def _build_temperature_cards(self):
        """SICAKLIKLAR bölümü kartları."""
        grid = QGridLayout()
        grid.setSpacing(10)
        cards = [
            ValueCard("motorTemp",    "MOTOR",    "°C"),
            ValueCard("inverterTemp", "İNVERTER", "°C"),
        ]
        for column, card in enumerate(cards):
            grid.addWidget(card, 0, column)
            self._register_card(card)
        # 4 sütunluk hizayı korumak için kalan sütunları da esnet.
        for column in range(4):
            grid.setColumnStretch(column, 1)
        return grid

    def _register_card(self, card: ValueCard):
        """Bir kartı sözlüğe kaydeder ve tıklama sinyalini detay paneline bağlar."""
        self.cards[card.key] = card
        card.clicked.connect(self._toggle_detail)

    def _build_detail_panel(self):
        """
        DETAY paneli (accordion): bir karta tıklanınca o verinin büyük grafiği
        burada açılır. Başlangıçta gizlidir.
        """
        self.detail_container = QWidget()
        layout = QVBoxLayout(self.detail_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Başlık (SectionTitle stiliyle ama metni değişebilsin diye düz QLabel).
        self.detail_title = QLabel("DETAY")
        self.detail_title.setStyleSheet(theme.STYLE_SECTION_TITLE)

        # Tek bir LiveChart; her açılışta reconfigure ile farklı veriye ayarlanır.
        self.detail_chart = LiveChart("—", "", max_points=150)
        self.detail_chart.setMinimumHeight(180)

        layout.addWidget(self.detail_title)
        layout.addWidget(self.detail_chart)

        self.detail_container.setVisible(False)   # kapalı başlar
        return self.detail_container

    def _build_status_chips(self):
        """AIR-, AIR+, PRECHARGE, SDC, INV EN durum chip'leri."""
        row = QHBoxLayout()
        row.setSpacing(8)
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
        row.addStretch()
        return row

    # ==================================================================
    # DETAY PANELİ (ACCORDION) MANTIĞI
    # ==================================================================

    def _toggle_detail(self, key: str):
        """
        Bir karta tıklanınca çağrılır (ValueCard.clicked sinyali).
        - Aynı kart yeniden tıklandıysa paneli kapatır.
        - Farklı bir kartsa paneli o veriye ayarlayıp açar.
        """
        if self.active_detail_key == key:
            self._close_detail()
            return

        # Önceki seçili kartın kırmızı kenarlığını kaldır.
        if self.active_detail_key is not None:
            self.cards[self.active_detail_key].set_selected(False)

        # Yeni kartı seç ve detay grafiğini o veriye göre sıfırla.
        card = self.cards[key]
        self.active_detail_key = key
        card.set_selected(True)
        self.detail_title.setText(f"DETAY — {card.title}")
        self.detail_chart.reconfigure(card.title, card.unit, theme.COLOR_ACCENT)
        self.detail_container.setVisible(True)

    def _close_detail(self):
        """Detay panelini kapatır ve seçili kart vurgusunu kaldırır."""
        if self.active_detail_key is not None:
            self.cards[self.active_detail_key].set_selected(False)
        self.active_detail_key = None
        self.detail_container.setVisible(False)

    # ==================================================================
    # SERİ PORT BAĞLANTI YÖNETİMİ
    # ==================================================================

    def _refresh_ports(self):
        """Bağlı seri portları tarayıp port seçim kutusunu doldurur."""
        self.port_combo.clear()
        for device, description in serial_reader.list_serial_ports():
            self.port_combo.addItem(f"{device} — {description}", device)
        if self.port_combo.count() == 0:
            self.port_combo.addItem("(port bulunamadı)", None)

    def _connect(self, port: str) -> bool:
        """Verilen porta bağlanmayı dener; başarılıysa True döner."""
        try:
            self.data_source = serial_reader.SerialReader(port)
        except Exception:
            self._set_connection_status(f"HATA: {port}", state=False)
            return False
        self._set_connection_status(f"BAĞLI: {port}", state=True)
        self.connect_button.setText("Kes")
        self._select_port_in_combo(port)
        return True

    def _disconnect(self):
        """Açık seri portu kapatır ve simülasyon moduna döner."""
        if isinstance(self.data_source, serial_reader.SerialReader):
            self.data_source.close()
        self._use_simulation()

    def _use_simulation(self):
        """Veri kaynağını sahte veriye çevirir (bağlantı yokken arayüz boş durmasın)."""
        self.data_source = fake_data.FakeDataSource()
        self._set_connection_status("SİMÜLASYON", state=None)
        self.connect_button.setText("Bağlan")

    def _toggle_connection(self):
        """Bağlan/Kes butonu: duruma göre bağlan ya da kes."""
        if isinstance(self.data_source, serial_reader.SerialReader):
            self._disconnect()
        else:
            port = self.port_combo.currentData()
            if port:
                self._connect(port)

    def _select_port_in_combo(self, port: str):
        """Seçim kutusunda verilen portu seçili hale getirir (varsa)."""
        index = self.port_combo.findData(port)
        if index >= 0:
            self.port_combo.setCurrentIndex(index)

    def _set_connection_status(self, text: str, state):
        """Bağlantı chip'ini günceller (True=yeşil, None=gri, False=kırmızı)."""
        self.connection_chip.name = text
        self.connection_chip.set_status(state)

    # ==================================================================
    # PERİYODİK GÜNCELLEME
    # ==================================================================

    def update_data(self):
        """
        QTimer tarafından saniyede 10 kez çağrılır. Veri kaynağından paketi
        alıp tüm ekranı günceller. Alanlara packet.get(...) ile erişiyoruz;
        eksik alan gelirse ilgili widget mevcut halini korur.
        """
        packet = self.data_source.next_packet()
        if packet is None:
            return   # (seri portta) henüz tam veri yok, bu turu atla

        # --- Ana grafik (çoklu seri) ---
        self.main_chart.add_points(packet)

        # --- Değer kartları ---
        for key, card in self.cards.items():
            card.update_value(packet.get(key))

        # --- Detay grafiği (bir kart seçiliyse) ---
        if self.active_detail_key is not None:
            self.detail_chart.add_point(packet.get(self.active_detail_key))

        # --- Araç durumu ---
        if packet.get("vehicleState") is not None:
            state = fake_data.state_text(packet["vehicleState"])
            self.state_label.setText(f"ARAÇ DURUMU: {state}")

        # --- Arıza ---
        fault = packet.get("faultCode")
        if fault is not None:
            if fault == 0:
                self.fault_label.setText("ARIZA: YOK")
                self.fault_label.setStyleSheet(f"color: {theme.COLOR_TEXT_MUTED};")
            else:
                self.fault_label.setText(f"ARIZA: KOD {fault}")
                self.fault_label.setStyleSheet(
                    f"color: {theme.COLOR_CRITICAL}; font-weight: bold;"
                )

        # --- Durum chip'leri ---
        for name, field_name in self.chip_fields.items():
            self.chips[name].set_status(packet.get(field_name))

        # --- Bağlantı bilgisi (üst satır) ---
        if packet.get("seqNumber") is not None:
            self.packet_label.setText(f"Paket: #{packet['seqNumber']}")
        if packet.get("lossPercent") is not None:
            self.loss_label.setText(f"Kayıp: %{packet['lossPercent']:.1f}")
        if packet.get("latencyMs") is not None:
            self.latency_label.setText(f"Gecikme: {packet['latencyMs']} ms")
        if packet.get("rssiDbm") is not None:
            self.rssi_label.setText(f"RSSI: {packet['rssiDbm']} dBm")

    # ==================================================================
    # PENCERE KAPANIŞI
    # ==================================================================

    def closeEvent(self, event):
        """Pencere kapanırken açık seri portu düzgünce kapatır."""
        if isinstance(self.data_source, serial_reader.SerialReader):
            self.data_source.close()
        super().closeEvent(event)
