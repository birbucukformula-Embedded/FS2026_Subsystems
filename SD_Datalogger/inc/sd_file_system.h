#ifndef SD_FILE_SYSTEM_H
#define SD_FILE_SYSTEM_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

/**
 * @brief SD kartı mount eder ve dosya sistemini başlatır.
 * 
 * @return true Başarılıysa
 * @return false Hata oluşursa (SD kart takılı değilse vb.)
 */
bool SD_Logger_Init(void);

/**
 * @brief Belirtilen isimde bir .csv dosyasını açar veya oluşturur.
 * 
 * @param filename Açılacak dosyanın adı (örn. "log.csv")
 * @return true Dosya başarıyla açıldıysa
 * @return false Dosya açılamazsa veya disk doluysa
 */
bool SD_Logger_OpenCSV(const char* filename);

/**
 * @brief Verilen string veriyi açık olan dosyaya yazar.
 * 
 * @param data Yazılacak karakter dizisi
 * @param len Yazılacak verinin boyutu (byte cinsinden)
 * @return true Yazma işlemi başarılıysa
 * @return false Yazma işlemi başarısızsa
 */
bool SD_Logger_Write(const char* data, size_t len);

/**
 * @brief RAM'de bekleyen veriyi (buffer) fiziksel SD karta kaydeder (f_sync).
 * 
 * @return true Eşzamanlama başarılıysa
 * @return false Eşzamanlama başarısızsa
 */
bool SD_Logger_Sync(void);

/**
 * @brief Açık olan dosyayı kapatır ve işlemleri sonlandırır.
 * 
 * @return true Kapatma başarılıysa
 * @return false Kapatma başarısızsa
 */
bool SD_Logger_Close(void);

#endif /* SD_FILE_SYSTEM_H */
