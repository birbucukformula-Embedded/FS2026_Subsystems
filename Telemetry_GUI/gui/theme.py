# -*- coding: utf-8 -*-
"""
gui/theme.py — RENKLER VE ORTAK STİLLER
========================================

Bütün renkler ve stil tanımları TEK BİR DOSYADA toplanır. Böylece:
  1. Bir rengi değiştirmek istersek sadece burayı düzenleriz.
  2. Bütün ekran otomatik olarak aynı temayı kullanır.

Renkler, takımın web sitesinden (https://birbucukformula-web.github.io/Deneme-bolgesi/)
birebir alınmıştır. Sitenin CSS'inde şu değişkenler tanımlı:
    --bg:             #0A0A0A   (neredeyse siyah arka plan)
    --surface:        #141414   (kart/yüzey rengi)
    --text-primary:   #F5F5F5   (ana yazı rengi)
    --text-secondary: #CCCCCC   (ikincil/soluk yazı)
    --accent:         #E8000D   (takım kırmızısı — logodaki şimşek rengi)

TASARIM KURALI (yeşil sırıtmasın diye):
  Ekranın genel görünümü SİYAH + KIRMIZI olmalıdır (site ile aynı).
  Yeşil/kırmızı durum renkleri KOCAMAN alanlara boyanmaz; sadece küçük
  gösterge noktaları (●) ve ince vurgular için kullanılır.
"""

# ---------------------------------------------------------------------------
# TAKIM RENK PALETİ (siteyle birebir aynı)
# ---------------------------------------------------------------------------
COLOR_BG         = "#0A0A0A"   # sitenin --bg değişkeni: koyu siyah zemin
COLOR_SURFACE    = "#141414"   # sitenin --surface değişkeni: kartların zemini
COLOR_TEXT       = "#F5F5F5"   # sitenin --text-primary: ana yazı rengi
COLOR_TEXT_MUTED = "#CCCCCC"   # sitenin --text-secondary: başlık/birim gibi
COLOR_ACCENT     = "#E8000D"   # sitenin --accent: takım kırmızısı

# ---------------------------------------------------------------------------
# DURUM RENKLERİ (README'deki renk kuralları tablosu)
# ---------------------------------------------------------------------------
# Bu renkler SADECE küçük noktalarda (●) ve kritik uyarı yazısında
# kullanılır; asla büyük yüzeylere boyanmaz.
COLOR_OK       = "#34A853"      # yeşil: her şey yolunda (küçük nokta olarak)
COLOR_CRITICAL = COLOR_ACCENT   # kritik uyarı = takım kırmızısı
COLOR_INACTIVE = "#6C757D"      # gri: veri yok / placeholder

# ---------------------------------------------------------------------------
# KENARLIKLAR
# ---------------------------------------------------------------------------
# Qt Style Sheet, CSS gibi rgba(...) yazımını destekler.
COLOR_BORDER        = "rgba(232, 0, 13, 0.25)"    # sitenin --border: saydam kırmızı
COLOR_BORDER_SUBTLE = "rgba(255, 255, 255, 0.08)" # sitedeki soluk beyaz çizgiler

# ---------------------------------------------------------------------------
# GRAFİK RENKLERİ (pyqtgraph için)
# ---------------------------------------------------------------------------
# ÖNEMLİ: pyqtgraph, Qt Style Sheet'in aksine "rgba(...)" metin biçimini
# ANLAMAZ; ona düz hex renk vermek gerekir. Bu yüzden grafik ekseni/ızgarası
# için ayrı, hex biçiminde bir renk tanımlıyoruz.
COLOR_CHART_AXIS = "#3A3A3A"   # grafik ekseni ve ızgara çizgileri (soluk gri)

# Ana grafikteki farklı çizgileri (seri) birbirinden ayırmak için renkler.
# Yeşilden kaçınıyoruz (önceki geri bildirim: yeşil sırıtıyor). Kırmızı ana
# renk; mavi ve amber siyah zeminde net ayrışır ve markayla uyumlu durur.
COLOR_SERIES_1 = "#E8000D"   # kırmızı  (örn: gaz pedalı)
COLOR_SERIES_2 = "#33B5E5"   # açık mavi (örn: fren basıncı)
COLOR_SERIES_3 = "#FFC107"   # amber    (örn: tork komutu)

# ---------------------------------------------------------------------------
# HAZIR STİL PARÇALARI
# ---------------------------------------------------------------------------
# Ana pencerenin genel stili: koyu zemin + açık yazı.
STYLE_WINDOW = f"background-color: {COLOR_BG}; color: {COLOR_TEXT};"

