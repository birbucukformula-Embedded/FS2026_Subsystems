# -*- coding: utf-8 -*-
"""
FS2026 — Yer İstasyonu (Telemetri) Arayüzü — GİRİŞ NOKTASI
===========================================================

Bu dosya SADECE uygulamayı başlatır. Akış:
  1. Açılış ekranını (StartupDialog) göster: port taraması + otomatik
     bağlanma ya da "Simülasyona Geç".
  2. Kullanıcının/otomatiğin verdiği karara göre ana pencereyi (MainWindow)
     seri port veya simülasyon modunda aç.

Kod, sorumluluklarına göre modüllere bölünmüştür:

    Telemetry_GUI/
    ├── main.py              <- bu dosya: uygulamayı başlatır
    ├── core/                <- VERİ katmanı (arayüzden bağımsız)
    │   ├── fake_data.py     <- simülasyon paketi üretir
    │   └── serial_reader.py <- gerçek seri porttan okur
    ├── gui/                 <- GÖRSEL katman
    │   ├── theme.py         <- takım renkleri ve ortak stiller
    │   ├── widgets.py       <- kart, chip, grafik parçaları
    │   ├── startup_dialog.py<- açılış / port seçim ekranı
    │   └── main_window.py   <- bölümleri birleştiren ana pencere
    └── assets/
        └── logo.png         <- takım logosu

Çalıştırmak için:
    source venv/bin/activate    (Windows'ta: venv\\Scripts\\activate)
    python main.py
"""

import sys

from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QIcon

from gui.main_window import MainWindow, LOGO_PATH
from gui.startup_dialog import StartupDialog

if __name__ == "__main__":
    # 1. Qt uygulama nesnesi (olay döngüsünü yönetir).
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(LOGO_PATH))   # Dock/görev çubuğu simgesi = logo

    # 2. Açılış ekranını göster (modal). exec_() kullanıcı bir karar verene
    #    kadar bekler: seri porta bağlan ya da simülasyona geç.
    startup = StartupDialog()
    if startup.exec_() != QDialog.Accepted:
        # Kullanıcı pencereyi çarpıyla kapattıysa programdan çık.
        sys.exit(0)

    # 3. Açılış ekranının kararıyla ana pencereyi başlat.
    window = MainWindow(
        start_mode=startup.result_mode,   # "serial" veya "simulation"
        start_port=startup.selected_port, # seri ise porta bağlan
    )
    window.show()

    # 4. Olay döngüsünü başlat.
    sys.exit(app.exec_())
