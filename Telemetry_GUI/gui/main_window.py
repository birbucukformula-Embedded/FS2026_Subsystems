# -*- coding: utf-8 -*-
"""
gui/main_window.py — ANA PENCERE (PIT TELEMETRİ EKRANI)
=======================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 3 (Arayüz - UI/UX & Canlı Grafik)
------------------------------------------------------------------
Pit alanındaki mühendislerin canlı araç durumunu izleyeceği, koyu temalı (dark mode)
ve 60 FPS akıcılıkla çalışan modern Formula Student yer istasyonu penceresidir.
"""

import time
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QFrame, QGridLayout, QGroupBox, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QColor

# Takım ortak çalışma dosyalarından içe aktarmalar
from core.serial_worker import SerialWorker, list_available_ports
from core.simulator import TelemetrySimulator
from core.parser import parse_text_line, ConnectionHealthTracker
from core.logger import TelemetryCSVLogger
from gui.plot_widget import RealtimePlotWidget
from gui.widgets.badges import StatusBadge, FaultCodeBadge
from gui.widgets.gauges import HalfCircleGauge


# === ANA EKRAN DARK MODE STİL ŞABLONU (QSS) ===
PIT_DARK_STYLESHEET = """
QMainWindow {
    background-color: #0D0E11;
}
QWidget {
    color: #E0E6ED;
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}
QGroupBox {
    background-color: #14161C;
    border: 1px solid #232731;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 16px;
    font-weight: bold;
    font-size: 11pt;
    color: #00E5FF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 6px;
    color: #00E5FF;
}
QFrame#CardFrame {
    background-color: #181A20;
    border: 1px solid #232731;
    border-radius: 10px;
}
QFrame#HeaderBar {
    background-color: #111318;
    border-bottom: 2px solid #1E222C;
}
QFrame#BottomBar {
    background-color: #111318;
    border-top: 1px solid #1E222C;
}
QComboBox {
    background-color: #1C202B;
    border: 1px solid #2C3242;
    border-radius: 6px;
    padding: 6px 12px;
    color: #FFFFFF;
    font-weight: bold;
    min-width: 130px;
}
QComboBox:hover {
    border-color: #00E5FF;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QPushButton {
    background-color: #1F2430;
    border: 1px solid #2C3242;
    border-radius: 6px;
    padding: 7px 16px;
    color: #FFFFFF;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #272E3D;
    border-color: #00E5FF;
}
QPushButton#ConnectButton {
    background-color: #0E2B1E;
    border: 1px solid #1B5E3C;
    color: #00E676;
}
QPushButton#ConnectButton:hover {
    background-color: #133D2A;
}
QPushButton#DisconnectButton {
    background-color: #381419;
    border: 1px solid #7F1D1D;
    color: #FF5252;
}
QPushButton#DisconnectButton:hover {
    background-color: #521C24;
}
QLabel#CardTitle {
    color: #8F9BBA;
    font-size: 9pt;
    font-weight: bold;
}
QLabel#CardValue {
    color: #FFFFFF;
    font-size: 18pt;
    font-weight: bold;
}
QLabel#CardUnit {
    color: #00E5FF;
    font-size: 10pt;
    font-weight: bold;
}
QLabel#PlaceholderValue {
    color: #4D566B;
    font-size: 16pt;
    font-weight: bold;
}
"""


