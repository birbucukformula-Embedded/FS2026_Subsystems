# -*- coding: utf-8 -*-
"""
gui/widgets/gauges.py — GAZ VE FREN YARIM DAİRE (İĞNELİ) GÖSTERGE BİLEŞENİ
==========================================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 3 (Arayüz - UI/UX & Görsel Tasarım)
------------------------------------------------------------------
Pit ekranında gaz pedalı pozisyonu (`appsPercent`, %) ve fren basıncı (`brakePressure`, bar)
gibi kritik sürücü komutlarını görselleştiren dairesel gauge bileşeni.
"""

import math
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QRadialGradient
from PyQt5.QtWidgets import QWidget


class HalfCircleGauge(QWidget):
    """
    Gaz pedalı (%0-100) ve fren basıncı (bar) için modern dairesel gösterge (gauge).
    """

    def __init__(
        self,
        title: str = "GÖSTERGE",
        unit: str = "%",
        min_val: float = 0.0,
        max_val: float = 100.0,
        parent=None,
    ):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = min_val
        self.setMinimumSize(200, 150)

    def set_value(self, value: float):
        """
        Göstergenin işaret ettiği değeri günceller ve paintEvent'i tetikler.
        """
        if value is not None:
            try:
                val_float = float(value)
                self.current_val = max(self.min_val, min(self.max_val, val_float))
                self.update()
            except (ValueError, TypeError):
                pass

    def _get_arc_color(self, ratio: float) -> QColor:
        """Dolum oranına göre dinamik renk (Yeşil -> Sarı -> Kırmızı) döndürür."""
        if ratio < 0.65:
            return QColor("#00E5FF")  # Neon Camgöbeği (Sabit/Stabil)
        elif ratio < 0.85:
            return QColor("#FFAB00")  # Uyarı Sarı/Turuncu
        else:
            return QColor("#FF1744")  # Kritik Kırmızı

    def paintEvent(self, event):
        """
        QPainter ile modern dairesel kadranı, dolum yayını ve iğneyi çizen metot.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Kare bir çizim alanı hesapla (ortalanmış)
        size = min(width, height) - 24
        x = (width - size) / 2.0
        y = (height - size) / 2.0
        rect = QRectF(x, y, size, size)

        # 1) Arka plan yayı (Koyu Track)
        # Qt açısı saat 3 yönünden başlar, saat yönünün tersidir. (16 ile çarpılır)
        # 210 dereceden başlayıp -240 derece dönüyoruz (saat yönünde, 210'dan -30'a)
        start_angle = 210 * 16
        span_angle = -240 * 16

        track_pen = QPen(QColor("#1D222E"), 14, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, start_angle, span_angle)

        # 2) Değer dolum yayı (Progress Arc)
        ratio = (self.current_val - self.min_val) / max(1e-6, (self.max_val - self.min_val))
        ratio = max(0.0, min(1.0, ratio))

        progress_span = int(-240 * 16 * ratio)
        active_color = self._get_arc_color(ratio)

        progress_pen = QPen(active_color, 14, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(progress_pen)
        if progress_span != 0:
            painter.drawArc(rect, start_angle, progress_span)

        # 3) İğne (Needle)
        # 210 derece (min) ile -30 derece (max) arası doğrusal dönüşüm
        angle_deg = 210.0 - (240.0 * ratio)
        angle_rad = math.radians(angle_deg)

        center_x = x + size / 2.0
        center_y = y + size / 2.0
        needle_len = (size / 2.0) - 18

        needle_end_x = center_x + needle_len * math.cos(angle_rad)
        needle_end_y = center_y - needle_len * math.sin(angle_rad)  # Qt'de Y aşağı artar

        needle_pen = QPen(QColor("#FFFFFF"), 3, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(needle_pen)
        painter.drawLine(
            QPointF(center_x, center_y),
            QPointF(needle_end_x, needle_end_y),
        )

        # Merkezdeki göbek noktası (Hub)
        painter.setBrush(active_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center_x, center_y), 6, 6)

        # 4) Metinler (Başlık, Değer ve Birim)
        painter.setPen(QColor("#8F9BBA"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(
            QRectF(x, y + size * 0.22, size, 24),
            Qt.AlignCenter,
            self.title.upper(),
        )

        # Büyük sayısal değer
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 18, QFont.Bold))
        value_str = f"{self.current_val:.1f}"
        painter.drawText(
            QRectF(x, y + size * 0.52, size, 36),
            Qt.AlignCenter,
            value_str,
        )

        # Birim (örn. %, bar)
        painter.setPen(active_color)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(
            QRectF(x, y + size * 0.76, size, 24),
            Qt.AlignCenter,
            self.unit,
        )

        painter.end()

