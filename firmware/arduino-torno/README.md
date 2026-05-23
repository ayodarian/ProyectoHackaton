# Conexión del prototipo físico — Arduino Uno + DHT11 + Potenciómetro

## 1. Conexiones eléctricas

| Componente | Pin Arduino |
|---|---|
| Potenciómetro (centro) | **A0** |
| DHT11 (DATA) | **A1** |
| DHT11 (VCC) | **5V** |
| DHT11 (GND) | **GND** |
| Motor paso a paso 28BYJ-48 → ULN2003 IN1 | **4** |
| ULN2003 IN2 | **5** |
| ULN2003 IN3 | **6** |
| ULN2003 IN4 | **7** |
| Relé (señal) | **8** |
| LED Verde (ánodo) | **11** |
| LED Rojo (ánodo) | **12** |
| USB | A la laptop |

DHT11 necesita resistencia pull-up 10kΩ entre DATA y VCC.

## 2. Subir el firmware

1. Abrir `firmware/arduino-torno/arduino-torno.ino` en Arduino IDE
2. Conectar Arduino por USB
3. Tools → Board → **Arduino Uno**
4. Tools → Port → seleccionar el puerto
5. Subir (→)

## 3. Encontrar el puerto

```bash
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

Si sale `Permission denied`:
```bash
sudo usermod -a -G dialout $USER
# cerrar sesión y volver a entrar
```

## 4. Configurar el gateway

Editar `backend/serial_gateway/config.yml` con el puerto correcto:
```yaml
devices:
  - port: /dev/ttyUSB0    # o ttyACM0
    torno_id: 1
    baudrate: 9600
```

## 5. Arrancar todo (automático)

```bash
bash scripts/iniciar_todo.sh
```

O manual (3 terminales):

```bash
# Terminal 1
cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2
cd backend && python3 serial_gateway/gateway.py

# Terminal 3
cd frontend && python3 -m http.server 3000
```

Abrir `http://localhost:3000` en el navegador.

## 6. Comportamiento

- Cada ~2s el Arduino envía temperatura (DHT11) y vibración (potenciómetro)
- Si temp > 40°C o carga > 900 → emergencia local (relé OFF, LED rojo)
- También se puede disparar emergencia remota desde el servidor
- Comando `R` por Serial reanuda el sistema
