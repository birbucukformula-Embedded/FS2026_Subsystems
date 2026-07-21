# -*- coding: utf-8 -*-
"""
gui/widgets.py — TEKRAR KULLANILABİLİR ARAYÜZ PARÇALARI
========================================================

Ekranda birden fazla kez kullanılan küçük görsel parçalar (widget'lar):

  - ValueCard    : tek bir telemetri değerini gösteren kutu
  - StatusChip   : ● noktalı, koyu zeminli küçük durum chip'i
  - SectionTitle : kırmızı vurgu çizgili bölüm başlığı (SÜRÜŞ, BATARYA...)

Neden ayrı dosya? Ana pencere "ekranı nasıl dizeceğim" ile uğraşsın;
"bir kart nasıl görünür" detayı burada saklı kalsın (sorumlulukların
ayrılması / separation of concerns).
"""

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Renkleri tek merkezden (theme.py) alıyoruz — burada renk TANIMLAMIYORUZ.
from gui import theme


class ValueCard(QFrame):
    """
    Tek bir telemetri değerini gösteren "kart".

    Görünümü:
        ┌─────────────┐
        │ GAZ PEDALI  │   <- küçük başlık
        │    72.4     │   <- büyük değer
        │      %      │   <- birim
        └─────────────┘

    Aynı sınıf bütün ölçümler için kullanılır (DRY: kod tekrarı yok).
    placeholder=True verilen kartlar CAN entegrasyonu bekleyen alanlardır;
    README kuralı gereği gri "—" gösterirler ve asla güncellenmezler.
    """

    def __init__(self, title: str, unit: str, placeholder: bool = False):
        # QFrame'in kendi kurucusunu çağırmayı unutmuyoruz.
        super().__init__()

        self.placeholder = placeholder
        self.setStyleSheet(theme.STYLE_CARD)   # koyu yüzey + soluk kenarlık
        self.setMinimumHeight(96)              # kartlar aynı boyda dursun

        # İçerideki elemanları üst üste dizen dikey yerleşim.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)   # iç kenar boşlukları (px)
        layout.setSpacing(2)                    # etiketler arası boşluk

        # --- Başlık etiketi (örn: "GAZ PEDALI") ---
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        # "border: none" önemli: kartın kenarlık stili içteki etiketlere
        # miras kalmasın diye her etikette kenarlığı kapatıyoruz.
        self.title_label.setStyleSheet(
            f"color: {theme.COLOR_TEXT_MUTED}; font-size: 11px;"
            "letter-spacing: 1px; border: none;"
        )

        # --- Değer etiketi ---
        # Başlangıç "—": README kuralı gereği gerçek 0 ile "veri yok"
        # birbirine karışmasın.
        self.value_label = QLabel("—")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.value_label.setStyleSheet(
            f"color: {theme.COLOR_INACTIVE}; border: none;"
        )

        # --- Birim etiketi (örn: "%", "bar", "V") ---
        self.unit_label = QLabel(unit)
        self.unit_label.setAlignment(Qt.AlignCenter)
        self.unit_label.setStyleSheet(
            f"color: {theme.COLOR_INACTIVE}; font-size: 11px; border: none;"
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.unit_label)

    def update_value(self, new_value):
        """
        Kartta gösterilen sayıyı günceller. Her yeni telemetri paketinde
        ana pencere tarafından çağrılır.
        """
        if self.placeholder:
            # Placeholder kartlara veri yazılmaz; hep gri "—" kalırlar.
            # CAN entegrasyonu tamamlanınca bu bayrak False yapılacak.
            return

        # f-string ile 1 ondalık basamaklı yazıya çevirip bas.
        self.value_label.setText(f"{new_value:.1f}")
        # Veri aktığı sürece değer beyaz görünsün (gri = veri yok demekti).
        self.value_label.setStyleSheet(
            f"color: {theme.COLOR_TEXT}; border: none;"
        )


class StatusChip(QLabel):
    """
    AIR-, AIR+, PRECHARGE, SDC, INV EN gibi AÇIK/KAPALI durumları gösteren
    küçük "chip".

    TASARIM NOTU: Eski sürümde rozetin TAMAMI yeşile boyanıyordu ve ekranda
    çok sırıtıyordu. Yeni tasarımda chip koyu zeminli; durum rengi sadece
    baştaki küçük ● noktasında:

        [ ● AIR- ]   [ ● SDC ]   ...

    Nokta yeşil = aktif/OK, kırmızı = devrede değil, gri = veri yok.
    """

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(theme.STYLE_CHIP)   # koyu hap görünümü (temadan)
        self.set_status(None)                  # başlangıçta veri yok -> gri nokta

    def set_status(self, active):
        """
        active=True  -> yeşil nokta (sistem devrede)
        active=False -> kırmızı nokta (devrede DEĞİL — dikkat)
        active=None  -> gri nokta (henüz veri gelmedi)
        """
        if active is None:
            color = theme.COLOR_INACTIVE
        elif active:
            color = theme.COLOR_OK
        else:
            color = theme.COLOR_CRITICAL

        # QLabel basit HTML destekler: sadece ● karakterini renklendirip
        # ismin rengine dokunmuyoruz. Böylece renk "sırıtmıyor".
        self.setText(f'<span style="color:{color};">●</span>&nbsp; {self.name}')


class SectionTitle(QLabel):
    """
    "SÜRÜŞ", "BATARYA (HV)" gibi bölüm başlıkları.
    Solda 3px kırmızı vurgu çizgisi + büyük harfli soluk yazı —
    takım sitesindeki bölüm başlıklarının aynısı.
    """

    def __init__(self, text: str):
        # .upper(): başlıklar her zaman BÜYÜK HARF görünsün.
        super().__init__(text.upper())
        self.setStyleSheet(theme.STYLE_SECTION_TITLE)
