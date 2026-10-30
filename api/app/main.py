from fastapi import FastAPI

from app.routers import saude

app = FastAPI(
    title="Piki API",
    version="0.1.0",
    description="API da nova versão do Piki. Migração gradual do sistema VB6.",
)

app.include_router(saude.router)
