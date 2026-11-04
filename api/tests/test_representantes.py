"""Representantes do consignado (D30): cadastro, limites e comissões, senha, importação do VB6. Dados fictícios."""
from decimal import Decimal

from sqlalchemy import create_engine, text

from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.clientes.modelos import Cliente
from app.dominios.consignacao import servico
from app.dominios.consignacao.modelos import Representante
from app.dominios.empresas.modelos import Empresa
from etl.representantes import importar_representantes


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _clientes(banco, *nomes):
    with banco() as db:
        lista = [Cliente(nome=nome, cpf_cnpj=cpf) for nome, cpf in nomes]
        db.add_all(lista)
        db.commit()
        return [c.id for c in lista]


def test_cadastro_limites_e_senha(banco, cliente, cenario):
    admin = _auth(cliente, "caio", cenario["e1"])
    with banco() as db:  # o davi cadastra, mas não mexe em limite nem comissão
        perfil = acesso.criar_perfil(db, "Consignado", ["representantes.editar"])
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "davi"), db.get(Empresa, cenario["e1"]), perfil)
    davi = _auth(cliente, "davi", cenario["e1"])
    maria, joao = _clientes(banco, ("Maria Ficticia", "52998224725"), ("Joao Ficticio", None))

    r = cliente.post("/representantes", headers=davi, json={"cliente_id": maria, "lembrete": "Acerta toda sexta"})
    assert r.status_code == 201, r.text
    rep = r.json()
    assert (rep["codigo"], rep["cliente"]["nome"], rep["ativo"], rep["bloqueado"], rep["limite"], rep["tem_senha"]) == (
        1, "Maria Ficticia", True, False, "0.00", False)
    assert [(c["tipo_cobranca"], c["percentual"], c["padrao"]) for c in rep["comissoes"]][:3] == [
        ("loja", "20.00", True), ("cliente", "15.00", True), ("representante", "20.00", True)]
    assert cliente.post("/representantes", headers=davi, json={"cliente_id": maria}).status_code == 409
    assert cliente.post("/representantes", headers=davi, json={"cliente_id": joao}).json()["codigo"] == 2

    url = f"/representantes/{rep['id']}"
    limites = {"limite": "5000.00", "bloqueado": False, "comissoes": [{"tipo_cobranca": "representante", "percentual": "25"}]}
    assert cliente.put(f"{url}/limites", headers=davi, json=limites).status_code == 403
    r = cliente.put(f"{url}/limites", headers=admin, json=limites | {"bloqueado": True})
    assert r.status_code == 422 and "motivo do bloqueio" in r.json()["detail"]
    r = cliente.put(f"{url}/limites", headers=admin, json=limites | {"bloqueado": True, "motivo_bloqueio": "Atrasou o acerto"})
    rep = r.json()
    assert (rep["limite"], rep["bloqueado"], rep["motivo_bloqueio"]) == ("5000.00", True, "Atrasou o acerto")
    assert [(c["tipo_cobranca"], c["percentual"], c["padrao"]) for c in rep["comissoes"]][:3] == [
        ("loja", "20.00", True), ("cliente", "15.00", True), ("representante", "25.00", False)]
    # desbloqueado, o motivo some; comissão vazia volta para a padrão
    rep = cliente.put(f"{url}/limites", headers=admin, json=limites | {"comissoes": []}).json()
    assert (rep["bloqueado"], rep["motivo_bloqueio"], rep["comissoes"][2]["padrao"]) == (False, None, True)

    assert cliente.put(f"{url}/senha", headers=davi, json={"senha": "ab"}).status_code == 422
    rep = cliente.put(f"{url}/senha", headers=davi, json={"senha": "Gato12"}).json()
    assert rep["tem_senha"] is True and "Gato12" not in str(rep)
    with banco() as db:
        representante = db.get(Representante, rep["id"])
        assert servico.conferir_senha(representante, "GATO12") and not servico.conferir_senha(representante, "outra")

    r = cliente.put(url, headers=davi, json={"ativo": True, "avalista_nome": "Avalista Ficticio", "avalista_cpf": "123"})
    assert r.status_code == 422 and "CPF do avalista" in r.json()["detail"]
    r = cliente.put(url, headers=davi, json={"ativo": False, "avalista_nome": " Avalista Ficticio ", "ultima_conferencia": "2026-10-01"})
    assert (r.json()["ativo"], r.json()["avalista_nome"], r.json()["ultima_conferencia"]) == (False, "Avalista Ficticio", "2026-10-01")

    # a busca: nome, CPF ou código
    assert [x["codigo"] for x in cliente.get("/representantes", headers=davi, params={"busca": "joao"}).json()] == [2]
    assert [x["codigo"] for x in cliente.get("/representantes", headers=davi, params={"busca": "529.982"}).json()] == [1]
    assert [x["codigo"] for x in cliente.get("/representantes", headers=davi, params={"busca": "2"}).json()] == [2]
    assert [x["codigo"] for x in cliente.get("/representantes", headers=davi, params={"so_ativos": True}).json()] == [2]


