"""Importa as formas de pagamento e os caixas de uma loja do VB6 (D26).

As formas viram uma lista só, uma por tipo: as "1X DUP" a "10X DUP" do VB6 são
uma forma "Crediário" com até 10 parcelas, e as marcadas como gerenciais
(7X a 10X) marcam a partir de quando as parcelas pedem a gerência. O cheque
não é mais aceito: a forma é criada desativada, só para as vendas antigas.
Cada código antigo fica no legado_mapa, apontando para a forma nova.

Os caixas são da loja, com os nomes do VB6. O "SEM CAIXA" (00) entra
desativado, porque há vendas antigas nele.
"""
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import Connection, select, text
from sqlalchemy.orm import Session

from app.dominios.caixa.modelos import Caixa, FormaPagamento
from app.dominios.empresas.modelos import Empresa
from etl import mapa
from etl.funcionarios import EmpresaNaoImportada

# tipo_cai do VB6 → (nome, tipo, ordem)
_FORMAS = {
    "DIN": ("Dinheiro", "dinheiro", 1),
    "PIX": ("PIX", "pix", 2),
    "CRT": ("Cartão de crédito", "cartao_credito", 3),
    "CRD": ("Cartão de débito", "cartao_debito", 4),
    "DUP": ("Crediário", "crediario", 5),
    "CRP": ("Cartão presente", "cartao_presente", 6),
    "DEP": ("Depósito bancário", "deposito", 7),
    "VAL": ("Vale", "vale", 8),
    "CHV": ("Cheque", "outro", 9),
    "CHP": ("Cheque", "outro", 9),
}
_CARTAO_PARCELAS = 12  # o VB6 registra as parcelas do cartão na venda, sem máximo na forma


@dataclass
class Resultado:
    formas: int = 0
    caixas: int = 0
    avisos: list[str] = field(default_factory=list)


def importar_caixa(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()

    linhas = origem.execute(text(
        "SELECT CAST(cod_for AS CHAR), CAST(nome_for AS CHAR), desconto_for, CAST(tipo_cai AS CHAR), parcelas_for,"
        " intervalo_for, CAST(gerencial_for AS CHAR), CAST(visivel_for AS CHAR) FROM tab_formaspag")).all()
    # agrupa por tipo: parcelas máximas, as que não são gerenciais, maior desconto
    grupos: dict[str, dict] = {}
    for cod, nome, desconto, tipo_cai, parcelas, intervalo, gerencial, visivel in linhas:
        tipo_cai = (tipo_cai or "").strip().upper()
        if tipo_cai not in _FORMAS:
            r.avisos.append(f"forma {cod} ({nome}): tipo {tipo_cai} desconhecido, não importada")
            continue
        nome_novo = _FORMAS[tipo_cai][0]
        g = grupos.setdefault(nome_novo, {"tipo_cai": tipo_cai, "codigos": [], "parcelas": 1, "livres": 1,
                                          "desconto": Decimal(0), "intervalo": 30, "ativo": False})
        g["codigos"].append((cod or "").strip())
        g["parcelas"] = max(g["parcelas"], int(parcelas or 1))
        if (gerencial or "N").strip().upper() != "S":
            g["livres"] = max(g["livres"], int(parcelas or 1))
        g["desconto"] = max(g["desconto"], Decimal(str(desconto or 0)).quantize(Decimal("0.01")))
        g["intervalo"] = int(intervalo or 30)
        g["ativo"] = g["ativo"] or (visivel or "S").strip().upper() != "N"

    for nome, g in grupos.items():
        _, tipo, ordem = _FORMAS[g["tipo_cai"]]
        forma = db.scalar(select(FormaPagamento).where(FormaPagamento.nome == nome))
        if forma is None:
            parcelas = _CARTAO_PARCELAS if tipo == "cartao_credito" else g["parcelas"]
            forma = FormaPagamento(
                nome=nome, tipo=tipo, desconto=g["desconto"], parcelas=parcelas,
                parcelas_sem_autorizacao=parcelas if tipo == "cartao_credito" else g["livres"],
                intervalo=g["intervalo"], ordem=ordem, ativo=g["ativo"] and nome != "Cheque",
            )
            db.add(forma)
            db.flush()
            r.formas += 1
        for cod in g["codigos"]:
            mapa.gravar(db, "tab_formaspag", empresa.id, cod, forma.id)

    for cod, nome, status in origem.execute(text(
            "SELECT CAST(cod_cai AS CHAR), CAST(nome_cai AS CHAR), CAST(status_cai AS CHAR) FROM tab_caixas")):
        cod = (cod or "").strip()
        nome = " ".join((nome or "").split())[:30] or f"Caixa {cod}"
        if cod == "00":
            nome = "Sem caixa"
        caixa_id = mapa.buscar(db, "tab_caixas", empresa.id, cod)
        caixa = db.get(Caixa, caixa_id) if caixa_id else None
        if caixa is None:
            caixa = db.scalar(select(Caixa).where(Caixa.empresa_id == empresa.id, Caixa.nome == nome))
        if caixa is None:
            caixa = Caixa(empresa_id=empresa.id, nome=nome, ativo=cod != "00" and (status or "A").strip().upper() == "A")
            db.add(caixa)
            db.flush()
            r.caixas += 1
        mapa.gravar(db, "tab_caixas", empresa.id, cod, caixa.id)

    db.commit()
    return r
