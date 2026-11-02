"""Importa o estoque de uma loja do VB6 (D24): saldo, reservado, localização e impostos.

Rode antes o ETL de produtos (da matriz). Cada loja tem a sua tab_produtos,
com os mesmos códigos da matriz; o produto é achado pelo código.

- Quantidade: o estoque fiscal (ef_pro), que passa a ser o real. Ele inclui o
  que está com os representantes: no VB6, a consignação mexe só no er_pro.
- Reservado: o que falta acertar das consignações (soma do reman_con da
  tab_consignacoes), que é a conta que o próprio VB6 usa para refazer o r_pro.
- Localização (endereco_pro), CST/CSOSN (cst_icms) e CFOP (cfop_pro) da loja.
- Código que a matriz não tem, ou que nesta loja é outro produto (nome bem
  diferente do da matriz), fica de fora, com aviso.

Cada diferença de saldo vira um movimento "Saldo do VB6"; na reimportação,
só entra a diferença para o saldo atual. Produto sem saldo, sem reservado e
sem localização não ganha linha (o saldo dele é zero).

É o saldo de partida: depois ele vai ser refeito a partir do inventário de
31/12/2025, com as notas desde então.
"""
import difflib
import re
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import Connection, inspect, select, text
from sqlalchemy.orm import Session

from app.dominios.empresas.modelos import Empresa
from app.dominios.estoque.modelos import Estoque
from app.dominios.estoque.servico import lancar
from app.dominios.produtos.modelos import Produto
from app.nucleo.documentos import so_digitos
from etl.funcionarios import EmpresaNaoImportada

ZERO = Decimal(0)
# localização que é sobra de outro campo
_SEM_LOCALIZACAO = {"", "0", "UN"}
_PRODUTOS = text("""
    SELECT CAST(cod_pro AS CHAR) cod_pro, CAST(nome_pro AS CHAR) nome_pro, CAST(ef_pro AS CHAR) ef_pro,
           CAST(endereco_pro AS CHAR) endereco_pro, CAST(cst_icms AS CHAR) cst_icms, CAST(cfop_pro AS CHAR) cfop_pro
      FROM tab_produtos""")
_RESERVADOS = text("SELECT CAST(cod_pro AS CHAR), SUM(reman_con) FROM tab_consignacoes GROUP BY cod_pro")


@dataclass
class Resultado:
    linhas: int = 0
    movimentos: int = 0
    negativos: int = 0
    ignorados: int = 0
    avisos: list[str] = field(default_factory=list)


def _quantidade(valor: object) -> Decimal:
    try:
        return Decimal(str(valor or "0")).quantize(Decimal("0.001"))
    except ArithmeticError:
        return ZERO


def _nome(valor: object) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(valor or "").upper()).strip()


def mesmo_produto(nome_matriz: str, nome_loja: object) -> bool:
    """O nome na loja é o da matriz, com pequenas diferenças ("...WOLFF##", "... KARSTEN/PINHEIRO")."""
    a, b = _nome(nome_matriz), _nome(nome_loja)
    return a == b or a.startswith(b) or b.startswith(a) or difflib.SequenceMatcher(None, a, b).ratio() >= 0.8


def importar_estoque(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()
    # código → (id, nome)
    produtos = {c: (i, n) for c, i, n in db.execute(select(Produto.codigo, Produto.id, Produto.nome))}
    estoques = {e.produto_id: e for e in db.scalars(select(Estoque).where(Estoque.empresa_id == empresa.id))}
    reservados: dict[str, Decimal] = {}
    if inspect(origem).has_table("tab_consignacoes"):
        reservados = {(c or "").strip(): _quantidade(q) for c, q in origem.execute(_RESERVADOS)}

    for linha in origem.execute(_PRODUTOS).mappings():
        cod = (linha["cod_pro"] or "").strip()
        quantidade = _quantidade(linha["ef_pro"])
        reservado = reservados.get(cod, ZERO)
        localizacao = (linha["endereco_pro"] or "").strip()[:30]
        localizacao = None if localizacao.upper() in _SEM_LOCALIZACAO else localizacao
        produto = produtos.get(int(cod)) if cod.isdigit() else None
        if produto is None or not mesmo_produto(produto[1], linha["nome_pro"]):
            if quantidade or reservado:
                motivo = "não existe na matriz" if produto is None else f"na matriz é {produto[1]}"
                r.avisos.append(f"produto {cod} ({_nome(linha['nome_pro'])}): {motivo}; saldo {quantidade} não importado")
            r.ignorados += 1
            continue

        estoque = estoques.get(produto[0])
        if estoque is None:
            if not (quantidade or reservado or localizacao):
                continue
            estoque = Estoque(empresa_id=empresa.id, produto_id=produto[0], quantidade=ZERO, reservado=ZERO)
            db.add(estoque)
            estoques[produto[0]] = estoque
            r.linhas += 1
        estoque.localizacao = localizacao
        cst = so_digitos(linha["cst_icms"])
        cfop = so_digitos(linha["cfop_pro"])
        estoque.cst_csosn = cst if len(cst) in (2, 3) else None
        estoque.cfop = cfop if len(cfop) == 4 else None
        diferenca = quantidade - (estoque.quantidade or ZERO)
        diferenca_reservado = reservado - (estoque.reservado or ZERO)
        if diferenca or diferenca_reservado:
            lancar(db, estoque, "importacao", diferenca, diferenca_reservado, observacao="Importado do VB6")
            r.movimentos += 1
        r.negativos += quantidade < 0
        if reservado < 0:
            r.avisos.append(f"produto {cod}: reservado negativo ({reservado}) nas consignações")

    db.commit()
    return r