class MainWindow(QMainWindow):
    """Pit takip ekranı ana pencere sınıfı."""

    def __init__(self, start_mode: str = "simulation", start_port: str = None):
        super().__init__()
        self.setWindowTitle("🏁 1.5 Adana Formula Student | FST-26 Yer İstasyonu (Pit Telemetry)")
        self.resize(1380, 880)
        self.setStyleSheet(PIT_DARK_STYLESHEET)

        self.start_mode = start_mode
        self.start_port = start_port

        # Asenkron İşçiler ve Takipçiler
        self.worker = None
        self.is_connected = False
        self.health_tracker = ConnectionHealthTracker()
        self.logger = TelemetryCSVLogger()

        self.init_ui()
        self.connect_signals()

        # Otomatik olarak portları tara
        self.refresh_ports()
        if self.start_mode == "simulation":
            self.mode_combo.setCurrentText("Simülasyon (10 Hz)")

    def init_ui(self):
        """Arayüz elemanlarının kurulması ve yerleşimi (Layout)."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. ÜST ŞERİT (Header Bar)
        main_layout.addWidget(self._build_header_bar())

        # 2. ORTA İÇERİK ALANI (3 Sütunlu Koyu Pit Duvarı Düzeni)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(14, 12, 14, 12)
        content_layout.setSpacing(14)

        # SOL SÜTUN: Araç Durumu, Arıza Kodu ve Sürücü Pedalları
        left_col = self._build_left_column()
        content_layout.addWidget(left_col, stretch=3)

        # ORTA SÜTUN: Canlı PyQtGraph Grafikleri
        center_col = self._build_center_column()
        content_layout.addWidget(center_col, stretch=5)

        # SAĞ SÜTUN: Batarya / Güç Kartları ve Güvenlik Devresi Rozetleri
        right_col = self._build_right_column()
        content_layout.addWidget(right_col, stretch=3)

        main_layout.addWidget(content_widget, stretch=1)

        # 3. ALT ŞERİT (Bottom Health Metrics Bar)
        main_layout.addWidget(self._build_bottom_bar())

    def _build_header_bar(self) -> QFrame:
        """Üst kontrol ve başlık şeridini oluşturur."""
        header_frame = QFrame()
        header_frame.setObjectName("HeaderBar")
        header_frame.setFixedHeight(64)
        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(18, 8, 18, 8)

        # Takım Başlığı
        lbl_title = QLabel("🏎️   1.5 ADANA FORMULA STUDENT  |  PIT TELEMETRİ YER İSTASYONU")
        lbl_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl_title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(lbl_title)

        layout.addStretch()

        # Kaynak Modu Seçimi
        lbl_mode = QLabel("Veri Kaynağı:")
        lbl_mode.setStyleSheet("color: #8F9BBA; font-weight: bold;")
        layout.addWidget(lbl_mode)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Simülasyon (10 Hz)", "COM Port (LoRa / USB)"])
        layout.addWidget(self.mode_combo)

        # Port Seçim Menüsü
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(160)
        layout.addWidget(self.port_combo)

        # Port Yenile Butonu
        self.btn_refresh = QPushButton("🔄 Yenile")
        layout.addWidget(self.btn_refresh)

        # Bağlan/Kes Butonu
        self.btn_connect = QPushButton("▶  BAĞLAN")
        self.btn_connect.setObjectName("ConnectButton")
        self.btn_connect.setMinimumWidth(130)
        layout.addWidget(self.btn_connect)

        # Bağlantı Durumu Rozeti
        self.lbl_status = QLabel("●  BAĞLANTISIZ")
        self.lbl_status.setStyleSheet(
            "background-color: #181A20; border: 1px solid #2D323E; border-radius: 12px; "
            "padding: 6px 14px; color: #8F9BBA; font-weight: bold;"
        )
        layout.addWidget(self.lbl_status)

        return header_frame

    def _build_left_column(self) -> QWidget:
        """Sol Sütun: Araç Durumu, Arıza Göstergesi ve Sürücü Pedalları."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # --- ARAÇ DURUMU KARTI ---
        state_group = QGroupBox("ARAÇ DURUMU (VEHICLE STATE)")
        state_layout = QVBoxLayout(state_group)
        self.lbl_vehicle_state = QLabel("STANDBY (BEKLEMEDE)")
        self.lbl_vehicle_state.setAlignment(Qt.AlignCenter)
        self.lbl_vehicle_state.setStyleSheet(
            "font-size: 15pt; font-weight: bold; color: #00E676; padding: 10px; "
            "background-color: #0E2B1E; border: 1px solid #1E5E3A; border-radius: 8px;"
        )
        state_layout.addWidget(self.lbl_vehicle_state)
        layout.addWidget(state_group)

        # --- ARIZA ROZETİ ---
        fault_group = QGroupBox("GÜVENLİK VE ARIZA KONTROLÜ")
        fault_layout = QVBoxLayout(fault_group)
        self.fault_badge = FaultCodeBadge()
        fault_layout.addWidget(self.fault_badge)
        layout.addWidget(fault_group)

        # --- SÜRÜCÜ PEDAL GÖSTERGELERİ ---
        pedal_group = QGroupBox("SÜRÜCÜ KOMUTLARI (GAZ & FREN)")
        pedal_layout = QHBoxLayout(pedal_group)
        pedal_layout.setSpacing(10)

        self.apps_gauge = HalfCircleGauge(title="GAZ PEDALI (APPS)", unit="%", min_val=0, max_val=100)
        self.brake_gauge = HalfCircleGauge(title="FREN BASINCI", unit="bar", min_val=0, max_val=100)

        pedal_layout.addWidget(self.apps_gauge)
        pedal_layout.addWidget(self.brake_gauge)
        layout.addWidget(pedal_group, stretch=1)

        return widget

    def _build_center_column(self) -> QWidget:
        """Orta Sütun: Gerçek Zamanlı PyQtGraph Çizgi Grafikleri."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Grafik 1: Gaz Pedalı (%) - APPS
        self.plot_apps = RealtimePlotWidget(title="GAZ PEDALI POZİSYONU (APPS)", unit="%", max_points=200)
        layout.addWidget(self.plot_apps, stretch=1)

        # Grafik 2: Batarya Gerilimi (V)
        self.plot_voltage = RealtimePlotWidget(title="BATARYA GERİLİMİ", unit="V", max_points=200)
        layout.addWidget(self.plot_voltage, stretch=1)

        return widget

    def _build_right_column(self) -> QWidget:
        """Sağ Sütun: Batarya / Güç Kartları ve Sistem Bayrakları."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # --- CANLI SENKRON GÜÇ VERİLERİ (Bölüm 1) ---
        power_group = QGroupBox("CANLI GÜÇ TELEMETRİSİ")
        power_layout = QGridLayout(power_group)
        power_layout.setSpacing(10)

        self.card_voltage = self._create_metric_card("BATARYA GERİLİMİ", "396.0", "V", is_placeholder=False)
        self.card_torque = self._create_metric_card("TORK KOMUTU", "0.0", "Nm", is_placeholder=False)

        power_layout.addWidget(self.card_voltage, 0, 0)
        power_layout.addWidget(self.card_torque, 0, 1)
        layout.addWidget(power_group)

        # --- CAN BEKLENEN PLACEHOLDER KARTLAR (README Bölüm 2: "—" Görüntüsü) ---
        can_group = QGroupBox("BATARYA & SICAKLIKLAR (CAN BEKLENİYOR)")
        can_layout = QGridLayout(can_group)
        can_layout.setSpacing(10)

        self.card_current = self._create_metric_card("BATARYA AKIMI", "—", "A", is_placeholder=True)
        self.card_soc = self._create_metric_card("BATARYA SOC", "—", "%", is_placeholder=True)
        self.card_motor_temp = self._create_metric_card("MOTOR SICAKLIĞI", "—", "°C", is_placeholder=True)
        self.card_inv_temp = self._create_metric_card("İNVERTER SICAK.", "—", "°C", is_placeholder=True)
        self.card_cell_temp = self._create_metric_card("MAX HÜCRE SICAK.", "—", "°C", is_placeholder=True)

        can_layout.addWidget(self.card_current, 0, 0)
        can_layout.addWidget(self.card_soc, 0, 1)
        can_layout.addWidget(self.card_motor_temp, 1, 0)
        can_layout.addWidget(self.card_inv_temp, 1, 1)
        can_layout.addWidget(self.card_cell_temp, 2, 0, 1, 2)
        layout.addWidget(can_group)

        # --- SİSTEM DURUM ROZETLERİ (README Bölüm 1 & 5) ---
        flags_group = QGroupBox("SİSTEM KONTAKTÖR & GÜVENLİK BAYRAKLARI")
        flags_layout = QVBoxLayout(flags_group)
        flags_layout.setSpacing(8)

        self.badge_air_minus = StatusBadge("AIR- (NEGATİF KONTAKTÖR)")
        self.badge_air_plus = StatusBadge("AIR+ (POZİTİF KONTAKTÖR)")
        self.badge_precharge = StatusBadge("PRECHARGE DEVRESİ")
        self.badge_sdc = StatusBadge("SDC (SHUTDOWN DEVRESİ)")
        self.badge_inverter = StatusBadge("INVERTER ENABLE")

        flags_layout.addWidget(self.badge_air_minus)
        flags_layout.addWidget(self.badge_air_plus)
        flags_layout.addWidget(self.badge_precharge)
        flags_layout.addWidget(self.badge_sdc)
        flags_layout.addWidget(self.badge_inverter)
        layout.addWidget(flags_group, stretch=1)

        return widget

    def _create_metric_card(self, title: str, initial_val: str, unit: str, is_placeholder: bool = False) -> QFrame:
        """Tekil sayısal değer kartı (Metric Card) oluşturur."""
        frame = QFrame()
        frame.setObjectName("CardFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("CardTitle")
        layout.addWidget(lbl_title)

        val_layout = QHBoxLayout()
        lbl_value = QLabel(initial_val)
        lbl_value.setObjectName("PlaceholderValue" if is_placeholder else "CardValue")

        lbl_unit = QLabel(unit)
        lbl_unit.setObjectName("CardUnit")

        val_layout.addWidget(lbl_value)
        val_layout.addWidget(lbl_unit, 0, Qt.AlignBottom)
        val_layout.addStretch()
        layout.addLayout(val_layout)

        # Referansı sonradan güncelleyebilmek için nitelik ata
        frame.lbl_value = lbl_value
        return frame

    def _build_bottom_bar(self) -> QFrame:
        """Alt durum ve sağlık metrikleri şeridi (Health Metrics Bar)."""
        frame = QFrame()
        frame.setObjectName("BottomBar")
        frame.setFixedHeight(36)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 4, 18, 4)

        self.lbl_loss = QLabel("Kayıp Oranı:  % 0.00")
        self.lbl_loss.setStyleSheet("color: #8F9BBA; font-weight: bold;")
        layout.addWidget(self.lbl_loss)

        self.lbl_latency = QLabel("Gecikme (Latency):  0 ms")
        self.lbl_latency.setStyleSheet("color: #8F9BBA; font-weight: bold;")
        layout.addWidget(self.lbl_latency)

        self.lbl_rssi = QLabel("📡 RSSI:  -65 dBm")
        self.lbl_rssi.setStyleSheet("color: #00E676; font-weight: bold;")
        layout.addWidget(self.lbl_rssi)

        layout.addStretch()

        self.lbl_seq = QLabel("Paket Sıra No:  0")
        self.lbl_seq.setStyleSheet("color: #6E7A8A;")
        layout.addWidget(self.lbl_seq)

        return frame

    def connect_signals(self):
        """Buton tıklamaları ve UI olaylarını fonksiyonlara bağlar."""
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_connect.clicked.connect(self.toggle_connection)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)

    def on_mode_changed(self):
        """Veri kaynağı değiştiğinde arayüzü ayarlar."""
        mode_text = self.mode_combo.currentText()
        if "Simülasyon" in mode_text:
            self.port_combo.setEnabled(False)
        else:
            self.port_combo.setEnabled(True)
            self.refresh_ports()

    def refresh_ports(self):
        """Mevcut COM portlarını tarayıp listeye ekler."""
        self.port_combo.clear()
        ports = list_available_ports()
        if ports:
            for device, desc in ports:
                self.port_combo.addItem(f"{device} ({desc})", device)
        else:
            self.port_combo.addItem("Port Bulunamadı", "")

    def toggle_connection(self):
        """Bağlantıyı başlatır veya sonlandırır."""
        if not self.is_connected:
            self.start_telemetry()
        else:
            self.stop_telemetry()

    def start_telemetry(self):
        """Seçilen moda göre QThread işçisini başlatır."""
        mode_text = self.mode_combo.currentText()

        # Yeni log dosyasını aç
        self.logger.open()

        if "Simülasyon" in mode_text:
            self.worker = TelemetrySimulator(interval_ms=100)
        else:
            port_device = self.port_combo.currentData()
            if not port_device:
                self.set_status_ui(False, "HATA: COM PORT SEÇİLMEDİ")
                return
            self.worker = SerialWorker(port_name=port_device, baudrate=115200)

        # Worker sinyallerini bağla
        self.worker.raw_line_received.connect(self.on_raw_line_received)
        self.worker.connection_status.connect(self.on_connection_status)
        self.worker.error_occurred.connect(self.on_error_occurred)

        self.worker.start()
        self.is_connected = True

        self.btn_connect.setText("■  BAĞLANTIYI KES")
        self.btn_connect.setObjectName("DisconnectButton")
        self.btn_connect.style().unpolish(self.btn_connect)
        self.btn_connect.style().polish(self.btn_connect)

    def stop_telemetry(self):
        """Aktif iletişimi durdurur ve iş parçacıklarını sonlandırır."""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None

        self.logger.close()
        self.is_connected = False

        self.btn_connect.setText("▶  BAĞLAN")
        self.btn_connect.setObjectName("ConnectButton")
        self.btn_connect.style().unpolish(self.btn_connect)
        self.btn_connect.style().polish(self.btn_connect)

        self.set_status_ui(None, "BAĞLANTISIZ")

    def on_connection_status(self, connected: bool, message: str):
        """Bağlantı durumu değiştiğinde rozet metnini günceller."""
        self.set_status_ui(connected, message.upper())

    def on_error_occurred(self, err_msg: str):
        """Bağlantı hatası durumunda rozeti uyarı moduna sokar."""
        self.set_status_ui(False, f"HATA: {err_msg[:24]}")

    def set_status_ui(self, status, text: str):
        """Üst şeritteki bağlantı durumu rozetini ve rengini günceller."""
        if status is True:
            self.lbl_status.setText(f"●  {text}")
            self.lbl_status.setStyleSheet(
                "background-color: #0E2B1E; border: 1px solid #1B5E3C; border-radius: 12px; "
                "padding: 6px 14px; color: #00E676; font-weight: bold;"
            )
        elif status is False:
            self.lbl_status.setText(f"●  {text}")
            self.lbl_status.setStyleSheet(
                "background-color: #381419; border: 1px solid #7F1D1D; border-radius: 12px; "
                "padding: 6px 14px; color: #FF5252; font-weight: bold;"
            )
        else:
            self.lbl_status.setText(f"●  {text}")
            self.lbl_status.setStyleSheet(
                "background-color: #181A20; border: 1px solid #2D323E; border-radius: 12px; "
                "padding: 6px 14px; color: #8F9BBA; font-weight: bold;"
            )

    def on_raw_line_received(self, line: str):
        """
        Arka plan iş parçacığından (QThread) gelen ham verinin işlendiği slot.
        """
        # 1. Mühendis 2'nin ayrıştırıcısı ile satırı çöz
        packet = parse_text_line(line)
        if not packet:
            return

        # 2. Bağlantı sağlığı metriklerini (kayıp %, latency ms) hesapla
        packet = self.health_tracker.process_health_metrics(packet)

        # 3. CSV dosyasına logla
        self.logger.log_packet(packet)

        # 4. Pit Arayüzünü ve Grafikleri güncelle
        self.update_ui(packet)

    def update_ui(self, packet: dict):
        """Grafikleri, kartları, iğneli göstergeleri ve rozetleri anlık günceller."""
        # 1. ARAÇ DURUMU (vehicleState)
        v_state = str(packet.get("vehicleState", "READY_TO_DRIVE"))
        self.lbl_vehicle_state.setText(v_state)

        # 2. ARIZA KODU (faultCode)
        try:
            f_code = int(packet.get("faultCode", 0))
        except (ValueError, TypeError):
            f_code = 0
        self.fault_badge.set_fault_code(f_code)

        # 3. PEDAL GÖSTERGELERİ (appsPercent, brakePressure)
        apps = packet.get("appsPercent", 0.0)
        brake = packet.get("brakePressure", 0.0)
        self.apps_gauge.set_value(apps)
        self.brake_gauge.set_value(brake)

        # 4. CANLI GÜÇ VERİLERİ
        voltage = packet.get("batteryVoltage", 0.0)
        torque = packet.get("torqueCommand", 0.0)
        self.card_voltage.lbl_value.setText(f"{float(voltage):.1f}")
        self.card_torque.lbl_value.setText(f"{float(torque):.1f}")

        # 5. CAN BEKLENEN ALANLAR (README Bölüm 2 - Gerçek veriler gelirse göster, yoksa "—" kalır)
        for key, card in [
            ("batteryCurrent", self.card_current),
            ("batterySOC", self.card_soc),
            ("motorTemp", self.card_motor_temp),
            ("inverterTemp", self.card_inv_temp),
            ("maxCellTemp", self.card_cell_temp),
        ]:
            val = packet.get(key)
            if val is not None and float(val) > 0:
                card.lbl_value.setText(f"{float(val):.1f}")
                card.lbl_value.setStyleSheet("color: #FFFFFF; font-size: 18pt; font-weight: bold;")
            else:
                card.lbl_value.setText("—")
                card.lbl_value.setStyleSheet("color: #4D566B; font-size: 16pt; font-weight: bold;")

        # 6. KONTAKTÖR & GÜVENLİK BAYRAKLARI (systemFlags ya da ayrı boolean alanlar)
        flags = packet.get("systemFlags", {})
        self.badge_air_minus.set_status(flags.get("AIR-", True))
        self.badge_air_plus.set_status(flags.get("AIR+", True))
        self.badge_precharge.set_status(flags.get("Precharge", True))
        self.badge_sdc.set_status(flags.get("SDC Closed", True))
        self.badge_inverter.set_status(flags.get("Inverter Enable", True))

        # 7. GRAFİKLERİ GÜNCELLE
        self.plot_apps.add_new_data(apps)
        self.plot_voltage.add_new_data(voltage)

        # 8. ALT ŞERİT METRİKLERİ
        loss = packet.get("lossPercent", 0.0)
        latency = packet.get("latencyMs", 0)
        rssi = packet.get("rssiDbm", -65)
        seq = packet.get("seqNumber", 0)

        self.lbl_loss.setText(f"Kayıp Oranı:  % {float(loss):.2f}")
        self.lbl_latency.setText(f"Gecikme (Latency):  {int(latency)} ms")
        self.lbl_rssi.setText(f"📡 RSSI:  {int(rssi)} dBm")
        self.lbl_seq.setText(f"Paket Sıra No:  {seq}")

    def closeEvent(self, event):
        """Pencere kapatılırken logları ve çalışan thread'leri güvenle kapatır."""
        self.stop_telemetry()
        super().closeEvent(event)
