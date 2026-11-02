"""Consultas de acesso."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominios.acesso.modelos import Permissao, Perfil, Usuario, UsuarioEmpresa
from app.dominios.empresas.modelos import Empresa


def usuario_por_login(db: Session, login: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(func.lower(Usuario.login) == login.strip().lower()))


def empresas_do_usuario(db: Session, usuario: Usuario) -> list[Empresa]:
    """Empresas ativas que o usuário pode acessar, em ordem de código."""
    consulta = select(Empresa).where(Empresa.ativa.is_(True)).order_by(Empresa.codigo)
    if not usuario.administrador:
        consulta = consulta.join(UsuarioEmpresa, UsuarioEmpresa.empresa_id == Empresa.id).where(
            UsuarioEmpresa.usuario_id == usuario.id, UsuarioEmpresa.ativo.is_(True)
        )
    return list(db.scalars(consulta))


def acesso(db: Session, usuario_id: int, empresa_id: int) -> UsuarioEmpresa | None:
    """Vínculo ativo do usuário com uma empresa ativa."""
    return db.scalar(
        select(UsuarioEmpresa)
        .join(Empresa, Empresa.id == UsuarioEmpresa.empresa_id)
        .where(
            UsuarioEmpresa.usuario_id == usuario_id,
            UsuarioEmpresa.empresa_id == empresa_id,
            UsuarioEmpresa.ativo.is_(True),
            Empresa.ativa.is_(True),
        )
    )


def empresa_ativa(db: Session, empresa_id: int) -> Empresa | None:
    emp = db.get(Empresa, empresa_id)
    return emp if emp and emp.ativa else None


def permissao(db: Session, codigo: str) -> Permissao | None:
    return db.get(Permissao, codigo)


def perfil_por_nome(db: Session, nome: str) -> Perfil | None:
    return db.scalar(select(Perfil).where(Perfil.nome == nome))


def listar_usuarios(db: Session) -> list[Usuario]:
    return list(db.scalars(select(Usuario).order_by(Usuario.nome)))


def usos_do_perfil(db: Session, perfil_id: int) -> int:
    """Quantos acessos (usuário em uma empresa) usam o perfil."""
    return db.scalar(select(func.count()).select_from(UsuarioEmpresa).where(UsuarioEmpresa.perfil_id == perfil_id))

