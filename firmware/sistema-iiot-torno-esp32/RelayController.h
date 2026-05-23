#ifndef RELAY_CONTROLLER_H
#define RELAY_CONTROLLER_H

#include <Arduino.h>

class RelayController {
public:
    RelayController(int pin) : _pin(pin), _state(false) {}

    void begin() {
        pinMode(_pin, OUTPUT);
        digitalWrite(_pin, LOW);
    }

    void setRelay(bool active) {
        if (active != _state) {
            _state = active;
            digitalWrite(_pin, active ? HIGH : LOW);
            Serial.print("Relevador: ");
            Serial.println(active ? "ACTIVADO (PARO)" : "DESACTIVADO");
        }
    }

    bool isActive() { return _state; }

private:
    int _pin;
    bool _state;
};

#endif
