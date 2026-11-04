"""Importa o que está com cada representante no VB6 (D30): o saldo do consignado. Rode depois dos representantes,
dos produtos, dos usuários e do estoque.

No VB6 não há cabeçalho de transferência: cada linha da tab_consignacoes é um item levado, com o preço da
transferência (unit_con) e o que ainda resta com ele (reman_con). Cada representante com saldo ganha uma
transferência confirmada com as linhas que ainda têm resto, cada uma com o seu preço e a sua quantidade, para o
limite e o acerto continuarem de onde o VB6 parou.

O reservado do estoque da loja já vem do ETL de estoque (a soma do reman_con); aqui não se mexe nele. Rodar de
novo refaz os itens da transferência importada de cada representante.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Connection, select, text
from sqlalchemy.orm import Session

from app.dominios.acesso.modelos import Usuario
from app.dominios.consignacao.modelos import CONFIRMADA, ItemTransferencia, Transferencia
from app.dominios.empresas.modelos import Empresa
from app.dominios.produtos.modelos import Produto
from etl import mapa
from etl.funcionarios import EmpresaNaoImportada, _texto

_LINHAS = text("""
    SELECT CAST(cod_rep AS CHAR) AS cod_rep, CAST(cod_pro AS CHAR) AS cod_pro, data_con, qtd_con, reman_con, unit_con,
           CAST(cod_usu AS CHAR) AS cod_usu
    FROM tab_consignacoes WHERE reman_con > 0
""")
_TABELA = "tab_consignacoes_saldo"  # no legado_mapa: cod_rep → a transferência importada


@dataclass
class Resultado:
    representantes: int = 0
    itens: int = 0
    pecas: Decimal = Decimal("0.000")
    valor: Decimal = Decimal("0.00")
    avisos: list[str] = field(default_factory=list)


def _numero(valor: object) -> Decimal:
    return Decimal(str(valor or 0))


def _data(valor: object) -> datetime:
    return valor if isinstance(valor, datetime) else datetime.fromisoformat(str(valor))


def importar_consignado(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()
    administrador = db.scalar(select(Usuario).where(Usuario.administrador.is_(True)).order_by(Usuario.id))

    linhas: dict[str, list] = {}
    for linha in origem.execute(_LINHAS).mappings():
        linhas.setdefault(_texto(linha["cod_rep"]) or "", []).append(linha)

    produtos: dict[int, Produto] = {}
    for cod_rep, itens in sorted(linhas.items(), key=lambda par: int(par[0]) if par[0].isdigit() else 0):
        representante_id = mapa.buscar(db, "tab_representantes", empresa.id, cod_rep)
        if representante_id is None:
            r.avisos.append(f"representante {cod_rep}: não importado, {len(itens)} itens de consignado de fora")
            continue
        itens.sort(key=lambda linha: _data(linha["data_con"]))
        transferencia = db.get(Transferencia, mapa.buscar(db, _TABELA, empresa.id, cod_rep) or 0)
        ultima = itens[-1]
        usuario_id = mapa.buscar(db, "tab_usuarios", empresa.id, _texto(ultima["cod_usu"]) or "") or administrador.id
        if transferencia is None:
            numero = (db.scalar(select(Transferencia.numero).where(Transferencia.empresa_id == empresa.id)
                                .order_by(Transferencia.numero.desc()).limit(1)) or 0) + 1
            transferencia = Transferencia(empresa_id=empresa.id, numero=numero, representante_id=representante_id,
                                          situacao=CONFIRMADA, atendida_por_id=usuario_id)
            db.add(transferencia)
        transferencia.confirmada_em = _data(ultima["data_con"])
        transferencia.itens = []
        for ordem, linha in enumerate(itens, start=1):
            codigo = int((_texto(linha["cod_pro"]) or "0").lstrip("0") or 0)
            if codigo not in produtos:
                produtos[codigo] = db.scalar(select(Produto).where(Produto.codigo == codigo))
            produto = produtos[codigo]
            if produto is None:
                r.avisos.append(f"representante {cod_rep}: produto {codigo} não importado, item de fora")
                continue
            restante, preco = _numero(linha["reman_con"]), _numero(linha["unit_con"]).quantize(Decimal("0.01"))
            transferencia.itens.append(ItemTransferencia(
                ordem=ordem, produto=produto, descricao=produto.nome, quantidade=max(_numero(linha["qtd_con"]), restante),
                preco=preco, restante=restante))
            r.itens += 1
            r.pecas += restante
            r.valor += (restante * preco).quantize(Decimal("0.01"))
        transferencia.total = sum((i.total for i in transferencia.itens), Decimal("0.00"))
        db.flush()
        mapa.gravar(db, _TABELA, empresa.id, cod_rep, transferencia.id)
        r.representantes += 1

    db.commit()
    return r
