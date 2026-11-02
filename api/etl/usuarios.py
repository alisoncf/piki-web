"""Importa os usuários de um banco de filial do VB6 (D23).

No VB6 o usuário é um funcionário: a tab_usuarios tem o cod_fun, o nível
(1 Operador, 2 Supervisor, 3 Gerente, 4 Gestor) e a senha codificada, e o
login é o apelido (guerra_fun). Por isso rode antes o ETL de funcionários.

- Entram só os usuários ativos de funcionários ativos. O login é o apelido em
  minúsculas; se já for de outra pessoa, ganha um número no fim.
- A mesma pessoa em várias filiais é um usuário só (pelo funcionário), com um
  acesso em cada filial, no perfil do nível que tinha nela. Os quatro perfis
  são criados vazios: as permissões são marcadas na tela de perfis. As
  marcações da tab_defusu não são importadas.
- A senha vem do VB6 (etl/senha_legado.py) e é provisória: o usuário troca no
  primeiro login. Vale a da filial onde o funcionário está lotado. Senha já
  trocada no sistema novo não é mais mexida.
- Um usuário que deixou de ser ativo no VB6 perde o acesso àquela filial.
- O acesso criado não muda de perfil numa reimportação: o perfil passa a ser
  cuidado na tela.
"""
from dataclasses import dataclass, field

from sqlalchemy import Connection, func, select, text
from sqlalchemy.orm import Session

from app.dominios.acesso.modelos import Perfil, Usuario, UsuarioEmpresa
from app.dominios.empresas.modelos import Empresa
from app.dominios.funcionarios.modelos import Funcionario
from etl import mapa
from etl.funcionarios import EmpresaNaoImportada
from etl.senha_legado import hash_para_importar

_USUARIOS = text(
    "SELECT CAST(u.COD_FUN AS CHAR) AS cod, CAST(u.NIVEL_USU AS CHAR) AS nivel, CAST(u.SENHA_USU AS CHAR) AS senha,"
    "       CAST(u.Status_USU AS CHAR) AS status, CAST(f.status_fun AS CHAR) AS status_fun"
    "  FROM tab_usuarios u LEFT JOIN tab_funcionarios f ON f.cod_fun = u.COD_FUN"
    " ORDER BY u.COD_FUN"
)
PERFIS_DOS_NIVEIS = {"1": "Operador", "2": "Supervisor", "3": "Gerente", "4": "Gestor"}


@dataclass
class Resultado:
    criados: int = 0
    ligados: int = 0  # já existiam: de outra filial, de uma importação anterior ou criados à mão com o mesmo login
    acessos_criados: int = 0
    desligados: int = 0
    perfis_criados: int = 0
    avisos: list[str] = field(default_factory=list)


def _texto(valor: object) -> str | None:
    v = str(valor).strip() if valor is not None else ""
    return v or None


def _perfis(db: Session, r: Resultado) -> dict[str, Perfil]:
    perfis = {}
    for nome in PERFIS_DOS_NIVEIS.values():
        perfil = db.scalar(select(Perfil).where(Perfil.nome == nome))
        if perfil is None:
            perfil = Perfil(nome=nome, descricao="Nível do VB6; marque as permissões na tela de perfis")
            db.add(perfil)
            r.perfis_criados += 1
        perfis[nome] = perfil
    db.flush()
    return perfis


def _login_livre(db: Session, base: str) -> str:
    login, n = base, 2
    while db.scalar(select(Usuario.id).where(func.lower(Usuario.login) == login)) is not None:
        login, n = f"{base}{n}", n + 1
    return login


def importar_usuarios(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()
    perfis = _perfis(db, r)

    for linha in origem.execute(_USUARIOS).mappings():
        codigo = _texto(linha["cod"])
        if not codigo:
            continue
        ativo = _texto(linha["status"]) == "1" and _texto(linha["status_fun"]) == "1"
        funcionario_id = mapa.buscar(db, "tab_funcionarios", empresa.id, codigo)
        funcionario = db.get(Funcionario, funcionario_id) if funcionario_id else None
        if funcionario is None:
            if ativo:
                r.avisos.append(f"usuário {codigo}: funcionário não importado (rode antes o ETL de funcionários)")
            continue

        usuario_id = mapa.buscar(db, "tab_usuarios", empresa.id, codigo)
        usuario = db.get(Usuario, usuario_id) if usuario_id else None
        if usuario is None:
            usuario = db.scalar(select(Usuario).where(Usuario.funcionario_id == funcionario.id))
        base = (funcionario.apelido or funcionario.nome.split()[0]).strip().lower().replace(" ", ".")
        if usuario is None:
            # criado à mão (pela linha de comando) com o mesmo login e sem funcionário: é a mesma pessoa
            usuario = db.scalar(select(Usuario).where(func.lower(Usuario.login) == base, Usuario.funcionario_id.is_(None)))
            if usuario is not None:
                usuario.funcionario_id = funcionario.id
                r.avisos.append(f"usuário {codigo}: ligado ao login {usuario.login}, que já existia")

        if not ativo:
            vinculo = db.get(UsuarioEmpresa, (usuario.id, empresa.id)) if usuario else None
            if vinculo is not None and vinculo.ativo:
                vinculo.ativo = False
                r.desligados += 1
            continue

        if usuario is None:
            usuario = Usuario(login=_login_livre(db, base), nome=funcionario.nome, funcionario_id=funcionario.id,
                              senha_sem_caixa=True, trocar_senha=True)
            db.add(usuario)
            r.criados += 1
        else:
            r.ligados += 1
        # a senha do VB6 vale enquanto não for trocada no sistema novo; manda a da loja de lotação
        senha = hash_para_importar(linha["senha"])
        if senha and (usuario.hash_senha is None or (usuario.senha_sem_caixa and funcionario.empresa_id == empresa.id)):
            usuario.hash_senha, usuario.senha_sem_caixa, usuario.trocar_senha = senha, True, True
        elif not senha and usuario.hash_senha is None:
            r.avisos.append(f"usuário {codigo} ({usuario.login}): sem senha no VB6; defina uma provisória na tela")
        db.flush()

        if not usuario.administrador:
            vinculo = db.get(UsuarioEmpresa, (usuario.id, empresa.id))
            nivel = _texto(linha["nivel"]) or "1"
            if vinculo is None:
                db.add(UsuarioEmpresa(usuario_id=usuario.id, empresa_id=empresa.id,
                                      perfil_id=perfis[PERFIS_DOS_NIVEIS.get(nivel, "Operador")].id))
                r.acessos_criados += 1
            else:
                vinculo.ativo = True
        mapa.gravar(db, "tab_usuarios", empresa.id, codigo, usuario.id)

    db.commit()
    return r
