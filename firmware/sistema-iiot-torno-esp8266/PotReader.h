#ifndef POT_READER_H
#define POT_READER_H

#include <Arduino.h>
#include "config.h"

class PotReader {
public:
    void begin() {
        pinMode(POT_PIN, INPUT);
    }

    int readRaw() {
        return analogRead(POT_PIN);
    }

    float readTemperatura() {
        int raw = readRaw();
        return TEMP_MIN + (raw / (float)POT_MAX) * (TEMP_MAX - TEMP_MIN);
    }

    float readVibracion() {
        int raw = readRaw();
        return VIB_MIN + (raw / (float)POT_MAX) * (VIB_MAX - VIB_MIN);
    }
};

#endif
