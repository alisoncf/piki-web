"""Regras do estoque de cada loja (D24).

Toda mudança de saldo passa por `movimentar`, que grava o movimento junto. As
vendas, entradas e consignações vão chamá-la quando existirem; por enquanto,
só o ajuste e a importação do VB6 movimentam.
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.dominios.estoque import repositorio as repo
from app.dominios.estoque.esquemas import EstoqueDados
from app.dominios.estoque.modelos import TIPOS, Estoque, MovimentoEstoque
from app.dominios.produtos.modelos import Produto

ZERO = Decimal("0.000")


class ErroEstoque(Exception):
    """Erro de regra do estoque; a mensagem vai para o usuário."""


class NaoEncontrado(ErroEstoque):
    pass


class DadoInvalido(ErroEstoque):
    pass


def _produto(db: Session, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise NaoEncontrado("Produto não encontrado")
    return produto


def obter_estoque(db: Session, empresa_id: int, produto_id: int) -> Estoque:
    """O produto na loja; se ainda não tem linha, uma vazia (não gravada)."""
    _produto(db, produto_id)
    return repo.estoque(db, empresa_id, produto_id) or Estoque(
        empresa_id=empresa_id, produto_id=produto_id, quantidade=ZERO, reservado=ZERO)


def _linha(db: Session, empresa_id: int, produto_id: int) -> Estoque:
    """A linha do produto na loja, travada para alterar; criada se não existe."""
    estoque = repo.estoque(db, empresa_id, produto_id, travar=True)
    if estoque is None:
        estoque = Estoque(empresa_id=empresa_id, produto_id=produto_id, quantidade=ZERO, reservado=ZERO)
        db.add(estoque)
        db.flush()  # as sessões não fazem autoflush: o próximo movimento na mesma transação precisa achá-la
    return estoque


def _tem_fracao(valor: Decimal) -> bool:
    return valor != valor.to_integral_value()


def lancar(db: Session, estoque: Estoque, tipo: str, quantidade: Decimal = ZERO, reservado: Decimal = ZERO,
           usuario_id: int | None = None, documento: str | None = None, observacao: str | None = None) -> MovimentoEstoque:
    """Muda o saldo da linha e grava o movimento, sem conferir nada nem dar commit (a importação usa direto)."""
    if tipo not in TIPOS:
        raise DadoInvalido(f"Tipo de movimento desconhecido: {tipo}")
    estoque.quantidade = (estoque.quantidade or ZERO) + quantidade
    estoque.reservado = (estoque.reservado or ZERO) + reservado
    movimento = MovimentoEstoque(
        empresa_id=estoque.empresa_id, produto_id=estoque.produto_id, tipo=tipo, quantidade=quantidade,
        reservado=reservado, saldo=estoque.quantidade, saldo_reservado=estoque.reservado,
        usuario_id=usuario_id, documento=documento, observacao=observacao,
    )
    db.add(movimento)
    return movimento


def movimentar(db: Session, empresa_id: int, produto_id: int, tipo: str, quantidade: Decimal = ZERO,
               reservado: Decimal = ZERO, usuario_id: int | None = None, documento: str | None = None,
               observacao: str | None = None) -> MovimentoEstoque:
    """Lança um movimento no estoque da loja. Não dá commit: vai na mesma transação da venda, da nota...

    Saldo negativo é permitido (D24); quem chama avisa o usuário. Produto que
    não aceita fração só movimenta quantidades inteiras.
    """
    produto = _produto(db, produto_id)
    if not produto.fracionado and (_tem_fracao(quantidade) or _tem_fracao(reservado)):
        raise DadoInvalido(f"{produto.nome} não aceita quantidade com fração")
    return lancar(db, _linha(db, empresa_id, produto_id), tipo, quantidade, reservado, usuario_id, documento, observacao)


def ajustar(db: Session, empresa_id: int, produto_id: int, quantidade: Decimal, motivo: str,
            usuario_id: int) -> Estoque:
    """Acerta a quantidade da loja para a informada; o movimento registra a diferença e o motivo."""
    atual = obter_estoque(db, empresa_id, produto_id).quantidade
    if quantidade == atual:
        raise DadoInvalido("O estoque já está com essa quantidade")
    movimentar(db, empresa_id, produto_id, "ajuste", quantidade - atual, usuario_id=usuario_id, observacao=motivo)
    db.commit()
    return obter_estoque(db, empresa_id, produto_id)


def alterar_dados(db: Session, empresa_id: int, produto_id: int, dados: EstoqueDados) -> Estoque:
    """Localização e impostos do produto na loja."""
    _produto(db, produto_id)
    estoque = _linha(db, empresa_id, produto_id)
    for campo, valor in dados.model_dump().items():
        setattr(estoque, campo, valor)
    db.commit()
    db.refresh(estoque)
    return estoque


def listar_movimentos(db: Session, empresa_id: int, produto_id: int, limite: int,
                      deslocamento: int) -> tuple[list[MovimentoEstoque], int]:
    _produto(db, produto_id)
    return repo.movimentos(db, empresa_id, produto_id, limite, deslocamento)
