# -*- coding: utf-8 -*-
"""
gui/widgets/badges.py — DURUM ROZETLERİ (CHIPS) VE ARIZA GÖSTERGELERİ
=====================================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 3 (Arayüz - UI/UX & Görsel Tasarım)
------------------------------------------------------------------
Bu dosya, aracın elektrik ve güvenlik devrelerinin (AIR-, AIR+, Precharge, SDC Closed,
Inverter Enable) kapalı/açık durumunu gösteren rozetler (chips) ile arıza kodlarını (FaultCode)
renkli etiket olarak sunan sınıflar için İSKELET / ŞABLON dosyadır.

GÖREV TANIMI VE ADIMLAR (MÜHENDİS 3 İÇİN TODO REHBERİ):
  1. `StatusBadge(QLabel)`:
     - `set_status(active: bool)`:
       * active=True -> Yeşil nokta (●) veya OK rengi (Sistem normal ve devrede).
       * active=False -> Kırmızı nokta (●) veya KRİTİK rengi (Kontaktör/devre açık/hatalı).
       * active=None -> Gri nokta (●) (Henüz veri gelmedi veya bağlantı yok).
  2. `FaultCodeBadge(QLabel)`:
     - `set_fault_code(code: int)`:
       * code == 0 -> "ARIZA: YOK" (Soluk yeşil/gri yazı).
       * code != 0 -> "ARIZA: KOD {code} — [Açıklama]" (Koyu kırmızı zemin, beyaz bold yazı).
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel

# Örnek Arıza Kodu -> Açıklama Eşlemesi (TODO: VCU dokümantasyonuna göre zenginleştirilecek)
FAULT_DESCRIPTIONS = {
    0: "YOK",
    1: "BMS Aşırı Sıcaklık (Over-temp)",
    2: "BMS Düşük Gerilim (Under-voltage)",
    3: "İnverter CAN İletişim Hatası",
    4: "APPS / Fren Çakışması (Implausibility)",
    5: "SDC Devre Dışı",
}


class StatusBadge(QLabel):
    """
    AIR-, AIR+, PRECHARGE, SDC, INV EN vb. durumları gösteren rozet bileşeni.

    TODO (MÜHENDİS 3):
        - QLabel CSS stilini (`self.setStyleSheet`) koyu yuvarlatılmış hap formunda hazırlayın.
        - `set_status(active)` metodu içinde HTML `<span style="color:...">●</span>` etiketleri ile
          duruma göre rengi değiştirin.
    """

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 11, QFont.Bold))
        # --- MÜHENDİS 3 KOD ALANI BAŞLANGICI ---
        self.setText(f"● {self.name}")
        # --- MÜHENDİS 3 KOD ALANI BİTİŞİ ---

    def set_status(self, active):
        """
        Rozetin durumunu günceller.
        active=True (Yeşil), active=False (Kırmızı), active=None (Gri).
        """
        # --- MÜHENDİS 3 KOD ALANI BAŞLANGICI ---
        pass
        # --- MÜHENDİS 3 KOD ALANI BİTİŞİ ---


class FaultCodeBadge(QLabel):
    """
    Aktif arıza kodunu (faultCode) açıklayıcı metinle gösteren uyarı rozeti.

    TODO (MÜHENDİS 3):
        - `set_fault_code(code)` metodu içinde FAULT_DESCRIPTIONS sözlüğünden kodu sorgulayın.
        - Arıza varsa (code != 0) rozeti dikkat çekici kırmızı/turuncu uyarı stiline sokun.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 13, QFont.Bold))
        self.set_fault_code(0)

    def set_fault_code(self, code: int):
        """
        Arıza koduna göre rozetin metnini ve rengini günceller.
        """
        # --- MÜHENDİS 3 KOD ALANI BAŞLANGICI ---
        desc = FAULT_DESCRIPTIONS.get(code, f"Bilinmeyen Arıza ({code})")
        if code == 0:
            self.setText("ARIZA: YOK")
        else:
            self.setText(f"ARIZA ({code}): {desc}")
        # --- MÜHENDİS 3 KOD ALANI BİTİŞİ ---
