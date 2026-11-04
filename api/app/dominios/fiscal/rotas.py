from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.config import configuracao
from app.dominios.empresas.modelos import Empresa, ImagemEmpresa
from app.dominios.fiscal import leiaute, servico
from app.dominios.fiscal.esquemas import (
    CancelamentoDados, Danfe, EmailDados, EmailEnviado, EmailSugerido, Faixa, Inutilizacao, InutilizacaoDados, Lacunas, Nota, Operacao, OperacaoDados,
    RetornoSefaz, Serie,
)
from app.dominios.fiscal.modelos import SITUACOES
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["notas fiscais"])

Ver = Annotated[Contexto, Depends(exige("notas.ver", "notas.emitir", "caixa.operar"))]
# o caixa emite a NFC-e da venda que recebeu
Emitir = Annotated[Contexto, Depends(exige("notas.emitir", "caixa.operar"))]
Cancelar = Annotated[Contexto, Depends(exige("notas.cancelar"))]
Inutilizar = Annotated[Contexto, Depends(exige("notas.inutilizar"))]
Configurar = Annotated[Contexto, Depends(exige("notas.configurar"))]

_STATUS = {
    servico.NaoEncontrada: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.SefazFora: status.HTTP_503_SERVICE_UNAVAILABLE,
    servico.EmailFora: status.HTTP_502_BAD_GATEWAY,
}


def _http(ctx: Contexto, erro: servico.ErroNota) -> HTTPException:
    ctx.db.rollback()
    return HTTPException(_STATUS[type(erro)], str(erro))


@router.post("/empresas/{empresa_id}/sefaz", response_model=RetornoSefaz)
def status_sefaz(empresa_id: int, ctx: Annotated[Contexto, Depends(exige("acesso.empresas"))]) -> RetornoSefaz:
    """Testa o certificado, o ambiente e a conexão da empresa com a SEFAZ (107: em operação)."""
    try:
        r = servico.status(ctx.db, empresa_id)
    except servico.ErroNota as e:
        raise _http(ctx, e)
    return RetornoSefaz(codigo=r.codigo, motivo=r.motivo)


@router.post("/vendas/{venda_id}/nota", response_model=Nota)
def emitir(venda_id: int, ctx: Emitir) -> Nota:
    """Emite a nota da venda recebida (NFC-e ou NF-e, a escolhida no recebimento); chamado de novo, transmite outra vez
    a que ficou pendente ou foi rejeitada. Rejeitada pela SEFAZ não é erro HTTP: a nota volta com a situação e o
    motivo."""
    try:
        nota = servico.emitir(ctx.db, ctx.empresa_id, ctx.usuario, venda_id)
    except servico.ErroNota as e:
        raise _http(ctx, e)
    return Nota.model_validate(nota)


@router.get("/vendas/{venda_id}/nota", response_model=Nota | None)
def nota_da_venda(venda_id: int, ctx: Ver) -> Nota | None:
    nota = servico.nota_da_venda(ctx.db, venda_id)
    if nota is None or nota.empresa_id != ctx.empresa_id:
        return None
    return Nota.model_validate(nota)


@router.get("/notas", response_model=list[Nota])
def listar(ctx: Ver, inicio: date | None = None, fim: date | None = None, situacao: str | None = None,
           numero: int | None = None, serie: int | None = None) -> list[Nota]:
    if situacao and situacao not in SITUACOES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Situação desconhecida")
    filtros = servico.Filtros(inicio, fim, situacao, numero, serie)
    return [Nota.model_validate(n) for n in servico.listar(ctx.db, ctx.empresa_id, filtros)]


def _ambiente(ctx: Contexto) -> str:
    return ctx.db.get(Empresa, ctx.empresa_id).nfe_ambiente


@router.get("/notas/operacoes", response_model=list[Operacao])
def operacoes(ctx: Annotated[Contexto, Depends(exige("notas.configurar", "notas.ver"))]) -> list[Operacao]:
    """A natureza e o CFOP de cada operação que gera nota (venda, remessa, retorno, devolução)."""
    lista = servico.operacoes(ctx.db)
    ctx.db.commit()
    return [Operacao.model_validate(o) for o in lista]


@router.put("/notas/operacoes/{operacao_id}", response_model=Operacao)
def alterar_operacao(operacao_id: int, dados: OperacaoDados, ctx: Configurar) -> Operacao:
    try:
        operacao = servico.alterar_operacao(ctx.db, operacao_id, dados.natureza, dados.tipo, dados.finalidade,
                                            dados.cfop_estado, dados.cfop_fora)
    except servico.ErroNota as e:
        raise _http(ctx, e)
    return Operacao.model_validate(operacao)


@router.get("/notas/series", response_model=list[Serie])
def series(ctx: Inutilizar) -> list[Serie]:
    """As séries da loja no ambiente atual, com o último número reservado."""
    return [Serie.model_validate(n) for n in servico.series(ctx.db, ctx.empresa_id, _ambiente(ctx))]


