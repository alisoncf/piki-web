"""Regras das notas fiscais (D29): numeração, emissão da NFC-e da venda, consulta e cancelamento.

A nota é gravada como pendente antes de ir para a SEFAZ: se a resposta se perder, ela continua
lá com o mesmo número e a mesma chave, e retransmitir manda o mesmo XML (a SEFAZ responde
"duplicidade" se já tinha autorizado, e aí a consulta traz o protocolo). Rejeitada, a nota é
montada de novo com os dados corrigidos (o NCM do produto...) e o mesmo número.
"""
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import configuracao
from app.dominios.acesso.modelos import Usuario
from app.dominios.caixa.modelos import TIPOS_DE_FORMA
from app.dominios.empresas.modelos import Empresa
from app.dominios.estoque.modelos import Estoque
from app.dominios.fiscal import nfce, sefaz
from app.dominios.fiscal.modelos import (
    AUTORIZADA, CANCELADA, DENEGADA, INUTILIZADA, PENDENTE, REJEITADA, InutilizacaoNota, NotaFiscal, NumeracaoNota,
)
from app.dominios.vendas.modelos import Venda
from app.nucleo import segredos
from app.nucleo.documentos import so_digitos

ZERO = Decimal("0.00")


class ErroNota(Exception):
    """Erro de regra das notas; a mensagem vai para o usuário."""


class NaoEncontrada(ErroNota):
    pass


class DadoInvalido(ErroNota):
    pass


class SefazFora(ErroNota):
    """A SEFAZ não respondeu. A nota, se já foi gravada, fica pendente."""


def numeracoes(db: Session, empresa_id: int) -> list[NumeracaoNota]:
    return list(db.scalars(select(NumeracaoNota).where(NumeracaoNota.empresa_id == empresa_id)
                           .order_by(NumeracaoNota.ambiente, NumeracaoNota.modelo.desc(), NumeracaoNota.serie)))


def proximo_numero(db: Session, empresa_id: int, modelo: str, serie: int, ambiente: str = "1") -> int:
    """Reserva o próximo número da série (trava a linha até o fim da transação: dois caixas não pegam o mesmo).
    Quem chama grava."""
    numeracao = db.scalar(select(NumeracaoNota).where(
        NumeracaoNota.empresa_id == empresa_id, NumeracaoNota.ambiente == ambiente,
        NumeracaoNota.modelo == modelo, NumeracaoNota.serie == serie).with_for_update())
    if numeracao is None:
        numeracao = NumeracaoNota(empresa_id=empresa_id, ambiente=ambiente, modelo=modelo, serie=serie, ultimo=0)
        db.add(numeracao)
    numeracao.ultimo += 1
    db.flush()
    return numeracao.ultimo


def continuar_de(db: Session, empresa_id: int, modelo: str, serie: int, ultimo: int) -> bool:
    """A numeração de produção continua de onde o VB6 parou: só sobe, nunca volta. Devolve se mudou."""
    numeracao = db.scalar(select(NumeracaoNota).where(
        NumeracaoNota.empresa_id == empresa_id, NumeracaoNota.ambiente == "1",
        NumeracaoNota.modelo == modelo, NumeracaoNota.serie == serie))
    if numeracao is None:
        db.add(NumeracaoNota(empresa_id=empresa_id, ambiente="1", modelo=modelo, serie=serie, ultimo=ultimo))
        return True
    if ultimo > numeracao.ultimo:
        numeracao.ultimo = ultimo
        return True
    return False


# --- conexão com a SEFAZ ---

def _segredo(cifrado: str) -> str:
    try:
        return segredos.decifrar(cifrado)
    except segredos.SemChave as e:
        raise DadoInvalido(str(e))


def certificado(empresa: Empresa) -> tuple[bytes, str]:
    if not empresa.certificado_arquivo or not empresa.certificado_senha:
        raise DadoInvalido("A loja não tem certificado digital: envie-o na ficha da empresa")
    if empresa.certificado_validade and empresa.certificado_validade < datetime.now():
        raise DadoInvalido(f"O certificado da loja venceu em {empresa.certificado_validade:%d/%m/%Y}")
    arquivo = Path(configuracao().certificados_pasta) / empresa.certificado_arquivo
    if not arquivo.exists():
        raise DadoInvalido("O arquivo do certificado não está na pasta do servidor: envie-o de novo")
    return arquivo.read_bytes(), _segredo(empresa.certificado_senha)


