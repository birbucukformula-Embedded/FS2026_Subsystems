# -*- coding: utf-8 -*-
"""
FS2026 — Yer İstasyonu (Telemetri) Arayüzü — GİRİŞ NOKTASI
===========================================================

Bu dosya SADECE uygulamayı başlatır; başka hiçbir iş yapmaz.
Asıl kod, sorumluluklarına göre modüllere bölünmüştür:

    Telemetry_GUI/
    ├── main.py              <- bu dosya: uygulamayı başlatır
    ├── core/                <- VERİ katmanı (arayüzden bağımsız)
    │   └── fake_data.py     <- simülasyon paketi üretir
    │                           (ileride serial_reader.py buraya eklenecek)
    ├── gui/                 <- GÖRSEL katman
    │   ├── theme.py         <- takım renkleri ve ortak stiller
    │   ├── widgets.py       <- ValueCard, StatusChip, SectionTitle parçaları
    │   └── main_window.py   <- bölümleri birleştiren ana pencere
    └── assets/
        └── logo.png         <- takım logosu (üst şeritte gösterilir)

Çalıştırmak için:
    source venv/bin/activate    (Windows'ta: venv\\Scripts\\activate)
    python main.py
"""

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Ana pencereyi ve logo yolunu kendi modülünden alıyoruz.
from gui.main_window import MainWindow, LOGO_PATH

# Bu blok, dosya DOĞRUDAN çalıştırıldığında (python main.py) çalışır;
# başka bir dosyadan import edilirse ÇALIŞMAZ (Python standart kalıbı).
if __name__ == "__main__":
    # 1. Qt uygulama nesnesi: olay döngüsünü (event loop) yönetir.
    #    Her PyQt uygulamasında TAM 1 tane olmak zorundadır.
    app = QApplication(sys.argv)

    # Uygulama simgesi: pencere köşesinde (Windows/Linux) ve macOS'ta
    # ALTTAKİ DOCK ÇUBUĞUNDA Python roketi yerine takım logosunu gösterir.
    # Not: Simge yalnızca uygulama ÇALIŞIRKEN değişir; menü çubuğundaki
    # "Python" yazısını kalıcı değiştirmek için uygulamayı .app paketine
    # dönüştürmek (py2app/pyinstaller) gerekir — o ayrı bir konu.
    app.setWindowIcon(QIcon(LOGO_PATH))

    # 2. Ana pencereyi oluştur ve göster.
    window = MainWindow()
    window.show()

    # 3. Olay döngüsünü başlat. exec_() pencere kapanana kadar bloklar;
    #    kapanınca dönen kodu sys.exit ile işletim sistemine iletiyoruz.
    sys.exit(app.exec_())
