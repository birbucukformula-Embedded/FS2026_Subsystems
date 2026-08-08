/**
 * Görev 4: Hata ve Durum Göstergeleri (Non-Blocking LED/Buzzer)
 * 
 * Bu proje, delay() kullanmadan millis() fonksiyonu ve bir Durum Makinesi (State Machine)
 * yardımıyla aracın durumuna göre LED ve Buzzer kontrolünü gerçekleştirir.
 */

// Pin Tanımlamaları
const int PIN_LED_GREEN  = 2;  // Sürüşe Hazır Göstergesi (Ready to Drive)
const int PIN_LED_BLUE   = 3;  // Şarj Oluyor Göstergesi (Charging)
const int PIN_LED_RED    = 4;  // Hata Göstergesi (Error)
const int PIN_BUZZER     = 5;  // Uyarı Buzzer'ı

// Araç Durumları (State Machine Enums)
enum VehicleState {
  STATE_IDLE,             // Araç beklemede. Işıklar kapalı.
  STATE_READY_TO_DRIVE,   // Sürüşe hazır. Yeşil LED sürekli açık, buzzer sessiz.
  STATE_CHARGING,         // Şarj oluyor. Mavi LED yavaşça yanıp söner.
  STATE_ERROR             // Hata durumu. Kırmızı LED hızlı yanıp söner, Buzzer kesik kesik çalar.
};

// Aktif Araç Durumu
VehicleState currentVehicleState = STATE_IDLE;

// Non-blocking Zamanlama Değişkenleri
unsigned long previousLedMillis = 0;
unsigned long previousBuzzerMillis = 0;
unsigned long previousStateSimulationMillis = 0; // Simülasyon için durum geçiş zamanlayıcısı

// LED ve Buzzer'ın anlık durumları (Açık/Kapalı)
bool ledState = false;
bool buzzerState = false;

// Zamanlama Aralıkları (milisaniye cinsinden)
unsigned long ledInterval = 500;    // LED yanıp sönme sıklığı (dinamik değişecek)
unsigned long buzzerInterval = 150; // Buzzer bip sıklığı (dinamik değişecek)

void setup() {
  // Pin modlarını ayarla
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  // Seri haberleşmeyi başlat (Simülasyon ve takip için)
  Serial.begin(9600);
  Serial.println("Non-Blocking LED/Buzzer Sistemi Baslatildi!");
  Serial.println("Durum gecislerini izlemek icin bekleyin veya seri porttan karakter gonderin:");
  Serial.println("'i' -> Idle, 'r' -> Ready, 'c' -> Charging, 'e' -> Error");
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Durum Gecislerini Yonetmek (Kullanıcı girdisi veya otomatik simülasyon)
  handleStateTransitions(currentMillis);

  // 2. Aktif Duruma Gore Parametreleri Belirlemek (Durum Makinesi)
  // Bu switch-case blogu, sadece aktif duruma gore zaman aralıklarını ve LED secimlerini ayarlar.
  // delay() OLMADIGI icin her dongude cok hızlı sekilde calısır ve gecer.
  switch (currentVehicleState) {
    
    case STATE_IDLE:
      // Hepsi kapalı
      digitalWrite(PIN_LED_GREEN, LOW);
      digitalWrite(PIN_LED_BLUE, LOW);
      digitalWrite(PIN_LED_RED, LOW);
      noTone(PIN_BUZZER);
      break;

    case STATE_READY_TO_DRIVE:
      // Yeşil LED sürekli açık, diğerleri kapalı, buzzer kapalı
      digitalWrite(PIN_LED_GREEN, HIGH);
      digitalWrite(PIN_LED_BLUE, LOW);
      digitalWrite(PIN_LED_RED, LOW);
      noTone(PIN_BUZZER);
      break;

    case STATE_CHARGING:
      // Mavi LED yavasca yanıp sönecek, digerleri kapalı, buzzer kapalı
      digitalWrite(PIN_LED_GREEN, LOW);
      digitalWrite(PIN_LED_RED, LOW);
      noTone(PIN_BUZZER);
      
      ledInterval = 1000; // Yavaş yanıp sönme (1 saniye açık, 1 saniye kapalı)
      updateBlinkingLed(PIN_LED_BLUE, currentMillis);
      break;

    case STATE_ERROR:
      // Kırmızı LED ve Buzzer hızlıca senkronize sekilde yanıp sönecek/ötecek
      digitalWrite(PIN_LED_GREEN, LOW);
      digitalWrite(PIN_LED_BLUE, LOW);
      
      ledInterval = 150;    // Hızlı yanıp sönme (150ms açık, 150ms kapalı)
      buzzerInterval = 150; // Hızlı bip sesi
      
      updateBlinkingLed(PIN_LED_RED, currentMillis);
      updateBlinkingBuzzer(currentMillis);
      break;
  }
}

