"""Importa as contas a receber de clientes de uma loja do VB6 (D26): tab_doc e tab_itdoc.

Rode antes os ETLs de clientes e de usuários desta loja.

- Entram os documentos a receber (tipo_doc R) de clientes (tipo_ter C) que têm
  alguma parcela em aberto (reman_itd > 0), com todas as parcelas, pagas ou não,
  para o carnê continuar "3 de 5". Os de representantes (R) e de funcionários
  (U) ficam para a consignação e os vales; só entram no resumo.
- A origem vem do esp_doc: V venda (crediário), A acerto de consignação, o resto
  avulso. Todas contam no limite do cliente, como no VB6.
- O seq_doc, o seq_itd e o num_doc do VB6 se repetem entre as lojas (cada uma
  tem a sua sequência). Por isso a ligação com o VB6 fica no legado_mapa, por
  loja, e o num_doc fica na conta (documento_legado), sempre mostrado com o
  código da loja (01-0001234).
- Reimportar atualiza o que falta pagar, o vencimento e o valor das parcelas já
  importadas, inclusive das que foram quitadas no VB6 depois; a parcela que já
  teve recebimento no sistema novo não é mexida (aviso).
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Connection, bindparam, select, text
from sqlalchemy.orm import Session

from app.dominios.empresas.modelos import Empresa
from app.dominios.receber.modelos import ContaReceber, ItemRecebimento, ParcelaReceber
from app.nucleo.legado import MapaLegado
from etl.funcionarios import EmpresaNaoImportada

ZERO = Decimal("0.00")
LOTE = 500
_ORIGENS = {"V": "venda", "A": "acerto"}
_TERCEIROS = {"R": "representantes", "U": "funcionários"}

# documentos a receber com parcela em aberto, por tipo de terceiro (para o resumo dos que não entram)
_ABERTOS_POR_TERCEIRO = text("""
    SELECT CAST(d.tipo_ter AS CHAR), COUNT(*), SUM(i.reman_itd)
      FROM tab_itdoc i JOIN tab_doc d ON d.seq_doc = i.seq_doc
     WHERE d.tipo_doc = 'R' AND d.excluido_doc <> 'S' AND i.reman_itd > 0
     GROUP BY d.tipo_ter""")
_DOCS_ABERTOS = text("""
    SELECT DISTINCT CAST(d.seq_doc AS CHAR)
      FROM tab_doc d JOIN tab_itdoc i ON i.seq_doc = d.seq_doc
     WHERE d.tipo_doc = 'R' AND d.tipo_ter = 'C' AND d.excluido_doc <> 'S' AND i.reman_itd > 0""")
_DOCS = text("""
    SELECT CAST(seq_doc AS CHAR) seq_doc, CAST(num_doc AS CHAR) num_doc, CAST(cod_ter AS CHAR) cod_ter,
           valor_doc, CAST(data_doc AS CHAR) data_doc, CAST(cod_usu AS CHAR) cod_usu,
           CAST(historico_doc AS CHAR) historico_doc, CAST(esp_doc AS CHAR) esp_doc, CAST(excluido_doc AS CHAR) excluido_doc
      FROM tab_doc WHERE seq_doc IN :seqs""").bindparams(bindparam("seqs", expanding=True))
_PARCELAS = text("""
    SELECT CAST(seq_itd AS CHAR) seq_itd, CAST(seq_doc AS CHAR) seq_doc, parcela_itd, valor_itd, reman_itd,
           CAST(venc_itd AS CHAR) venc_itd, CAST(vencini_itd AS CHAR) vencini_itd
      FROM tab_itdoc WHERE seq_doc IN :seqs ORDER BY seq_doc, parcela_itd, venc_itd, seq_itd
