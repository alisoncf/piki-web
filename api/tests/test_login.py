from app.legado import senha as senha_legado
from app.modelos import Credencial, Usuario


def _login(cliente, usuario="MARIA", senha="segredo", **extra):
    return cliente.post("/auth/login", json={"usuario": usuario, "senha": senha, **extra})


def test_primeiro_login_migra_a_senha(cliente, banco, criar_usuario):
    criar_usuario()
    r = _login(cliente)
    assert r.status_code == 200
    assert r.json()["cod_fun"] == "001"
    with banco() as s:
        cred = s.get(Credencial, "001")
        assert cred is not None
        assert cred.hash_senha.startswith("$argon2")
        assert cred.ultimo_login is not None


def test_login_pelo_codigo(cliente, criar_usuario):
    criar_usuario()
    assert _login(cliente, usuario="001").status_code == 200


def test_segundo_login_usa_o_hash(cliente, banco, criar_usuario):
    criar_usuario()
    _login(cliente)
    with banco() as s:
        hash_antes = s.get(Credencial, "001").hash_senha
    assert _login(cliente).status_code == 200
    with banco() as s:
        assert s.get(Credencial, "001").hash_senha == hash_antes


def test_senha_errada(cliente, banco, criar_usuario):
    criar_usuario()
    r = _login(cliente, senha="errada")
    assert r.status_code == 401
    with banco() as s:
        assert s.get(Credencial, "001") is None  # nada é gravado com senha errada


def test_usuario_inexistente_tem_a_mesma_mensagem(cliente, criar_usuario):
    criar_usuario()
    a = _login(cliente, usuario="NINGUEM")
    b = _login(cliente, senha="errada")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_senha_trocada_no_vb6(cliente, banco, criar_usuario):
    criar_usuario()
    assert _login(cliente).status_code == 200
    with banco() as s:
        s.get(Usuario, "001").senha = senha_legado.codificar("NOVA")
        s.commit()
    assert _login(cliente, senha="segredo").status_code == 401
    assert _login(cliente, senha="nova").status_code == 200
    assert _login(cliente, senha="nova").status_code == 200


def test_usuario_desabilitado(cliente, banco, criar_usuario):
    criar_usuario(status="0")
    assert _login(cliente).status_code == 403
    with banco() as s:
        assert s.get(Credencial, "001") is None


def test_desabilitado_com_senha_errada_nao_revela_status(cliente, criar_usuario):
    criar_usuario(status="0")
    assert _login(cliente, senha="errada").status_code == 401


def test_apelido_repetido(cliente, criar_usuario):
    criar_usuario(cod_fun="001", apelido="ANA")
    criar_usuario(cod_fun="002", apelido="ANA")
    assert _login(cliente, usuario="ANA").status_code == 409
    assert _login(cliente, usuario="002").status_code == 200


def test_eu_com_token(cliente, criar_usuario):
    criar_usuario()
    token = _login(cliente, cod_emp="03").json()["access_token"]
    r = cliente.get("/auth/eu", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["cod_fun"] == "001"
    assert r.json()["cod_emp"] == "03"


def test_eu_sem_token(cliente):
    assert cliente.get("/auth/eu").status_code == 401


def test_eu_com_token_invalido(cliente):
    r = cliente.get("/auth/eu", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401


def test_eu_depois_de_desabilitado(cliente, banco, criar_usuario):
    criar_usuario()
    token = _login(cliente).json()["access_token"]
    with banco() as s:
        s.get(Usuario, "001").status = "0"
        s.commit()
    assert cliente.get("/auth/eu", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_filial_invalida_no_login(cliente, criar_usuario):
    criar_usuario()
    assert _login(cliente, cod_emp="x1").status_code == 422
