from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import alertas, hardware, predicciones, registros, telemetria, ws


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Sistema IIoT - Torno CNC",
    description="Backend para mantenimiento predictivo y control de seguridad de torno CNC",
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetria.router)
app.include_router(alertas.router)
app.include_router(hardware.router)
app.include_router(ws.router)
app.include_router(registros.router)
app.include_router(predicciones.router)
