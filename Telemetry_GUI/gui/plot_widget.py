# -*- coding: utf-8 -*-
"""
gui/plot_widget.py — PYQTGRAPH + CIRCULAR BUFFER CANLI ÇİZGİ GRAFİK BİLEŞENİ
=============================================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 3 (Arayüz - UI/UX & Gerçek Zamanlı Grafik Çizimi)
-------------------------------------------------------------------------------
Saniyede 10-20 kez akmakta olan araç telemetri verilerini arayüzü KİLİTLEMEDEN
(freeze olmadan) ve akıcı bir FPS'te çizmek için PyQtGraph tabanlı grafik bileşeni.
"""

from collections import deque
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout

# Koyu Pit Ekranı Renk Paleti:
COLOR_CHART_BG = "#0D0E11"
COLOR_ACCENT = "#00E5FF"
COLOR_GRID = "#262B38"
COLOR_TEXT = "#8F9BBA"


class RealtimePlotWidget(pg.PlotWidget):
    """
    Takılma (freeze) yaratmayan gerçek zamanlı dairesel arabellekli çizim widget'ı.

    KULLANIM (Ana Pencere Tarafında):
        self.speed_chart = RealtimePlotWidget(title="ARAÇ HIZI", unit="km/h", max_points=200)
        self.speed_chart.add_new_data(packet.get("speed", 0.0))
    """

    def __init__(self, title: str = "TELEMETRİ", unit: str = "", max_points: int = 200, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.unit_text = unit
        self.max_points = max_points

        # 1) Sabit uzunluklu dairesel arabellek (Circular Buffer)
        self.y_buffer = deque([0.0] * self.max_points, maxlen=self.max_points)

        # 2) Pit ekranı koyu zemin rengi
        self.setBackground(COLOR_CHART_BG)
        self.showGrid(x=True, y=True, alpha=0.25)

        # 3) Başlık ve eksen etiketleri tasarımı
        self.setTitle(
            f"{title} ({unit})" if unit else title,
            color=COLOR_TEXT,
            size="11pt",
            bold=True,
        )
        self.setLabel("left", unit if unit else "Değer", color=COLOR_TEXT)
        self.setLabel("bottom", "Zaman / Örnek No", color=COLOR_TEXT)

        # 4) Çizer eğrisini (Curve) başlat — Neon Camgöbeği (Cyan) vurgu
        pen = pg.mkPen(color=COLOR_ACCENT, width=2.5)
        self.curve = self.plot(
            list(self.y_buffer),
            pen=pen,
            name=title,
            antialias=True,
        )

        # 5) 33 ms (~30 FPS) tetiklenen render zamanlayıcısı (Decoupled Rendering)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(33)

    def add_new_data(self, value: float):
        """
        Mühendis 2'nin parser katmanından gelen sayısal değeri sadece arabelleğe ekler.
        (Burada KESİNLİKLE self.curve.setData() ÇAĞRILMAZ — çizimi QTimer yapar.)
        """
        if value is not None:
            try:
                val_float = float(value)
                self.y_buffer.append(val_float)
            except (ValueError, TypeError):
                pass

    def update_plot(self):
        """
        QTimer tarafından 33 ms'de bir (~30 FPS) tetiklenen render metodu.
        """
        self.curve.setData(list(self.y_buffer))

    def clear_buffer(self):
        """Grafiği temizlemek için arabelleği sıfırlar."""
        self.y_buffer.clear()
        self.y_buffer.extend([0.0] * self.max_points)

