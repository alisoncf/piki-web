"""Leitura e gravação do legado_mapa: código antigo (por empresa) → id novo."""
from sqlalchemy.orm import Session

from app.nucleo.legado import MapaLegado


def buscar(db: Session, tabela: str, empresa_id: int, codigo: str) -> int | None:
    mapa = db.get(MapaLegado, (tabela, empresa_id, codigo))
    return mapa.novo_id if mapa else None


def gravar(db: Session, tabela: str, empresa_id: int, codigo: str, novo_id: int) -> None:
    mapa = db.get(MapaLegado, (tabela, empresa_id, codigo))
    if mapa is None:
        db.add(MapaLegado(tabela=tabela, empresa_id=empresa_id, codigo=codigo, novo_id=novo_id))
    else:
        mapa.novo_id = novo_id
    # as sessões não fazem autoflush: sem isto, um buscar() logo depois não acharia o registro
    db.flush()
