"""Importa seções, subseções e produtos do banco da matriz do VB6 (D24).

O cadastro de produtos é um só e quem manda nele é a matriz: as outras lojas
recebem os produtos dela, com os mesmos códigos. Então este ETL lê só o banco
da matriz; o código do produto no VB6 (cod_pro) vira o código no sistema novo,
e é por ele que as vendas e o estoque das lojas vão achar o produto.

- Preço e custo são iguais em todas as lojas. O custo é o da última entrada
  com nota (cf_pro, o "fiscal": D24 assume o fiscal como o real); sem ele, o
  cr_pro.
- O preço de atacado (pa_pro) e os restos de farmácia (princípio ativo,
  controle, fabricante, gênero, combustível, balança) não vêm.
- Códigos de barras: só os de 8 a 14 dígitos. O igual ao próprio código não
  vem (o código já é o código de barras interno); o igual ao código de outro
  produto também não, porque seria ambíguo. Repetido em dois produtos fica no
  mais novo.
- O fabricante do VB6 (cod_fab) é, na verdade, o fornecedor; vira o primeiro
  fornecedor do produto, se o fornecedor foi importado.
- Fracionado: a marcação do VB6, ou se o produto já foi vendido com fração.
- Ativo: vendido, comprado, cadastrado ou alterado no último ano, nesta loja
  ou nas outras passadas em `outras` (os bancos das outras lojas, só para
  ver as vendas e compras).

Na reimportação, os dados do produto são os do VB6 de novo; códigos de
barras e fornecedores acrescentados no sistema novo ficam.
"""
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import Connection, select, text
from sqlalchemy.orm import Session

from app.dominios.empresas.modelos import Empresa
from app.dominios.produtos.modelos import CodigoBarras, Produto, ProdutoFornecedor, Secao, Subsecao
from app.nucleo.documentos import so_digitos
from etl import mapa
from etl.funcionarios import EmpresaNaoImportada

_UNIDADES = {"UN", "JG", "PC", "PCT", "KG", "G", "M", "M2", "M3", "CX", "PAR", "KIT", "LT", "ML", "CJ", "DZ", "RL"}
_SEM_SECAO = "DIVERSOS"

_PRODUTOS = text("""
    SELECT CAST(cod_pro AS CHAR) cod_pro, CAST(nome_pro AS CHAR) nome_pro, CAST(cod_sub AS CHAR) cod_sub,
           CAST(cr_pro AS CHAR) cr_pro, CAST(cf_pro AS CHAR) cf_pro, CAST(pv_pro AS CHAR) pv_pro,
           CAST(pq_pro AS CHAR) pq_pro, CAST(lucro_pro AS CHAR) lucro_pro, CAST(unidade_pro AS CHAR) unidade_pro,
           CAST(fracionado_pro AS CHAR) fracionado_pro, CAST(cod_fab AS CHAR) cod_fab, CAST(ncm_pro AS CHAR) ncm_pro,
           CAST(cest_pro AS CHAR) cest_pro, CAST(cod_ori AS CHAR) cod_ori, CAST(dataalt_pro AS CHAR) dataalt_pro,
           CAST(ean_pro AS CHAR) ean_pro, CAST(codbarra_pro AS CHAR) codbarra_pro
      FROM tab_produtos ORDER BY cod_pro""")
_VENDIDOS = text("""
    SELECT DISTINCT CAST(i.cod_pro AS CHAR) FROM tab_itvendas i JOIN tab_vendas v ON v.num_ven = i.num_ven
     WHERE v.data_ven >= :desde AND v.situacao_ven <> '5'""")  # 5 = venda cancelada
_COMPRADOS = text("""
    SELECT DISTINCT CAST(i.cod_pro AS CHAR) FROM tab_itcompras i JOIN tab_compras c ON c.seq_not = i.seq_not
     WHERE c.entrada_not >= :desde""")
_COM_FRACAO = text("SELECT DISTINCT CAST(cod_pro AS CHAR) FROM tab_itvendas WHERE ROUND(qtd_ite * 100) % 100 <> 0")


@dataclass
class Resultado:
    secoes: int = 0
    subsecoes: int = 0
    criados: int = 0
    atualizados: int = 0
    ativos: int = 0
    inativos: int = 0
    fracionados: int = 0
    codigos_barras: int = 0
    fornecedores: int = 0
    avisos: list[str] = field(default_factory=list)


def _texto(valor: object) -> str | None:
    if valor is None:
        return None
    v = " ".join(str(valor).split())
    return v or None


