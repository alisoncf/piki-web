from fastapi import FastAPI

from app.dominios.acesso.rotas import router as acesso
from app.dominios.caixa.rotas import router as caixa
from app.dominios.cidades.rotas import router as cidades
from app.dominios.clientes.rotas import router as clientes
from app.dominios.empresas.rotas import router as empresas
from app.dominios.enderecos.rotas import router as enderecos
from app.dominios.entradas.rotas import router as entradas
from app.dominios.estoque.rotas import router as estoque
from app.dominios.financeiro.rotas import router as financeiro
from app.dominios.fornecedores.rotas import router as fornecedores
from app.dominios.funcionarios.rotas import router as funcionarios
from app.dominios.produtos.rotas import router as produtos
from app.dominios.receber.rotas import router as receber
from app.dominios.fiscal.rotas import router as fiscal
from app.dominios.sistema.rotas import router as sistema
from app.dominios.vendas.rotas import router as vendas

app = FastAPI(
    title="Piki API",
    version="0.2.0",
    description="API da nova versão do Piki.",
)

app.include_router(sistema)
app.include_router(acesso)
app.include_router(empresas)
app.include_router(funcionarios)
app.include_router(cidades)
app.include_router(clientes)
app.include_router(enderecos)
app.include_router(fornecedores)
app.include_router(produtos)
app.include_router(estoque)
app.include_router(entradas)
app.include_router(caixa)
app.include_router(financeiro)
app.include_router(vendas)
app.include_router(receber)
app.include_router(fiscal)