def conectar(empresa: Empresa) -> sefaz.Sefaz:
    """Os testes trocam esta função pela SEFAZ de mentira."""
    pfx, senha = certificado(empresa)
    return sefaz.Sefaz(empresa.nfe_ambiente, pfx, senha)


def _chamar(funcao, *args):
    try:
        return funcao(*args)
    except sefaz.SemConexao as e:
        raise SefazFora(str(e))


def status(db: Session, empresa_id: int) -> sefaz.Retorno:
    """Testa o certificado e a conexão: a SEFAZ responde 107 quando está em operação."""
    empresa = db.get(Empresa, empresa_id)
    if empresa is None:
        raise NaoEncontrada("Empresa não encontrada")
    return _chamar(conectar(empresa).status)


# --- NFC-e da venda ---

def _emitente(empresa: Empresa) -> nfce.Emitente:
    cidade = empresa.cidade
    return nfce.Emitente(
        cnpj=empresa.cnpj or "", razao_social=empresa.razao_social or empresa.nome, nome_fantasia=empresa.nome_fantasia,
        inscricao_estadual=so_digitos(empresa.inscricao_estadual or ""), logradouro=empresa.logradouro or "",
        numero=empresa.numero or "", complemento=empresa.complemento, bairro=empresa.bairro or "",
        codigo_municipio=cidade.codigo_ibge if cidade else "", municipio=cidade.nome if cidade else "",
        uf=cidade.uf if cidade else "GO", cep=so_digitos(empresa.cep or ""),
        telefone=so_digitos(empresa.telefone or "") or None, crt=empresa.crt or "1")


def _gtin(produto) -> str | None:
    validos = [c.codigo for c in produto.codigos_barras if nfce.gtin_valido(c.codigo)]
    return validos[0] if validos else None


def _itens(db: Session, venda: Venda) -> list[nfce.ItemNota]:
    impostos = {e.produto_id: e for e in db.scalars(select(Estoque).where(
        Estoque.empresa_id == venda.empresa_id, Estoque.produto_id.in_([i.produto_id for i in venda.itens])))}
    itens = []
    for item in sorted(venda.itens, key=lambda i: i.ordem):
        produto, estoque = item.produto, impostos.get(item.produto_id)
        itens.append(nfce.ItemNota(
            codigo=str(produto.codigo), gtin=_gtin(produto), descricao=item.descricao, ncm=produto.ncm,
            cest=produto.cest, cfop=(estoque and estoque.cfop) or "5102", unidade=produto.unidade or "UN",
            quantidade=item.quantidade, preco=item.preco, bruto=item.total + item.desconto, desconto=item.desconto,
            origem=produto.origem or 0, csosn=(estoque and estoque.cst_csosn) or "102"))
    return itens


def _pagamentos(venda: Venda) -> tuple[list[nfce.PagamentoNota], Decimal]:
    """As formas da venda com o código da NFC-e (tPag); o dinheiro vai com o que o cliente deu, e o troco à parte.
    O que ficou no carnê vai como crédito da loja."""
    troco = venda.troco or ZERO
    pagamentos = []
    for p in sorted(venda.pagamentos, key=lambda p: p.ordem):
        tipo = p.forma_pagamento.tipo
        valor = p.valor + troco if tipo == "dinheiro" and troco > 0 else p.valor
        pagamentos.append(nfce.PagamentoNota(TIPOS_DE_FORMA[tipo][1], valor, p.forma_pagamento.nome))
    if venda.a_prazo > 0:
        pagamentos.append(nfce.PagamentoNota(TIPOS_DE_FORMA["crediario"][1], venda.a_prazo))
    if not pagamentos:
        pagamentos.append(nfce.PagamentoNota("90", ZERO))  # sem pagamento
    return pagamentos, max(troco, ZERO)


