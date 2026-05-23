from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./sistema_iiot.db"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    polling_interval: int = 5
    temp_alerta_amarilla: float = 38.0
    temp_emergencia_roja: float = 40.0
    vibracion_alerta_amarilla: float = 3.0
    vibracion_emergencia_roja: float = 4.0
    ventana_analisis: int = 50
    intervalo_guardado_amarillo: int = 10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
