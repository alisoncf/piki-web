from app.dominios.acesso.modelos import Usuario, UsuarioEmpresa


def _login(cliente, login, senha=None, **extra):
    return cliente.post("/auth/login", json={"login": login, "senha": senha or f"senha-{login}", **extra})


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------ login


def test_usuario_de_uma_empresa_entra_direto(cliente, cenario):
    r = _login(cliente, "ana")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["empresa"]["codigo"] == "01"
    assert [e["codigo"] for e in corpo["empresas"]] == ["01"]


def test_usuario_de_varias_empresas_precisa_escolher(cliente, cenario):
    corpo = _login(cliente, "bia").json()
    assert corpo["empresa"] is None
    # a empresa 03 está desativada e não aparece
    assert [e["codigo"] for e in corpo["empresas"]] == ["01", "02"]


def test_escolher_empresa_no_login(cliente, cenario):
    corpo = _login(cliente, "bia", empresa_id=cenario["e2"]).json()
    assert corpo["empresa"]["codigo"] == "02"


def test_empresa_nao_permitida_no_login(cliente, cenario):
    assert _login(cliente, "ana", empresa_id=cenario["e2"]).status_code == 403
    assert _login(cliente, "bia", empresa_id=cenario["e3"]).status_code == 403


def test_login_ignora_maiusculas_no_usuario(cliente, cenario):
    assert _login(cliente, "ANA", senha="senha-ana").status_code == 200


def test_senha_diferencia_maiusculas(cliente, cenario):
    # senhas criadas no sistema novo diferenciam maiúsculas (as importadas do VB6 não)
    assert _login(cliente, "ana", senha="SENHA-ANA").status_code == 401


def test_senha_errada_e_usuario_inexistente_iguais(cliente, cenario):
    a = _login(cliente, "ana", senha="errada")
    b = _login(cliente, "ninguem", senha="qualquer")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_usuario_desativado(cliente, banco, cenario):
    with banco() as db:
        db.query(Usuario).filter_by(login="ana").one().ativo = False
        db.commit()
    assert _login(cliente, "ana").status_code == 403
    assert _login(cliente, "ana", senha="errada").status_code == 401  # não revela o status


def test_usuario_sem_empresa(cliente, cenario):
    r = _login(cliente, "davi")
    assert r.status_code == 403
    assert "nenhuma empresa" in r.json()["detail"]


def test_administrador_ve_todas_as_empresas_ativas(cliente, cenario):
    corpo = _login(cliente, "caio").json()
    assert [e["codigo"] for e in corpo["empresas"]] == ["01", "02"]


# ------------------------------------------------------- troca de empresa


def test_trocar_de_empresa(cliente, cenario):
    token = _login(cliente, "bia", empresa_id=cenario["e1"]).json()["access_token"]
    r = cliente.post("/auth/empresa", json={"empresa_id": cenario["e2"]}, headers=_auth(token))
    assert r.status_code == 200
    novo = r.json()["access_token"]
    eu = cliente.get("/auth/eu", headers=_auth(novo)).json()
    assert eu["empresa"]["codigo"] == "02"


def test_trocar_para_empresa_sem_acesso(cliente, cenario):
    token = _login(cliente, "ana").json()["access_token"]
    r = cliente.post("/auth/empresa", json={"empresa_id": cenario["e2"]}, headers=_auth(token))
    assert r.status_code == 403


def test_ultima_empresa_e_sugerida(cliente, cenario):
    token = _login(cliente, "bia").json()["access_token"]
    cliente.post("/auth/empresa", json={"empresa_id": cenario["e2"]}, headers=_auth(token))
    assert _login(cliente, "bia").json()["ultima_empresa_id"] == cenario["e2"]


# ------------------------------------------------------------- permissões


def test_permissoes_mudam_com_a_empresa(cliente, cenario):
    t1 = _login(cliente, "bia", empresa_id=cenario["e1"]).json()["access_token"]
    t2 = _login(cliente, "bia", empresa_id=cenario["e2"]).json()["access_token"]
    assert cliente.get("/auth/eu", headers=_auth(t1)).json()["permissoes"] == ["acesso.perfis", "acesso.usuarios"]
    assert cliente.get("/auth/eu", headers=_auth(t2)).json()["permissoes"] == []
    # a mesma pessoa, a mesma rota: liberada na 01 (Gerente), negada na 02 (Consulta)
    assert cliente.get("/acesso/usuarios", headers=_auth(t1)).status_code == 200
    assert cliente.get("/acesso/usuarios", headers=_auth(t2)).status_code == 403


def test_rota_exige_empresa_escolhida(cliente, cenario):
    token = _login(cliente, "bia").json()["access_token"]
    r = cliente.get("/acesso/usuarios", headers=_auth(token))
    assert r.status_code == 409
    assert r.json()["detail"] == "Escolha a empresa"


def test_administrador_tem_todas_as_permissoes(cliente, cenario):
    token = _login(cliente, "caio", empresa_id=cenario["e2"]).json()["access_token"]
    usuarios = cliente.get("/acesso/usuarios", headers=_auth(token))
    assert usuarios.status_code == 200
    bia = next(u for u in usuarios.json() if u["login"] == "bia")
    assert {(a["empresa"]["codigo"], a["perfil"]) for a in bia["acessos"]} >= {("01", "Gerente"), ("02", "Consulta")}


def test_acesso_retirado_vale_na_hora(cliente, banco, cenario):
    token = _login(cliente, "ana").json()["access_token"]
    assert cliente.get("/acesso/usuarios", headers=_auth(token)).status_code == 200
    with banco() as db:
        db.query(UsuarioEmpresa).filter_by(empresa_id=cenario["e1"]).update({"ativo": False})
        db.commit()
    # o token ainda é válido, mas o acesso à empresa foi retirado
    assert cliente.get("/acesso/usuarios", headers=_auth(token)).status_code == 403


def test_sem_token(cliente, cenario):
    assert cliente.get("/auth/eu").status_code == 401
    assert cliente.get("/acesso/usuarios").status_code == 401


def test_token_invalido(cliente, cenario):
    assert cliente.get("/auth/eu", headers=_auth("abc.def.ghi")).status_code == 401
