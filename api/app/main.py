from fastapi import FastAPI

from app.dominios.acesso.rotas import router as acesso
from app.dominios.funcionarios.rotas import router as funcionarios
from app.dominios.sistema.rotas import router as sistema

app = FastAPI(
    title="Piki API",
    version="0.2.0",
    description="API da nova versão do Piki.",
)

app.include_router(sistema)
app.include_router(acesso)
app.include_router(funcionarios)
