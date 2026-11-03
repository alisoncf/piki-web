"""NF-e (modelo 55) da venda (D29): destinatário com endereço, natureza e CFOP parametrizáveis, DANFE em PDF.
A SEFAZ é de mentira. Dados fictícios."""
from lxml import etree
from test_nfce import NS, _com_ncm, falsa, loja  # noqa: F401 (as fixtures vêm junto)

from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.clientes.modelos import Cliente, Setor


def _cliente(banco, cep="01001000", uf="SP"):
    with banco() as db:
        cidade = Cidade(codigo_ibge="3550308" if uf == "SP" else "5201108", nome="Cidade Ficticia", uf=uf,
                        nome_busca=nome_de_busca(f"Cidade Ficticia {uf}"))
        db.add(cidade)
        db.flush()
        setor = Setor(nome="Centro", cidade_id=cidade.id)
        db.add(setor)
        db.flush()
        cliente = Cliente(nome="Freguesa Ficticia", cpf_cnpj="52998224725", logradouro="Rua Ficticia", numero="5",
                          cep=cep, setor_id=setor.id, email="freguesa@exemplo.com")
        db.add(cliente)
        db.commit()
        return cliente.id


def _venda_nfe(cliente, loja, dados):
    quem = loja["davi"]
    url = f"/vendas/{cliente.post('/vendas', headers=quem).json()['id']}"
    cliente.post(f"{url}/itens", headers=quem, json={"produto_id": loja["produto"], "quantidade": "1"})
    cliente.put(url, headers=quem, json={"forma_pagamento_id": loja["dinheiro"]} | dados)
    cliente.post(f"{url}/fechar", headers=quem)
    r = cliente.post(f"{url}/receber", headers=quem, json={
        "sessao_caixa_id": loja["sessao"], "modelo_nota": "55",
        "pagamentos": [{"forma_pagamento_id": loja["dinheiro"], "valor": "100.00"}]})
    assert r.status_code == 200, r.text
    return url


def test_nfe_da_venda_para_cliente_de_fora(banco, cliente, loja, falsa):  # noqa: F811
    _com_ncm(banco, loja)
    davi = loja["davi"]
    freguesa = _cliente(banco, cep=None)
    url = _venda_nfe(cliente, loja, {"cliente_id": freguesa})
    r = cliente.post(f"{url}/nota", headers=davi)
    assert r.status_code == 422 and "Falta no cadastro do cliente Freguesa Ficticia: o CEP" in r.json()["detail"]
    with banco() as db:
        db.get(Cliente, freguesa).cep = "01001000"
        db.commit()

    # a natureza e o CFOP da venda são parametrizáveis
    operacoes = cliente.get("/notas/operacoes", headers=loja["admin"]).json()
    assert [(o["uso"], o["cfop_estado"], o["cfop_fora"]) for o in operacoes] == [
        ("venda", "5102", "6102"), ("remessa", "5904", "6904"), ("retorno_remessa", "5904", "6904"),
        ("devolucao", "5915", "6915")]
    venda = operacoes[0]
    dados = {k: venda[k] for k in ("natureza", "tipo", "finalidade", "cfop_estado", "cfop_fora")}
    assert cliente.put(f"/notas/operacoes/{venda['id']}", headers=davi, json=dados).status_code == 403
    r = cliente.put(f"/notas/operacoes/{venda['id']}", headers=loja["admin"], json=dados | {"natureza": "Venda de mercadoria"})
    assert r.status_code == 200, r.text

    nota = cliente.post(f"{url}/nota", headers=davi).json()
    assert (nota["modelo"], nota["situacao"], nota["serie"], nota["numero"], nota["destinatario"]) == (
        "55", "autorizada", 101, 1, "Freguesa Ficticia")
    enviado = etree.fromstring(falsa.enviados[-1].encode())
    texto = lambda caminho: enviado.find(caminho, NS).text  # noqa: E731
    assert (texto(".//n:mod"), texto(".//n:natOp"), texto(".//n:idDest"), texto(".//n:tpImp")) == (
        "55", "Venda de mercadoria", "2", "1")
    assert texto(".//n:CFOP") == "6102"  # cliente de São Paulo
    assert (texto(".//n:enderDest/n:UF"), texto(".//n:enderDest/n:xBairro"), texto(".//n:dest/n:email")) == (
        "SP", "Centro", "freguesa@exemplo.com")
    assert enviado.find(".//n:infNFeSupl", NS) is None  # QR Code só na NFC-e
    assert texto(".//n:xProd") != "NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"

    r = cliente.get(f"/notas/{nota['id']}/danfe.pdf", headers=davi)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")


def test_nfe_dentro_do_estado(banco, cliente, loja, falsa):  # noqa: F811
    _com_ncm(banco, loja)
    url = _venda_nfe(cliente, loja, {"cliente_id": _cliente(banco, uf="GO")})
    nota = cliente.post(f"{url}/nota", headers=loja["davi"]).json()
    assert nota["situacao"] == "autorizada"
    enviado = etree.fromstring(falsa.enviados[-1].encode())
    assert (enviado.find(".//n:idDest", NS).text, enviado.find(".//n:CFOP", NS).text) == ("1", "5102")
    # a NFC-e não tem DANFE em PDF
    nfce = cliente.post(f"{_venda_nfe_65(cliente, loja)}/nota", headers=loja["davi"]).json()
    assert cliente.get(f"/notas/{nfce['id']}/danfe.pdf", headers=loja["davi"]).status_code == 422


def _venda_nfe_65(cliente, loja):
    from test_nfce import _venda
    return _venda(cliente, loja, loja["davi"])