/**
 * Belirtilen LED pinini millis() ile non-blocking olarak yanıp söndürür.
 */
void updateBlinkingLed(int pin, unsigned long currentMillis) {
  if (currentMillis - previousLedMillis >= ledInterval) {
    previousLedMillis = currentMillis; // Zamanı güncelle
    ledState = !ledState;              // LED durumunu tersine çevir (HIGH ise LOW, LOW ise HIGH)
    digitalWrite(pin, ledState ? HIGH : LOW);
  }
}

/**
 * Buzzer'ı millis() ile non-blocking olarak kesik kesik (bip bip) öttürür.
 */
void updateBlinkingBuzzer(unsigned long currentMillis) {
  if (currentMillis - previousBuzzerMillis >= buzzerInterval) {
    previousBuzzerMillis = currentMillis; // Zamanı güncelle
    buzzerState = !buzzerState;           // Buzzer durumunu tersine çevir
    
    if (buzzerState) {
      tone(PIN_BUZZER, 1000); // 1000 Hz frekansında ses ver
    } else {
      noTone(PIN_BUZZER);     // Sesi kes
    }
  }
}

/**
 * Seri haberlesme veya otomatik simulasyon ile durum gecislerini kontrol eder.
 */
void handleStateTransitions(unsigned long currentMillis) {
  // A. Kullanıcı Seri Porttan Deger Gonderdi mi?
  if (Serial.available() > 0) {
    char input = Serial.read();
    VehicleState newState = currentVehicleState;
    
    if (input == 'i' || input == 'I') newState = STATE_IDLE;
    else if (input == 'r' || input == 'R') newState = STATE_READY_TO_DRIVE;
    else if (input == 'c' || input == 'C') newState = STATE_CHARGING;
    else if (input == 'e' || input == 'E') newState = STATE_ERROR;
    
    if (newState != currentVehicleState) {
      changeState(newState);
    }
    return; // Kullanıcı elle degistirdiyse otomatik simulasyonu es gec
  }

  // B. Otomatik Simulasyon (Her 7 saniyede bir durumu degistir)
  if (currentMillis - previousStateSimulationMillis >= 7000) {
    previousStateSimulationMillis = currentMillis;
    
    VehicleState nextState;
    switch (currentVehicleState) {
      case STATE_IDLE:           nextState = STATE_READY_TO_DRIVE; break;
      case STATE_READY_TO_DRIVE: nextState = STATE_CHARGING;       break;
      case STATE_CHARGING:       nextState = STATE_ERROR;          break;
      case STATE_ERROR:          nextState = STATE_IDLE;           break;
      default:                   nextState = STATE_IDLE;           break;
    }
    
    changeState(nextState);
  }
}

/**
 * Durum degistiginde temizlik yapar ve yeni durumu ekrana yazdırır.
 */
void changeState(VehicleState newState) {
  currentVehicleState = newState;
  
  // LED ve Buzzer anlık durumlarını sıfırla
  ledState = false;
  buzzerState = false;
  noTone(PIN_BUZZER);
  
  // Eski durumdan kalan pinleri temizle
  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_BLUE, LOW);
  digitalWrite(PIN_LED_RED, LOW);

  // Konsola bilgi yazdır
  Serial.print("Durum Degisti: ");
  switch (currentVehicleState) {
    case STATE_IDLE:           Serial.println("IDLE (Beklemede)"); break;
    case STATE_READY_TO_DRIVE: Serial.println("READY_TO_DRIVE (Suruse Hazır)"); break;
    case STATE_CHARGING:       Serial.println("CHARGING (Sarj Oluyor)"); break;
    case STATE_ERROR:          Serial.println("ERROR (Hata Var!)"); break;
  }
}
