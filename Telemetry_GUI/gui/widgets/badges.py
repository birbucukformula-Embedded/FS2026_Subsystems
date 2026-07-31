# -*- coding: utf-8 -*-
"""
gui/widgets/badges.py — DURUM ROZETLERİ (CHIPS) VE ARIZA GÖSTERGELERİ
=====================================================================

SORUMLU MÜHENDİS: 🧑‍💻 MÜHENDİS 3 (Arayüz - UI/UX & Görsel Tasarım)
------------------------------------------------------------------
Aracın elektrik ve güvenlik devrelerinin (AIR-, AIR+, Precharge, SDC Closed,
Inverter Enable) kapalı/açık durumunu gösteren rozetler (chips) ile arıza kodlarını
(FaultCode) renkli etiket olarak sunan sınıflar.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel

FAULT_DESCRIPTIONS = {
    0: "YOK (Sistem Normal)",
    1: "BMS Aşırı Sıcaklık (Over-temp)",
    2: "BMS Düşük Gerilim (Under-voltage)",
    3: "İnverter CAN İletişim Hatası",
    4: "APPS / Fren Çakışması (Implausibility)",
    5: "SDC Devre Dışı (Acil Durum Devresi Açıldı)",
    6: "Aşırı Motor Akımı",
    7: "Telemetri İletişim Zaman Aşımı",
}


class StatusBadge(QLabel):
    """
    AIR-, AIR+, PRECHARGE, SDC, INV EN vb. durumları gösteren rozet bileşeni.
    """

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.setMinimumHeight(32)
        self.set_status(None)

    def set_status(self, active):
        """
        Rozetin durumunu günceller.
        active=True (Yeşil OK), active=False (Kırmızı Kritik), active=None (Gri Bekleniyor).
        """
        if active is True:
            # Yeşil (Aktif / Devrede / OK)
            dot_color = "#00E676"
            text_color = "#E0F2F1"
            bg_color = "#0E2B1E"
            border_color = "#1B5E3C"
            status_text = "OK"
        elif active is False:
            # Kırmızı (Devre Dışı / Hata / Açık)
            dot_color = "#FF1744"
            text_color = "#FFEBEE"
            bg_color = "#381419"
            border_color = "#7F1D1D"
            status_text = "AÇIK"
        else:
            # Gri (Veri Yok / Beklemede)
            dot_color = "#6E7A8A"
            text_color = "#9CA3AF"
            bg_color = "#181A20"
            border_color = "#2D323E"
            status_text = "—"

        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 14px;
                padding: 4px 12px;
                color: {text_color};
                font-weight: bold;
            }}
            """
        )
        self.setText(
            f'<html><head/><body>'
            f'<span style="color: {dot_color}; font-size: 13pt;">●</span> &nbsp;'
            f'<b>{self.name}</b> <span style="color: #6E7A8A;">|</span> '
            f'<span style="color: {dot_color};">{status_text}</span>'
            f'</body></html>'
        )


class FaultCodeBadge(QLabel):
    """
    Aktif arıza kodunu (faultCode) açıklayıcı metinle gösteren uyarı rozeti.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.setMinimumHeight(42)
        self.set_fault_code(0)

    def set_fault_code(self, code: int):
        """
        Arıza koduna göre rozetin metnini ve rengini günceller.
        """
        desc = FAULT_DESCRIPTIONS.get(code, f"Bilinmeyen Arıza ({code})")
        if code == 0:
            self.setStyleSheet(
                """
                QLabel {
                    background-color: #0F291E;
                    border: 1px solid #1E5E3A;
                    border-radius: 8px;
                    color: #00E676;
                    padding: 6px 14px;
                }
                """
            )
            self.setText("✓  ARIZA KODU: 0 — SİSTEM NORMAL (HATASIZ)")
        else:
            self.setStyleSheet(
                """
                QLabel {
                    background-color: #3B1219;
                    border: 2px solid #FF1744;
                    border-radius: 8px;
                    color: #FF5252;
                    padding: 6px 14px;
                }
                """
            )
            self.setText(f"⚠️  KRİTİK ARIZA (KOD {code}) :  {desc.upper()}")

