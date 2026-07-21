# Telemetry GUI — Yer İstasyonu Arayüzü

Pit alanındaki mühendislerin pistteki aracı canlı olarak takip etmesi için geliştirilen masaüstü telemetri programı. Raspberry Pi üzerinden LoRa ile gelen araç verisini (hız, sıcaklık vb.) seri port üzerinden okuyup gerçek zamanlı çizgi grafiklere döker.

## Proje yapısı

```
Telemetry_GUI/
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── logs/
└── assets/
```

## Bölümler

**`main.py`**
Uygulamanın tek giriş noktası. PyQt5 penceresini oluşturur, seri port bağlantısını yönetir, pyqtgraph ile gelen veriyi canlı grafiğe çizer. Proje şu an tek dosyalık (monolitik) bir yapıda; ileride büyürse `gui/` ve `core/` gibi ayrı modüllere bölünebilir.

**`requirements.txt`**
Projenin çalışması için gereken Python kütüphaneleri (PyQt5, pyqtgraph, pyserial, numpy). Kurulum: `pip install -r requirements.txt`

**`logs/`**
Yarış/test sırasında kaydedilen telemetri verilerinin (CSV) tutulduğu klasör. Sonradan analiz için kullanılır.

**`assets/`**
Arayüzde kullanılan ikon, logo veya stil dosyaları.

**`.gitignore`**
Sürüm kontrolüne dahil edilmeyecek dosyalar: sanal ortam (`venv/`), derlenmiş Python dosyaları (`__pycache__/`), ve `logs/` altındaki kayıt verileri.

## Kurulum ve çalıştırma

```bash
pip install -r requirements.txt
python main.py
```