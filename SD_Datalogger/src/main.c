#include "sd_file_system.h"
#include "can_parser_buffer.h"

#include <stdio.h>

/* Gercek donanimda while(1) sonsuz donguye girip arac kapanana kadar veri toplanir.
 * Biz burada PC'de test edebilmek icin sabit sayida CAN paketi uretip duruyoruz. */
#define TEST_FRAME_COUNT 500

int main(void) {
    /* 1. SD kart baslatilir (mount) */
    if (!SD_Logger_Init()) {
        printf("%s\n", SD_Logger_GetStatusString(SD_Logger_GetLastStatus()));
        return 1;
    }

    /* 2. CSV dosyasi acilir (ilk kez aciliyorsa basligi otomatik yazar) */
    if (!SD_Logger_OpenCSV("telemetry_log.csv")) {
        printf("%s\n", SD_Logger_GetStatusString(SD_Logger_GetLastStatus()));
        return 1;
    }

    /* 3. Buffer sistemi sifirlanir */
    CAN_Buffer_Init();

    /* 4. Dongude sanal CAN verisi uretilip buffera atilir; buffer 512 bayti gecince
     *    can_parser_buffer.c otomatik olarak SD_Logger_Write() cagirir. */
    for (int i = 0; i < TEST_FRAME_COUNT; i++) {
        CAN_DataFrame_t frame;
        CAN_SimulateData(&frame);

        if (!CAN_Buffer_Push(&frame)) {
            printf("Buffer -> SD yazma hatasi: %s\n",
                   SD_Logger_GetStatusString(SD_Logger_GetLastStatus()));
            break;
        }
    }

    /* 5. Donguden cikildiginda, buffer'da 512 bayta ulasmamis kalan veri varsa
     *    zorla diske yazilir ve f_sync tetiklenir. */
    if (!CAN_Buffer_Flush()) {
        printf("Buffer flush hatasi: %s\n",
               SD_Logger_GetStatusString(SD_Logger_GetLastStatus()));
    }

    /* 6. Dosya guvenli sekilde kapatilir */
    SD_Logger_Close();

    printf("Test tamamlandi: %d CAN paketi telemetry_log.csv dosyasina yazildi.\n",
           TEST_FRAME_COUNT);

    return 0;
}
