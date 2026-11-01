"""Regras de acesso (decisão D10). Não depende de HTTP: levanta erros de domínio."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominios.acesso import repositorio as repo
from app.dominios.acesso.modelos import Perfil, Permissao, Usuario, UsuarioEmpresa
from app.dominios.empresas.modelos import Empresa
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
    if usuario is None or not conferir_hash(senha, usuario.hash_senha, usuario.senha_sem_caixa):
        raise CredenciaisInvalidas
    if not usuario.ativo:
        raise UsuarioInativo
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
