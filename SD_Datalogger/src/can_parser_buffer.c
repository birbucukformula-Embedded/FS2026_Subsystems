#include "can_parser_buffer.h"
#include "sd_file_system.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* =========================================================================================
 * 2. KİŞİ GÖREVİ: CAN VERİ SİMÜLASYONU, CSV FORMATLAMA VE SEKTÖR BUFFER YÖNETİMİ
 * ========================================================================================= */

/* 512 Baytlık Sektör Buffer (RAM) ve imleç indisi */
static char     s_sector_buffer[CAN_BUFFER_SECTOR_SIZE];
static uint32_t s_buffer_idx = 0;

/* Simülasyon durum değişkenleri */
static uint32_t s_sim_timestamp_ms = 0;
static float    s_sim_speed        = 0.0f;
static float    s_sim_temp         = 35.0f;
static uint8_t  s_sim_error        = 0;

void CAN_SimulateData(CAN_DataFrame_t* frame) {
    if (frame == NULL) return;

    /* Zaman damgası her çağrıda 10 ms (100 Hz CAN paketi) ilerlesin */
    s_sim_timestamp_ms += 10;
    frame->timestamp_ms = s_sim_timestamp_ms;

    /* Hız senaryosu: 0 km/h'den 115 km/h'ye kadar hızlanma ve yavaşlama */
    s_sim_speed += 0.45f;
    if (s_sim_speed > 115.0f) {
        s_sim_speed = 25.0f; /* Viraj yavaşlaması simülasyonu */
    }
    frame->speed_kmh = s_sim_speed;

    /* Sıcaklık senaryosu: Yavaşça ısınma (35.0 C -> 85.0 C) */
    s_sim_temp += 0.05f;
    if (s_sim_temp > 85.0f) {
        s_sim_temp = 75.0f; /* Soğutma devreye giriyor */
    }
    frame->engine_temp_c = s_sim_temp;

    /* Arıza kodu senaryosu: Her 200 pakette 1 anlık uyarı kodu (örn: Hata kodu 12) */
    if ((s_sim_timestamp_ms % 2000) == 0) {
        s_sim_error = 12;
    } else {
        s_sim_error = 0;
    }
    frame->error_code = s_sim_error;
}

int CAN_FormatCSV(const CAN_DataFrame_t* frame, char* out_str, size_t max_len) {
    if (frame == NULL || out_str == NULL || max_len == 0) {
        return -1;
    }

    /* "Timestamp,Speed,Temp,ErrorCode\r\n" formatında CSV satırı oluşturulur */
    int len = snprintf(out_str, max_len, "%lu,%.2f,%.2f,%u\r\n",
                       (unsigned long)frame->timestamp_ms,
                       frame->speed_kmh,
                       frame->engine_temp_c,
                       (unsigned int)frame->error_code);

    if (len < 0 || (size_t)len >= max_len) {
        return -1; /* Formatlama hatası veya tampon taşması */
    }

    return len;
}

const char* CAN_GetCSVHeader(void) {
    return CAN_CSV_HEADER_STRING;
}

void CAN_Buffer_Init(void) {
    memset(s_sector_buffer, 0, sizeof(s_sector_buffer));
    s_buffer_idx = 0;
    s_sim_timestamp_ms = 0;
    s_sim_speed = 0.0f;
    s_sim_temp = 35.0f;
    s_sim_error = 0;
}

bool CAN_Buffer_Push(const CAN_DataFrame_t* frame) {
    if (frame == NULL) {
        return false;
    }

    char line_buf[128];
    int line_len = CAN_FormatCSV(frame, line_buf, sizeof(line_buf));
    if (line_len <= 0) {
        return false;
    }

    /* Yeni satır eklendiğinde 512 baytı aşacaksa mevcut tamponu 1. Kişinin modülüyle SD karta yaz */
    if (s_buffer_idx + (uint32_t)line_len > CAN_BUFFER_SECTOR_SIZE) {
        bool write_ok = SD_Logger_Write(s_sector_buffer, s_buffer_idx);
        if (!write_ok) {
            return false;
        }
        /* Tampon diske yazıldığı için sıfırlıyoruz */
        s_buffer_idx = 0;
    }

    /* Yeni CSV satırını RAM Sektör Buffer'a kopyala */
    memcpy(&s_sector_buffer[s_buffer_idx], line_buf, (size_t)line_len);
    s_buffer_idx += (uint32_t)line_len;

    /* Eğer tampon tam 512 bayt olduysa anında diske yaz */
    if (s_buffer_idx == CAN_BUFFER_SECTOR_SIZE) {
        bool write_ok = SD_Logger_Write(s_sector_buffer, s_buffer_idx);
        if (!write_ok) {
            return false;
        }
        s_buffer_idx = 0;
    }

    return true;
}

bool CAN_Buffer_Flush(void) {
    bool ok = true;

    /* Eğer tamponda henüz 512 bayta ulaşmamış veri varsa zorla diske yaz */
    if (s_buffer_idx > 0) {
        ok = SD_Logger_Write(s_sector_buffer, s_buffer_idx);
        s_buffer_idx = 0;
    }

    /* Fiziksel senkronizasyon (f_sync) tetiklenir */
    if (ok) {
        ok = SD_Logger_Sync();
    }

    return ok;
}

uint32_t CAN_Buffer_GetPendingBytes(void) {
    return s_buffer_idx;
}
