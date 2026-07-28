# -*- coding: utf-8 -*-
"""
gui/widgets/gauges.py — GAZ VE FREN YARIM DAİRE (İĞNELİ) GÖSTERGE BİLEŞENİ
==========================================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 3 (Arayüz - UI/UX & Görsel Tasarım)
------------------------------------------------------------------
Bu dosya, pit ekranında gaz pedalı pozisyonu (`appsPercent`, %) ve fren basıncı (`brakePressure`, bar)
gibi kritik sürücü komutlarını görselleştiren yarım daire gauge (iğneli veya bar dolum tipi)
bileşeni için İSKELET / ŞABLON dosyadır.

GÖREV TANIMI VE ADIMLAR (MÜHENDİS 3 İÇİN TODO REHBERİ):
  1. `HalfCircleGauge(QWidget)`:
     - `paintEvent(self, event)` metodu içinde `QPainter` kullanarak:
       * Dairesel veya yarım daire bir arka plan yayı çizdirin.
       * 0 ile 100 arası açısal dönüşüm hesabı yaparak (`value_to_angle`) renkli bir dolum yayı (arc)
         ya da bir iğne (needle) çizin.
     - `set_value(self, value: float)` çağrıldığında `self.update()` tetiklenmeli ve
       arayüz kilitlenmeden pürüzsüzce yeniden çizilmelidir.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QWidget


class HalfCircleGauge(QWidget):
    """
    Gaz pedalı (%0-100) ve fren basıncı (bar) için yarım daire gösterge (gauge) şablonu.

    KULLANIM (Ana Pencere Tarafında):
        self.apps_gauge = HalfCircleGauge(title="GAZ PEDALI", unit="%", min_val=0, max_val=100)
        # Veri geldiğinde:
        self.apps_gauge.set_value(packet.get("appsPercent", 0.0))
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
        self.setMinimumSize(180, 120)

    def set_value(self, value: float):
        """
        Göstergenin işaret ettiği değeri günceller ve paintEvent'i tetikler.

        TODO (MÜHENDİS 3):
            - Gelen value sınırların dışındaysa clamp yapın: max(min_val, min(max_val, value)).
            - self.current_val güncelledikten sonra self.update() çağırarak çizimi tetikleyin.
        """
        # --- MÜHENDİS 3 KOD ALANI BAŞLANGICI ---
        if value is not None:
            self.current_val = max(self.min_val, min(self.max_val, float(value)))
            self.update()
        # --- MÜHENDİS 3 KOD ALANI BİTİŞİ ---

    def paintEvent(self, event):
        """
        QPainter ile yarım daire kadranı ve iğneyi/dolumu ekrana çizen metot.

        TODO (MÜHENDİS 3):
            - painter = QPainter(self) başlatıp setRenderHint(QPainter.Antialiasing) açın.
            - QPainter.drawArc veya QPainterPath kullanarak ana yayı çizin.
            - self.current_val değerine karşılık gelen açıyı hesaplayıp iğneyi çizin.
            - Ortaya veya alta büyük punto ile sayısal değeri ve birimi yazdırın.
        """
        # --- MÜHENDİS 3 KOD ALANI BAŞLANGICI ---
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Örnek taslak: Şimdilik basitçe ortada başlık ve sayısal değeri göster
        rect = self.rect()
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(
            rect,
            Qt.AlignCenter,
            f"{self.title}\n{self.current_val:.1f} {self.unit}",
        )
        painter.end()
        # --- MÜHENDİS 3 KOD ALANI BİTİŞİ ---