def nome_da_secao(valor: object) -> str | None:
    """Corta o lixo que ficou no fim de alguns nomes: "CAMA)</item" → "CAMA"."""
    v = _texto(re.split(r"[)<>]", str(valor or ""))[0])
    return v[:50] if v else None


def _decimal(valor: object) -> Decimal:
    try:
        return max(Decimal(str(valor or "0")).quantize(Decimal("0.01")), Decimal(0))
    except ArithmeticError:
        return Decimal(0)


def _codigo(valor: object) -> int | None:
    v = (valor or "").strip()
    return int(v) if v.isdigit() else None


def unidade(valor: object) -> str:
    v = (_texto(valor) or "").upper().replace("²", "2")
    return v if v in _UNIDADES else "UN"


def _data(valor: object) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except (TypeError, ValueError):
        return None  # vazia ou 0000-00-00


def _codigos(conexao: Connection, consulta, **params) -> set[int]:
    return {c for (v,) in conexao.execute(consulta, params) if (c := _codigo(v)) is not None}


def _importar_secoes(origem: Connection, db: Session, empresa: Empresa, r: Resultado) -> dict[str, int]:
    """Devolve cod_sub → id da subseção."""
    secoes: dict[str, Secao] = {}
    for cod, nome in origem.execute(text("SELECT CAST(cod_sec AS CHAR), CAST(nome_sec AS CHAR) FROM tab_secoes")):
        cod, nome = (cod or "").strip(), nome_da_secao(nome)
        if not cod or not nome:
            continue
        secao_id = mapa.buscar(db, "tab_secoes", empresa.id, cod)
        secao = db.get(Secao, secao_id) if secao_id else None
        if secao is None:
            secao = db.scalar(select(Secao).where(Secao.nome == nome))
        if secao is None:
            secao = Secao(nome=nome[:40])
            db.add(secao)
            r.secoes += 1
        db.flush()
        mapa.gravar(db, "tab_secoes", empresa.id, cod, secao.id)
        secoes[cod] = secao

    subsecoes: dict[str, int] = {}
    linhas = origem.execute(text(
        "SELECT CAST(cod_sub AS CHAR), CAST(nome_sub AS CHAR), CAST(cod_sec AS CHAR) FROM tab_subsec"))
    for cod, nome, cod_sec in linhas:
        cod, nome = (cod or "").strip(), nome_da_secao(nome)
        if not cod or not nome:
            continue
        secao = secoes.get((cod_sec or "").strip())
        if secao is None:
            secao = db.scalar(select(Secao).where(Secao.nome == _SEM_SECAO)) or Secao(nome=_SEM_SECAO)
            db.add(secao)
            db.flush()
            r.avisos.append(f"subseção {cod} ({nome}): seção {cod_sec} não existe, foi para {_SEM_SECAO}")
        sub_id = mapa.buscar(db, "tab_subsec", empresa.id, cod)
        sub = db.get(Subsecao, sub_id) if sub_id else None
        if sub is None:
            sub = db.scalar(select(Subsecao).where(Subsecao.secao_id == secao.id, Subsecao.nome == nome))
        if sub is None:
            sub = Subsecao(secao_id=secao.id, nome=nome)
            db.add(sub)
            r.subsecoes += 1
        db.flush()
        mapa.gravar(db, "tab_subsec", empresa.id, cod, sub.id)
        subsecoes[cod] = sub.id
    return subsecoes


def _barras(origem: Connection, codigos: set[int], r: Resultado) -> dict[int, list[str]]:
    """Os códigos de barras que valem, por código de produto (o repetido fica no produto mais novo)."""
    linhas = [(c, so_digitos(b)) for c, b in origem.execute(text(
        "SELECT CAST(cod_pro AS CHAR), CAST(cod_bar AS CHAR) FROM tab_codbarras"))]
    for cod, ean, outro in origem.execute(text(
            "SELECT CAST(cod_pro AS CHAR), CAST(ean_pro AS CHAR), CAST(codbarra_pro AS CHAR) FROM tab_produtos")):
        linhas += [(cod, so_digitos(ean)), (cod, so_digitos(outro))]
    dono: dict[str, int] = {}
    for cod, barra in linhas:
        produto = _codigo(cod)
        if produto not in codigos or not 8 <= len(barra) <= 14 or int(barra) == produto:
            continue
        if len(barra) <= 9 and int(barra) in codigos:
            r.avisos.append(f"produto {produto}: código de barras {barra} é o código de outro produto, não importado")
            continue
        if barra in dono and dono[barra] != produto:
            r.avisos.append(f"código de barras {barra} em {dono[barra]} e {produto}: ficou no {max(dono[barra], produto)}")
        dono[barra] = max(dono.get(barra, 0), produto)
    por_produto: dict[int, list[str]] = {}
    for barra, produto in sorted(dono.items()):
        por_produto.setdefault(produto, []).append(barra)
    return por_produto