@router.get("/notas/lacunas", response_model=Lacunas)
def lacunas(ctx: Inutilizar, serie: int, desde: date, modelo: str = "65") -> Lacunas:
    """Os números pulados da série, da primeira nota emitida desde a data até o último reservado (como no VB6)."""
    achadas = servico.lacunas(ctx.db, ctx.empresa_id, _ambiente(ctx), modelo, serie, desde)
    return Lacunas(faixas=[Faixa(inicial=i, final=f) for i, f in achadas.faixas], pendentes=achadas.pendentes)


@router.get("/notas/inutilizacoes", response_model=list[Inutilizacao])
def inutilizacoes(ctx: Inutilizar) -> list[Inutilizacao]:
    return [Inutilizacao.model_validate(i) for i in servico.inutilizacoes(ctx.db, ctx.empresa_id)]


@router.post("/notas/inutilizacoes", response_model=Inutilizacao, status_code=status.HTTP_201_CREATED)
def inutilizar(dados: InutilizacaoDados, ctx: Inutilizar) -> Inutilizacao:
    """Pede à SEFAZ a inutilização da faixa de números."""
    try:
        feita = servico.inutilizar(ctx.db, ctx.empresa_id, ctx.usuario, dados.modelo, dados.serie, dados.inicial,
                                   dados.final, dados.justificativa)
    except servico.ErroNota as e:
        raise _http(ctx, e)
    return Inutilizacao.model_validate(feita)


def _obter(ctx: Contexto, nota_id: int):
    try:
        return servico.obter(ctx.db, ctx.empresa_id, nota_id)
    except servico.ErroNota as e:
        raise _http(ctx, e)


@router.get("/notas/{nota_id}", response_model=Nota)
def obter(nota_id: int, ctx: Ver) -> Nota:
    return Nota.model_validate(_obter(ctx, nota_id))


@router.get("/notas/{nota_id}/danfe", response_model=Danfe)
def danfe(nota_id: int, ctx: Ver) -> Danfe:
    """O que vai impresso no DANFE NFC-e (bobina de 80 mm), com o QR Code em SVG."""
    nota = _obter(ctx, nota_id)
    return Danfe(situacao=nota.situacao, **leiaute.danfe(nota.xml))


@router.get("/notas/{nota_id}/danfe.pdf")
def danfe_pdf(nota_id: int, ctx: Ver) -> Response:
    """O DANFE da NF-e em A4, em PDF, com o logotipo da loja."""
    nota = _obter(ctx, nota_id)
    if nota.modelo != "55":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "O DANFE em PDF é da NF-e; a NFC-e sai na bobina")
    logo = ctx.db.get(ImagemEmpresa, (nota.empresa_id, "logo"))
    conteudo = leiaute.danfe_pdf(nota.xml, logo.conteudo if logo else None, nota.situacao == "cancelada")
    return Response(conteudo, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{nota.chave}.pdf"'})


@router.get("/notas/{nota_id}/xml")
def xml(nota_id: int, ctx: Ver) -> Response:
    nota = _obter(ctx, nota_id)
    nome = f"{nota.chave}-{'procNFe' if nota.protocolo else 'NFe'}.xml"
    return Response(nota.xml, media_type="application/xml",
                    headers={"Content-Disposition": f'attachment; filename="{nome}"'})


@router.get("/notas/{nota_id}/email", response_model=EmailSugerido)
def email_sugerido(nota_id: int, ctx: Emitir) -> EmailSugerido:
    """Para quem vai o e-mail: o do cliente; em homologação, a conta do sistema."""
    nota = _obter(ctx, nota_id)
    if nota.ambiente == "2":
        return EmailSugerido(para=configuracao().email_usuario or None, homologacao=True)
    return EmailSugerido(para=servico.email_do_cliente(ctx.db, nota), homologacao=False)


@router.post("/notas/{nota_id}/email", response_model=EmailEnviado)
def enviar_email(nota_id: int, dados: EmailDados, ctx: Emitir) -> EmailEnviado:
    """Manda o DANFE (da NF-e, em PDF) e o XML por e-mail, pela conta do sistema."""
    try:
        return EmailEnviado(para=servico.enviar_email(ctx.db, ctx.empresa_id, nota_id, dados.para))
    except servico.ErroNota as e:
        raise _http(ctx, e)


@router.post("/notas/{nota_id}/consultar", response_model=Nota)
def consultar(nota_id: int, ctx: Emitir) -> Nota:
    """Pergunta à SEFAZ a situação da nota pela chave."""
    try:
        return Nota.model_validate(servico.consultar(ctx.db, ctx.empresa_id, nota_id))
    except servico.ErroNota as e:
        raise _http(ctx, e)


@router.post("/notas/{nota_id}/cancelar", response_model=Nota)
def cancelar(nota_id: int, dados: CancelamentoDados, ctx: Cancelar) -> Nota:
    """Cancela a nota autorizada na SEFAZ. A venda continua como está (cancelar a venda é na tela da venda)."""
    try:
        return Nota.model_validate(servico.cancelar(ctx.db, ctx.empresa_id, ctx.usuario, nota_id, dados.justificativa))
    except servico.ErroNota as e:
        raise _http(ctx, e)
