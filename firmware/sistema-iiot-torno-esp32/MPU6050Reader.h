#ifndef MPU6050_READER_H
#define MPU6050_READER_H

#include <Arduino.h>
#include <Wire.h>

#define MPU6050_ADDR 0x68
#define MPU6050_REG_ACCEL_XOUT_H 0x3B
#define MPU6050_REG_TEMP_OUT_H 0x41

class MPU6050Reader {
public:
    bool begin() {
        Wire.beginTransmission(MPU6050_ADDR);
        Wire.write(0x6B);
        Wire.write(0x00);
        if (Wire.endTransmission() != 0) {
            Serial.println("Error: MPU6050 no detectado");
            return false;
        }
        Serial.println("MPU6050 inicializado correctamente");
        return true;
    }

    void read() {
        Wire.beginTransmission(MPU6050_ADDR);
        Wire.write(MPU6050_REG_ACCEL_XOUT_H);
        Wire.endTransmission(false);
        Wire.requestFrom(MPU6050_ADDR, (uint8_t)14);

        if (Wire.available() < 14) return;

        int16_t axRaw = Wire.read() << 8 | Wire.read();
        int16_t ayRaw = Wire.read() << 8 | Wire.read();
        int16_t azRaw = Wire.read() << 8 | Wire.read();
        int16_t tempRaw = Wire.read() << 8 | Wire.read();

        _ax = axRaw / 16384.0;
        _ay = ayRaw / 16384.0;
        _az = azRaw / 16384.0;
        _temp = (tempRaw / 340.0) + 36.53;

        Wire.read(); Wire.read(); Wire.read(); Wire.read();
    }

    float getTemperatura() { return _temp; }
    float getAceleracionX() { return _ax; }
    float getAceleracionY() { return _ay; }
    float getAceleracionZ() { return _az; }

private:
    float _ax = 0, _ay = 0, _az = 0;
    float _temp = 0;
};

#endif
