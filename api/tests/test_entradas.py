"""Entrada de notas pelo XML da NF-e (D25). XMLs fictícios, montados aqui; arquivos numa pasta temporária."""
from decimal import Decimal

import pytest

from app.dominios.empresas.modelos import Empresa
from app.dominios.entradas import nfe
from app.main import app
from app.nucleo import arquivos
from app.nucleo.arquivos import Pasta

CNPJ_LOJA = "11444777000161"
CNPJ_FORNECEDOR = "11222333000181"
CHAVE = "35261111222333000181550010000012341000012345"


def _item(n, codigo, descricao, qtd, unitario, ean="SEM GTIN", unidade="UN", frete="0", ipi=None, st=None, desconto=None):
    total = Decimal(qtd) * Decimal(unitario)
    ipi_xml = f"<IPI><cEnq>999</cEnq><IPITrib><CST>50</CST><vBC>{total}</vBC><pIPI>10</pIPI><vIPI>{ipi}</vIPI></IPITrib></IPI>" if ipi else ""
    st_xml = f"<vICMSST>{st}</vICMSST>" if st else ""
    desc_xml = f"<vDesc>{desconto}</vDesc>" if desconto else ""
    frete_xml = f"<vFrete>{frete}</vFrete>" if frete != "0" else ""
    return f"""<det nItem="{n}"><prod><cProd>{codigo}</cProd><cEAN>{ean}</cEAN><xProd>{descricao}</xProd><NCM>63023100</NCM>
        <CFOP>6102</CFOP><uCom>{unidade}</uCom><qCom>{qtd}</qCom><vUnCom>{unitario}</vUnCom><vProd>{total:.2f}</vProd>
        <cEANTrib>{ean}</cEANTrib><uTrib>{unidade}</uTrib><qTrib>{qtd}</qTrib><vUnTrib>{unitario}</vUnTrib>{frete_xml}{desc_xml}
        <indTot>1</indTot></prod><imposto><ICMS><ICMS10><orig>0</orig><CST>10</CST>{st_xml}</ICMS10></ICMS>{ipi_xml}</imposto></det>"""


