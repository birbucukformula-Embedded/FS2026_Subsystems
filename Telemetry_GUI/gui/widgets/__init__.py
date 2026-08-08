# -*- coding: utf-8 -*-
"""
gui/widgets/ — ÖZEL GÖRSEL BİLEŞENLER VE DURUM ROZETLERİ PAKETİ
==============================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 3 (Arayüz - UI/UX & Görsel Tasarım)
------------------------------------------------------------------
Bu klasör, ana pit ekranında (main_window.py) tekrar tekrar kullanılan özel
küçük widget'ların ayrı modüllerde tutulması için oluşturulmuş pakettir:

  - badges.py : AIR-, AIR+, PRECHARGE, SDC, INV EN rozetleri ve arıza (FaultCode) çipleri.
  - gauges.py : Gaz pedalı (APPS %) ve fren basıncı (bar) için dairesel / iğneli göstergeler.
"""

from .badges import StatusBadge, FaultCodeBadge
from .gauges import HalfCircleGauge
