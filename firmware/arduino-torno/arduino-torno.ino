#include <Stepper.h>
#include <DHT.h>

const int pasosPorVuelta = 2048;
Stepper miMotor(pasosPorVuelta, 4, 6, 5, 7);

#define DHTPIN A1
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const int pinRelevador = 8;
const int pinPot = A0;
const int pinLedVerde = 11;
const int pinLedRojo = 12;

const int TORNO_ID = 1;
const float VIB_MAX = 5.0;
const unsigned long INTERVALO_MS = 2000;

bool emergenciaActiva = false;
unsigned long ultimoEnvio = 0;

void setup() {
  pinMode(pinRelevador, OUTPUT);
  pinMode(pinLedVerde, OUTPUT);
  pinMode(pinLedRojo, OUTPUT);

  digitalWrite(pinRelevador, HIGH);
  digitalWrite(pinLedVerde, HIGH);
  digitalWrite(pinLedRojo, LOW);

  miMotor.setSpeed(10);
  dht.begin();

  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'E' && !emergenciaActiva) {
      activarEmergencia();
    } else if (cmd == 'R' && emergenciaActiva) {
      desactivarEmergencia();
    }
  }

  if (!emergenciaActiva) {
    for (int i = 0; i < 50; i++) {
      miMotor.step(1);
    }
  } else {
    delay(100);
  }

  if (millis() - ultimoEnvio >= INTERVALO_MS) {
    ultimoEnvio = millis();

    float temperatura = dht.readTemperature();
    int lecturaCarga = analogRead(pinPot);
    float vib_total = (lecturaCarga / 1023.0) * VIB_MAX;

    if (isnan(temperatura)) {
      temperatura = 0;
    }

    if ((lecturaCarga > 900 || temperatura > 40.0) && !emergenciaActiva) {
      activarEmergencia();
    }

    Serial.print("{\"type\":\"telemetry\",\"torno_id\":");
    Serial.print(TORNO_ID);
    Serial.print(",\"temperatura\":");
    Serial.print(temperatura, 1);
    Serial.print(",\"vib_total\":");
    Serial.print(vib_total, 2);
    Serial.println("}");
  }
}

void activarEmergencia() {
  emergenciaActiva = true;
  digitalWrite(pinRelevador, LOW);
  digitalWrite(pinLedVerde, LOW);
  digitalWrite(pinLedRojo, HIGH);
  Serial.println("{\"type\":\"status\",\"message\":\"EMERGENCIA activada\"}");
}

void desactivarEmergencia() {
  emergenciaActiva = false;
  digitalWrite(pinRelevador, HIGH);
  digitalWrite(pinLedVerde, HIGH);
  digitalWrite(pinLedRojo, LOW);
  Serial.println("{\"type\":\"status\",\"message\":\"Sistema reanudado\"}");
}
