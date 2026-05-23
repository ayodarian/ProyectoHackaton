#ifndef RELAY_CONTROLLER_H
#define RELAY_CONTROLLER_H

#include <Arduino.h>
#include "config.h"

class RelayController {
public:
    void begin() {
        pinMode(RELAY_PIN, OUTPUT);
        pinMode(LED_PIN, OUTPUT);
        digitalWrite(RELAY_PIN, LOW);
        digitalWrite(LED_PIN, LOW);
    }

    void setParo(bool activo) {
        digitalWrite(RELAY_PIN, activo ? HIGH : LOW);
        digitalWrite(LED_PIN, activo ? HIGH : LOW);
        Serial.print("{\"type\":\"status\",\"paro_emergencia\":");
        Serial.print(activo ? "true" : "false");
        Serial.println("}");
    }

    bool isActive() {
        return digitalRead(RELAY_PIN) == HIGH;
    }
};

#endif
