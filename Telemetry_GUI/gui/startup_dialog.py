# -*- coding: utf-8 -*-
"""
gui/startup_dialog.py — AÇILIŞ / PORT SEÇİM EKRANI
===================================================

Program açılınca ANA EKRANDAN ÖNCE görünen küçük karşılama penceresi.
Görevi, telemetriye hangi kaynaktan başlanacağını belirlemek:

  1. Açılır açılmaz seri portları taramaya başlar (her saniye tekrar tarar).
  2. Raspberry Pi / USB-UART adayı bir port bulursa: "bulundu, bağlanılıyor"
     mesajını gösterip OTOMATİK olarak o portla ana ekrana geçer.
  3. Bulamazsa: kullanıcı açılır listeden (dropdown) bir port seçip
     "Bağlan"a basabilir VEYA "Simülasyona Geç" ile sahte veriyle başlayabilir.
     Bu sırada tarama arka planda sürer; Pi sonradan takılırsa yakalanır.

Bu pencere GERÇEK bağlantıyı kendisi kurmaz; sadece "hangi port" veya
"simülasyon" kararını verir. Kararı `result_mode` ve `selected_port`
alanlarında saklar, ana pencere bunu okuyup bağlantıyı kurar.
"""

import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

from gui import theme
from core import serial_reader

# Logo yolu (bu dosyadan bir üst klasördeki assets/logo.png).
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")

# Portların ne sıklıkla yeniden taranacağı (milisaniye).
SCAN_INTERVAL_MS = 1000

# Pi bulununca "bağlanılıyor" mesajının kaç ms gösterilip otomatik geçileceği.
AUTO_CONNECT_DELAY_MS = 1500


class StartupDialog(QDialog):
    """Açılış/port seçim penceresi. Kapanınca kararı alanlarında tutar."""

    def __init__(self):
        super().__init__()

        # --- Sonuç alanları (ana pencere bunları okuyacak) ---
        # result_mode: "serial" -> selected_port'a bağlan, "simulation" -> sahte veri.
        self.result_mode = "simulation"
        self.selected_port = None

        # Pi bulunup otomatik bağlanma başlatıldıysa tekrar tetiklenmesin diye bayrak.
        self._auto_connecting = False

        # --- Pencere görünümü ---
        self.setWindowTitle("Pit Telemetri — Başlangıç")
        self.setFixedSize(460, 440)
        self.setStyleSheet(theme.STYLE_WINDOW)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignTop)

        # --- Logo (ortada) ---
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_pixmap = QPixmap(LOGO_PATH)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaledToHeight(90, Qt.SmoothTransformation))
        layout.addWidget(logo_label)

        # --- Başlık ---
        title = QLabel("PIT TELEMETRİ")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet(f"color: {theme.COLOR_TEXT}; letter-spacing: 4px;")
        layout.addWidget(title)

        # --- Durum metni (taranıyor / bulundu / ...) ---
        self.status_label = QLabel("Cihaz aranıyor…")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: {theme.COLOR_TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(self.status_label)

        layout.addSpacing(6)

        # --- Port seçim kutusu ---
        self.port_combo = QComboBox()
        self.port_combo.setStyleSheet(theme.STYLE_COMBOBOX)
        layout.addWidget(self.port_combo)

        # --- "Seçili Porta Bağlan" butonu (birincil) ---
        self.connect_button = QPushButton("Seçili Porta Bağlan")
        self.connect_button.setStyleSheet(theme.STYLE_BUTTON)
        self.connect_button.setCursor(Qt.PointingHandCursor)
        self.connect_button.clicked.connect(self._connect_selected)
        layout.addWidget(self.connect_button)

        # --- "Simülasyona Geç" butonu (ikincil) ---
        self.sim_button = QPushButton("Simülasyona Geç")
        self.sim_button.setStyleSheet(theme.STYLE_BUTTON_SECONDARY)
        self.sim_button.setCursor(Qt.PointingHandCursor)
        self.sim_button.clicked.connect(self._use_simulation)
        layout.addWidget(self.sim_button)

        # --- Sürekli tarama zamanlayıcısı ---
        # Hemen bir kez tara, sonra her SCAN_INTERVAL_MS'de tekrar.
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self._scan)
        self.scan_timer.start(SCAN_INTERVAL_MS)
        self._scan()   # açılışta beklemeden ilk taramayı yap

    def _scan(self):
        """Portları tarar; listeyi günceller ve Pi bulursa otomatik bağlanır."""
        if self._auto_connecting:
            return   # zaten otomatik bağlanma başladı, taramayı boşver

        # Açılır listeyi güncel portlarla doldur (seçili portu korumaya çalış).
        previous = self.port_combo.currentData()
        self.port_combo.clear()
        ports = serial_reader.list_serial_ports()
        for device, description in ports:
            self.port_combo.addItem(f"{device} — {description}", device)
        if not ports:
            self.port_combo.addItem("(port bulunamadı)", None)
        else:
            # Önceden seçili port hâlâ varsa onu tekrar seç.
            index = self.port_combo.findData(previous)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)

        # Raspberry Pi / USB-UART adayı var mı?
        vehicle_port = serial_reader.find_vehicle_port()
        if vehicle_port:
            self._start_auto_connect(vehicle_port)
        else:
            self.status_label.setText(
                "Cihaz aranıyor…  Bir port seçebilir veya simülasyona geçebilirsiniz."
            )

    def _start_auto_connect(self, port: str):
        """Pi bulununca: mesaj göster, taramayı durdur, kısa süre sonra bağlan."""
        self._auto_connecting = True
        self.scan_timer.stop()
        self.status_label.setText(f"Raspberry Pi bulundu: {port}\nBağlanılıyor…")
        self.status_label.setStyleSheet(
            f"color: {theme.COLOR_OK}; font-size: 13px; font-weight: bold;"
        )
        # Kullanıcı mesajı görsün diye kısa gecikmeyle ana ekrana geç.
        QTimer.singleShot(
            AUTO_CONNECT_DELAY_MS, lambda: self._accept_serial(port)
        )

    def _connect_selected(self):
        """'Bağlan' butonu: açılır listede seçili porta bağlan."""
        port = self.port_combo.currentData()
        if port:
            self._accept_serial(port)

    def _accept_serial(self, port: str):
        """Seri port kararını kaydet ve pencereyi kapat (ana ekran açılacak)."""
        self.result_mode = "serial"
        self.selected_port = port
        self.scan_timer.stop()
        self.accept()

    def _use_simulation(self):
        """'Simülasyona Geç' butonu: simülasyon kararını kaydet ve kapat."""
        self.result_mode = "simulation"
        self.selected_port = None
        self.scan_timer.stop()
        self.accept()