""").bindparams(bindparam("seqs", expanding=True))


@dataclass
class Resultado:
    contas: int = 0  # novas
    parcelas: int = 0  # novas
    atualizadas: int = 0  # parcelas já importadas que mudaram
    em_aberto: Decimal = ZERO
    parcelas_em_aberto: int = 0
    sem_cliente: int = 0  # documentos de cliente que não foi importado
    fora: list[str] = field(default_factory=list)  # o que não entra (representantes, funcionários)
    avisos: list[str] = field(default_factory=list)


def _texto(valor: object) -> str:
    return " ".join(str(valor or "").split())


def _data(valor: object) -> date | None:
    texto = _texto(valor)[:10]
    if not texto or texto.startswith("0000"):
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def _dinheiro(valor: object) -> Decimal:
    return Decimal(str(valor or 0)).quantize(Decimal("0.01"))


def _codigo_cliente(valor: object) -> str:
    # cod_ter é int zerofill no VB6; o mapa de clientes guarda o número sem os zeros
    texto = _texto(valor)
    return str(int(texto)) if texto.isdigit() else texto


def _em_lotes(itens: list[str]):
    for i in range(0, len(itens), LOTE):
        yield tuple(itens[i:i + LOTE])


def _mapa(db: Session, tabela: str, empresa_id: int) -> dict[str, int]:
    return dict(db.execute(select(MapaLegado.codigo, MapaLegado.novo_id).where(
        MapaLegado.tabela == tabela, MapaLegado.empresa_id == empresa_id)).all())


def importar_receber(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()
    for tipo, quantas, valor in origem.execute(_ABERTOS_POR_TERCEIRO):
        tipo = _texto(tipo)
        if tipo != "C":
            r.fora.append(f"{quantas} parcelas em aberto de {_TERCEIROS.get(tipo, f'terceiro {tipo}')} "
                          f"({_dinheiro(valor)}), que não entram aqui")

    clientes = _mapa(db, "tab_clientes", empresa.id)
    usuarios = _mapa(db, "tab_usuarios", empresa.id)
    contas_importadas = _mapa(db, "tab_doc", empresa.id)
    parcelas_importadas = _mapa(db, "tab_itdoc", empresa.id)
    # parcelas que já tiveram recebimento no sistema novo: o VB6 não manda mais nelas
    recebidas = set(db.scalars(select(ItemRecebimento.parcela_id).distinct()))

    # os abertos agora e os que já vieram antes (podem ter sido quitados no VB6 depois)
    seqs = sorted({s.strip() for (s,) in origem.execute(_DOCS_ABERTOS)} | set(contas_importadas))
    for lote in _em_lotes(seqs):
        docs = {d["seq_doc"].strip(): d for d in origem.execute(_DOCS, {"seqs": list(lote)}).mappings()}
        parcelas_por_doc: dict[str, list] = {}
        for p in origem.execute(_PARCELAS, {"seqs": list(lote)}).mappings():
            parcelas_por_doc.setdefault(p["seq_doc"].strip(), []).append(p)
        for seq in lote:
            doc = docs.get(seq)
            if doc is None:
                if seq in contas_importadas:
                    r.avisos.append(f"documento {seq}: sumiu do VB6; a conta {contas_importadas[seq]} ficou como estava")
                continue
            _importar_documento(db, empresa, doc, parcelas_por_doc.get(seq, []), clientes, usuarios,
                                contas_importadas, parcelas_importadas, recebidas, r)
        db.flush()
    db.commit()
    return r


def _importar_documento(db: Session, empresa: Empresa, doc, parcelas: list, clientes: dict[str, int],
                        usuarios: dict[str, int], contas_importadas: dict[str, int],
                        parcelas_importadas: dict[str, int], recebidas: set[int], r: Resultado) -> None:
    seq = doc["seq_doc"].strip()
    num_doc = _texto(doc["num_doc"]) or seq
    if not parcelas:
        r.avisos.append(f"documento {num_doc}: sem parcelas no VB6, não importado")
        return
    conta_id = contas_importadas.get(seq)
    conta = db.get(ContaReceber, conta_id) if conta_id else None
    if conta is None:
        cliente_id = clientes.get(_codigo_cliente(doc["cod_ter"]))
        if cliente_id is None:
            r.sem_cliente += 1
            r.avisos.append(f"documento {num_doc}: cliente {_texto(doc['cod_ter'])} não foi importado; ficou de fora")
            return
        criado = _data(doc["data_doc"]) or _data(parcelas[0]["venc_itd"]) or date.today()
        conta = ContaReceber(
            empresa_id=empresa.id, cliente_id=cliente_id, venda_id=None,
            valor=sum((_dinheiro(p["valor_itd"]) for p in parcelas), ZERO),
            historico=(_texto(doc["historico_doc"]) or f"Documento {num_doc}")[:80],
            usuario_id=usuarios.get(_texto(doc["cod_usu"])),
            origem=_ORIGENS.get(_texto(doc["esp_doc"]).upper(), "avulso"), documento_legado=num_doc[:20],
            criado_em=datetime.combine(criado, datetime.min.time()),
        )
        db.add(conta)
        db.flush()
        db.add(MapaLegado(tabela="tab_doc", empresa_id=empresa.id, codigo=seq, novo_id=conta.id))
        contas_importadas[seq] = conta.id
        r.contas += 1

    # o número da parcela é o do VB6; se repetir no documento, renumera na ordem do vencimento
    numeros = [int(p["parcela_itd"] or 0) for p in parcelas]
    renumerar = len(set(numeros)) != len(numeros) or 0 in numeros
    if renumerar:
        r.avisos.append(f"documento {num_doc}: números de parcela repetidos ou vazios no VB6; renumeradas de 1 a {len(parcelas)}")
    for ordem, p in enumerate(parcelas, start=1):
        seq_itd = p["seq_itd"].strip()
        vencimento = _data(p["venc_itd"]) or _data(p["vencini_itd"])
        if vencimento is None:
            r.avisos.append(f"documento {num_doc}, parcela {p['parcela_itd']}: sem vencimento no VB6, não importada")
            continue
        valor = _dinheiro(p["valor_itd"])
        aberto = max(_dinheiro(p["reman_itd"]), ZERO)
        if aberto > valor:
            r.avisos.append(f"documento {num_doc}, parcela {p['parcela_itd']}: falta pagar {aberto}, mais que o valor {valor}")
        if aberto:
            r.em_aberto += aberto
            r.parcelas_em_aberto += 1
        parcela_id = parcelas_importadas.get(seq_itd)
        parcela = db.get(ParcelaReceber, parcela_id) if parcela_id else None
        if parcela is None:
            parcela = ParcelaReceber(numero=ordem if renumerar else int(p["parcela_itd"]), vencimento=vencimento,
                                     valor=valor, aberto=aberto)
            conta.parcelas.append(parcela)
            db.flush()
            db.add(MapaLegado(tabela="tab_itdoc", empresa_id=empresa.id, codigo=seq_itd, novo_id=parcela.id))
            parcelas_importadas[seq_itd] = parcela.id
            r.parcelas += 1
        elif (parcela.vencimento, parcela.valor, parcela.aberto) != (vencimento, valor, aberto):
            if parcela.id in recebidas:
                r.avisos.append(f"documento {num_doc}, parcela {parcela.numero}: já recebida no sistema novo; "
                                "a mudança do VB6 não foi aplicada")
                continue
            parcela.vencimento, parcela.valor, parcela.aberto = vencimento, valor, aberto
            r.atualizadas += 1
    conta.valor = sum((p.valor for p in conta.parcelas), ZERO)
