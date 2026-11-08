"""Importa as comissões dos acertos de uma loja do VB6 (D30): tab_comissparc, todo o histórico. Rode depois dos
representantes e das contas a receber.

- Cada linha vira uma comissão, paga (status_com 2) ou em aberto (1), como está no VB6. Os acertos antigos não vêm:
  o número, a data, o cliente e a parcela ficam na própria comissão, para o relatório. A linha só se liga à parcela
  do sistema novo se o carnê foi importado (os quitados não são).
- As linhas pagas viram pagamentos, um por lançamento de caixa do VB6 (seq_cai), com a data do caixa.
- As de cheque (tipo_com 2) entram também, com a parcela "cheque 2/5", ainda que o sistema novo não tenha cheques.
- Rodar de novo acrescenta as linhas novas, atualiza valor e vencimento das que seguem sem nada pago e dá baixa nas
  que foram pagas no VB6 depois. O que já foi pago no sistema novo não é mexido (aviso).
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Connection, bindparam, insert, select, text
from sqlalchemy.orm import Session

from app.dominios.consignacao.modelos import BaixaComissao, ComissaoParcela, PagamentoComissao
from app.dominios.empresas.modelos import Empresa
from app.nucleo.textos import nome_proprio
from etl.funcionarios import EmpresaNaoImportada
from etl.receber import _data, _dinheiro, _mapa, _texto

ZERO = Decimal("0.00")
LOTE = 5000
_LINHAS = text("""
    SELECT CAST(tc.seq_itd AS CHAR) seq_itd, CAST(tc.seq_ace AS CHAR) seq_ace, tc.valor_com,
           CAST(tc.venc_com AS CHAR) venc_com, CAST(tc.status_com AS CHAR) status_com, CAST(tc.cod_rep AS CHAR) cod_rep,
           CAST(tc.tipo_com AS CHAR) tipo_com, CAST(tc.seq_cai AS CHAR) seq_cai, CAST(ta.data_ace AS CHAR) data_ace,
           CAST(cli.nome_cli AS CHAR) nome_cli, ti.parcela_itd, ti.valor_itd, td.parcelas_doc
      FROM tab_comissparc tc
      LEFT JOIN tab_acertos ta ON ta.seq_ace = tc.seq_ace
      LEFT JOIN tab_clientes cli ON cli.cod_cli = ta.cod_cli
      LEFT JOIN tab_itdoc ti ON ti.seq_itd = tc.seq_itd AND tc.tipo_com = '1'
      LEFT JOIN tab_doc td ON td.seq_doc = ti.seq_doc
     WHERE tc.seq_itd > :ultimo ORDER BY tc.seq_itd LIMIT :quantas""")
_CHEQUES = text("""
    SELECT CAST(c.seq_che AS CHAR) seq_che, c.parc_che, c.valor_che, d.parcelas_doc
      FROM tab_cheques c LEFT JOIN tab_doc d ON d.seq_doc = c.seq_doc
     WHERE c.seq_che IN :seqs""").bindparams(bindparam("seqs", expanding=True))
_CAIXA = text("SELECT CAST(seq_cai AS CHAR) seq_cai, CAST(data_cai AS CHAR) data_cai FROM tab_caixa WHERE seq_cai IN :seqs"
              ).bindparams(bindparam("seqs", expanding=True))


@dataclass
class Resultado:
    novas: int = 0
    atualizadas: int = 0
    baixadas: int = 0  # linhas que entraram ou passaram a pagas agora
    pagamentos: int = 0  # novos
    em_aberto: int = 0
    valor_em_aberto: Decimal = ZERO
    valor_pago: Decimal = ZERO
    sem_representante: int = 0
    sem_vencimento: int = 0
    avisos: list[str] = field(default_factory=list)


def _parcela(numero: object, total: object, prefixo: str = "") -> str | None:
    if not numero:
        return None
    return f"{prefixo}{int(numero)}/{int(total)}" if total else f"{prefixo}{int(numero)}"


def _inserir(db: Session, modelo: type, linhas: list[dict]) -> None:
    # um INSERT por bloco: linha a linha, as centenas de milhares de comissões levariam muito tempo
    for i in range(0, len(linhas), 1000):
        db.execute(insert(modelo).values(linhas[i:i + 1000]))


def importar_comissoes(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()
    representantes = _mapa(db, "tab_representantes", empresa.id)
    parcelas = _mapa(db, "tab_itdoc", empresa.id)
    existentes = {c.legado: c for c in db.execute(select(
        ComissaoParcela.legado, ComissaoParcela.id, ComissaoParcela.valor, ComissaoParcela.vencimento, ComissaoParcela.pago,
    ).where(ComissaoParcela.empresa_id == empresa.id, ComissaoParcela.legado.is_not(None)))}
    sem_rep: dict[str, int] = {}
    pagas: dict[str, list[tuple[str, int, Decimal]]] = {}  # seq_cai → (seq_itd, representante, valor)

    ultimo = ""
    while True:
        lote = origem.execute(_LINHAS, {"ultimo": ultimo, "quantas": LOTE}).mappings().all()
        if not lote:
            break
        ultimo = lote[-1]["seq_itd"]
        cheques = {}
        seqs_cheque = [linha["seq_itd"] for linha in lote if _texto(linha["tipo_com"]) == "2"]
        if seqs_cheque:
            cheques = {c["seq_che"].strip(): c for c in origem.execute(_CHEQUES, {"seqs": seqs_cheque}).mappings()}
        novas, mudadas = [], []
        for linha in lote:
            seq = linha["seq_itd"].strip()
            representante_id = representantes.get(_texto(linha["cod_rep"]))
            if representante_id is None:
                r.sem_representante += 1
                sem_rep[_texto(linha["cod_rep"])] = sem_rep.get(_texto(linha["cod_rep"]), 0) + 1
                continue
            data_acerto = _data(linha["data_ace"])
            vencimento = _data(linha["venc_com"]) or data_acerto
            if vencimento is None:
                r.sem_vencimento += 1
                r.avisos.append(f"comissão {seq}: sem vencimento no VB6, não importada")
                continue
            valor = _dinheiro(linha["valor_com"])
            paga = _texto(linha["status_com"]) == "2"
            ja = existentes.get(seq)
            if ja is None:
                cheque = cheques.get(seq)
                if cheque is not None:
                    parcela, valor_parcela = _parcela(cheque["parc_che"], cheque["parcelas_doc"], "cheque "), cheque["valor_che"]
                else:
                    parcela, valor_parcela = _parcela(linha["parcela_itd"], linha["parcelas_doc"]), linha["valor_itd"]
                nome = _texto(linha["nome_cli"])
                novas.append({
                    "empresa_id": empresa.id, "representante_id": representante_id,
                    "parcela_id": parcelas.get(seq) if _texto(linha["tipo_com"]) == "1" else None, "vencimento": vencimento,
                    "valor": valor, "pago": valor if paga else ZERO, "legado": seq,
                    "acerto_legado": _texto(linha["seq_ace"])[:7] or None, "data_acerto_legado": data_acerto,
                    "cliente_legado": (nome_proprio(nome) or nome)[:80] or None, "parcela_legado": parcela,
                    "valor_parcela_legado": _dinheiro(valor_parcela) if valor_parcela is not None else None,
                })
                r.novas += 1
            elif paga and ja.pago == valor:  # já baixada (a de valor zero também cai aqui)
                r.valor_pago += valor
                continue
            elif ja.pago:
                if paga:
                    r.avisos.append(f"comissão {seq}: paga no VB6 e com outro valor pago no sistema novo; ficou como estava")
                if paga:
                    r.valor_pago += ja.pago
                else:
                    r.em_aberto += 1
                    r.valor_em_aberto += ja.valor - ja.pago
                continue
            elif paga or (ja.valor, ja.vencimento) != (valor, vencimento):
                mudadas.append({"id": ja.id, "valor": valor, "vencimento": vencimento, "pago": valor if paga else ZERO})
                r.atualizadas += 1
            if paga:
                pagas.setdefault(_texto(linha["seq_cai"]), []).append((seq, representante_id, valor))
                r.baixadas += 1
                r.valor_pago += valor
            else:
                r.em_aberto += 1
                r.valor_em_aberto += valor
        if novas:
            _inserir(db, ComissaoParcela, novas)
        if mudadas:
            db.bulk_update_mappings(ComissaoParcela, mudadas)
    _baixar(origem, db, empresa, pagas, r)
    for cod_rep, quantas in sorted(sem_rep.items()):
        r.avisos.append(f"representante {cod_rep}: não importado, {quantas} comissões de fora")
    db.commit()
    return r


def _baixar(origem: Connection, db: Session, empresa: Empresa, pagas: dict[str, list[tuple[str, int, Decimal]]],
            r: Resultado) -> None:
    """Os pagamentos do VB6, um por lançamento de caixa, com as baixas das linhas que passaram a pagas."""
    if not pagas:
        return
    ids = dict(db.execute(select(ComissaoParcela.legado, ComissaoParcela.id).where(
        ComissaoParcela.empresa_id == empresa.id, ComissaoParcela.legado.is_not(None))).all())
    pagamentos = {p.legado: p for p in db.scalars(select(PagamentoComissao).where(
        PagamentoComissao.empresa_id == empresa.id, PagamentoComissao.legado.is_not(None)))}
    caixa: dict[str, date] = {}
    seqs = sorted(s for s in pagas if s)
    for i in range(0, len(seqs), LOTE):
        for c in origem.execute(_CAIXA, {"seqs": seqs[i:i + LOTE]}).mappings():
            quando = _data(c["data_cai"])
            if quando:
                caixa[c["seq_cai"].strip()] = quando
    baixas = []
    for seq_cai, linhas in pagas.items():
        valor = sum((v for _, _, v in linhas), ZERO)
        pagamento = pagamentos.get(seq_cai)
        if pagamento is None:
            if seq_cai not in caixa:
                r.avisos.append(f"pagamento {seq_cai or '(sem número)'}: não está no caixa do VB6; ficou sem data certa")
            quando = caixa.get(seq_cai) or date(1900, 1, 1)
            pagamento = PagamentoComissao(empresa_id=empresa.id, representante_id=linhas[0][1], valor=valor,
                                          data_hora=datetime.combine(quando, datetime.min.time()), legado=seq_cai or None)
            db.add(pagamento)
            db.flush()
            r.pagamentos += 1
        else:
            pagamento.valor += valor
        baixas.extend({"pagamento_id": pagamento.id, "comissao_id": ids[seq], "valor": v} for seq, _, v in linhas)
    _inserir(db, BaixaComissao, baixas)
