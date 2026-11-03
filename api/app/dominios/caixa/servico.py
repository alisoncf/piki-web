"""Regras das formas de pagamento e do caixa (D26)."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominios.caixa.esquemas import CaixaDados, FormaDados, LancamentoDados, PedidoFechamento
from app.dominios.caixa.modelos import (
    ABERTO, FECHADO, MOTIVOS, Caixa, ConferenciaCaixa, FormaPagamento, LancamentoCaixa, SessaoCaixa,
)
from app.dominios.financeiro.modelos import ContaPlano
from app.dominios.funcionarios.modelos import Funcionario

ZERO = Decimal("0.00")


class ErroCaixa(Exception):
    """Erro de regra do caixa; a mensagem vai para o usuário."""


class NaoEncontrado(ErroCaixa):
    pass


class DadoInvalido(ErroCaixa):
    pass


class Duplicado(ErroCaixa):
    pass


# formas de pagamento

def listar_formas(db: Session, so_ativas: bool = False) -> list[FormaPagamento]:
    consulta = select(FormaPagamento).order_by(FormaPagamento.ordem, FormaPagamento.nome)
    if so_ativas:
        consulta = consulta.where(FormaPagamento.ativo.is_(True))
    return list(db.scalars(consulta))


def _salvar_forma(db: Session, forma: FormaPagamento, dados: FormaDados) -> FormaPagamento:
    outra = db.scalar(select(FormaPagamento).where(func.lower(FormaPagamento.nome) == dados.nome.lower()))
    if outra is not None and outra.id != forma.id:
        raise Duplicado("Já existe uma forma de pagamento com este nome")
    for campo, valor in dados.model_dump().items():
        setattr(forma, campo, valor)
    db.add(forma)
    db.commit()
    db.refresh(forma)
    return forma


def criar_forma(db: Session, dados: FormaDados) -> FormaPagamento:
    return _salvar_forma(db, FormaPagamento(), dados)


def alterar_forma(db: Session, forma_id: int, dados: FormaDados) -> FormaPagamento:
    forma = db.get(FormaPagamento, forma_id)
    if forma is None:
        raise NaoEncontrado("Forma de pagamento não encontrada")
    return _salvar_forma(db, forma, dados)


def _dinheiro(db: Session) -> FormaPagamento:
    forma = db.scalar(select(FormaPagamento).where(FormaPagamento.tipo == "dinheiro", FormaPagamento.ativo.is_(True))
                      .order_by(FormaPagamento.ordem, FormaPagamento.id).limit(1))
    if forma is None:
        raise DadoInvalido("Cadastre a forma de pagamento Dinheiro")
    return forma


# caixas

def sessao_aberta(db: Session, caixa_id: int) -> SessaoCaixa | None:
    return db.scalar(select(SessaoCaixa).where(SessaoCaixa.caixa_id == caixa_id, SessaoCaixa.situacao == ABERTO))


def listar_caixas(db: Session, empresa_id: int) -> list[tuple[Caixa, SessaoCaixa | None]]:
    caixas = db.scalars(select(Caixa).where(Caixa.empresa_id == empresa_id).order_by(Caixa.nome))
    return [(c, sessao_aberta(db, c.id)) for c in caixas]


def _caixa(db: Session, empresa_id: int, caixa_id: int) -> Caixa:
    caixa = db.get(Caixa, caixa_id)
    if caixa is None or caixa.empresa_id != empresa_id:
        raise NaoEncontrado("Caixa não encontrado")
    return caixa


def _salvar_caixa(db: Session, caixa: Caixa, dados: CaixaDados) -> Caixa:
    outro = db.scalar(select(Caixa).where(Caixa.empresa_id == caixa.empresa_id,
                                          func.lower(Caixa.nome) == dados.nome.lower()))
    if outro is not None and outro.id != caixa.id:
        raise Duplicado("Já existe um caixa com este nome nesta loja")
    if not dados.ativo and caixa.id and sessao_aberta(db, caixa.id):
        raise DadoInvalido("Feche o caixa antes de desativá-lo")
    if dados.serie_nfe is not None:
        outro = db.scalar(select(Caixa).where(Caixa.empresa_id == caixa.empresa_id, Caixa.serie_nfe == dados.serie_nfe))
        if outro is not None and outro.id != caixa.id:
            raise Duplicado(f"A série {dados.serie_nfe} já é do caixa {outro.nome}: cada caixa tem a sua")
    caixa.nome, caixa.ativo, caixa.serie_nfe = dados.nome, dados.ativo, dados.serie_nfe
    db.add(caixa)
    db.commit()
    db.refresh(caixa)
    return caixa


def criar_caixa(db: Session, empresa_id: int, dados: CaixaDados) -> Caixa:
    return _salvar_caixa(db, Caixa(empresa_id=empresa_id), dados)


def alterar_caixa(db: Session, empresa_id: int, caixa_id: int, dados: CaixaDados) -> Caixa:
    return _salvar_caixa(db, _caixa(db, empresa_id, caixa_id), dados)


# abrir, lançar, fechar

def abrir(db: Session, empresa_id: int, caixa_id: int, fundo: Decimal, usuario_id: int) -> SessaoCaixa:
    caixa = _caixa(db, empresa_id, caixa_id)
    if not caixa.ativo:
        raise DadoInvalido("Este caixa está desativado")
    if sessao_aberta(db, caixa.id):
        raise DadoInvalido(f"O caixa {caixa.nome} já está aberto")
    _dinheiro(db)  # o fundo de troco e a conferência partem do dinheiro
    sessao = SessaoCaixa(caixa_id=caixa.id, fundo=fundo, situacao=ABERTO, aberto_por_id=usuario_id)
    db.add(sessao)
    db.commit()
    db.refresh(sessao)
    return sessao


def obter_sessao(db: Session, empresa_id: int, sessao_id: int) -> SessaoCaixa:
    sessao = db.get(SessaoCaixa, sessao_id)
    if sessao is None or sessao.caixa.empresa_id != empresa_id:
        raise NaoEncontrado("Caixa não encontrado")
    return sessao


def _aberta(db: Session, empresa_id: int, sessao_id: int) -> SessaoCaixa:
    sessao = obter_sessao(db, empresa_id, sessao_id)
    if sessao.situacao != ABERTO:
        raise DadoInvalido("Este caixa já foi fechado")
    return sessao


def lancar(db: Session, empresa_id: int, sessao_id: int, dados: LancamentoDados, usuario_id: int) -> LancamentoCaixa:
    """Entrada ou saída avulsa (troco, despesa, vale, comissão...)."""
    sessao = _aberta(db, empresa_id, sessao_id)
    if dados.forma_pagamento_id is None:
        forma = _dinheiro(db)
    else:
        forma = db.get(FormaPagamento, dados.forma_pagamento_id)
        if forma is None:
            raise DadoInvalido("Forma de pagamento não encontrada")
    if dados.motivo in ("vale", "comissao"):
        if dados.funcionario_id is None:
            raise DadoInvalido("Informe o funcionário")
    if dados.funcionario_id is not None and db.get(Funcionario, dados.funcionario_id) is None:
        raise DadoInvalido("Funcionário não encontrado")
    if dados.motivo in ("despesa", "outra_entrada") and not dados.historico:
        raise DadoInvalido("Diga do que é o lançamento")
    # a despesa vai para uma conta de despesa; a outra entrada, para uma de receita
    tipo_conta = {"despesa": "despesa", "outra_entrada": "receita"}.get(dados.motivo)
    if tipo_conta:
        conta = db.get(ContaPlano, dados.plano_conta_id) if dados.plano_conta_id else None
        if conta is None or not conta.ativo:
            raise DadoInvalido(f"Escolha a conta de {tipo_conta} no plano de contas")
        if conta.tipo != tipo_conta:
            raise DadoInvalido(f"{conta.nome} não é uma conta de {tipo_conta}")
    elif dados.plano_conta_id is not None:
        raise DadoInvalido("Só a despesa e a outra entrada levam conta do plano de contas")
    lancamento = LancamentoCaixa(
        sessao_id=sessao.id, tipo=MOTIVOS[dados.motivo][0], motivo=dados.motivo, forma_pagamento_id=forma.id,
        valor=dados.valor, historico=dados.historico, funcionario_id=dados.funcionario_id, usuario_id=usuario_id,
        plano_conta_id=dados.plano_conta_id,
    )
    db.add(lancamento)
    db.commit()
    db.refresh(lancamento)
    return lancamento


def estornar(db: Session, empresa_id: int, sessao_id: int, lancamento_id: int, usuario_id: int) -> LancamentoCaixa:
    """O lançamento errado deixa de contar, mas continua na lista, com quem estornou."""
    sessao = _aberta(db, empresa_id, sessao_id)
    lancamento = next((x for x in sessao.lancamentos if x.id == lancamento_id), None)
    if lancamento is None:
        raise NaoEncontrado("Lançamento não encontrado")
    if lancamento.estornado_em is not None:
        raise DadoInvalido("Este lançamento já foi estornado")
    if lancamento.documento:
        raise DadoInvalido("Lançamento de venda ou recebimento é desfeito por lá, não aqui")
    lancamento.estornado_em = datetime.now()
    lancamento.estornado_por_id = usuario_id
    db.commit()
    db.refresh(lancamento)
    return lancamento


def totais(db: Session, sessao: SessaoCaixa) -> list[dict]:
    """O saldo de cada forma no caixa: o fundo (em dinheiro) + entradas − saídas, sem os estornados."""
    dinheiro = _dinheiro(db)
    formas = {dinheiro.id: dinheiro}
    entradas: dict[int, Decimal] = defaultdict(lambda: ZERO)
    saidas: dict[int, Decimal] = defaultdict(lambda: ZERO)
    entradas[dinheiro.id] += sessao.fundo
    for x in sessao.lancamentos:
        if x.estornado_em is not None:
            continue
        formas[x.forma_pagamento_id] = x.forma_pagamento
        (entradas if x.tipo == "entrada" else saidas)[x.forma_pagamento_id] += x.valor
    ordem = sorted(formas.values(), key=lambda f: (f.ordem, f.nome))
    return [{"forma_pagamento": f, "entradas": entradas[f.id], "saidas": saidas[f.id],
             "saldo": entradas[f.id] - saidas[f.id]} for f in ordem]


def fechar(db: Session, empresa_id: int, sessao_id: int, pedido: PedidoFechamento, usuario_id: int) -> SessaoCaixa:
    """Grava o contado ao lado do esperado de cada forma. Forma com saldo que não foi contada conta como zero."""
    sessao = _aberta(db, empresa_id, sessao_id)
    contado = {c.forma_pagamento_id: c.contado for c in pedido.contagem}
    esperado = {t["forma_pagamento"].id: t["saldo"] for t in totais(db, sessao)}
    desconhecidas = set(contado) - set(esperado)
    for forma_id in desconhecidas:  # contou uma forma que não teve lançamento: vai com esperado zero
        if db.get(FormaPagamento, forma_id) is None:
            raise DadoInvalido("Forma de pagamento não encontrada")
        esperado[forma_id] = ZERO
    for forma_id, valor in esperado.items():
        sessao.conferencia.append(ConferenciaCaixa(
            forma_pagamento_id=forma_id, esperado=valor, contado=contado.get(forma_id, ZERO)))
    sessao.situacao = FECHADO
    sessao.fechado_em = datetime.now()
    sessao.fechado_por_id = usuario_id
    sessao.observacao = (pedido.observacao or "").strip() or None
    db.commit()
    db.refresh(sessao)
    return sessao


def listar_sessoes(db: Session, empresa_id: int, caixa_id: int, limite: int,
                   deslocamento: int) -> tuple[list[SessaoCaixa], int]:
    _caixa(db, empresa_id, caixa_id)
    filtro = SessaoCaixa.caixa_id == caixa_id
    total = db.scalar(select(func.count()).select_from(SessaoCaixa).where(filtro))
    itens = db.scalars(select(SessaoCaixa).where(filtro).order_by(SessaoCaixa.id.desc()).limit(limite).offset(deslocamento))
    return list(itens), total
