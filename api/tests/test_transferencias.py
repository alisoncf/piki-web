"""Transferência do consignado (D30): o representante leva produtos, confirma com a senha, dentro do limite.
Dados fictícios."""
from decimal import Decimal

import pytest

from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.clientes.modelos import Cliente
from app.dominios.consignacao.modelos import Representante
from app.dominios.empresas.modelos import Empresa
from app.dominios.estoque.modelos import Estoque, MovimentoEstoque
from app.dominios.produtos.modelos import Produto
from app.nucleo.seguranca import gerar_hash


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def balcao(banco, cliente, cenario):
    """O representante 7 (limite R$ 500, senha "gato"), dois produtos com estoque e o davi no balcão do consignado."""
    with banco() as db:
        maria = Cliente(nome="Maria Ficticia", cpf_cnpj="52998224725")
        db.add(maria)
        db.flush()
        rep = Representante(codigo=7, cliente_id=maria.id, limite=Decimal("500.00"),
                            senha_hash=gerar_hash("gato", sem_caixa=True))
        perfume = Produto(codigo=1, nome="Perfume Ficticio", preco_venda=Decimal("120.00"))
        toalha = Produto(codigo=2, nome="Toalha Ficticia", preco_venda=Decimal("30.00"))
        db.add_all([rep, perfume, toalha])
        db.flush()
        db.add(Estoque(empresa_id=cenario["e1"], produto_id=perfume.id, quantidade=Decimal("3"), reservado=Decimal(0)))
        perfil = acesso.criar_perfil(db, "Balcão do consignado", ["consignacao.transferir"])
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "davi"), db.get(Empresa, cenario["e1"]), perfil)
        db.commit()
        ids = {"rep": rep.id, "perfume": perfume.id, "toalha": toalha.id}
    return ids | {"davi": _auth(cliente, "davi", cenario["e1"]), "admin": _auth(cliente, "caio", cenario["e1"])}


def test_transferencia_do_balcao(banco, cliente, cenario, balcao):
    davi = balcao["davi"]
    t = cliente.post("/consignacao/transferencias", headers=davi, json={"representante_id": balcao["rep"]}).json()
    assert (t["numero"], t["situacao"], t["atendida_por"]["nome"], t["representante"]["codigo"]) == (1, "aberta", "Davi Sem Acesso", 7)
    # abrir de novo continua a mesma
    assert cliente.post("/consignacao/transferencias", headers=davi, json={"representante_id": balcao["rep"]}).json()["id"] == t["id"]

    url = f"/consignacao/transferencias/{t['id']}"
    cliente.post(f"{url}/itens", headers=davi, json={"produto_id": balcao["perfume"], "quantidade": "2"})
    cliente.post(f"{url}/itens", headers=davi, json={"produto_id": balcao["perfume"]})  # soma na linha
    t = cliente.post(f"{url}/itens", headers=davi, json={"produto_id": balcao["toalha"], "quantidade": "2"}).json()
    assert [(i["descricao"], i["quantidade"], i["preco"], i["total"]) for i in t["itens"]] == [
        ("Perfume Ficticio", "3.000", "120.00", "360.00"), ("Toalha Ficticia", "2.000", "30.00", "60.00")]
    assert t["total"] == "420.00"
    r = cliente.post(f"{url}/itens", headers=davi, json={"produto_id": balcao["toalha"], "quantidade": "0.5"})
    assert r.status_code == 422 and "fração" in r.json()["detail"]

    r = cliente.post(f"{url}/confirmar", headers=davi, json={"senha": "errada"})
    assert r.status_code == 422 and "senha do representante não confere" in r.json()["detail"]
    r = cliente.post(f"{url}/confirmar", headers=davi, json={"senha": "GATO"})  # sem diferenciar maiúsculas
    assert r.status_code == 200, r.text
    t = r.json()
    assert (t["situacao"], [i["restante"] for i in t["itens"]]) == ("confirmada", ["3.000", "2.000"])
    assert t["avisos"] == ["Toalha Ficticia: o disponível na loja ficou em -2"]
    with banco() as db:
        perfume = db.query(Estoque).filter_by(empresa_id=cenario["e1"], produto_id=balcao["perfume"]).one()
        assert (perfume.quantidade, perfume.reservado, perfume.disponivel) == (3, 3, 0)  # continua da loja, com ele
        mov = db.query(MovimentoEstoque).filter_by(produto_id=balcao["perfume"], tipo="consignacao_envio").one()
        assert (mov.quantidade, mov.reservado, mov.documento) == (0, 3, "transferência 1")
    assert cliente.post(f"{url}/itens", headers=davi, json={"produto_id": balcao["toalha"]}).status_code == 422

    posicao = cliente.get(f"/representantes/{balcao['rep']}/posicao", headers=davi).json()
    assert (posicao["em_uso"], posicao["disponivel"], posicao["pecas"]) == ("420.00", "80.00", "5.000")
    # o preço mudou: o em uso continua pelo da transferência, e mostra também pelo atual
    with banco() as db:
        db.get(Produto, balcao["perfume"]).preco_venda = Decimal("150.00")
        db.commit()
    posicao = cliente.get(f"/representantes/{balcao['rep']}/posicao", headers=davi).json()
    assert (posicao["em_uso"], posicao["em_uso_atual"]) == ("420.00", "510.00")
    assert [(i["descricao"], i["quantidade"], i["total_transferencia"], i["total_atual"]) for i in posicao["itens"]] == [
        ("Perfume Ficticio", "3.000", "360.00", "450.00"), ("Toalha Ficticia", "2.000", "60.00", "60.00")]

    # a próxima passa do limite (420 + 150 > 500): não leva
    t2 = cliente.post("/consignacao/transferencias", headers=davi, json={"representante_id": balcao["rep"]}).json()
    assert t2["numero"] == 2
    url2 = f"/consignacao/transferencias/{t2['id']}"
    cliente.post(f"{url2}/itens", headers=davi, json={"produto_id": balcao["perfume"]})
    r = cliente.post(f"{url2}/confirmar", headers=davi, json={"senha": "gato"})
    assert r.status_code == 422 and "Passa do limite" in r.json()["detail"]
    item = cliente.get(url2, headers=davi).json()["itens"][0]
    t2 = cliente.put(f"{url2}/itens/{item['id']}", headers=davi, json={"quantidade": "0"}).json()
    assert t2["itens"] == [] and t2["total"] == "0.00"
    assert cliente.delete(url2, headers=davi).status_code == 204
    assert [x["numero"] for x in cliente.get("/consignacao/transferencias", headers=davi).json()] == [1]


