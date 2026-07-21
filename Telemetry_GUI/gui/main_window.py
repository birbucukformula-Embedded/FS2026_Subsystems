# -*- coding: utf-8 -*-
"""
gui/main_window.py — ANA PENCERE
=================================

Bütün bölümleri birleştiren ana pencere sınıfı. Yerleşim:

    ┌───────────────────────────────────────────────────────┐
    │  LOGO  PIT TELEMETRİ            [● BAĞLANTI CHIP]     │  üst şerit
    ├───────────────────────────────────────────────────────┤
    │  ARAÇ DURUMU: READY             ARIZA: YOK            │  durum satırı
    ├───────────────────────────────────────────────────────┤
    │  ▍SÜRÜŞ                                               │
    │  [GAZ] [FREN] [TORK] [MOTOR RPM —]                    │
    │  ▍BATARYA (HV)                                        │
    │  [GERİLİM] [AKIM —] [SOC —] [MAX HÜCRE °C —]          │
    │  ▍SICAKLIKLAR                                         │
    │  [MOTOR °C —] [İNVERTER °C —]                         │
    ├───────────────────────────────────────────────────────┤
    │  ▍SİSTEM    [●AIR-] [●AIR+] [●PRECHARGE] [●SDC] [●INV]│  rozetler
    ├───────────────────────────────────────────────────────┤
    │  Paket#  Kayıp  Gecikme  RSSI                         │  alt şerit
    └───────────────────────────────────────────────────────┘

"—" işaretli kartlar README Bölüm 2'deki placeholder alanlardır: pakette
var ama CAN entegrasyonu bitene kadar sabit 0 geliyor; gri gösterilirler.

Bu dosya SADECE görsel dizilim ve güncelleme ile ilgilenir; veri üretimi
core katmanındadır (core/fake_data.py). Küçük parçalar (kart, chip,
bölüm başlığı) gui/widgets.py içindedir.
"""

import os   # logo dosyasının tam yolunu bulmak için

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QComboBox, QPushButton,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap

# Kendi modüllerimiz: theme (renkler), widgets (parçalar), veri kaynakları.
from gui import theme
from gui.widgets import ValueCard, StatusChip, SectionTitle, LiveChart
from core import fake_data
from core import serial_reader

# Logo dosyasının yolu. __file__ = bu dosyanın konumu; oradan bir üst
# klasöre çıkıp assets/logo.png'ye ulaşıyoruz. Böylece program hangi
# klasörden çalıştırılırsa çalıştırılsın logo bulunur.
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")


