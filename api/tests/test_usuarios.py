"""Telas de usuários e perfis, senha provisória e bloqueio do login. Dados fictícios."""
import pytest

from app.dominios.acesso.modelos import Usuario
from app.dominios.funcionarios.modelos import Funcionario


def _login(cliente, login, senha=None, empresa_id=None):
    corpo = {"login": login, "senha": senha or f"senha-{login}"}
    if empresa_id:
        corpo["empresa_id"] = empresa_id
    return cliente.post("/auth/login", json=corpo)


def _auth(cliente, login, empresa_id, senha=None):
    r = _login(cliente, login, senha, empresa_id)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    return _auth(cliente, "caio", cenario["e1"])


@pytest.fixture
def gerente(cliente, cenario):
    """A ana: Gerente na 01, com acesso.usuarios e acesso.perfis, sem ser administradora."""
    return _auth(cliente, "ana", cenario["e1"])


def _perfis(cliente, admin):
    return {p["nome"]: p["id"] for p in cliente.get("/acesso/perfis", headers=admin).json()}


def _novo(cliente, cabecalho, **extra):
    corpo = {"login": "joana", "nome": "Joana Teste", "senha": "provisoria1", **extra}
    return cliente.post("/acesso/usuarios", headers=cabecalho, json=corpo)


# ------------------------------------------------------------------ login


def test_bloqueia_na_quinta_senha_errada(cliente, cenario, admin):
    for _ in range(4):
        assert _login(cliente, "ana", "errada").status_code == 401
    r = _login(cliente, "ana", "errada")
    assert r.status_code == 403
    assert "bloqueado" in r.json()["detail"]
    # bloqueado, nem a senha certa entra
    assert _login(cliente, "ana").status_code == 403

    ana = next(u for u in cliente.get("/acesso/usuarios", headers=admin).json() if u["login"] == "ana")
    assert ana["bloqueado_ate"] is not None
    r = cliente.post(f"/acesso/usuarios/{ana['id']}/desbloquear", headers=admin)
    assert (r.status_code, r.json()["bloqueado_ate"]) == (200, None)
    assert _login(cliente, "ana").status_code == 200


def test_login_certo_zera_as_tentativas(cliente, cenario, banco):
    for _ in range(4):
        _login(cliente, "ana", "errada")
    assert _login(cliente, "ana").status_code == 200
    for _ in range(4):
        assert _login(cliente, "ana", "errada").status_code == 401


def test_senha_provisoria_obriga_a_trocar(cliente, cenario, admin):
    criado = _novo(cliente, admin, perfil_id=_perfis(cliente, admin)["Gerente"]).json()
    assert criado["trocar_senha"] is True
    r = _login(cliente, "joana", "provisoria1")
    assert r.status_code == 200 and r.json()["usuario"]["trocar_senha"] is True
    joana = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # antes de trocar, só a troca de senha (e o /auth/eu) funcionam
    r = cliente.get("/acesso/usuarios", headers=joana)
    assert (r.status_code, r.json()["detail"]) == (403, "Troque a senha provisória antes de continuar")
    assert cliente.get("/auth/eu", headers=joana).json()["usuario"]["trocar_senha"] is True

    assert cliente.post("/auth/senha", headers=joana, json={"senha_atual": "outra", "senha_nova": "nova-senha-1"}).status_code == 422
    r = cliente.post("/auth/senha", headers=joana, json={"senha_atual": "provisoria1", "senha_nova": "curta"})
    assert (r.status_code, r.json()["detail"]) == (422, "A senha precisa ter pelo menos 8 caracteres")
    r = cliente.post("/auth/senha", headers=joana, json={"senha_atual": "provisoria1", "senha_nova": "provisoria1"})
    assert r.status_code == 422
    assert cliente.post("/auth/senha", headers=joana, json={"senha_atual": "provisoria1", "senha_nova": "Nova-Senha-1"}).status_code == 204
    assert cliente.get("/acesso/usuarios", headers=joana).status_code == 200
    assert _login(cliente, "joana", "provisoria1").status_code == 401
    assert _login(cliente, "joana", "nova-senha-1").status_code == 401  # agora diferencia maiúsculas
    assert _login(cliente, "joana", "Nova-Senha-1").status_code == 200


