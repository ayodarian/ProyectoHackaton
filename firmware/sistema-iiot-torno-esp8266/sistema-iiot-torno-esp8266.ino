#include <Arduino.h>
#include "config.h"
#include "PotReader.h"
#include "SerialComm.h"
#include "RelayController.h"
#include "Simulation.h"

PotReader potReader;
SerialComm serialComm;
RelayController relayController;
Simulation simulation;

unsigned long lastTelemetry = 0;
bool paroEmergencia = false;

void setup() {
    serialComm.begin();
    potReader.begin();
    relayController.begin();
    pinMode(BOTON_SIMULACION, INPUT_PULLUP);

    Serial.println("{\"type\":\"status\",\"message\":\"ESP8266 IIoT iniciado\"}");
}

void loop() {
    if (digitalRead(BOTON_SIMULACION) == LOW) {
        delay(300);
        simulation.toggle();
    }

    bool cmdParo;
    if (serialComm.readCommand(cmdParo)) {
        if (cmdParo != paroEmergencia) {
            paroEmergencia = cmdParo;
            relayController.setParo(paroEmergencia);
        }
    }

    if (millis() - lastTelemetry >= TELEMETRY_INTERVAL_MS) {
        lastTelemetry = millis();

        float temperatura, vib_total;

        if (simulation.isActive()) {
            simulation.step();
            temperatura = simulation.getTemperatura();
            vib_total = simulation.getVibracion();
        } else {
            temperatura = potReader.readTemperatura();
            vib_total = potReader.readVibracion();
        }

        serialComm.sendTelemetry(temperatura, vib_total);
    }

    delay(50);
}