def _destinatario(venda: Venda) -> tuple[str | None, str | None]:
    if venda.cliente is not None and venda.cliente.cpf_cnpj:
        return venda.cliente.cpf_cnpj, venda.cliente.nome
    if venda.consumidor is not None and venda.consumidor.cpf:
        return venda.consumidor.cpf, venda.consumidor.nome
    return None, None


def _montar(db: Session, venda: Venda, nota: NotaFiscal, empresa: Empresa) -> str:
    """O XML assinado da nota, conferido com o esquema oficial."""
    if not empresa.csc_id or not empresa.csc_token:
        raise DadoInvalido("A loja não tem o CSC da NFC-e: cadastre-o na ficha da empresa")
    documento, nome = _destinatario(venda)
    pagamentos, troco = _pagamentos(venda)
    dados = nfce.DadosNfce(
        emitente=_emitente(empresa), ambiente=nota.ambiente, serie=nota.serie, numero=nota.numero,
        emissao=nota.emitida_em, itens=_itens(db, venda), pagamentos=pagamentos, outros=venda.taxa_entrega,
        troco=troco, cpf_cnpj_destinatario=documento, nome_destinatario=nome,
        informacoes=f"Venda {venda.numero}", codigo_numerico=nota.codigo_numerico)
    try:
        chave, xml = nfce.montar(dados)
    except nfce.NotaInvalida as e:
        raise DadoInvalido(str(e))
    xml = nfce.com_qrcode(xml, chave, nota.ambiente, empresa.csc_id, _segredo(empresa.csc_token))
    pfx, senha = certificado(empresa)
    assinado = sefaz.assinar(xml, pfx, senha, chave)
    erros = sefaz.erros_de_leiaute(assinado)
    if erros:
        raise DadoInvalido("A nota não passou na conferência do leiaute: " + "; ".join(erros)[:500])
    nota.chave, nota.xml, nota.valor = chave, assinado, venda.total
    return assinado


def _aplicar(db: Session, nota: NotaFiscal, retorno: sefaz.Retorno, conexao: sefaz.Sefaz) -> None:
    """Põe a resposta da SEFAZ na nota."""
    if retorno.codigo == sefaz.DUPLICIDADE:  # já estava autorizada: a consulta traz o protocolo
        retorno = _chamar(conexao.consultar, nota.chave)
    nota.codigo_retorno, nota.motivo_retorno = retorno.codigo, (retorno.motivo or "")[:255]
    if retorno.codigo in (sefaz.AUTORIZADA, sefaz.AUTORIZADA_FORA_DO_PRAZO, sefaz.CANCELADA,
                          sefaz.CANCELADA_FORA_DO_PRAZO) and retorno.xml_protocolo:
        if nota.situacao != AUTORIZADA:
            nota.xml = sefaz.com_protocolo(nota.xml, retorno.xml_protocolo)
        nota.protocolo, nota.autorizada_em = retorno.protocolo, retorno.recebido_em
        nota.situacao = CANCELADA if retorno.codigo in (sefaz.CANCELADA, sefaz.CANCELADA_FORA_DO_PRAZO) else AUTORIZADA
    elif retorno.codigo in sefaz.DENEGADAS:
        nota.situacao = DENEGADA
    elif retorno.codigo == sefaz.EM_PROCESSAMENTO:
        nota.situacao = PENDENTE
    elif nota.situacao == PENDENTE:
        nota.situacao = REJEITADA
    db.commit()


def nota_da_venda(db: Session, venda_id: int) -> NotaFiscal | None:
    """A nota que vale para a venda (a última; uma cancelada só fica se não houver outra)."""
    return db.scalar(select(NotaFiscal).where(NotaFiscal.venda_id == venda_id)
                     .order_by((NotaFiscal.situacao == CANCELADA), NotaFiscal.id.desc()).limit(1))