def importar_produtos(origem: Connection, db: Session, codigo_empresa: str, outras: list[Connection] = (),
                      hoje: date | None = None) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()
    desde = (hoje or date.today()) - timedelta(days=365)
    subsecoes = _importar_secoes(origem, db, empresa, r)

    movimentados: set[int] = set()
    com_fracao: set[int] = set()
    for conexao in (origem, *outras):
        movimentados |= _codigos(conexao, _VENDIDOS, desde=desde.isoformat())
        movimentados |= _codigos(conexao, _COMPRADOS, desde=desde.isoformat())
        com_fracao |= _codigos(conexao, _COM_FRACAO)

    linhas = [dict(linha) for linha in origem.execute(_PRODUTOS).mappings()]
    codigos = {c for linha in linhas if (c := _codigo(linha["cod_pro"])) is not None}
    barras = _barras(origem, codigos, r)
    existentes = {p.codigo: p for p in db.scalars(select(Produto))}
    dono_das_barras = dict(db.execute(select(CodigoBarras.codigo, CodigoBarras.produto_id)).all())

    for linha in linhas:
        codigo = _codigo(linha["cod_pro"])
        nome = _texto(linha["nome_pro"])
        if codigo is None or not nome:
            r.avisos.append(f"produto {linha['cod_pro']!r}: sem código numérico ou sem nome, não importado")
            continue
        subsecao_id = subsecoes.get((linha["cod_sub"] or "").strip())
        if subsecao_id is None:
            r.avisos.append(f"produto {codigo} ({nome}): subseção {linha['cod_sub']} não existe, ficou sem")
        alterado = _data(linha["dataalt_pro"])
        ativo = codigo in movimentados or (alterado is not None and alterado >= desde)
        custo = _decimal(linha["cf_pro"]) or _decimal(linha["cr_pro"])
        preco = _decimal(linha["pv_pro"])
        queima = _decimal(linha["pq_pro"])
        ncm = so_digitos(linha["ncm_pro"])
        cest = so_digitos(linha["cest_pro"])
        origem_fiscal = (linha["cod_ori"] or "").strip()
        dados = {
            "nome": nome[:120],
            "subsecao_id": subsecao_id,
            "unidade": unidade(linha["unidade_pro"]),
            "fracionado": (linha["fracionado_pro"] or "").strip().upper() == "S" or codigo in com_fracao,
            "custo": custo,
            "margem": min(_decimal(linha["lucro_pro"]), Decimal("99999.99")),
            "preco_venda": preco,
            # queima só vale abaixo do preço de venda
            "preco_queima": queima if Decimal(0) < queima < preco else None,
            "ncm": ncm if len(ncm) == 8 else None,
            "cest": cest if len(cest) == 7 else None,
            "origem": int(origem_fiscal) if origem_fiscal.isdigit() and int(origem_fiscal) <= 8 else 0,
            "ativo": ativo,
        }
        produto = existentes.get(codigo)
        if produto is None:
            produto = Produto(codigo=codigo, **dados)
            db.add(produto)
            existentes[codigo] = produto
            r.criados += 1
        else:
            for campo, valor in dados.items():
                setattr(produto, campo, valor)
            r.atualizados += 1
        r.ativos += ativo
        r.inativos += not ativo
        r.fracionados += dados["fracionado"]
        db.flush()

        ja_tem = {c.codigo for c in produto.codigos_barras}
        for barra in barras.get(codigo, []):
            if barra in ja_tem:
                continue
            if dono_das_barras.get(barra, produto.id) != produto.id:
                r.avisos.append(f"produto {codigo}: código de barras {barra} já é de outro produto no sistema novo")
                continue
            produto.codigos_barras.append(CodigoBarras(codigo=barra))
            dono_das_barras[barra] = produto.id
            r.codigos_barras += 1

        cod_fab = (linha["cod_fab"] or "").strip()
        if cod_fab.isdigit() and int(cod_fab):
            fornecedor_id = mapa.buscar(db, "tab_fornecedores", empresa.id, str(int(cod_fab)))
            if fornecedor_id is None:
                r.avisos.append(f"produto {codigo} ({nome}): fornecedor {int(cod_fab)} não foi importado (sem CNPJ válido?)")
            elif fornecedor_id not in {f.fornecedor_id for f in produto.fornecedores}:
                produto.fornecedores.append(ProdutoFornecedor(fornecedor_id=fornecedor_id))
                r.fornecedores += 1

    db.commit()
    return r
