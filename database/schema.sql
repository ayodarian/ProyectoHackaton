CREATE TABLE IF NOT EXISTS telemetria_torno (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    torno_id INTEGER NOT NULL,
    temperatura REAL NOT NULL,
    vibracion_x REAL NOT NULL,
    vibracion_y REAL NOT NULL,
    vibracion_z REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alertas_mantenimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    torno_id INTEGER NOT NULL,
    tipo_alerta VARCHAR(50) NOT NULL,
    descripcion TEXT,
    atendida INTEGER DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telemetria_torno_id ON telemetria_torno(torno_id);
CREATE INDEX idx_telemetria_timestamp ON telemetria_torno(timestamp);
CREATE INDEX idx_alertas_torno_id ON alertas_mantenimiento(torno_id);
CREATE INDEX idx_alertas_atendida ON alertas_mantenimiento(atendida);