def emitir_nfce(db: Session, empresa_id: int, usuario: Usuario, venda_id: int) -> NotaFiscal:
    """Emite a NFC-e da venda recebida, ou transmite de novo a que ficou pendente ou foi rejeitada."""
    venda = db.get(Venda, venda_id)
    if venda is None or venda.empresa_id != empresa_id:
        raise NaoEncontrada("Venda não encontrada")
    if venda.situacao != "recebida":
        raise DadoInvalido("Só se emite a nota da venda recebida")
    if venda.modelo_nota != "65":
        raise DadoInvalido("Esta venda é com NF-e (modelo 55), que ainda não sai por aqui")
    empresa = db.get(Empresa, empresa_id)
    nota = nota_da_venda(db, venda_id)
    if nota is not None and nota.situacao in (AUTORIZADA, DENEGADA):
        return nota
    conexao = conectar(empresa)
    if nota is not None and nota.situacao == PENDENTE and nota.ambiente == empresa.nfe_ambiente:
        assinado = nota.xml  # o mesmo XML: se a SEFAZ já autorizou, responde duplicidade
    else:
        nova = nota is None or nota.situacao in (CANCELADA, INUTILIZADA) or nota.ambiente != empresa.nfe_ambiente
        if nova:
            caixa = venda.sessao_caixa.caixa if venda.sessao_caixa else None
            if caixa is None or not caixa.serie_nfe:
                raise DadoInvalido("O caixa que recebeu a venda não tem série das notas: configure-a nos caixas")
            nota = NotaFiscal(empresa_id=empresa_id, ambiente=empresa.nfe_ambiente, modelo="65", serie=caixa.serie_nfe,
                              codigo_numerico=nfce.novo_codigo_numerico(), venda_id=venda.id)
            nota.numero = proximo_numero(db, empresa_id, "65", nota.serie, nota.ambiente)
        nota.emitida_em, nota.emitida_por = datetime.now().replace(microsecond=0), usuario
        try:
            assinado = _montar(db, venda, nota, empresa)
        except ErroNota as e:
            if nova:  # nem chegou a existir: o número volta
                db.rollback()
            else:
                nota.situacao, nota.codigo_retorno, nota.motivo_retorno = REJEITADA, None, str(e)[:255]
                db.commit()
            raise
        nota.situacao = PENDENTE
        db.add(nota)
    db.commit()  # gravada antes de ir: se a resposta se perder, a nota está aqui para consultar
    _aplicar(db, nota, _chamar_pendente(db, nota, conexao.autorizar, assinado), conexao)
    return nota


def _chamar_pendente(db: Session, nota: NotaFiscal, funcao, *args) -> sefaz.Retorno:
    try:
        return funcao(*args)
    except sefaz.SemConexao as e:
        nota.situacao, nota.motivo_retorno = PENDENTE, str(e)[:255]
        db.commit()
        raise SefazFora(f"{e} A nota ficou pendente: consulte ou transmita de novo.")


def obter(db: Session, empresa_id: int, nota_id: int) -> NotaFiscal:
    nota = db.get(NotaFiscal, nota_id)
    if nota is None or nota.empresa_id != empresa_id:
        raise NaoEncontrada("Nota não encontrada")
    return nota


def consultar(db: Session, empresa_id: int, nota_id: int) -> NotaFiscal:
    """Pergunta à SEFAZ a situação da nota pela chave (a pendente vira autorizada, se foi)."""
    nota = obter(db, empresa_id, nota_id)
    conexao = conectar(db.get(Empresa, empresa_id))
    retorno = _chamar(conexao.consultar, nota.chave)
    if retorno.codigo == "217" and nota.situacao == PENDENTE:  # a SEFAZ não tem a nota: não chegou lá
        nota.situacao = REJEITADA
        nota.codigo_retorno, nota.motivo_retorno = retorno.codigo, retorno.motivo[:255]
        db.commit()
        return nota
    if retorno.codigo in (sefaz.AUTORIZADA, sefaz.AUTORIZADA_FORA_DO_PRAZO, sefaz.CANCELADA, sefaz.CANCELADA_FORA_DO_PRAZO):
        _aplicar(db, nota, retorno, conexao)
    else:
        nota.codigo_retorno, nota.motivo_retorno = retorno.codigo, retorno.motivo[:255]
        db.commit()
    return nota


