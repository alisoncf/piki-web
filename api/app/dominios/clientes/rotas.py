from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dominios.clientes import repositorio as repo
from app.dominios.clientes import servico
from app.dominios.clientes.esquemas import (
    AnotacaoDados, Cliente, ClienteDados, ClienteResumo, GrupoCliente, GrupoClienteDados, Orgao, OrgaoDados,
    PaginaClientes, Parentesco, ParentescoDados, Setor, SetorDados,
)
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["clientes"])

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicado: status.HTTP_409_CONFLICT,
}

Ver = Annotated[Contexto, Depends(exige("clientes.ver"))]
Editar = Annotated[Contexto, Depends(exige("clientes.editar"))]


def _http(erro: servico.ErroCliente) -> HTTPException:
    return HTTPException(_STATUS[type(erro)], str(erro))


@router.get("/clientes", response_model=PaginaClientes)
def listar_clientes(
    ctx: Ver,
    busca: Annotated[str | None, Query(description="Parte do nome, início do CPF/CNPJ ou final do telefone")] = None,
    setor_id: int | None = None,
    orgao_id: int | None = None,
    bloqueado: bool | None = None,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
) -> PaginaClientes:
    """Clientes de todas as lojas (cadastro global), uma página por vez."""
    itens, total = repo.listar_clientes(ctx.db, busca, setor_id, orgao_id, bloqueado, limite, deslocamento)
    return PaginaClientes(itens=[ClienteResumo.model_validate(c) for c in itens], total=total)


@router.get("/clientes/{cliente_id}", response_model=Cliente)
def obter_cliente(cliente_id: int, ctx: Ver) -> Cliente:
    try:
        return Cliente.model_validate(servico.obter_cliente(ctx.db, cliente_id))
    except servico.ErroCliente as e:
        raise _http(e)


@router.post("/clientes", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def criar_cliente(dados: ClienteDados, ctx: Editar) -> Cliente:
    """Cadastra o cliente, registrando a loja ativa como a loja do cadastro."""
    try:
        return Cliente.model_validate(servico.criar_cliente(ctx.db, dados, ctx.empresa_id))
    except servico.ErroCliente as e:
        raise _http(e)


@router.put("/clientes/{cliente_id}", response_model=Cliente)
def alterar_cliente(cliente_id: int, dados: ClienteDados, ctx: Editar) -> Cliente:
    """Altera o cadastro. Telefones e referências enviados substituem os que existiam."""
    try:
        return Cliente.model_validate(servico.alterar_cliente(ctx.db, cliente_id, dados))
    except servico.ErroCliente as e:
        raise _http(e)


@router.post("/clientes/{cliente_id}/anotacoes", response_model=Cliente, status_code=status.HTTP_201_CREATED)
def anotar(cliente_id: int, dados: AnotacaoDados, ctx: Editar) -> Cliente:
    """Acrescenta uma anotação, com o usuário e a loja de quem anotou."""
    try:
        return Cliente.model_validate(servico.anotar(ctx.db, cliente_id, dados, ctx.usuario.id, ctx.empresa_id))
    except servico.ErroCliente as e:
        raise _http(e)


@router.get("/setores", response_model=list[Setor])
def listar_setores(ctx: Ver, busca: str | None = None) -> list[Setor]:
    return [Setor.model_validate(s) for s in repo.listar_setores(ctx.db, busca)]


@router.post("/setores", response_model=Setor, status_code=status.HTTP_201_CREATED)
def criar_setor(dados: SetorDados, ctx: Editar) -> Setor:
    try:
        return Setor.model_validate(servico.criar_setor(ctx.db, dados))
    except servico.ErroCliente as e:
        raise _http(e)


@router.put("/setores/{setor_id}", response_model=Setor)
def alterar_setor(setor_id: int, dados: SetorDados, ctx: Editar) -> Setor:
    """Altera o setor. Os cobradores enviados substituem os que existiam."""
    try:
        return Setor.model_validate(servico.alterar_setor(ctx.db, setor_id, dados))
    except servico.ErroCliente as e:
        raise _http(e)


@router.get("/orgaos", response_model=list[Orgao])
def listar_orgaos(ctx: Ver, busca: str | None = None) -> list[Orgao]:
    return [Orgao.model_validate(o) for o in repo.listar_orgaos(ctx.db, busca)]


@router.post("/orgaos", response_model=Orgao, status_code=status.HTTP_201_CREATED)
def criar_orgao(dados: OrgaoDados, ctx: Editar) -> Orgao:
    try:
        return Orgao.model_validate(servico.criar_orgao(ctx.db, dados))
    except servico.ErroCliente as e:
        raise _http(e)


@router.put("/orgaos/{orgao_id}", response_model=Orgao)
def alterar_orgao(orgao_id: int, dados: OrgaoDados, ctx: Editar) -> Orgao:
    try:
        return Orgao.model_validate(servico.alterar_orgao(ctx.db, orgao_id, dados))
    except servico.ErroCliente as e:
        raise _http(e)


@router.get("/grupos-clientes", response_model=list[GrupoCliente])
def listar_grupos(ctx: Ver) -> list[GrupoCliente]:
    return [GrupoCliente.model_validate(g) for g in repo.listar_grupos(ctx.db)]


@router.post("/grupos-clientes", response_model=GrupoCliente, status_code=status.HTTP_201_CREATED)
def criar_grupo(dados: GrupoClienteDados, ctx: Editar) -> GrupoCliente:
    try:
        return GrupoCliente.model_validate(servico.criar_grupo(ctx.db, dados))
    except servico.ErroCliente as e:
        raise _http(e)


@router.get("/parentescos", response_model=list[Parentesco])
def listar_parentescos(ctx: Ver) -> list[Parentesco]:
    return [Parentesco.model_validate(p) for p in repo.listar_parentescos(ctx.db)]


@router.post("/parentescos", response_model=Parentesco, status_code=status.HTTP_201_CREATED)
def criar_parentesco(dados: ParentescoDados, ctx: Editar) -> Parentesco:
    try:
        return Parentesco.model_validate(servico.criar_parentesco(ctx.db, dados))
    except servico.ErroCliente as e:
        raise _http(e)


@router.put("/parentescos/{parentesco_id}", response_model=Parentesco)
def alterar_parentesco(parentesco_id: int, dados: ParentescoDados, ctx: Editar) -> Parentesco:
    try:
        return Parentesco.model_validate(servico.alterar_parentesco(ctx.db, parentesco_id, dados))
    except servico.ErroCliente as e:
        raise _http(e)


@router.put("/grupos-clientes/{grupo_id}", response_model=GrupoCliente)
def alterar_grupo(grupo_id: int, dados: GrupoClienteDados, ctx: Editar) -> GrupoCliente:
    try:
        return GrupoCliente.model_validate(servico.alterar_grupo(ctx.db, grupo_id, dados))
    except servico.ErroCliente as e:
        raise _http(e)
