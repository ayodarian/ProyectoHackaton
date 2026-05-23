#ifndef SIMULATION_H
#define SIMULATION_H

#include <Arduino.h>
#include "config.h"

class Simulation {
public:
    Simulation() : _step(0), _active(false) {}

    void toggle() {
        _active = !_active;
        _step = 0;
    }

    bool isActive() { return _active; }

    void step() {
        if (!_active) return;
        _step++;
    }

    float getTemperatura() {
        if (!_active) return TEMP_MIN;
        float t = TEMP_MIN + (_step * 2.0f) + random(-5, 6) * 0.1f;
        return constrain(t, TEMP_MIN, TEMP_MAX);
    }

    float getVibracion() {
        if (!_active) return VIB_MIN;
        float v = VIB_MIN + (_step * 0.5f) + random(-10, 11) * 0.01f;
        return constrain(v, VIB_MIN, VIB_MAX);
    }

private:
    int _step;
    bool _active;
};

#endif