def cancelar(db: Session, empresa_id: int, usuario: Usuario, nota_id: int, justificativa: str) -> NotaFiscal:
    """Cancela a nota autorizada na SEFAZ (no prazo dela). A venda não muda: cancelar a venda é outra tela."""
    nota = obter(db, empresa_id, nota_id)
    if nota.situacao != AUTORIZADA:
        raise DadoInvalido("Só se cancela a nota autorizada")
    justificativa = " ".join(justificativa.split())
    if not 15 <= len(justificativa) <= 255:
        raise DadoInvalido("A justificativa do cancelamento precisa ter de 15 a 255 letras")
    empresa = db.get(Empresa, empresa_id)
    conexao = conectar(empresa)
    retorno = _chamar(conexao.cancelar, nota.chave, nota.protocolo, justificativa, empresa.cnpj)
    nota.codigo_retorno, nota.motivo_retorno = retorno.codigo, (retorno.motivo or "")[:255]
    if retorno.codigo in sefaz.EVENTO_REGISTRADO:
        nota.situacao = CANCELADA
        nota.cancelada_em, nota.cancelada_por = retorno.recebido_em or datetime.now(), usuario
        nota.justificativa_cancelamento, nota.protocolo_cancelamento = justificativa, retorno.protocolo
        nota.xml_cancelamento = retorno.xml_protocolo
        db.commit()
        return nota
    db.commit()
    raise DadoInvalido(f"A SEFAZ não cancelou: {retorno.codigo} - {retorno.motivo}")


# --- inutilização: os números da série que não vão ser usados ---

@dataclass
class Lacunas:
    faixas: list[tuple[int, int]]  # de, até
    pendentes: list[int]  # notas sem resposta da SEFAZ no meio: consultar antes de inutilizar


def series(db: Session, empresa_id: int, ambiente: str) -> list[NumeracaoNota]:
    return [n for n in numeracoes(db, empresa_id) if n.ambiente == ambiente]


def _numeracao(db: Session, empresa_id: int, ambiente: str, modelo: str, serie: int) -> NumeracaoNota | None:
    return db.scalar(select(NumeracaoNota).where(
        NumeracaoNota.empresa_id == empresa_id, NumeracaoNota.ambiente == ambiente,
        NumeracaoNota.modelo == modelo, NumeracaoNota.serie == serie))


def _da_serie(modelo_classe, empresa_id: int, ambiente: str, modelo: str, serie: int):
    return (modelo_classe.empresa_id == empresa_id, modelo_classe.ambiente == ambiente,
            modelo_classe.modelo == modelo, modelo_classe.serie == serie)


def lacunas(db: Session, empresa_id: int, ambiente: str, modelo: str, serie: int, desde: date) -> Lacunas:
    """Como no VB6 (frmInutilizarNFe): os números pulados na série, da primeira nota emitida desde a data até o último
    número reservado. Contam como usados os das notas autorizadas, canceladas, denegadas e pendentes, e os já
    inutilizados; os das rejeitadas (nunca autorizadas) são lacuna."""
    numeracao = _numeracao(db, empresa_id, ambiente, modelo, serie)
    inicio = db.scalar(select(func.min(NotaFiscal.numero)).where(
        *_da_serie(NotaFiscal, empresa_id, ambiente, modelo, serie),
        NotaFiscal.emitida_em >= datetime.combine(desde, time.min)))
    if numeracao is None or inicio is None:
        return Lacunas([], [])
    notas = db.execute(select(NotaFiscal.numero, NotaFiscal.situacao).where(
        *_da_serie(NotaFiscal, empresa_id, ambiente, modelo, serie), NotaFiscal.numero >= inicio)).all()
    usados = {numero for numero, situacao in notas if situacao not in (REJEITADA, INUTILIZADA)}
    for faixa in db.scalars(select(InutilizacaoNota).where(
            *_da_serie(InutilizacaoNota, empresa_id, ambiente, modelo, serie), InutilizacaoNota.final >= inicio)):
        usados.update(range(faixa.inicial, faixa.final + 1))
    faixas, aberta = [], None
    for numero in range(inicio, numeracao.ultimo + 2):  # o +2 fecha a última faixa
        livre = numero <= numeracao.ultimo and numero not in usados
        if livre and aberta is None:
            aberta = numero
        elif not livre and aberta is not None:
            faixas.append((aberta, numero - 1))
            aberta = None
    pendentes = sorted(numero for numero, situacao in notas if situacao == PENDENTE)
    return Lacunas(faixas, pendentes)


