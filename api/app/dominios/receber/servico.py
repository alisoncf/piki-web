"""Regras das contas a receber: o limite de crédito do cliente e as parcelas do carnê."""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_DOWN, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominios.clientes.modelos import Cliente
from app.dominios.receber.modelos import ContaReceber, ParcelaReceber

ZERO = Decimal("0.00")
CENTAVO = Decimal("0.01")


@dataclass
class Credito:
    limite: Decimal
    em_aberto: Decimal  # parcelas em aberto em todas as lojas
    disponivel: Decimal
    bloqueado: bool
    suspenso: bool

    @property
    def impedimento(self) -> str | None:
        """Por que o cliente não pode comprar no crediário, mesmo com autorização."""
        if self.bloqueado:
            return "O cliente está bloqueado e não pode comprar no crediário"
        if self.suspenso:
            return "O crédito do cliente está suspenso"
        return None


def em_aberto(db: Session, cliente_id: int) -> Decimal:
    total = db.scalar(select(func.sum(ParcelaReceber.aberto)).join(ContaReceber)
                      .where(ContaReceber.cliente_id == cliente_id))
    return Decimal(total or 0).quantize(CENTAVO)


def credito(db: Session, cliente: Cliente) -> Credito:
    """O limite restante é o limite do cliente menos tudo o que ele tem em aberto, em qualquer loja."""
    aberto = em_aberto(db, cliente.id)
    return Credito(limite=cliente.limite_credito, em_aberto=aberto, disponivel=cliente.limite_credito - aberto,
                   bloqueado=cliente.bloqueado, suspenso=cliente.credito_suspenso)


def somar_meses(inicio: date, meses: int) -> date:
    mes = inicio.month - 1 + meses
    ano, mes = inicio.year + mes // 12, mes % 12 + 1
    return date(ano, mes, min(inicio.day, calendar.monthrange(ano, mes)[1]))


def vencimentos(primeiro: date, parcelas: int, intervalo: int) -> list[date]:
    """Intervalo de 30 dias (ou múltiplo) vence no mesmo dia de cada mês, como no VB6; outro, a cada tantos dias."""
    if intervalo % 30 == 0:
        return [somar_meses(primeiro, i * intervalo // 30) for i in range(parcelas)]
    return [primeiro + timedelta(days=i * intervalo) for i in range(parcelas)]


def dividir(valor: Decimal, parcelas: int) -> list[Decimal]:
    """Parcelas iguais, sem juros; os centavos que sobram vão na última."""
    parcela = (valor / parcelas).quantize(CENTAVO, rounding=ROUND_DOWN)
    return [parcela] * (parcelas - 1) + [valor - parcela * (parcelas - 1)]


def lancar_carne(db: Session, empresa_id: int, cliente_id: int, venda_id: int | None, valor: Decimal,
                 parcelas: int, primeiro_vencimento: date, intervalo: int, historico: str,
                 usuario_id: int) -> ContaReceber:
    """Cria a conta e as parcelas; quem chama grava."""
    conta = ContaReceber(empresa_id=empresa_id, cliente_id=cliente_id, venda_id=venda_id, valor=valor,
                         historico=historico[:80], usuario_id=usuario_id)
    datas = vencimentos(primeiro_vencimento, parcelas, intervalo)
    for numero, (vencimento, parte) in enumerate(zip(datas, dividir(valor, parcelas)), start=1):
        conta.parcelas.append(ParcelaReceber(numero=numero, vencimento=vencimento, valor=parte, aberto=parte))
    db.add(conta)
    return conta


def conta_da_venda(db: Session, venda_id: int) -> ContaReceber | None:
    return db.scalar(select(ContaReceber).where(ContaReceber.venda_id == venda_id))
