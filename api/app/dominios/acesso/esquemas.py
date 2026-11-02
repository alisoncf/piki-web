from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dominios.empresas.esquemas import EmpresaResumo


class UsuarioResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    nome: str
    administrador: bool
    trocar_senha: bool = Field(description="Senha provisória: o front leva para a troca de senha antes de tudo")


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


class PerfilResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class AcessoEmpresa(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    empresa: EmpresaResumo
    perfil: PerfilResumo
    ativo: bool


class FuncionarioDoUsuario(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    apelido: str | None


class UsuarioDetalhe(UsuarioResumo):
    """Uma linha da lista de usuários, e a ficha."""

    email: str | None
    ativo: bool
    bloqueado_ate: datetime | None = Field(description="Preenchido enquanto o login estiver bloqueado")
    ultimo_login: datetime | None
    funcionario: FuncionarioDoUsuario | None
    acessos: list[AcessoEmpresa]


def _limpar(v: object) -> object:
    return (v.strip() or None) if isinstance(v, str) else v


class UsuarioDados(BaseModel):
    """O que se altera na ficha do usuário. A senha e os acessos têm rotas próprias."""

    login: str = Field(min_length=1, max_length=30, pattern=r"^\S+$", description="Sem espaços")
    nome: str = Field(min_length=1, max_length=80)
    email: str | None = Field(default=None, max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    funcionario_id: int | None = Field(default=None, description="O funcionário que usa este login")
    ativo: bool = True
    administrador: bool = Field(default=False, description="Acesso total a todas as empresas; só administrador muda")

    @field_validator("login", "nome", "email", mode="before")
    @classmethod
    def _sem_espacos_nas_pontas(cls, v: object) -> object:
        return _limpar(v)

    @field_validator("email")
    @classmethod
    def _email_minusculo(cls, v: str | None) -> str | None:
        return v.lower() if v else v


class UsuarioNovo(UsuarioDados):
    senha: str = Field(min_length=1, max_length=100, description="Provisória: o usuário troca no primeiro login")
    perfil_id: int | None = Field(default=None, description="Perfil na empresa ativa (obrigatório para quem não é administrador)")


class PedidoSenhaProvisoria(BaseModel):
    senha: str = Field(min_length=1, max_length=100)


class PedidoTrocaSenha(BaseModel):
    senha_atual: str = Field(min_length=1, max_length=100)
    senha_nova: str = Field(min_length=1, max_length=100)


class AcessoDados(BaseModel):
    perfil_id: int
    ativo: bool = True


class Permissao(BaseModel):
    codigo: str
    descricao: str
    area: str = Field(description="Nome da área, para agrupar na tela")


class PerfilDados(BaseModel):
    nome: str = Field(min_length=1, max_length=50)
    descricao: str | None = Field(default=None, max_length=150)
    permissoes: list[str] = []

    @field_validator("nome", "descricao", mode="before")
    @classmethod
    def _sem_espacos_nas_pontas(cls, v: object) -> object:
        return _limpar(v)


class Perfil(BaseModel):
    id: int
    nome: str
    descricao: str | None
    permissoes: list[str]
    usuarios: int = Field(description="Quantos acessos (usuário numa empresa) usam o perfil")