# Veri kartı: koyu yüzey + soluk kenarlık + yuvarlak köşe.
# Kenarlığı kırmızı değil SOLUK BEYAZ yaptık; kırmızıyı sadece bölüm
# başlıklarındaki vurgu çizgisine sakladık (site de böyle yapıyor).
# :hover -> fare üzerine gelince kenarlık kırmızıya döner: kart tıklanabilir
# (detay grafiği açar) olduğunun görsel ipucu.
STYLE_CARD = (
    f"QFrame {{"
    f"  background-color: {COLOR_SURFACE};"
    f"  border: 1px solid {COLOR_BORDER_SUBTLE};"
    f"  border-radius: 8px;"
    f"}}"
    f"QFrame:hover {{ border: 1px solid {COLOR_ACCENT}; }}"
)

# Seçili (detay grafiği açık) kart: kenarlık takım kırmızısı — hangi kartın
# grafiğinin açık olduğunu belli eder.
STYLE_CARD_SELECTED = (
    f"QFrame {{"
    f"  background-color: {COLOR_SURFACE};"
    f"  border: 1px solid {COLOR_ACCENT};"
    f"  border-radius: 8px;"
    f"}}"
)

# Durum "chip"i: rozetlerin ve bağlantı göstergesinin küçük hap görünümü.
# Arka plan koyu, yazı soluk — renk sadece içindeki ● noktasından gelir.
STYLE_CHIP = (
    f"background-color: {COLOR_SURFACE};"
    f"border: 1px solid {COLOR_BORDER_SUBTLE};"
    f"border-radius: 12px;"
    f"padding: 4px 12px;"
    f"color: {COLOR_TEXT_MUTED};"
    f"font-weight: bold;"
    f"font-size: 12px;"
)

# Bölüm başlığı: solda 3px kalınlığında kırmızı çizgi + büyük harfli
# soluk yazı. Sitedeki bölüm başlıklarının PyQt karşılığı.
STYLE_SECTION_TITLE = (
    f"border-left: 3px solid {COLOR_ACCENT};"
    f"padding-left: 8px;"
    f"color: {COLOR_TEXT_MUTED};"
    f"font-size: 13px;"
    f"font-weight: bold;"
    f"letter-spacing: 2px;"
)

# Port seçim kutusu (QComboBox): koyu zemin, soluk kenarlık — temaya uyumlu.
STYLE_COMBOBOX = (
    f"QComboBox {{"
    f"  background-color: {COLOR_SURFACE};"
    f"  border: 1px solid {COLOR_BORDER_SUBTLE};"
    f"  border-radius: 6px;"
    f"  padding: 4px 8px;"
    f"  color: {COLOR_TEXT};"
    f"  font-size: 12px;"
    f"}}"
    # Açılır listenin kendisi de koyu görünsün.
    f"QComboBox QAbstractItemView {{"
    f"  background-color: {COLOR_SURFACE};"
    f"  color: {COLOR_TEXT};"
    f"  selection-background-color: {COLOR_ACCENT};"
    f"}}"
)

# Bağlan/Kes butonu (QPushButton): takım kırmızısı zemin, beyaz yazı.
STYLE_BUTTON = (
    f"QPushButton {{"
    f"  background-color: {COLOR_ACCENT};"
    f"  border: none;"
    f"  border-radius: 6px;"
    f"  padding: 5px 14px;"
    f"  color: white;"
    f"  font-weight: bold;"
    f"  font-size: 12px;"
    f"}}"
    # Fare üzerine gelince biraz koyulaşsın (basit bir geri bildirim).
    f"QPushButton:hover {{ background-color: #B00009; }}"
)

# İKİNCİL buton (örn: "Simülasyona Geç"): koyu zemin + soluk kenarlık.
# Birincil kırmızı butondan ayrışsın diye daha sakin bir görünüm.
STYLE_BUTTON_SECONDARY = (
    f"QPushButton {{"
    f"  background-color: {COLOR_SURFACE};"
    f"  border: 1px solid {COLOR_BORDER_SUBTLE};"
    f"  border-radius: 6px;"
    f"  padding: 5px 14px;"
    f"  color: {COLOR_TEXT};"
    f"  font-weight: bold;"
    f"  font-size: 12px;"
    f"}}"
    f"QPushButton:hover {{ border: 1px solid {COLOR_ACCENT}; }}"
)

# Ana grafiğin üstündeki seri aç/kapa kutucukları (QCheckBox).
# İşaretliyken kutu takım kırmızısı olur.
STYLE_CHECKBOX = (
    f"QCheckBox {{"
    f"  color: {COLOR_TEXT_MUTED};"
    f"  font-size: 12px;"
    f"  font-weight: bold;"
    f"  spacing: 6px;"
    f"}}"
    f"QCheckBox::indicator {{"
    f"  width: 13px; height: 13px;"
    f"  border-radius: 3px;"
    f"  border: 1px solid {COLOR_BORDER_SUBTLE};"
    f"  background-color: {COLOR_SURFACE};"
    f"}}"
    f"QCheckBox::indicator:checked {{"
    f"  background-color: {COLOR_ACCENT};"
    f"  border: 1px solid {COLOR_ACCENT};"
    f"}}"
)