def test_senha_provisoria_para_quem_esqueceu(cliente, cenario, admin):
    ana = next(u for u in cliente.get("/acesso/usuarios", headers=admin).json() if u["login"] == "ana")
    r = cliente.put(f"/acesso/usuarios/{ana['id']}/senha", headers=admin, json={"senha": "temporaria"})
    assert (r.status_code, r.json()["trocar_senha"]) == (200, True)
    assert _login(cliente, "ana").status_code == 401
    assert _login(cliente, "ana", "temporaria").json()["usuario"]["trocar_senha"] is True


# ---------------------------------------------------------------- usuários


def test_administrador_cria_e_altera(cliente, cenario, admin, banco):
    with banco() as db:
        func = Funcionario(nome="Joana Teste", apelido="JOANA", empresa_id=cenario["e1"])
        db.add(func)
        db.commit()
        func_id = func.id
    r = _novo(cliente, admin, email="Joana@Exemplo.com", funcionario_id=func_id)
    assert r.status_code == 201, r.text
    criado = r.json()
    assert (criado["email"], criado["funcionario"]["apelido"], criado["acessos"]) == ("joana@exemplo.com", "JOANA", [])

    perfis = _perfis(cliente, admin)
    r = cliente.put(f"/acesso/usuarios/{criado['id']}/acessos/{cenario['e2']}", headers=admin,
                    json={"perfil_id": perfis["Consulta"]})
    assert [(a["empresa"]["codigo"], a["perfil"]["nome"], a["ativo"]) for a in r.json()["acessos"]] == [("02", "Consulta", True)]
    r = cliente.put(f"/acesso/usuarios/{criado['id']}/acessos/{cenario['e2']}", headers=admin,
                    json={"perfil_id": perfis["Consulta"], "ativo": False})
    assert r.json()["acessos"][0]["ativo"] is False

    r = cliente.put(f"/acesso/usuarios/{criado['id']}", headers=admin,
                    json={"login": "joana.t", "nome": "Joana T.", "funcionario_id": None, "ativo": False})
    assert (r.status_code, r.json()["login"], r.json()["ativo"], r.json()["funcionario"]) == (200, "joana.t", False, None)


def test_repetidos(cliente, cenario, admin, banco):
    with banco() as db:
        func = Funcionario(nome="Joana Teste", empresa_id=cenario["e1"])
        db.add(func)
        db.commit()
        func_id = func.id
    assert _novo(cliente, admin, email="j@exemplo.com", funcionario_id=func_id).status_code == 201
    assert _novo(cliente, admin, login="ANA").status_code == 409  # login não diferencia maiúsculas
    assert _novo(cliente, admin, login="outra", email="J@exemplo.com").status_code == 409
    r = _novo(cliente, admin, login="outra", funcionario_id=func_id)
    assert (r.status_code, r.json()["detail"]) == (409, "Este funcionário já tem o login joana")
    assert _novo(cliente, admin, login="com espaço").status_code == 422
    assert _novo(cliente, admin, login="outra", senha="curta").status_code == 422


