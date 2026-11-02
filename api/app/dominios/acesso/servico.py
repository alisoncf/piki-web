"""Regras de acesso (decisão D10). Não depende de HTTP: levanta erros de domínio."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominios.acesso import repositorio as repo
from app.dominios.acesso.modelos import Perfil, Permissao, Usuario, UsuarioEmpresa
from app.dominios.empresas.modelos import Empresa
from app.dominios.funcionarios.modelos import Funcionario
from app.nucleo.permissoes import PERMISSOES
from app.nucleo.seguranca import conferir_hash, criar_token, gerar_hash


class ErroAcesso(Exception):
    """Base dos erros de acesso."""


class CredenciaisInvalidas(ErroAcesso):
    pass


class UsuarioInativo(ErroAcesso):
    pass


class SemEmpresa(ErroAcesso):
    """O usuário não tem acesso a nenhuma empresa ativa."""


class EmpresaNaoPermitida(ErroAcesso):
    pass


class UsuarioBloqueado(ErroAcesso):
    """Senha errada vezes demais seguidas: o login espera um tempo."""

    def __init__(self, ate: datetime) -> None:
        super().__init__(f"Login bloqueado por excesso de tentativas. Tente de novo às {ate:%H:%M} "
                         "ou peça ao administrador para desbloquear.")
        self.ate = ate


class NaoEncontrado(ErroAcesso):
    pass


class DadoInvalido(ErroAcesso):
    pass


class Duplicado(ErroAcesso):
    pass


class Proibido(ErroAcesso):
    """Quem não é administrador tentando mexer fora do que lhe cabe."""


# login: na quinta senha errada seguida, bloqueia por 15 minutos (o VB6 bloqueava na quarta)
TENTATIVAS = 5
MINUTOS_BLOQUEADO = 15
SENHA_MINIMA = 8


@dataclass
class SessaoAberta:
    token: str
    usuario: Usuario
    empresa: Empresa | None
    empresas: list[Empresa]


# ------------------------------------------------------------------ login


def autenticar(db: Session, login: str, senha: str) -> Usuario:
    usuario = repo.usuario_por_login(db, login)
    # a mesma mensagem para usuário inexistente e senha errada
    if usuario is None:
        raise CredenciaisInvalidas
    agora = datetime.now()
    if usuario.bloqueado_ate and usuario.bloqueado_ate > agora:
        raise UsuarioBloqueado(usuario.bloqueado_ate)
    if not conferir_hash(senha, usuario.hash_senha, usuario.senha_sem_caixa):
        usuario.tentativas_erradas = (usuario.tentativas_erradas or 0) + 1
        if usuario.tentativas_erradas >= TENTATIVAS:
            usuario.tentativas_erradas, usuario.bloqueado_ate = 0, agora + timedelta(minutes=MINUTOS_BLOQUEADO)
            db.commit()
            raise UsuarioBloqueado(usuario.bloqueado_ate)
        db.commit()
        raise CredenciaisInvalidas
    if not usuario.ativo:
        raise UsuarioInativo
    usuario.tentativas_erradas, usuario.bloqueado_ate = 0, None
    return usuario


def abrir_sessao(db: Session, usuario: Usuario, empresa_id: int | None = None) -> SessaoAberta:
    """Escolhe a empresa do login.

    Com empresa_id, entra nela (se permitido). Sem empresa_id, entra direto se
    o usuário só tem acesso a uma; se tem várias, a sessão abre sem empresa e
    o front-end pede a escolha.
    """
    empresas = repo.empresas_do_usuario(db, usuario)
    if not empresas:
        raise SemEmpresa
    if empresa_id is not None:
        empresa = next((e for e in empresas if e.id == empresa_id), None)
        if empresa is None:
            raise EmpresaNaoPermitida
    elif len(empresas) == 1:
        empresa = empresas[0]
    else:
        empresa = None

    usuario.ultimo_login = datetime.now()
    if empresa is not None:
        usuario.ultima_empresa_id = empresa.id
    db.commit()
    return SessaoAberta(criar_token(usuario.id, empresa.id if empresa else None), usuario, empresa, empresas)


def login(db: Session, login: str, senha: str, empresa_id: int | None = None) -> SessaoAberta:
    return abrir_sessao(db, autenticar(db, login, senha), empresa_id)


def trocar_empresa(db: Session, usuario: Usuario, empresa_id: int) -> SessaoAberta:
    """Saltar para outra empresa sem sair do sistema: emite um token novo."""
    return abrir_sessao(db, usuario, empresa_id)


# ------------------------------------------------------------- permissões


def pode_acessar(db: Session, usuario: Usuario, empresa_id: int) -> bool:
    if usuario.administrador:
        return repo.empresa_ativa(db, empresa_id) is not None
    return repo.acesso(db, usuario.id, empresa_id) is not None


def permissoes_na_empresa(db: Session, usuario: Usuario, empresa_id: int) -> set[str]:
    if usuario.administrador:
        return set(PERMISSOES) if repo.empresa_ativa(db, empresa_id) else set()
    vinculo = repo.acesso(db, usuario.id, empresa_id)
    if vinculo is None:
        return set()
    return {p.codigo for p in vinculo.perfil.permissoes}


def limite_de_desconto(db: Session, usuario: Usuario, empresa_id: int) -> Decimal:
    """O % de desconto que o usuário dá na venda sem pedir autorização: o do perfil dele na empresa (D26)."""
    if usuario.administrador:
        return Decimal(100)
    vinculo = repo.acesso(db, usuario.id, empresa_id)
    return vinculo.perfil.desconto_maximo if vinculo else Decimal(0)


# ---------------------------------------------------------- administração


def sincronizar_permissoes(db: Session) -> int:
    """Grava no banco o catálogo de permissões do código. Devolve quantas foram criadas."""
    novas = 0
    for codigo, descricao in PERMISSOES.items():
        p = repo.permissao(db, codigo)
        if p is None:
            db.add(Permissao(codigo=codigo, descricao=descricao))
            novas += 1
        else:
            p.descricao = descricao
    db.commit()
    return novas


def criar_perfil(db: Session, nome: str, permissoes: list[str], descricao: str | None = None) -> Perfil:
    desconhecidas = set(permissoes) - set(PERMISSOES)
    if desconhecidas:
        raise ValueError(f"Permissões inexistentes: {', '.join(sorted(desconhecidas))}")
    sincronizar_permissoes(db)
    perfil = Perfil(nome=nome, descricao=descricao)
    perfil.permissoes = list(db.scalars(select(Permissao).where(Permissao.codigo.in_(permissoes))))
    db.add(perfil)
    db.commit()
    return perfil


def criar_usuario(db: Session, login: str, nome: str, senha: str, administrador: bool = False) -> Usuario:
    usuario = Usuario(login=login.strip(), nome=nome, hash_senha=gerar_hash(senha), administrador=administrador)
    db.add(usuario)
    db.commit()
    return usuario


def dar_acesso(db: Session, usuario: Usuario, empresa: Empresa, perfil: Perfil) -> UsuarioEmpresa:
    """Cria ou atualiza o acesso do usuário à empresa, com o perfil indicado."""
    vinculo = db.get(UsuarioEmpresa, (usuario.id, empresa.id))
    if vinculo is None:
        vinculo = UsuarioEmpresa(usuario_id=usuario.id, empresa_id=empresa.id, perfil_id=perfil.id)
        db.add(vinculo)
    else:
        vinculo.perfil_id, vinculo.ativo = perfil.id, True
    db.commit()
    return vinculo


# ------------------------------------------------------------------ senha


def _conferir_senha_nova(senha: str) -> None:
    if len(senha) < SENHA_MINIMA:
        raise DadoInvalido(f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres")


def trocar_propria_senha(db: Session, usuario: Usuario, atual: str, nova: str) -> None:
    """O próprio usuário troca a senha (obrigatório depois de uma senha provisória)."""
    if not conferir_hash(atual, usuario.hash_senha, usuario.senha_sem_caixa):
        raise DadoInvalido("A senha atual não confere")
    _conferir_senha_nova(nova)
    if conferir_hash(nova, usuario.hash_senha, usuario.senha_sem_caixa):
        raise DadoInvalido("A senha nova precisa ser diferente da atual")
    # a partir daqui a senha diferencia maiúsculas, mesmo a de quem veio do VB6
    usuario.hash_senha, usuario.senha_sem_caixa, usuario.trocar_senha = gerar_hash(nova), False, False
    db.commit()


# ------------------------------------------------- gestão de usuários e perfis
#
# O administrador mexe em tudo. Quem tem acesso.usuarios sem ser administrador
# (o gerente da loja) cuida dos usuários da empresa ativa: só dá acesso a ela e
# só com perfis cujas permissões ele mesmo tem nela. Não mexe em administradores
# nem em quem é só de outras empresas.


@dataclass
class Gestor:
    """Quem está administrando: o usuário, a empresa ativa e as permissões dele nela."""

    usuario: Usuario
    empresa_id: int
    permissoes: set[str]


def _conferir_alvo(gestor: Gestor, alvo: Usuario) -> None:
    if gestor.usuario.administrador:
        return
    if alvo.administrador:
        raise Proibido("Só um administrador altera outro administrador")
    empresas = {a.empresa_id for a in alvo.acessos if a.ativo}
    if empresas and gestor.empresa_id not in empresas:
        raise Proibido("Este usuário é de outra empresa; peça ao administrador")


def obter_usuario(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise NaoEncontrado("Usuário não encontrado")
    return usuario


def _aplicar_usuario(db: Session, gestor: Gestor, usuario: Usuario, dados) -> None:
    outro = repo.usuario_por_login(db, dados.login)
    if outro and outro.id != usuario.id:
        raise Duplicado(f"O login {dados.login} já é de {outro.nome}")
    if dados.email:
        outro = db.scalar(select(Usuario).where(Usuario.email == dados.email))
        if outro and outro.id != usuario.id:
            raise Duplicado(f"O e-mail já é de {outro.nome}")
    if dados.funcionario_id is not None:
        if db.get(Funcionario, dados.funcionario_id) is None:
            raise DadoInvalido("Funcionário não encontrado")
        outro = db.scalar(select(Usuario).where(Usuario.funcionario_id == dados.funcionario_id))
        if outro and outro.id != usuario.id:
            raise Duplicado(f"Este funcionário já tem o login {outro.login}")
    if dados.administrador != bool(usuario.administrador) and not gestor.usuario.administrador:
        raise Proibido("Só um administrador cria ou tira administradores")
    if usuario.id == gestor.usuario.id and (not dados.ativo or (usuario.administrador and not dados.administrador)):
        raise Proibido("Você não pode desativar o seu próprio usuário nem tirar de si a administração")
    usuario.login, usuario.nome, usuario.email = dados.login, dados.nome, dados.email
    usuario.funcionario_id, usuario.ativo, usuario.administrador = dados.funcionario_id, dados.ativo, dados.administrador


def criar_usuario_pela_tela(db: Session, gestor: Gestor, dados) -> Usuario:
    """Usuário novo com senha provisória: ele troca no primeiro login."""
    _conferir_senha_nova(dados.senha)
    usuario = Usuario(hash_senha=gerar_hash(dados.senha), trocar_senha=True, administrador=False)
    _aplicar_usuario(db, gestor, usuario, dados)
    # quem não é administrador cria o usuário já com acesso à empresa dele, senão não o veria mais
    if not gestor.usuario.administrador and dados.perfil_id is None:
        raise DadoInvalido("Escolha o perfil do usuário nesta empresa")
    db.add(usuario)
    db.flush()
    if dados.perfil_id is not None:
        _salvar_acesso(db, gestor, usuario, gestor.empresa_id, dados.perfil_id, True)
    db.commit()
    db.refresh(usuario)
    return usuario


def alterar_usuario(db: Session, gestor: Gestor, usuario_id: int, dados) -> Usuario:
    usuario = obter_usuario(db, usuario_id)
    _conferir_alvo(gestor, usuario)
    _aplicar_usuario(db, gestor, usuario, dados)
    db.commit()
    db.refresh(usuario)
    return usuario


def definir_senha_provisoria(db: Session, gestor: Gestor, usuario_id: int, senha: str) -> Usuario:
    """Para quem esqueceu a senha: uma provisória, que precisa ser trocada no próximo login."""
    usuario = obter_usuario(db, usuario_id)
    _conferir_alvo(gestor, usuario)
    _conferir_senha_nova(senha)
    usuario.hash_senha, usuario.senha_sem_caixa, usuario.trocar_senha = gerar_hash(senha), False, True
    usuario.tentativas_erradas, usuario.bloqueado_ate = 0, None
    db.commit()
    db.refresh(usuario)
    return usuario


def desbloquear(db: Session, gestor: Gestor, usuario_id: int) -> Usuario:
    usuario = obter_usuario(db, usuario_id)
    _conferir_alvo(gestor, usuario)
    usuario.tentativas_erradas, usuario.bloqueado_ate = 0, None
    db.commit()
    db.refresh(usuario)
    return usuario


def _salvar_acesso(db: Session, gestor: Gestor, usuario: Usuario, empresa_id: int, perfil_id: int,
                   ativo: bool) -> None:
    if not gestor.usuario.administrador and empresa_id != gestor.empresa_id:
        raise Proibido("Você só dá acesso à empresa em que está")
    if db.get(Empresa, empresa_id) is None:
        raise NaoEncontrado("Empresa não encontrada")
    perfil = db.get(Perfil, perfil_id)
    if perfil is None:
        raise DadoInvalido("Perfil não encontrado")
    if not gestor.usuario.administrador:
        a_mais = {p.codigo for p in perfil.permissoes} - gestor.permissoes
        if a_mais:
            raise Proibido(f"O perfil {perfil.nome} tem permissões que você não tem: {', '.join(sorted(a_mais))}")
    vinculo = db.get(UsuarioEmpresa, (usuario.id, empresa_id))
    if vinculo is None:
        db.add(UsuarioEmpresa(usuario_id=usuario.id, empresa_id=empresa_id, perfil_id=perfil.id, ativo=ativo))
    else:
        vinculo.perfil_id, vinculo.ativo = perfil.id, ativo


def salvar_acesso(db: Session, gestor: Gestor, usuario_id: int, empresa_id: int, perfil_id: int,
                  ativo: bool) -> Usuario:
    """Dá, troca o perfil ou desliga (ativo falso) o acesso do usuário a uma empresa."""
    usuario = obter_usuario(db, usuario_id)
    _conferir_alvo(gestor, usuario)
    if usuario.id == gestor.usuario.id and not gestor.usuario.administrador:
        raise Proibido("Você não pode mudar o seu próprio acesso")
    _salvar_acesso(db, gestor, usuario, empresa_id, perfil_id, ativo)
    db.commit()
    db.refresh(usuario)
    return usuario


def listar_perfis(db: Session) -> list[Perfil]:
    return list(db.scalars(select(Perfil).order_by(Perfil.nome)))


def obter_perfil(db: Session, perfil_id: int) -> Perfil:
    perfil = db.get(Perfil, perfil_id)
    if perfil is None:
        raise NaoEncontrado("Perfil não encontrado")
    return perfil


def _aplicar_perfil(db: Session, gestor: Gestor, perfil: Perfil, dados) -> None:
    desconhecidas = set(dados.permissoes) - set(PERMISSOES)
    if desconhecidas:
        raise DadoInvalido(f"Permissões inexistentes: {', '.join(sorted(desconhecidas))}")
    outro = repo.perfil_por_nome(db, dados.nome)
    if outro and outro.id != perfil.id:
        raise Duplicado(f"Já existe o perfil {outro.nome}")
    if not gestor.usuario.administrador:
        # sem isto, quem edita perfis daria a si mesmo, pelo próprio perfil, o que não tem
        novas = set(dados.permissoes) - {p.codigo for p in perfil.permissoes} - gestor.permissoes
        if novas:
            raise Proibido(f"Você não pode dar permissões que não tem: {', '.join(sorted(novas))}")
        meu_limite = limite_de_desconto(db, gestor.usuario, gestor.empresa_id)
        if dados.desconto_maximo > max(meu_limite, perfil.desconto_maximo or 0):
            raise Proibido(f"Você não pode dar desconto máximo acima do seu ({meu_limite:g}%)")
    sincronizar_permissoes(db)
    perfil.nome, perfil.descricao = dados.nome, dados.descricao
    perfil.desconto_maximo = dados.desconto_maximo.quantize(Decimal("0.01"))
    perfil.permissoes = list(db.scalars(select(Permissao).where(Permissao.codigo.in_(dados.permissoes))))


def criar_perfil_pela_tela(db: Session, gestor: Gestor, dados) -> Perfil:
    perfil = Perfil()
    _aplicar_perfil(db, gestor, perfil, dados)
    db.add(perfil)
    db.commit()
    return perfil


def alterar_perfil(db: Session, gestor: Gestor, perfil_id: int, dados) -> Perfil:
    perfil = obter_perfil(db, perfil_id)
    _aplicar_perfil(db, gestor, perfil, dados)
    db.commit()
    return perfil


def excluir_perfil(db: Session, perfil_id: int) -> None:
    perfil = obter_perfil(db, perfil_id)
    if repo.usos_do_perfil(db, perfil.id):
        raise Proibido("Há usuários com este perfil; troque o perfil deles antes de excluir")
    db.delete(perfil)
    db.commit()