def inutilizacoes(db: Session, empresa_id: int, limite: int = 100) -> list[InutilizacaoNota]:
    return list(db.scalars(select(InutilizacaoNota).where(InutilizacaoNota.empresa_id == empresa_id)
                           .order_by(InutilizacaoNota.id.desc()).limit(limite)))


def inutilizar(db: Session, empresa_id: int, usuario: Usuario, modelo: str, serie: int, inicial: int, final: int,
               justificativa: str) -> InutilizacaoNota:
    """Pede à SEFAZ a inutilização da faixa. Só números já reservados e sem nota que valha (autorizada, cancelada,
    denegada ou pendente); as rejeitadas da faixa ficam inutilizadas."""
    empresa = db.get(Empresa, empresa_id)
    ambiente = empresa.nfe_ambiente
    justificativa = " ".join(justificativa.split())
    if not 15 <= len(justificativa) <= 255:
        raise DadoInvalido("A justificativa da inutilização precisa ter de 15 a 255 letras")
    if not 1 <= inicial <= final:
        raise DadoInvalido("A faixa vai do número inicial até o final")
    numeracao = _numeracao(db, empresa_id, ambiente, modelo, serie)
    if numeracao is None or final > numeracao.ultimo:
        raise DadoInvalido(f"A série {serie} só chegou ao número {numeracao.ultimo if numeracao else 0}: "
                           "não se inutiliza número que ainda vai ser usado")
    na_faixa = list(db.scalars(select(NotaFiscal).where(
        *_da_serie(NotaFiscal, empresa_id, ambiente, modelo, serie), NotaFiscal.numero.between(inicial, final))))
    usadas = [n for n in na_faixa if n.situacao not in (REJEITADA, INUTILIZADA)]
    if usadas:
        n = usadas[0]
        raise DadoInvalido(f"O número {n.numero} é de uma nota {n.situacao}" +
                           (": consulte-a na SEFAZ antes" if n.situacao == PENDENTE else ""))
    if db.scalar(select(InutilizacaoNota.id).where(
            *_da_serie(InutilizacaoNota, empresa_id, ambiente, modelo, serie),
            InutilizacaoNota.inicial <= final, InutilizacaoNota.final >= inicial).limit(1)):
        raise DadoInvalido("Parte desta faixa já foi inutilizada")
    retorno = _chamar(conectar(empresa).inutilizar, empresa.cnpj, modelo, serie, inicial, final, justificativa)
    if retorno.codigo != sefaz.INUTILIZACAO_HOMOLOGADA:
        raise DadoInvalido(f"A SEFAZ não inutilizou: {retorno.codigo} - {retorno.motivo}")
    feita = InutilizacaoNota(empresa_id=empresa_id, ambiente=ambiente, modelo=modelo, serie=serie, inicial=inicial,
                             final=final, justificativa=justificativa, protocolo=retorno.protocolo,
                             homologada_em=retorno.recebido_em, feita_por=usuario, xml=retorno.xml_protocolo)
    db.add(feita)
    for nota in na_faixa:
        nota.situacao = INUTILIZADA
    db.commit()
    return feita


@dataclass
class Filtros:
    inicio: date | None = None
    fim: date | None = None
    situacao: str | None = None
    numero: int | None = None
    serie: int | None = None


def listar(db: Session, empresa_id: int, filtros: Filtros, limite: int = 200) -> list[NotaFiscal]:
    consulta = select(NotaFiscal).where(NotaFiscal.empresa_id == empresa_id)
    if filtros.inicio:
        consulta = consulta.where(NotaFiscal.emitida_em >= datetime.combine(filtros.inicio, time.min))
    if filtros.fim:
        consulta = consulta.where(NotaFiscal.emitida_em <= datetime.combine(filtros.fim, time.max))
    if filtros.situacao:
        consulta = consulta.where(NotaFiscal.situacao == filtros.situacao)
    if filtros.numero:
        consulta = consulta.where(NotaFiscal.numero == filtros.numero)
    if filtros.serie:
        consulta = consulta.where(NotaFiscal.serie == filtros.serie)
    return list(db.scalars(consulta.order_by(NotaFiscal.emitida_em.desc(), NotaFiscal.id.desc()).limit(limite)))