def test_gerente_so_cuida_da_propria_empresa(cliente, cenario, admin, gerente, banco):
    perfis = _perfis(cliente, admin)
    caixa = cliente.post("/acesso/perfis", headers=admin, json={"nome": "Caixa", "permissoes": ["clientes.ver"]}).json()

    assert _novo(cliente, gerente).status_code == 422  # precisa do perfil na empresa
    assert _novo(cliente, gerente, perfil_id=caixa["id"]).status_code == 403  # o Caixa tem o que ela não tem
    assert _novo(cliente, gerente, perfil_id=perfis["Consulta"], administrador=True).status_code == 403
    r = _novo(cliente, gerente, perfil_id=perfis["Consulta"])
    assert r.status_code == 201, r.text
    joana = r.json()
    assert [(a["empresa"]["codigo"], a["perfil"]["nome"]) for a in joana["acessos"]] == [("01", "Consulta")]

    r = cliente.put(f"/acesso/usuarios/{joana['id']}/acessos/{cenario['e2']}", headers=gerente,
                    json={"perfil_id": perfis["Consulta"]})
    assert (r.status_code, r.json()["detail"]) == (403, "Você só dá acesso à empresa em que está")

    with banco() as db:
        caio_id = db.query(Usuario).filter_by(login="caio").one().id
        ana_id = db.query(Usuario).filter_by(login="ana").one().id
    assert cliente.put(f"/acesso/usuarios/{caio_id}/senha", headers=gerente, json={"senha": "temporaria"}).status_code == 403
    r = cliente.put(f"/acesso/usuarios/{ana_id}/acessos/{cenario['e1']}", headers=gerente, json={"perfil_id": perfis["Consulta"]})
    assert r.status_code == 403  # o próprio acesso

    # usuário só da 02: é de outra empresa
    so_02 = _novo(cliente, admin, login="davi2").json()
    cliente.put(f"/acesso/usuarios/{so_02['id']}/acessos/{cenario['e2']}", headers=admin, json={"perfil_id": perfis["Consulta"]})
    r = cliente.put(f"/acesso/usuarios/{so_02['id']}/senha", headers=gerente, json={"senha": "temporaria"})
    assert (r.status_code, r.json()["detail"]) == (403, "Este usuário é de outra empresa; peça ao administrador")


# ------------------------------------------------------------------ perfis


def test_perfis(cliente, cenario, admin, gerente):
    catalogo = cliente.get("/acesso/permissoes", headers=admin).json()
    assert {"codigo": "clientes.ver", "descricao": "Consultar clientes, setores, órgãos e grupos de clientes",
            "area": "Clientes"} in catalogo

    r = cliente.post("/acesso/perfis", headers=admin, json={"nome": " Caixa ", "descricao": "", "permissoes": ["clientes.ver"]})
    assert r.status_code == 201, r.text
    caixa = r.json()
    assert caixa == {"id": caixa["id"], "nome": "Caixa", "descricao": None, "permissoes": ["clientes.ver"], "usuarios": 0}
    assert cliente.post("/acesso/perfis", headers=admin, json={"nome": "Caixa"}).status_code == 409
    assert cliente.post("/acesso/perfis", headers=admin, json={"nome": "X", "permissoes": ["nao.existe"]}).status_code == 422

    # a gerente não dá a si, pelo próprio perfil, o que não tem; tirar pode
    perfis = _perfis(cliente, admin)
    r = cliente.put(f"/acesso/perfis/{perfis['Gerente']}", headers=gerente,
                    json={"nome": "Gerente", "permissoes": ["acesso.usuarios", "acesso.perfis", "clientes.ver"]})
    assert (r.status_code, r.json()["detail"]) == (403, "Você não pode dar permissões que não tem: clientes.ver")
    r = cliente.put(f"/acesso/perfis/{caixa['id']}", headers=gerente, json={"nome": "Caixa", "permissoes": []})
    assert (r.status_code, r.json()["permissoes"]) == (200, [])

    r = cliente.delete(f"/acesso/perfis/{perfis['Gerente']}", headers=admin)
    assert r.status_code == 403  # tem usuários
    assert cliente.delete(f"/acesso/perfis/{caixa['id']}", headers=admin).status_code == 204
    assert "Caixa" not in _perfis(cliente, admin)


def test_sem_permissao(cliente, cenario):
    bia_02 = _auth(cliente, "bia", cenario["e2"])  # Consulta na 02: nenhuma permissão
    assert cliente.get("/acesso/perfis", headers=bia_02).status_code == 403
    assert cliente.post("/acesso/usuarios", headers=bia_02, json={"login": "x", "nome": "X", "senha": "provisoria1"}).status_code == 403
