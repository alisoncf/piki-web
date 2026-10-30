from pydantic import BaseModel, ConfigDict, Field


class EmpresaResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nome: str
    cor: str = Field(validation_alias="cor_hex", serialization_alias="cor",
                     description="Cor de identificação da empresa na tela (#rrggbb)")


class UsuarioResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    nome: str
    administrador: bool


class PedidoLogin(BaseModel):
    login: str = Field(min_length=1, max_length=30)
    senha: str = Field(min_length=1, max_length=100)
    empresa_id: int | None = Field(default=None, description="Empresa em que vai entrar. Opcional se o usuário só tem uma.")


class PedidoTrocaEmpresa(BaseModel):
    empresa_id: int


class RespostaSessao(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResumo
    empresa: EmpresaResumo | None = Field(description="Empresa ativa. Nula quando o usuário precisa escolher.")
    empresas: list[EmpresaResumo] = Field(description="Empresas que o usuário pode acessar")
    ultima_empresa_id: int | None = Field(description="Sugestão para pré-selecionar na escolha")


class RespostaEu(BaseModel):
    usuario: UsuarioResumo
    empresa: EmpresaResumo | None
    permissoes: list[str]
    empresas: list[EmpresaResumo]


class AcessoEmpresa(BaseModel):
    empresa: EmpresaResumo
    perfil: str
    ativo: bool


class UsuarioDetalhe(UsuarioResumo):
    ativo: bool
    acessos: list[AcessoEmpresa]
