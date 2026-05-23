#ifndef SERIAL_COMM_H
#define SERIAL_COMM_H

#include <Arduino.h>
#include "config.h"

class SerialComm {
public:
    void begin() {
        Serial.begin(SERIAL_BAUD);
    }

    void sendTelemetry(float temperatura, float vib_total) {
        Serial.print("{\"type\":\"telemetry\",\"torno_id\":");
        Serial.print(TORNO_ID);
        Serial.print(",\"temperatura\":");
        Serial.print(temperatura, 1);
        Serial.print(",\"vib_total\":");
        Serial.print(vib_total, 2);
        Serial.println("}");
    }

    bool readCommand(bool &paro) {
        if (Serial.available() <= 0) return false;

        String line = Serial.readStringUntil('\n');
        line.trim();
        if (line.length() == 0) return false;

        if (line.indexOf("\"paro_emergencia\"") >= 0) {
            paro = line.indexOf("true") >= 0;
            return true;
        }
        return false;
    }
};

#endif