def xml_nota(itens, chave=CHAVE, destinatario=CNPJ_LOJA, emitente=CNPJ_FORNECEDOR, numero=1234):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><NFe><infNFe Id="NFe{chave}" versao="4.00">
<ide><cUF>35</cUF><mod>55</mod><serie>1</serie><nNF>{numero}</nNF><dhEmi>2026-10-30T09:15:00-03:00</dhEmi></ide>
<emit><CNPJ>{emitente}</CNPJ><xNome>TECIDOS FICTICIOS LTDA</xNome><xFant>FICTICIA TEXTIL</xFant>
<enderEmit><xLgr>RUA DAS FLORES</xLgr><nro>100</nro><xBairro>CENTRO</xBairro><cMun>4202404</cMun><xMun>Blumenau</xMun>
<UF>SC</UF><CEP>89010000</CEP><fone>4733334444</fone></enderEmit><IE>250000000</IE></emit>
<dest><CNPJ>{destinatario}</CNPJ><xNome>LOJA FICTICIA</xNome></dest>
{''.join(itens)}
<total><ICMSTot><vNF>999.99</vNF></ICMSTot></total></infNFe></NFe></nfeProc>""".encode()


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def pasta(tmp_path):
    armazenamento = Pasta(tmp_path)
    app.dependency_overrides[arquivos.armazenamento] = lambda: armazenamento
    yield tmp_path
    app.dependency_overrides.pop(arquivos.armazenamento, None)


@pytest.fixture
def admin(banco, cliente, cenario, pasta):
    with banco() as db:
        db.get(Empresa, cenario["e1"]).cnpj = CNPJ_LOJA
        db.commit()
    return _auth(cliente, "caio", cenario["e1"])


@pytest.fixture
def jogo(cliente, admin):
    """Um produto já cadastrado, com o código que o fornecedor usa."""
    cama = cliente.post("/secoes", headers=admin, json={"nome": "Cama"}).json()
    sub = cliente.post("/subsecoes", headers=admin, json={"nome": "Jogo de cama", "secao_id": cama["id"]}).json()
    fornecedor = cliente.post("/fornecedores", headers=admin, json={"nome": "Tecidos Fictícios Ltda", "cpf_cnpj": CNPJ_FORNECEDOR}).json()
    r = cliente.post("/produtos", headers=admin, json={
        "nome": "JOGO DE CAMA FICTICIO", "subsecao_id": sub["id"], "margem": "100", "preco_venda": "99.90",
        "fornecedores": [{"fornecedor_id": fornecedor["id"], "codigo": "JC-01"}]})
    return {"produto": r.json()["id"], "subsecao": sub["id"], "fornecedor": fornecedor["id"]}


def test_ler_xml():
    nota = nfe.ler(xml_nota([_item(1, "JC-01", "JOGO DE CAMA", "2", "50", ean="7891234567895", frete="10", ipi="10", st="5.5")]))
    assert (nota.chave, nota.numero, nota.serie, nota.emitente.cpf_cnpj, nota.destinatario_cpf_cnpj) == (
        CHAVE, 1234, 1, CNPJ_FORNECEDOR, CNPJ_LOJA)
    item = nota.itens[0]
    assert (item.codigo, item.ean, item.quantidade, item.valor_produtos, item.valor_frete, item.valor_ipi, item.valor_st) == (
        "JC-01", "7891234567895", 2, Decimal("100.00"), 10, 10, Decimal("5.5"))
    assert nfe.ler(xml_nota([_item(1, "X", "Y", "1", "1")])).itens[0].ean is None  # SEM GTIN
    with pytest.raises(nfe.XmlInvalido):
        nfe.ler(b"<html>nada</html>")
    with pytest.raises(nfe.XmlInvalido):
        nfe.ler(b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><x>&a;</x>')


def test_entrada_completa(cliente, admin, jogo, pasta):
    xml = xml_nota([
        # o fornecedor manda em caixa com 6: 2 caixas de 120 = 12 unidades
        _item(1, "JC-01", "JOGO DE CAMA FICT", "2", "120", unidade="CX", frete="12", ipi="24", desconto="4"),
        _item(2, "TA-99", "TAPETE NOVO FICTICIO", "3", "40", ean="7890000000017"),
    ])
    r = cliente.post("/entradas", headers=admin, content=xml)
    assert r.status_code == 201, r.text
    nota = r.json()
    assert (nota["situacao"], nota["fornecedor"]["id"], nota["fornecedor_novo"]) == ("aberta", jogo["fornecedor"], False)
    um, dois = nota["itens"]
    assert um["produto"]["id"] == jogo["produto"]  # achado pelo código do fornecedor
    assert dois["produto"] is None
    assert len(list(pasta.rglob("*.xml"))) == 1
    # a mesma nota não entra duas vezes; a resposta diz qual é
    r = cliente.post("/entradas", headers=admin, content=xml)
    assert r.status_code == 409 and r.headers["x-nota-id"] == str(nota["id"])
    assert cliente.post(f"/entradas/{nota['id']}/confirmar", headers=admin).status_code == 422  # falta ligar o item 2

    # o produto do item 2 é cadastrado depois (o atalho da tela), com o EAN da nota: ao abrir de novo, já vem ligado
    tapete = cliente.post("/produtos", headers=admin, json={
        "nome": "TAPETE NOVO FICTICIO", "subsecao_id": jogo["subsecao"], "codigos_barras": ["7890000000017"]}).json()["id"]
    nota = cliente.get(f"/entradas/{nota['id']}", headers=admin).json()
    assert nota["itens"][1]["produto"]["id"] == tapete

    url = f"/entradas/{nota['id']}/itens/{um['id']}"
    r = cliente.put(url, headers=admin, json={"produto_id": jogo["produto"], "embalagem": 6, "preco_venda": "59.90"})
    assert r.status_code == 200
    # (240 − 4 + 12 + 24) / 12 unidades
    assert (r.json()["unidades"], r.json()["custo_unitario"]) == ("12.0000", "22.67")

    r = cliente.post(f"/entradas/{nota['id']}/confirmar", headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["situacao"] == "confirmada" and r.json()["confirmada_por"]["nome"] == "Caio Admin"
    produto = cliente.get(f"/produtos/{jogo['produto']}", headers=admin).json()
    assert (produto["custo"], produto["preco_venda"]) == ("22.67", "59.90")
    assert produto["fornecedores"][0]["embalagem"] == 6  # lembrada para a próxima nota
    tapete_ficha = cliente.get(f"/produtos/{tapete}", headers=admin).json()
    assert (tapete_ficha["custo"], tapete_ficha["fornecedores"][0]["codigo"]) == ("40.00", "TA-99")
    estoque = cliente.get(f"/produtos/{jogo['produto']}/estoque", headers=admin).json()
    assert estoque["quantidade"] == "12.000"
    movimento = cliente.get(f"/produtos/{jogo['produto']}/estoque/movimentos", headers=admin).json()["itens"][0]
    assert (movimento["descricao"], movimento["documento"]) == ("Entrada", "NF 1234/1")
    assert cliente.post(f"/entradas/{nota['id']}/confirmar", headers=admin).status_code == 422  # só uma vez
    assert cliente.get("/entradas", headers=admin, params={"situacao": "confirmada"}).json()["total"] == 1


def test_proxima_nota_ja_vem_ligada_com_a_embalagem(cliente, admin, jogo):
    cliente.put(f"/produtos/{jogo['produto']}", headers=admin, json={
        "nome": "JOGO DE CAMA FICTICIO", "subsecao_id": jogo["subsecao"], "margem": "100", "preco_venda": "99.90",
        "fornecedores": [{"fornecedor_id": jogo["fornecedor"], "codigo": "jc-01", "embalagem": 6}]})
    nota = cliente.post("/entradas", headers=admin, content=xml_nota([_item(1, "JC-01", "JOGO", "1", "60", unidade="CX")])).json()
    assert (nota["itens"][0]["produto"]["id"], nota["itens"][0]["embalagem"], nota["itens"][0]["custo_unitario"]) == (
        jogo["produto"], 6, "10.00")


def test_nota_de_outra_empresa_e_fornecedor_novo(cliente, admin, pasta):
    r = cliente.post("/entradas", headers=admin, content=xml_nota([_item(1, "A", "B", "1", "1")], destinatario="11222333000181"))
    assert r.status_code == 422 and "não é para Loja Centro" in r.json()["detail"]

    # emitente sem cadastro: entra com os dados do XML
    r = cliente.post("/entradas", headers=admin, content=xml_nota([_item(1, "A", "B", "1", "1")]))
    assert r.status_code == 201 and r.json()["fornecedor_novo"] is True
    fornecedor = cliente.get(f"/fornecedores/{r.json()['fornecedor']['id']}", headers=admin).json()
    assert (fornecedor["nome"], fornecedor["nome_fantasia"], fornecedor["cep"]) == ("Tecidos Ficticios Ltda", "Ficticia Textil", "89010000")

    # descartar a nota aberta
    assert cliente.delete(f"/entradas/{r.json()['id']}", headers=admin).status_code == 204
    assert cliente.get("/entradas", headers=admin).json()["total"] == 0


def test_fracao_e_preco_sem_permissao(banco, cliente, admin, jogo, cenario):
    nota = cliente.post("/entradas", headers=admin, content=xml_nota([_item(1, "JC-01", "JOGO", "1.5", "60")])).json()
    r = cliente.post(f"/entradas/{nota['id']}/confirmar", headers=admin)
    assert r.status_code == 422 and "não aceita quantidade com fração" in r.json()["detail"]

    from app.dominios.acesso import repositorio
    from app.dominios.acesso import servico as acesso
    with banco() as db:
        perfil = acesso.criar_perfil(db, "Estoquista", ["entradas.ver", "entradas.lancar"])
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "davi"), db.get(Empresa, cenario["e1"]), perfil)
    davi = _auth(cliente, "davi", cenario["e1"])
    url = f"/entradas/{nota['id']}/itens/{nota['itens'][0]['id']}"
    assert cliente.put(url, headers=davi, json={"produto_id": jogo["produto"], "preco_venda": "10"}).status_code == 403
    assert cliente.put(url, headers=davi, json={"produto_id": jogo["produto"], "embalagem": 2}).status_code == 200
    assert cliente.post(f"/entradas/{nota['id']}/confirmar", headers=davi).status_code == 200
