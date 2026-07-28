# -*- coding: utf-8 -*-
"""
gui/plot_widget.py — PYQTGRAPH + CIRCULAR BUFFER CANLI ÇİZGİ GRAFİK BİLEŞENİ
=============================================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 3 (Arayüz - UI/UX & Gerçek Zamanlı Grafik Çizimi)
-------------------------------------------------------------------------------
Bu dosya, saniyede 10-20 kez akmakta olan araç telemetri verilerini arayüzü KİLİTLEMEDEN
(freeze olmadan) ve akıcı bir FPS'te çizebilmek için hazırlanmış İSKELET / ŞABLON dosyadır.

GÖREV TANIMI VE TEKNİK KURALLAR (MÜHENDİS 3 İÇİN TODO REHBERİ):
  1. Matplotlib YERİNE Kesinlikle PyQtGraph Kullanımı:
     - Matplotlib her yenilemede tuvali (canvas) baştan hesapladığı için yüksek frekansta UI donar.
     - `pyqtgraph.PlotWidget` ise C++ / Qt GraphicsView ve NumPy tabanlı olduğu için akıcı 60 FPS sunar.
  2. Decoupled Rendering (Veri Alımı ile Çizimi Ayırma):
     - `add_new_data(value)` metodu SADECE sabit uzunluklu arabelleğe (`collections.deque`) ekleme
       yapar, grafiği yeniden ÇİZDİRMEZ.
     - `QTimer` (33 ms ~ 30 FPS) tarafından tetiklenen `update_plot()` metodu, buffer içindeki güncel
       veriyi tek seferde `self.curve.setData(...)` ile ekrana render eder.
"""

from collections import deque
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout

# Renk temaları (theme.py'den alınabilir):
COLOR_CHART_BG = "#121212"
COLOR_ACCENT = "#00E5FF"
COLOR_GRID = "#333333"


class RealtimePlotWidget(pg.PlotWidget):
    """
    Takılma (freeze) yaratmayan gerçek zamanlı tek seri veya çoklu seri çizim widget'ı.

    KULLANIM (Ana Pencere Tarafında):
        self.speed_chart = RealtimePlotWidget(title="ARAÇ HIZI", unit="km/h", max_points=200)
        # Yeni paket geldiğinde:
        self.speed_chart.add_new_data(packet.get("speed", 0.0))
    """

    def __init__(self, title: str = "TELEMETRİ", unit: str = "", max_points: int = 200, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.unit_text = unit
        self.max_points = max_points

        # TODO (MÜHENDİS 3):
        # 1) self.y_buffer = deque([0.0] * max_points, maxlen=max_points) ile sabit uzunluklu
        #    arabellek tanımlayın.
        # 2) self.setBackground(COLOR_CHART_BG) ile koyu pit arayüzü zemin rengini ayarlayın.
        # 3) self.showGrid(x=True, y=True, alpha=0.3) ile ızgara (grid) açın.
        # 4) self.curve = self.plot(pen=pg.mkPen(color=COLOR_ACCENT, width=2)) ile çizer eğrisini başlatın.
        # 5) 33 ms'de bir (saniyede ~30 kare) çalışan self.timer = QTimer(self) kurup update_plot
        #    metoduna bağlayın (self.timer.start(33)).

        # --- MÜHENDİS 3 KOD ALANI BAŞLANGICI ---
        self.y_buffer = deque([0.0] * self.max_points, maxlen=self.max_points)
        # --- MÜHENDİS 3 KOD ALANI BİTİŞİ ---

    def add_new_data(self, value: float):
        """
        Mühendis 2'nin parser katmanından gelen sayısal değeri sadece arabelleğe ekler.
        (Burada KESİNLİKLE self.curve.setData() ÇAĞRILMAZ — çizimi timer yapar.)

        TODO (MÜHENDİS 3):
            - Gelen value None değilse float(value) değerini self.y_buffer.append(value) ile ekleyin.
        """
        # --- MÜHENDİS 3 KOD ALANI BAŞLANGICI ---
        pass
        # --- MÜHENDİS 3 KOD ALANI BİTİŞİ ---

    def update_plot(self):
        """
        QTimer tarafından 33 ms'de bir (~30 FPS) tetiklenen render metodu.

        TODO (MÜHENDİS 3):
            - self.curve.setData(list(self.y_buffer)) veya np.array(self.y_buffer) çağırarak
              tüm geçmiş noktaları tek seferde çizin.
        """
        # --- MÜHENDİS 3 KOD ALANI BAŞLANGICI ---
        pass
        # --- MÜHENDİS 3 KOD ALANI BİTİŞİ ---

    def clear_buffer(self):
        """Grafiği temizlemek için arabelleği sıfırlar."""
        # --- MÜHENDİS 3 KOD ALANI BAŞLANGICI ---
        self.y_buffer.clear()
        self.y_buffer.extend([0.0] * self.max_points)
        # --- MÜHENDİS 3 KOD ALANI BİTİŞİ ---
