#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

class WifiManager {
public:
    WifiManager(const char* ssid, const char* password, const char* host, uint16_t port)
        : _ssid(ssid), _password(password), _host(host), _port(port) {}

    void connect() {
        WiFi.begin(_ssid, _password);
        Serial.print("Conectando WiFi");
        int attempts = 0;
        while (WiFi.status() != WL_CONNECTED && attempts < 40) {
            delay(500);
            Serial.print(".");
            attempts++;
        }
        if (WiFi.status() == WL_CONNECTED) {
            Serial.println("\nWiFi conectado. IP: " + WiFi.localIP().toString());
        } else {
            Serial.println("\nError: No se pudo conectar WiFi");
        }
    }

    void checkConnection() {
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("WiFi desconectado, reconectando...");
            connect();
        }
    }

    bool sendTelemetry(int tornoId, float temp, float vx, float vy, float vz) {
        if (WiFi.status() != WL_CONNECTED) return false;

        HTTPClient http;
        String url = "http://" + String(_host) + ":" + String(_port) + "/api/telemetria";
        http.begin(url);
        http.addHeader("Content-Type", "application/json");

        JsonDocument doc;
        doc["torno_id"] = tornoId;
        doc["temperatura"] = temp;
        doc["vibracion_x"] = vx;
        doc["vibracion_y"] = vy;
        doc["vibracion_z"] = vz;

        String payload;
        serializeJson(doc, payload);

        int httpCode = http.POST(payload);
        bool success = (httpCode == 201 || httpCode == 200);
        if (!success) {
            Serial.print("Error enviando telemetria: HTTP ");
            Serial.println(httpCode);
        }
        http.end();
        return success;
    }

    bool checkEmergencyStop() {
        if (WiFi.status() != WL_CONNECTED) return false;

        HTTPClient http;
        String url = "http://" + String(_host) + ":" + String(_port) + "/api/control-hardware";
        http.begin(url);
        http.addHeader("Content-Type", "application/json");

        int httpCode = http.GET();
        if (httpCode == 200) {
            String response = http.getString();
            JsonDocument doc;
            deserializeJson(doc, response);
            bool paro = doc["paro_emergencia"] | false;
            http.end();
            return paro;
        }
        http.end();
        return false;
    }

private:
    const char* _ssid;
    const char* _password;
    const char* _host;
    uint16_t _port;
};

#endif
