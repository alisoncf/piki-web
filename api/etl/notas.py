"""A numeração das notas de uma loja do VB6 (D29): o último número de cada modelo e série.

Na virada, a NFC-e e a NF-e do sistema novo continuam de onde o VB6 parou. A
numeração só sobe: reimportar depois que o sistema novo já emitiu não volta para trás.
Rode de novo no dia da virada, com a cópia mais nova do banco da loja.
"""
from dataclasses import dataclass, field

from sqlalchemy import Connection, select, text
from sqlalchemy.orm import Session

from app.dominios.empresas.modelos import Empresa
from app.dominios.fiscal.servico import continuar_de
from etl.funcionarios import EmpresaNaoImportada

_ULTIMOS = text("""
    SELECT CAST(modelo AS CHAR), CAST(serie AS CHAR), MAX(nNF)
      FROM nfe WHERE modelo IN ('55', '65') GROUP BY modelo, serie""")


@dataclass
class Resultado:
    series: list[str] = field(default_factory=list)  # "NFC-e série 102: 44536"
    avisos: list[str] = field(default_factory=list)


def importar_numeracao(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()
    for modelo, serie, ultimo in origem.execute(_ULTIMOS):
        serie = (serie or "").strip()
        if not serie.isdigit() or int(serie) == 0:
            r.avisos.append(f"modelo {modelo}: série '{serie}' não é um número (até o número {ultimo}); ignorada")
            continue
        continuar_de(db, empresa.id, modelo.strip(), int(serie), int(ultimo or 0))
        r.series.append(f"{'NFC-e' if modelo.strip() == '65' else 'NF-e'} série {int(serie)}: {ultimo}")
    db.commit()
    return r
