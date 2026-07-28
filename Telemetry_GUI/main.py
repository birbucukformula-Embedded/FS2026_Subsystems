# -*- coding: utf-8 -*-
"""
FS2026 — Yer İstasyonu (Telemetri) Arayüzü — GİRİŞ NOKTASI
===========================================================

Bu dosya yer istasyonu uygulamasını başlatan ana giriş noktasıdır.
Mühendislerin geliştirdiği GUI ve Backend katmanlarını birbirine bağlayıp
Qt olay döngüsünü (event loop) başlatır.
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

if __name__ == "__main__":
    # Qt Uygulama nesnesini oluştur
    app = QApplication(sys.argv)

    # Ana pencereyi oluştur ve görüntüle
    window = MainWindow(start_mode="simulation")
    window.show()

    # Olay döngüsünü başlat
    sys.exit(app.exec_())
