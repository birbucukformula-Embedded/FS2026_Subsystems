# Araştırma Notları — Görev 3: Sensör Gürültü Filtreleme

## 1. C Dilinde Pointer'lar ve Diziler
- **Pointer nedir:** Bir değişkenin kendisini değil, o değişkenin bellekte durduğu **adresi** tutan değişken türüdür (`float* p` gibi). `MovingAverage_Update(MovingAverageFilter_t* filter, ...)` fonksiyonunda struct'ı değer olarak (`by value`) değil, adres olarak (`by reference`, yani pointer ile) aldık.
- **Neden pointer kullandık:** Eğer struct'ı değer olarak alsaydık, fonksiyon içinde struct'ın bir **kopyası** oluşurdu; fonksiyon içinde yapılan değişiklikler (buffer'a yeni örnek ekleme, index güncelleme) çağıran tarafın orijinal struct'ına hiç yansımazdı. Pointer kullanınca fonksiyon doğrudan orijinal struct'ın adresine erişip içeriğini kalıcı olarak günceller — hem doğru çalışır hem de gömülü sistemlerde (RAM kısıtlı) gereksiz kopyalamadan kaçınmış oluruz.
- **Diziler ve pointer ilişkisi:** C'de bir dizinin adı, aslında dizinin ilk elemanının adresine (pointer'ına) çevrilebilir. `filter->buffer[filter->index]` yazımı, arka planda `*(filter->buffer + filter->index)` ile aynı işi yapar — dizi indeksleme aslında pointer aritmetiğinin kısayolu.

## 2. Sabit Boyutlu Dizilerde Veri Kaydırma — Circular Buffer (Dairesel Tampon) Mantığı
- **Saf/naif yöntem (kullanmadık):** Her yeni örnek geldiğinde dizideki tüm elemanları bir sola kaydırıp yeni elemanı sona eklemek. Bu yöntem her seferinde N elemanı kopyalamayı gerektirir (O(N) işlem) — N büyüdükçe yavaşlar.
- **Bizim kullandığımız yöntem (circular/ring buffer):** Dizi hiç kaydırılmaz. Bunun yerine bir `index` değişkeni tutulur; yeni örnek her geldiğinde `buffer[index]` üzerine yazılır, sonra `index = (index + 1) % N` ile bir sonraki hücreye geçilir. `index`, `N-1`'e ulaştığında `%` (mod) operatörü sayesinde otomatik olarak `0`'a döner — yani dizi "dairesel" gibi davranır. Bu yöntem her örnek için sadece 1 işlem gerektirir (O(1)), kaydırmaya göre çok daha hızlıdır.
- **Toplamı canlı tutma optimizasyonu:** Ortalamayı her seferinde 10 elemanı toplayıp bulmak yerine, `sum` değişkeninde güncel toplamı tutuyoruz: yeni değer eklenirken önce üzerine yazılacak eski değeri toplamdan çıkarıyoruz, sonra yeni değeri ekliyoruz. Böylece ortalama hesaplamak da O(1) sürede oluyor.

## 3. Moving Average (Hareketli Ortalama) Filtresi
- Son N (bizde 10) örneğin aritmetik ortalamasını çıktı olarak verir: `ortalama = (x1 + x2 + ... + x10) / 10`.
- Rastgele gürültü genelde gerçek değerin etrafında hem pozitif hem negatif yönde sapar; birden fazla örneğin ortalamasını almak bu sapmaların birbirini götürmesini sağlar ve gerçek eğilim (trend) ortaya çıkar.
- Dezavantajı: pencere boyutu (N) büyüdükçe gürültü daha iyi temizlenir ama gerçek sinyaldeki ani değişikliklere tepki de o kadar gecikir (çünkü eski değerler hâlâ ortalamayı etkiliyor).

## 4. Low-Pass Filter (Alçak Geçiren Filtre) — Matematiksel Formül
- Formül: **Y_yeni = (A × X_yeni) + ((1 − A) × Y_eski)**
  - `X_yeni`: sensörden gelen yeni ham örnek.
  - `Y_eski`: filtrenin bir önceki çıktısı.
  - `A (alpha)`: 0 ile 1 arasında bir katsayı.
- Bu formül aslında "üstel hareketli ortalama" (Exponential Moving Average) olarak da bilinir — Moving Average'dan farklı olarak geçmiş TÜM örnekleri (üstel olarak azalan ağırlıkla) hesaba katar, ama hafızada sadece tek bir değer (`Y_eski`) tutması yeterlidir; 10 elemanlık bir diziye ihtiyaç yoktur.
- **Alpha seçimi bir denge (trade-off):**
  - Alpha büyük (1'e yakın) → filtre yeni veriye hızlı tepki verir ama gürültüyü az temizler.
  - Alpha küçük (0'a yakın) → filtre gürültüyü çok iyi temizler ama gerçek değişikliklere tepkisi gecikmeli olur.
  - Bizim demo kodunda `alpha = 0.2` seçildi — gürültüyü belirgin şekilde azaltırken sinyaldeki değişime de makul sürede tepki veriyor.
