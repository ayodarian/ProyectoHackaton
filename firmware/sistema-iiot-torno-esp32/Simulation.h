#ifndef SIMULATION_H
#define SIMULATION_H

#include <Arduino.h>

class Simulation {
public:
    Simulation()
        : _temp(62.0), _vibX(1.1), _vibY(1.0), _vibZ(0.9), _stepCount(0), _active(false) {}

    void reset() {
        _temp = 62.0;
        _vibX = 1.1;
        _vibY = 1.0;
        _vibZ = 0.9;
        _stepCount = 0;
        _active = !_active;
    }

    void step() {
        if (!_active) return;

        _stepCount++;

        float incrementoTemp = (_stepCount * 2.0) / 10.0;
        float incrementoVib = (_stepCount * 0.5) / 10.0;

        _temp = 62.0 + incrementoTemp + random(-5, 6) * 0.1;
        _vibX = 1.1 + incrementoVib + random(-10, 11) * 0.01;
        _vibY = 1.0 + incrementoVib * 0.8 + random(-10, 11) * 0.01;
        _vibZ = 0.9 + incrementoVib * 0.6 + random(-10, 11) * 0.01;

        _temp = constrain(_temp, 25.0, 100.0);
        _vibX = constrain(_vibX, 0.0, 6.0);
        _vibY = constrain(_vibY, 0.0, 5.0);
        _vibZ = constrain(_vibZ, 0.0, 4.0);
    }

    float getTemperatura() { return _temp; }
    float getVibracionX() { return _vibX; }
    float getVibracionY() { return _vibY; }
    float getVibracionZ() { return _vibZ; }

private:
    float _temp, _vibX, _vibY, _vibZ;
    int _stepCount;
    bool _active;
};

#endif