_DDL = [
    """CREATE TABLE tab_representantes (cod_rep INTEGER PRIMARY KEY, nome_rep TEXT, limite_rep REAL, endereco_rep TEXT,
        cep_rep TEXT, nasc_rep TEXT, rg_rep TEXT, cpf_rep TEXT, datacad_rep TEXT, obs_rep TEXT, status_rep TEXT,
        cod_set TEXT, senha_rep TEXT, excluido_rep TEXT, avalista_nome TEXT, avalista_cpf TEXT, avalista_rg TEXT,
        avalista_endereco TEXT, avalista_telefones TEXT, avalista_anotacoes TEXT, motivo_bloqueio TEXT, lembrete TEXT,
        lembreteAcerto TEXT, ultimaconferencia TEXT, bloqimpr TEXT, bloqdev TEXT)""",
    "CREATE TABLE tab_reptip (cod_tip TEXT, cod_rep INTEGER, comissao_tip REAL)",
    "CREATE TABLE tab_telefones (cod_cli INTEGER, num_tel TEXT, tipo_tel TEXT, tipo_ter TEXT)",
]


def _rep(cod, nome, cpf, **outros):
    return {"cod_rep": cod, "nome_rep": nome, "cpf_rep": cpf, "limite_rep": 1000, "status_rep": "1", "excluido_rep": "N",
            "senha_rep": "", "bloqimpr": "N", "bloqdev": "N", "datacad_rep": "2020-01-10", "ultimaconferencia": "0000-00-00",
            "endereco_rep": "RUA FICTICIA 1", "cep_rep": "75000-000", **outros}


def test_importa_os_representantes_do_vb6(banco, cenario, tmp_path):
    _clientes(banco, ("JA CLIENTE FICTICIA", "52998224725"))
    origem = create_engine(f"sqlite:///{tmp_path / 'vb6.db'}")
    with origem.begin() as c:
        for ddl in _DDL:
            c.execute(text(ddl))
        for rep in [
            _rep(7, "JA CLIENTE FICTICIA", "529.982.247-25", senha_rep="abc1", limite_rep=2500.5),
            _rep(8, "NOVA REPRESENTANTE", "111.444.777-35", excluido_rep="S"),  # o mesmo CPF, cadastro velho
            _rep(9, "SEM CPF", "123", excluido_rep="S"),
            _rep(10, "NOVA REPRESENTANTE", "111.444.777-35", status_rep="2", motivo_bloqueio="Sumiu", bloqdev="S"),
        ]:
            c.execute(text(f"INSERT INTO tab_representantes ({', '.join(rep)}) VALUES ({', '.join(':' + k for k in rep)})"), rep)
        c.execute(text("INSERT INTO tab_reptip VALUES ('3', 7, 25), ('2', 7, 15), ('01', 10, 30)"))
        c.execute(text("INSERT INTO tab_telefones VALUES (8, '(62) 99999-0000', '3', 'R'), (8, '6233330000', '1', 'C')"))

    with origem.connect() as conexao, banco() as db:
        r = importar_representantes(conexao, db, "01")
        assert (r.representantes, r.ja_clientes, r.clientes_criados, r.inativos) == (3, 1, 2, 1)
        assert any("mesmo CPF" in a for a in r.avisos) and any("SEM CPF" in a for a in r.avisos)
        reps = {rep.codigo: rep for rep in db.query(Representante)}
        assert set(reps) == {7, 9, 10}  # o 8 e o 10 são a mesma pessoa: fica o código do ativo
        sete, oito = reps[7], reps[10]
        assert (sete.cliente.nome, sete.limite, sete.ativo) == ("JA CLIENTE FICTICIA", Decimal("2500.50"), True)
        assert servico.conferir_senha(sete, "ABC1")
        # só a comissão diferente da padrão fica gravada
        assert [(c.tipo_cobranca, c.percentual) for c in sete.comissoes] == [("representante", Decimal("25.00"))]
        assert sete.comissao("cliente") == Decimal("15.00")
        assert (oito.bloqueado, oito.motivo_bloqueio, oito.bloqueia_devolucao, oito.senha_hash) == (True, "Sumiu", True, None)
        assert [(c.tipo_cobranca, c.percentual) for c in oito.comissoes] == [("loja", Decimal("30.00"))]
        assert (oito.cliente.cpf_cnpj, [t.numero for t in oito.cliente.telefones]) == ("11144477735", ["62999990000"])
        assert reps[9].cliente.cpf_cnpj is None and reps[9].ativo is False

        # de novo: nada duplicado
        assert importar_representantes(conexao, db, "01").representantes == 0
        assert db.query(Representante).count() == 3