def test_bloqueado_nao_leva(banco, cliente, cenario, balcao):
    davi = balcao["davi"]
    t = cliente.post("/consignacao/transferencias", headers=davi, json={"representante_id": balcao["rep"]}).json()
    cliente.post(f"/consignacao/transferencias/{t['id']}/itens", headers=davi, json={"produto_id": balcao["toalha"]})
    with banco() as db:
        rep = db.get(Representante, balcao["rep"])
        rep.bloqueado, rep.motivo_bloqueio = True, "Atrasou o acerto"
        db.commit()
    r = cliente.post(f"/consignacao/transferencias/{t['id']}/confirmar", headers=davi, json={"senha": "gato"})
    assert r.status_code == 422 and "bloqueado e não leva mercadoria: Atrasou o acerto" in r.json()["detail"]
    r = cliente.post("/consignacao/transferencias", headers=davi, json={"representante_id": balcao["rep"]})
    assert r.status_code == 422
    # sem a permissão do balcão, não transfere
    with banco() as db:
        db.get(Representante, balcao["rep"]).bloqueado = False
        db.commit()
    ana = _auth(cliente, "ana", cenario["e1"])
    assert cliente.post("/consignacao/transferencias", headers=ana, json={"representante_id": balcao["rep"]}).status_code == 403


def test_importa_o_consignado_do_vb6(banco, cenario, balcao, tmp_path):
    from sqlalchemy import create_engine, text

    from app.dominios.consignacao.modelos import Transferencia
    from etl import mapa
    from etl.consignado import importar_consignado

    with banco() as db:
        mapa.gravar(db, "tab_representantes", cenario["e1"], "7", balcao["rep"])
        db.commit()
    origem = create_engine(f"sqlite:///{tmp_path / 'vb6.db'}")
    with origem.begin() as c:
        c.execute(text("CREATE TABLE tab_consignacoes (cod_rep INTEGER, cod_pro TEXT, data_con TEXT, qtd_con REAL, "
                       "reman_con REAL, unit_con REAL, cod_usu TEXT)"))
        c.execute(text("INSERT INTO tab_consignacoes VALUES "
                       "(7, '00000001', '2026-09-01 10:00:00', 2, 1, 100, '001'), "  # levou 2 a 100, resta 1
                       "(7, '00000002', '2026-10-01 10:00:00', 3, 3, 28, '001'), "
                       "(7, '00000001', '2026-08-01 10:00:00', 1, 0, 90, '001'), "  # já acertado: fica de fora
                       "(9, '00000002', '2026-10-01 10:00:00', 1, 1, 28, '001')"))  # representante não importado
    with origem.connect() as conexao, banco() as db:
        r = importar_consignado(conexao, db, "01")
        assert (r.representantes, r.itens, r.pecas, r.valor) == (1, 2, Decimal("4"), Decimal("184.00"))
        assert any("representante 9" in a for a in r.avisos)
        t = db.query(Transferencia).one()
        assert (t.situacao, t.total, [(i.descricao, i.quantidade, i.restante, i.preco) for i in t.itens]) == (
            "confirmada", Decimal("284.00"),
            [("Perfume Ficticio", 2, 1, Decimal("100.00")), ("Toalha Ficticia", 3, 3, Decimal("28.00"))])
        assert importar_consignado(conexao, db, "01").itens == 2  # de novo: refaz os itens, sem duplicar
        assert db.query(Transferencia).count() == 1
