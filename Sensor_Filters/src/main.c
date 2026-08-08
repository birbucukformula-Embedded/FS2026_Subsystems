#include "moving_average_filter.h"
#include "low_pass_filter.h"

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define TEST_SAMPLE_COUNT   200
#define PI                  3.14159265f

/* Gercek bir sensor yerine, sanal olarak "gurultulu" bir sinyal uretiyoruz:
 * temiz bir sinus dalgasi (gercek fiziksel deger, orn: sicaklik dalgalanmasi)
 * ustune, -5..+5 arasi rastgele gurultu (parazit) ekliyoruz. */
static float GenerateNoisySample(int i) {
    float clean_signal = 50.0f + 20.0f * sinf(2.0f * PI * (float)i / 200.0f);
    float noise = ((float)(rand() % 1000) / 1000.0f - 0.5f) * 10.0f; /* -5..+5 */
    return clean_signal + noise;
}

int main(void) {
    MovingAverageFilter_t ma_filter;
    LowPassFilter_t       lp_filter;

    MovingAverage_Init(&ma_filter);
    LowPass_Init(&lp_filter, 0.2f); /* alpha=0.2 -> gurultuyu iyi temizler, biraz gecikmeli tepki verir */

    FILE* csv = fopen("filter_output.csv", "w");
    if (csv == NULL) {
        printf("HATA: filter_output.csv acilamadi.\n");
        return 1;
    }
    fprintf(csv, "Sample,Raw,MovingAverage,LowPass\r\n");

    double raw_sum_sq_diff = 0.0;
    double ma_sum_sq_diff  = 0.0;
    double lp_sum_sq_diff  = 0.0;

    for (int i = 0; i < TEST_SAMPLE_COUNT; i++) {
        float raw_value = GenerateNoisySample(i);

        float ma_value = MovingAverage_Update(&ma_filter, raw_value);
        float lp_value = LowPass_Update(&lp_filter, raw_value);

        fprintf(csv, "%d,%.2f,%.2f,%.2f\r\n", i, raw_value, ma_value, lp_value);

        /* Filtrelerin gurultuyu gercekten azalttigini gostermek icin, temiz sinyale
         * gore sapmanin karesini (varyansa benzer bir olcum) topluyoruz. */
        float clean_signal = 50.0f + 20.0f * sinf(2.0f * PI * (float)i / 200.0f);
        raw_sum_sq_diff += (double)((raw_value - clean_signal) * (raw_value - clean_signal));
        ma_sum_sq_diff  += (double)((ma_value  - clean_signal) * (ma_value  - clean_signal));
        lp_sum_sq_diff  += (double)((lp_value  - clean_signal) * (lp_value  - clean_signal));
    }

    fclose(csv);

    printf("Test tamamlandi: %d ornek filter_output.csv dosyasina yazildi.\n\n", TEST_SAMPLE_COUNT);
    printf("Gercek sinyale gore ortalama kare hata (kucuk = daha temiz):\n");
    printf("  Ham (filtresiz)     : %.3f\n", raw_sum_sq_diff / TEST_SAMPLE_COUNT);
    printf("  Moving Average      : %.3f\n", ma_sum_sq_diff  / TEST_SAMPLE_COUNT);
    printf("  Low-Pass Filter     : %.3f\n", lp_sum_sq_diff  / TEST_SAMPLE_COUNT);

    return 0;
}
