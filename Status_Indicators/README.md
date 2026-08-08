# Görev 4: Non-Blocking LED ve Buzzer Durum Göstergeleri

Bu rehberde, gömülü sistemlerde neden `delay()` fonksiyonundan kaçınmamız gerektiğini, `millis()` kullanarak nasıl zamanlayıcı (timer) yazacağımızı ve basit bir **Durum Makinesi (State Machine)** ile aracın durumuna göre LED ve Buzzer animasyonlarını nasıl yöneteceğimizi adım adım öğreneceğiz.

---

## 1. Gömülü Sistemlerde Neden `delay()` Kullanılmaz?

Arduino veya benzeri mikrodenetleyicilerde `delay(1000)` komutunu çağırdığınızda, işlemci belirtilen süre boyunca (örneğin 1 saniye) hiçbir şey yapmadan bekler (aslında boş bir döngüde döner). Bu duruma **Blocking (Bloklayıcı/Kilitleyici) Kodlama** denir.

### Neden Tehlikelidir?
Bir elektrikli veya otonom araç projesi düşündüğümüzde:
* Araç **1000 ms'lik bir delay** içindeyken frene basılırsa veya bir sensörden **"ACİL DURUM / HATA"** sinyali gelirse, işlemci bunu göremez!
* Haberleşme hattından (CAN Bus, Serial vb.) gelen kritik veriler kaçırılabilir.
* Kısacası, sistem kilitlendiği için araç o an kontrol dışı kalır.

**Hedefimiz:** İşlemcinin sürekli aktif olduğu, sensörleri kontrol ederken aynı zamanda arka planda LED ve buzzer animasyonlarını yürütebildiği **Non-blocking (Bloklamayan)** bir yapı kurmaktır.

---

## 2. `millis()` ile Zamanı Yönetmek (Saat Kontrol Analojisi)

`delay()` kullanmak, iş yapmak için alarm kurup o süre boyunca **uyumaya** benzer. Uykudayken etrafınızda olan biteni fark edemezsiniz.

`millis()` kullanmak ise kolunuzdaki **saate sürekli bakarak** zamanı takip etmeye benzer. Saate bakıp "10 dakika geçmiş mi?" diye kontrol eder, geçmediyse diğer işlerinizi yapmaya devam edersiniz.

### `millis()` Nedir?
* `millis()`, mikrodenetleyici açıldığından itibaren geçen süreyi **milisaniye (ms)** cinsinden veren bir fonksiyondur.
* Geriye döndürdüğü değer çok büyük olabileceği için veri tipi **`unsigned long`** (32-bit işaretsiz tam sayı) olmalıdır. (Yaklaşık 50 gün sonra sıfırlanır/taşar).

### Non-Blocking Zamanlama Formülü

Herhangi bir işlemi belirli aralıklarla tetiklemek için şu şablonu kullanırız:

```cpp
unsigned long currentMillis = millis(); // Şu anki zamanı al

if (currentMillis - previousMillis >= interval) {
    // Son işlemden bu yana 'interval' kadar süre geçmiş!
    previousMillis = currentMillis; // Zamanı güncelle
    
    // Yapılacak işlem (örneğin LED durumunu tersine çevirmek)
    ledState = !ledState;
    digitalWrite(LED_PIN, ledState);
}
```

---

## 3. Durum Makinesi (State Machine) Nedir?

Aracın farklı durumları (Modları) olduğunu biliyoruz. Durum makinesi, sistemin o an hangi modda olduğunu takip eden ve bu moda göre davranmasını sağlayan bir yapıdır.

C++ dilinde bunu en temiz şekilde `enum` (numaralandırma) ve `switch-case` yapısı ile kurarız.

### Durumlarımızı Tanımlayalım (`enum`)
```cpp
enum VehicleState {
  STATE_IDLE,             // Beklemede (LED kapalı, sessiz)
  STATE_READY_TO_DRIVE,   // Sürüşe Hazır (Yeşil LED sabit açık)
  STATE_CHARGING,         // Şarj Oluyor (Mavi LED yavaşça yanıp sönüyor)
  STATE_ERROR             // Hata Var (Kırmızı LED hızlıca yanıp sönüyor + Buzzer ötüyor)
};

VehicleState currentVehicleState = STATE_IDLE; // Varsayılan durum
```

---

## 4. Adım Adım Örnek Uygulama Kodu

Bu mantığı birleştiren, tamamen non-blocking çalışan Arduino kodunu inceleyelim. Kodu anlamak için aşağıdaki bağlantıdan kaynak dosyaya gidebilirsiniz:
👉 [NonBlockingIndicator.ino](./NonBlockingIndicator.ino)

### Kodun Çalışma Mantığı

1. **Girişlerin Okunması:** Loop içerisinde butonlar veya sensör verileri okunarak aracın durumu değiştirilir (Örneğin hata butonu durumunu `STATE_ERROR` yapar).
2. **Durum Seçimi (`switch-case`):** Aktif olan duruma göre LED ve buzzer'ın yanıp sönme hızları (`interval`) dinamik olarak belirlenir.
3. **Zaman Kontrolü (`millis()`):** Belirlenen `interval` süresine göre LED'in ve Buzzer'ın durumu `delay()` olmadan değiştirilir.

---

## 5. Uygulama ve Ödev Soruları

Bu yapıyı tam olarak kavramak için şu soruları kendiniz yanıtlamaya çalışın veya kod üzerinde deneyin:
1. `unsigned long` yerine normal `long` veya `int` veri tipi kullansaydık `millis()` taşma yaptığında ne gibi bir sorunla karşılaşırdık?
2. Hata durumunda (`STATE_ERROR`) buzzer'ın kesik kesik (bip - bip - bip) ötmesini non-blocking olarak nasıl sağlayabiliriz?
3. Kodda durum geçişlerini simüle etmek için seri porttan (`Serial.read()`) karakter okuyarak durum değiştiren bir mantık ekleyebilir miyiz?

---

> [!TIP]
> **Önemli Tavsiye:** Gömülü yazılım projelerinde kodunuzun her zaman duyarlı (responsive) kalmasını istiyorsanız `delay()` fonksiyonunu tamamen unutun! Projenizin ilerleyen aşamalarında buton arkası arkasına basmaları (debounce), sensör okumaları ve ekran güncellemeleri de hep bu `millis()` mantığı ile yapılacaktır.
