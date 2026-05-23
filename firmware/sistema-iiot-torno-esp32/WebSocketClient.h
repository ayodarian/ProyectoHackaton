#ifndef WEBSOCKET_CLIENT_H
#define WEBSOCKET_CLIENT_H

#include <Arduino.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

class IIoTWebSocket {
public:
    IIoTWebSocket(const char* host, uint16_t port, int tornoId)
        : _host(host), _port(port), _tornoId(tornoId), _paroEmergencia(false), _connected(false) {}

    void setCallback(void (*callback)(bool paro)) {
        _onParoChange = callback;
    }

    void begin() {
        _ws.begin(_host, _port, "/ws/" + String(_tornoId));
        _ws.onEvent([this](WStype_t type, uint8_t* payload, size_t length) {
            _onEvent(type, payload, length);
        });
        _ws.setReconnectInterval(3000);
    }

    void loop() {
        _ws.loop();
    }

    bool isConnected() { return _connected; }
    bool getParoEmergencia() { return _paroEmergencia; }

private:
    WebSocketsClient _ws;
    const char* _host;
    uint16_t _port;
    int _tornoId;
    bool _paroEmergencia;
    bool _connected;
    void (*_onParoChange)(bool) = nullptr;

    void _onEvent(WStype_t type, uint8_t* payload, size_t length) {
        switch (type) {
            case WStype_DISCONNECTED:
                _connected = false;
                Serial.println("WS Desconectado");
                break;

            case WStype_CONNECTED:
                _connected = true;
                Serial.println("WS Conectado al servidor");
                break;

            case WStype_TEXT: {
                JsonDocument doc;
                deserializeJson(doc, (const char*)payload);

                const char* msgType = doc["type"];
                if (strcmp(msgType, "estado") == 0) {
                    JsonObject data = doc["data"];
                    bool nuevoParo = data["paro_emergencia"] | false;
                    if (nuevoParo != _paroEmergencia) {
                        _paroEmergencia = nuevoParo;
                        if (_onParoChange) {
                            _onParoChange(_paroEmergencia);
                        }
                    }
                }
                break;
            }

            default:
                break;
        }
    }
};

#endif