class MainWindow(QMainWindow):
    """Uygulamanın ana penceresi: bölümleri kurar ve periyodik günceller."""

    def __init__(self):
        super().__init__()

        # --- Pencere temel ayarları ---
        self.setWindowTitle("FS2026 — 1.5 Adana Formula Student | Pit Telemetri")
        # Grafik bölümü de eklendiği için pencereyi biraz daha uzun açıyoruz.
        self.resize(1000, 920)
        self.setStyleSheet(theme.STYLE_WINDOW)    # koyu tema (site renkleri)

        # QMainWindow'a doğrudan yerleşim verilemez; önce bir "merkez
        # widget" koyup yerleşimi ona bağlamak gerekir (PyQt kalıbı).
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)  # pencere iç boşluğu
        main_layout.setSpacing(10)                      # bölümler arası boşluk

        # Bölümleri sırayla kur. Her bölüm ayrı metod; __init__ kısa kalsın.
        main_layout.addLayout(self._build_top_bar())
        main_layout.addLayout(self._build_vehicle_status_row())
        main_layout.addWidget(SectionTitle("Sürüş"))
        main_layout.addLayout(self._build_drive_cards())
        main_layout.addWidget(SectionTitle("Batarya (HV)"))
        main_layout.addLayout(self._build_battery_cards())
        main_layout.addWidget(SectionTitle("Sıcaklıklar"))
        main_layout.addLayout(self._build_temperature_cards())
        main_layout.addWidget(SectionTitle("Sistem"))
        main_layout.addLayout(self._build_status_chips())
        main_layout.addWidget(SectionTitle("Canlı Grafikler"))
        # Grafik ızgarasını "stretch faktörü 1" ile ekliyoruz: pencere
        # büyüdükçe fazladan yeri GRAFİKLER kaplasın (kartlar sabit kalsın).
        main_layout.addLayout(self._build_charts(), stretch=1)
        main_layout.addLayout(self._build_bottom_bar())

        # --- VERİ ZAMANLAYICISI ---
        # QTimer: belirli aralıkla bir fonksiyonu çağırır. Qt'nin olay
        # döngüsü (event loop) içinde çalıştığı için arayüzü DONDURMAZ.
        # README'deki "saniyede 10 veri ekranı dondurmadan nasıl çizilir?"
        # sorusunun cevabı budur (while+sleep yerine QTimer).
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(100)   # 100 ms = saniyede 10 kez (10 Hz)

        # --- VERİ KAYNAĞI ---
        # data_source: o an verinin geldiği nesne (FakeDataSource ya da
        # SerialReader). İkisi de next_packet() sunduğu için arayüz ayrımı
        # bilmek zorunda değil.
        self.data_source = None

        # Açılışta: portları tara, Raspberry Pi / USB-UART adayı varsa ona
        # otomatik bağlan; yoksa (ya da bağlanma başarısızsa) simülasyona düş.
        self._refresh_ports()
        self._auto_connect()

    # ------------------------------------------------------------------
    # SERİ PORT BAĞLANTI YÖNETİMİ
    # ------------------------------------------------------------------

    def _refresh_ports(self):
        """Bağlı seri portları tarayıp port seçim kutusunu doldurur."""
        self.port_combo.clear()
        # Her port için "device — açıklama" metnini göster; asıl port adını
        # (device) item'ın verisi olarak sakla (currentData ile alacağız).
        for device, description in serial_reader.list_serial_ports():
            self.port_combo.addItem(f"{device} — {description}", device)
        if self.port_combo.count() == 0:
            # Hiç port yoksa kullanıcı görsün diye bilgilendirici bir satır.
            self.port_combo.addItem("(port bulunamadı)", None)

    def _auto_connect(self):
        """
        Raspberry Pi / USB-UART adayı bir port varsa ona otomatik bağlanır.
        Aday yoksa veya bağlanma başarısızsa simülasyon moduna geçer.
        """
        port = serial_reader.find_vehicle_port()
        if port and self._connect(port):
            return
        self._use_simulation()

    def _connect(self, port: str) -> bool:
        """
        Verilen porta bağlanmayı dener. Başarılıysa True döner ve veri
        kaynağını seri porta çevirir; başarısızsa False döner.
        """
        try:
            self.data_source = serial_reader.SerialReader(port)
        except Exception:
            # Port meşgul, izin yok, kayboldu vb. — çökmeden hata göster.
            self._set_connection_status(f"HATA: {port}", state=False)
            return False

        # Bağlantı açık: chip'i yeşil yap, butonu "Kes"e çevir, portu seçili
        # göster.
        self._set_connection_status(f"BAĞLI: {port}", state=True)
        self.connect_button.setText("Kes")
        self._select_port_in_combo(port)
        return True

    def _disconnect(self):
        """Açık seri portu kapatır ve simülasyon moduna döner."""
        if isinstance(self.data_source, serial_reader.SerialReader):
            self.data_source.close()
        self._use_simulation()

    def _use_simulation(self):
        """Veri kaynağını sahte veriye çevirir (bağlantı yokken arayüz boş durmasın)."""
        self.data_source = fake_data.FakeDataSource()
        self._set_connection_status("SİMÜLASYON", state=None)
        self.connect_button.setText("Bağlan")

    def _toggle_connection(self):
        """Bağlan/Kes butonuna basılınca çağrılır: duruma göre bağlan ya da kes."""
        if isinstance(self.data_source, serial_reader.SerialReader):
            self._disconnect()
        else:
            port = self.port_combo.currentData()   # seçili portun device adı
            if port:
                self._connect(port)

    def _select_port_in_combo(self, port: str):
        """Seçim kutusunda verilen portu seçili hale getirir (varsa)."""
        index = self.port_combo.findData(port)
        if index >= 0:
            self.port_combo.setCurrentIndex(index)

    def _set_connection_status(self, text: str, state):
        """
        Üst şeritteki bağlantı chip'ini günceller.
        state: True -> yeşil (bağlı), None -> gri (simülasyon), False -> kırmızı (hata).
        """
        self.connection_chip.name = text
        self.connection_chip.set_status(state)

    # ------------------------------------------------------------------
    # BÖLÜM KURULUM METODLARI — her biri bir yerleşim (layout) döndürür
    # ------------------------------------------------------------------

    def _build_top_bar(self):
        """Üst şerit: solda takım logosu + başlık, sağda bağlantı chip'i."""
        bar = QHBoxLayout()

        # --- Takım logosu ---
        # QPixmap resmi yükler; scaledToHeight ile 36 px yüksekliğe
        # küçültürüz (SmoothTransformation = kaliteli küçültme).
        logo_label = QLabel()
        logo_pixmap = QPixmap(LOGO_PATH)
        if not logo_pixmap.isNull():   # dosya yoksa çökme, logosuz devam et
            logo_label.setPixmap(
                logo_pixmap.scaledToHeight(36, Qt.SmoothTransformation)
            )

        # --- Başlık ---
        title = QLabel("1.5 Adana Formula Student | Pit Telemetri")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet(f"color: {theme.COLOR_TEXT}; letter-spacing: 3px;")

        # --- Port seçim kutusu ---
        # Bağlı seri portlar burada listelenir; kullanıcı manuel seçebilir.
        # _refresh_ports() bunu doldurur.
        self.port_combo = QComboBox()
        self.port_combo.setStyleSheet(theme.STYLE_COMBOBOX)
        self.port_combo.setMinimumWidth(220)

        # --- Yenile butonu ---
        # Sonradan takılan bir portu görmek için listeyi yeniden taratır.
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setStyleSheet(theme.STYLE_BUTTON)
        self.refresh_button.clicked.connect(self._refresh_ports)

        # --- Bağlan/Kes butonu ---
        # Metni duruma göre değişir ("Bağlan" <-> "Kes"); tıklama
        # _toggle_connection'a gider.
        self.connect_button = QPushButton("Bağlan")
        self.connect_button.setStyleSheet(theme.STYLE_BUTTON)
        self.connect_button.clicked.connect(self._toggle_connection)

        # --- Bağlantı durumu chip'i ---
        # Koyu hap + renkli nokta: yeşil=bağlı, gri=simülasyon, kırmızı=hata.
        self.connection_chip = StatusChip("SİMÜLASYON")

        bar.addWidget(logo_label)
        bar.addSpacing(10)          # logo ile başlık arası sabit boşluk
        bar.addWidget(title)
        bar.addStretch()            # esnek boşluk -> sağdaki grubu sağa yaslar
        bar.addWidget(self.port_combo)
        bar.addSpacing(6)
        bar.addWidget(self.refresh_button)
        bar.addSpacing(6)
        bar.addWidget(self.connect_button)
        bar.addSpacing(10)
        bar.addWidget(self.connection_chip)
        return bar

    def _build_vehicle_status_row(self):
        """
        Araç durumu (vehicleState) ve arıza (faultCode) satırı.
        Yazılar normalde BEYAZ kalır; sadece arıza anında kırmızıya döner.
        (Sürekli yeşil yanmaz — göz yormasın.)
        """
        row = QHBoxLayout()

        self.state_label = QLabel("ARAÇ DURUMU: —")
        self.state_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.state_label.setStyleSheet(f"color: {theme.COLOR_TEXT};")

        self.fault_label = QLabel("ARIZA: —")
        self.fault_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.fault_label.setStyleSheet(f"color: {theme.COLOR_TEXT_MUTED};")

        row.addWidget(self.state_label)
        row.addStretch()
        row.addWidget(self.fault_label)
        return row

    def _build_drive_cards(self):
        """SÜRÜŞ bölümü: gaz, fren, tork (canlı) + motor RPM (placeholder)."""
        grid = QGridLayout()
        grid.setSpacing(10)

        self.card_apps   = ValueCard("GAZ PEDALI", "%")
        self.card_brake  = ValueCard("FREN BASINCI", "bar")
        self.card_torque = ValueCard("TORK KOMUTU", "Nm")
        # README Bölüm 2: motorRPM inverter CAN'ı bağlanınca gerçek olacak.
        self.card_rpm    = ValueCard("MOTOR DEVRİ", "RPM", placeholder=True)

        # addWidget(widget, satır, sütun)
        grid.addWidget(self.card_apps,   0, 0)
        grid.addWidget(self.card_brake,  0, 1)
        grid.addWidget(self.card_torque, 0, 2)
        grid.addWidget(self.card_rpm,    0, 3)
        return grid

    def _build_battery_cards(self):
        """BATARYA bölümü: gerilim (canlı) + akım, SOC, max hücre (placeholder)."""
        grid = QGridLayout()
        grid.setSpacing(10)

        self.card_voltage = ValueCard("GERİLİM", "V")
        # README Bölüm 2: bu üçü BMS CAN'ı bağlanınca gerçek olacak.
        self.card_current   = ValueCard("AKIM", "A", placeholder=True)
        self.card_soc       = ValueCard("ŞARJ DURUMU (SOC)", "%", placeholder=True)
        self.card_cell_temp = ValueCard("MAX HÜCRE SICAKLIĞI", "°C", placeholder=True)

        grid.addWidget(self.card_voltage,   0, 0)
        grid.addWidget(self.card_current,   0, 1)
        grid.addWidget(self.card_soc,       0, 2)
        grid.addWidget(self.card_cell_temp, 0, 3)
        return grid

    def _build_temperature_cards(self):
        """SICAKLIKLAR bölümü: motor ve inverter sıcaklığı (ikisi de placeholder)."""
        grid = QGridLayout()
        grid.setSpacing(10)

        # README Bölüm 2: ikisi de inverter CAN'ı bağlanınca gerçek olacak.
        self.card_motor_temp    = ValueCard("MOTOR", "°C", placeholder=True)
        self.card_inverter_temp = ValueCard("İNVERTER", "°C", placeholder=True)

        grid.addWidget(self.card_motor_temp,    0, 0)
        grid.addWidget(self.card_inverter_temp, 0, 1)
        # Diğer bölümlerle sütun hizası tutsun diye 4 sütunun DA genişliğini
        # eşitliyoruz (stretch=1). Böylece 2 kart, üstteki kartlarla aynı
        # genişlikte olur; kalan 2 sütun boş kalır ama yer kaplar.
        for column in range(4):
            grid.setColumnStretch(column, 1)
        return grid

    def _build_status_chips(self):
        """AIR-, AIR+, PRECHARGE, SDC, INV EN durum chip'leri satırı."""
        row = QHBoxLayout()
        row.setSpacing(8)

        # Eşleme: chip üzerindeki isim -> paketteki alan adı.
        # Güncellerken bu sözlüğü dolaşarak her chip'e kendi verisini vereceğiz.
        self.chip_fields = {
            "AIR-":      "airMinus",
            "AIR+":      "airPlus",
            "PRECHARGE": "precharge",
            "SDC":       "sdcClosed",
            "INV EN":    "inverterEnable",
        }
        self.chips = {}
        for name in self.chip_fields:
            chip = StatusChip(name)
            self.chips[name] = chip
            row.addWidget(chip)

        row.addStretch()   # chip'leri sola yasla
        return row

    def _build_charts(self):
        """
        CANLI GRAFİKLER bölümü: canlı verilerin her biri için ayrı küçük
        çizgi grafik. 2x2 ızgara düzeni:

            [ GAZ PEDALI ]   [ FREN BASINCI ]
            [ TORK KOMUTU]   [ GERİLİM      ]

        Her grafik kendi ölçeğinde çizer (gaz 0-100, gerilim ~380-400);
        bu yüzden ayrı ayrı tutmak, hepsini tek eksende sıkıştırmaktan
        daha okunaklıdır.
        """
        grid = QGridLayout()
        grid.setSpacing(10)

        # Grafikleri oluştur ve self'e kaydet (update_data'dan besleyeceğiz).
        # Renkleri tutarlı olsun diye hepsinde takım kırmızısını kullanıyoruz.
        self.chart_apps    = LiveChart("GAZ PEDALI", "%")
        self.chart_brake   = LiveChart("FREN BASINCI", "bar")
        self.chart_torque  = LiveChart("TORK KOMUTU", "Nm")
        self.chart_voltage = LiveChart("BATARYA GERİLİMİ", "V")

        # addWidget(widget, satır, sütun)
        grid.addWidget(self.chart_apps,    0, 0)
        grid.addWidget(self.chart_brake,   0, 1)
        grid.addWidget(self.chart_torque,  1, 0)
        grid.addWidget(self.chart_voltage, 1, 1)
        return grid

    def _build_bottom_bar(self):
        """Alt şerit: paket no + bağlantı sağlığı metrikleri."""
        bar = QHBoxLayout()

        # Paket sırası (seqNumber) küçük referans metni olarak gösterilir
        # (README önerisi). Kayıp/gecikme/RSSI pit tarafında hesaplanır.
        self.packet_label  = QLabel("Paket: —")
        self.loss_label    = QLabel("Kayıp: —%")
        self.latency_label = QLabel("Gecikme: — ms")
        self.rssi_label    = QLabel("RSSI: — dBm")

        for label in (self.packet_label, self.loss_label,
                      self.latency_label, self.rssi_label):
            label.setStyleSheet(
                f"color: {theme.COLOR_INACTIVE}; font-size: 11px;"
            )
            bar.addWidget(label)
            bar.addSpacing(20)

        bar.addStretch()
        return bar

    # ------------------------------------------------------------------
    # PERİYODİK GÜNCELLEME
    # ------------------------------------------------------------------

    def update_data(self):
        """
        QTimer tarafından saniyede 10 kez çağrılır.

        Akış: veri kaynağından bir paket al -> ekrandaki widget'lara işle.
        Veri kaynağı FakeDataSource ya da SerialReader olabilir; ikisi de
        next_packet() sunduğu için bu kod ikisiyle de aynı şekilde çalışır.

        NOT: Paketteki alanlara packet.get(...) ile erişiyoruz (packet[...]
        değil). Çünkü gerçek seri veride bir alan eksik gelebilir; .get()
        eksikse KeyError yerine None döndürür ve ilgili widget o değeri
        görmezden gelir (mevcut halini korur).
        """
        packet = self.data_source.next_packet()
        if packet is None:
            # Seri portta henüz tam bir satır oluşmadı; bu turda işlenecek
            # veri yok. Sessizce çık, bir sonraki tetikte tekrar bak.
            return

        # --- Canlı sayısal kartlar ---
        self.card_apps.update_value(packet.get("appsPercent"))
        self.card_brake.update_value(packet.get("brakePressure"))
        self.card_torque.update_value(packet.get("torqueCommand"))
        self.card_voltage.update_value(packet.get("batteryVoltage"))
        # Placeholder kartlar (RPM, akım, SOC, sıcaklıklar) güncellenmez.

        # --- Canlı grafikler ---
        self.chart_apps.add_point(packet.get("appsPercent"))
        self.chart_brake.add_point(packet.get("brakePressure"))
        self.chart_torque.add_point(packet.get("torqueCommand"))
        self.chart_voltage.add_point(packet.get("batteryVoltage"))

        # --- Araç durumu ---
        # vehicleState varsa metne çevirip göster; yoksa dokunma.
        if packet.get("vehicleState") is not None:
            state = fake_data.state_text(packet["vehicleState"])
            self.state_label.setText(f"ARAÇ DURUMU: {state}")

        # --- Arıza ---
        # README renk kuralı: faultCode != 0 ise KIRMIZI; normalde soluk beyaz.
        fault = packet.get("faultCode")
        if fault is not None:
            if fault == 0:
                self.fault_label.setText("ARIZA: YOK")
                self.fault_label.setStyleSheet(f"color: {theme.COLOR_TEXT_MUTED};")
            else:
                self.fault_label.setText(f"ARIZA: KOD {fault}")
                self.fault_label.setStyleSheet(
                    f"color: {theme.COLOR_CRITICAL}; font-weight: bold;"
                )

        # --- Durum chip'leri ---
        # Alan yoksa set_status(None) -> gri "veri yok" noktası gösterir.
        for name, field_name in self.chip_fields.items():
            self.chips[name].set_status(packet.get(field_name))

        # --- Alt şerit ---
        if packet.get("seqNumber") is not None:
            self.packet_label.setText(f"Paket: #{packet['seqNumber']}")
        if packet.get("latencyMs") is not None:
            self.latency_label.setText(f"Gecikme: {packet['latencyMs']} ms")
        if packet.get("rssiDbm") is not None:
            self.rssi_label.setText(f"RSSI: {packet['rssiDbm']} dBm")

    # ------------------------------------------------------------------
    # PENCERE KAPANIŞI
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        """
        Pencere kapatılırken çağrılır (Qt olayı). Açık seri port varsa
        düzgünce kapatıyoruz ki port kilitli kalmasın.
        """
        if isinstance(self.data_source, serial_reader.SerialReader):
            self.data_source.close()
        super().closeEvent(event)
