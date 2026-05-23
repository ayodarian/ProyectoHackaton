#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#include "WifiManager.h"
#include "MPU6050Reader.h"
#include "RelayController.h"
#include "Simulation.h"
#include "WebSocketClient.h"

const char* SSID = "IIoT-Torno";
const char* PASSWORD = "torno2024";
const char* SERVER_HOST = "192.168.1.100";
const uint16_t SERVER_PORT = 8000;

const int BOTON_SIMULACION = 4;
const int LED_PIN = 19;

WifiManager wifiManager(SSID, PASSWORD, SERVER_HOST, SERVER_PORT);
MPU6050Reader mpuReader;
RelayController relayController(18);
Simulation simulation;
IIoTWebSocket wsClient(SERVER_HOST, SERVER_PORT, 1);

unsigned long lastTelemetrySend = 0;
const unsigned long TELEMETRY_INTERVAL = 2000;
bool simulationMode = false;
bool paroEmergencia = false;

void onParoChange(bool paro) {
    paroEmergencia = paro;
    relayController.setRelay(paro);
    digitalWrite(LED_PIN, paro ? HIGH : LOW);
    Serial.print("Paro de emergencia via WS: ");
    Serial.println(paro ? "ACTIVADO" : "DESACTIVADO");
}

void setup() {
    Serial.begin(115200);
    pinMode(BOTON_SIMULACION, INPUT_PULLUP);
    pinMode(LED_PIN, OUTPUT);

    Wire.begin(21, 22);
    mpuReader.begin();
    relayController.begin();
    wifiManager.connect();

    wsClient.setCallback(onParoChange);
    wsClient.begin();

    digitalWrite(LED_PIN, LOW);
    Serial.println("Sistema IIoT Torno CNC iniciado");
}

void loop() {
    wifiManager.checkConnection();
    wsClient.loop();

    if (digitalRead(BOTON_SIMULACION) == LOW) {
        simulationMode = !simulationMode;
        simulation.reset();
        Serial.print("Modo simulacion: ");
        Serial.println(simulationMode ? "ACTIVADO" : "DESACTIVADO");
        delay(500);
    }

    float temp, ax, ay, az;

    if (simulationMode) {
        simulation.step();
        temp = simulation.getTemperatura();
        ax = simulation.getVibracionX();
        ay = simulation.getVibracionY();
        az = simulation.getVibracionZ();
    } else {
        mpuReader.read();
        temp = mpuReader.getTemperatura();
        ax = mpuReader.getAceleracionX();
        ay = mpuReader.getAceleracionY();
        az = mpuReader.getAceleracionZ();
    }

    Serial.print("T: "); Serial.print(temp);
    Serial.print("C  V: "); Serial.print(ax);
    Serial.print(", "); Serial.print(ay);
    Serial.print(", "); Serial.println(az);

    if (millis() - lastTelemetrySend >= TELEMETRY_INTERVAL) {
        if (wifiManager.sendTelemetry(1, temp, ax, ay, az)) {
            lastTelemetrySend = millis();
        }
    }

    if (!wsClient.isConnected()) {
        bool paro = wifiManager.checkEmergencyStop();
        if (paro != paroEmergencia) {
            paroEmergencia = paro;
            relayController.setRelay(paro);
            digitalWrite(LED_PIN, paro ? HIGH : LOW);
        }
    }

    delay(100);
}
