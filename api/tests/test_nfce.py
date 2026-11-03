"""NFC-e da venda (D29): montar, assinar, transmitir, consultar, cancelar. A SEFAZ é de mentira. Dados fictícios."""
import base64
from datetime import datetime
from decimal import Decimal

import pytest
from lxml import etree
from test_fiscal import CNPJ, _pfx

from app.config import configuracao
from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.empresas.modelos import Empresa
from app.dominios.estoque.modelos import Estoque
from app.dominios.fiscal import leiaute, sefaz
from app.dominios.fiscal import servico as fiscal
from app.dominios.fiscal.modelos import NotaFiscal, NumeracaoNota
from app.dominios.produtos.modelos import CodigoBarras, Produto
from app.nucleo import segredos

NS = {"n": leiaute.NS}


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class SefazFalsa:
    """Responde o que o teste mandar; guarda o que recebeu."""

    def __init__(self):
        self.enviados, self.consultas, self.cancelamentos, self.inutilizacoes = [], [], [], []
        self.resposta = "100"  # ou "204", "778", "fora"
        self.consulta = "100"

    def _protocolo(self, chave, codigo, motivo):
        xml = (f'<protNFe xmlns="{leiaute.NS}" versao="4.00"><infProt><tpAmb>2</tpAmb><verAplic>GO</verAplic>'
               f"<chNFe>{chave}</chNFe><dhRecbto>2026-11-03T10:00:00-03:00</dhRecbto><nProt>152260000000123</nProt>"
               f"<digVal>abc=</digVal><cStat>{codigo}</cStat><xMotivo>{motivo}</xMotivo></infProt></protNFe>")
        return sefaz.Retorno(codigo, motivo, "152260000000123", datetime(2026, 11, 3, 10), xml)

    def status(self):
        return sefaz.Retorno("107", "Servico em Operacao")

    def autorizar(self, xml):
        self.enviados.append(xml)
        chave = etree.fromstring(xml.encode()).find(".//n:infNFe", NS).get("Id")[3:]
        if self.resposta == "fora":
            raise sefaz.SemConexao("A SEFAZ não respondeu (ReadTimeout): tente de novo em instantes")
        if self.resposta == "100":
            return self._protocolo(chave, "100", "Autorizado o uso da NF-e")
        if self.resposta == "204":
            return sefaz.Retorno("204", "Rejeicao: Duplicidade de NF-e")
        return sefaz.Retorno(self.resposta, "Rejeicao: NCM inexistente")

    def consultar(self, chave):
        self.consultas.append(chave)
        if self.consulta == "217":
            return sefaz.Retorno("217", "Rejeicao: NF-e nao consta na base de dados da SEFAZ")
        return self._protocolo(chave, "100", "Autorizado o uso da NF-e")

    def inutilizar(self, cnpj, modelo, serie, inicial, final, justificativa):
        self.inutilizacoes.append((cnpj, modelo, serie, inicial, final, justificativa))
        return sefaz.Retorno("102", "Inutilizacao de numero homologado", "152260000000777", datetime(2026, 11, 3, 11),
                             f'<retInutNFe xmlns="{leiaute.NS}" versao="4.00"/>')

    def cancelar(self, chave, protocolo, justificativa, cnpj):
        self.cancelamentos.append((chave, protocolo, justificativa, cnpj))
        return sefaz.Retorno("135", "Evento registrado e vinculado a NF-e", "152260000000999", datetime(2026, 11, 3, 10, 5),
                             f'<retEvento xmlns="{leiaute.NS}" versao="1.00"/>')


@pytest.fixture
def falsa(monkeypatch):
    s = SefazFalsa()
    monkeypatch.setattr(fiscal, "conectar", lambda empresa: (fiscal.certificado(empresa), s)[1])
    return s


@pytest.fixture
def loja(banco, cliente, cenario, monkeypatch, tmp_path):
    """A loja 01 com os dados fiscais, o certificado e o CSC; um produto; o caixa da série 101 aberto."""
    c = configuracao()
    monkeypatch.setattr(c, "chave_segredos", segredos.nova_chave())
    monkeypatch.setattr(c, "certificados_pasta", str(tmp_path / "certificados"))
    with banco() as db:
        cidade = Cidade(codigo_ibge="5208707", nome="Goiânia", uf="GO", nome_busca=nome_de_busca("Goiânia"))
        db.add(cidade)
        db.flush()
        empresa = db.get(Empresa, cenario["e1"])
        empresa.cnpj, empresa.razao_social, empresa.inscricao_estadual, empresa.crt = CNPJ, "LOJA FICTICIA LTDA", "100000001", "1"
        empresa.logradouro, empresa.numero, empresa.bairro, empresa.cep = "RUA FICTICIA", "10", "CENTRO", "74000000"
        empresa.cidade_id = cidade.id
        lencol = Produto(codigo=1, nome="Lençol Ficticio Casal", preco_venda=Decimal("100.00"), ncm=None)
        db.add(lencol)
        db.flush()
        db.add(CodigoBarras(produto_id=lencol.id, codigo="7891234567895"))
        db.add(Estoque(empresa_id=cenario["e1"], produto_id=lencol.id, quantidade=Decimal("50"), reservado=Decimal(0)))
        caixa = acesso.criar_perfil(db, "Caixa", ["vendas.vender", "caixa.operar"])
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "davi"), db.get(Empresa, cenario["e1"]), caixa)
        fiscal.continuar_de(db, cenario["e1"], "65", 101, 500)  # produção, vindo do VB6
        db.commit()
        produto = lencol.id
    admin = _auth(cliente, "caio", cenario["e1"])
    url = f"/empresas/{cenario['e1']}"
    arquivo = base64.b64encode(_pfx(CNPJ, "senha-certa")).decode()
    assert cliente.put(f"{url}/certificado", headers=admin, json={"arquivo": arquivo, "senha": "senha-certa"}).status_code == 200
    assert cliente.put(f"{url}/fiscal", headers=admin, json={"ambiente": "2", "csc_id": "000001", "csc_token": "CSC-FICTICIO"}).status_code == 200
    dinheiro = cliente.post("/formas-pagamento", headers=admin, json={"nome": "Dinheiro", "tipo": "dinheiro"}).json()["id"]
    cx = cliente.post("/caixas", headers=admin, json={"nome": "Cx 01", "serie_nfe": 101}).json()
    sessao = cliente.post(f"/caixas/{cx['id']}/abrir", headers=admin, json={"fundo": "50"}).json()["id"]
    return {"admin": admin, "davi": _auth(cliente, "davi", cenario["e1"]), "produto": produto, "dinheiro": dinheiro,
            "sessao": sessao, "empresa": cenario["e1"]}


def _venda(cliente, loja, quem):
    url = f"/vendas/{cliente.post('/vendas', headers=quem).json()['id']}"
    cliente.post(f"{url}/itens", headers=quem, json={"produto_id": loja["produto"], "quantidade": "2"})
    cliente.put(url, headers=quem, json={"forma_pagamento_id": loja["dinheiro"], "consumidor": {"nome": "José"}})
    cliente.post(f"{url}/fechar", headers=quem)
    r = cliente.post(f"{url}/receber", headers=quem, json={
        "sessao_caixa_id": loja["sessao"], "valor_recebido": "250.00",
        "pagamentos": [{"forma_pagamento_id": loja["dinheiro"], "valor": "200.00"}]})
    assert r.status_code == 200, r.text
    return url


def _com_ncm(banco, loja):
    with banco() as db:
        db.get(Produto, loja["produto"]).ncm = "63022100"
        db.commit()


def test_monta_xml_valido_no_leiaute():
    """O XML montado passa no esquema oficial; a chave tem o dígito certo; o QR Code é o da versão 2."""
    emitente = leiaute.Emitente(CNPJ, "LOJA FICTICIA LTDA", None, "100000001", "RUA FICTICIA", "10", None, "CENTRO",
                             "5208707", "Goiânia", "GO", "74000000", None)
    item = leiaute.ItemNota("1", "123", "TOALHA & CIA", "63026000", None, "5102", "UN", Decimal("1"), Decimal("30"),
                         Decimal("30.00"), Decimal("0.00"), 0, "500")
    dados = leiaute.DadosNota(emitente, "1", 101, 44537, datetime(2026, 11, 3, 10), [item],
                           [leiaute.PagamentoNota("17", Decimal("30.00")), leiaute.PagamentoNota("99", Decimal("5.00"), "Vale")],
                           outros=Decimal("5.00"), destinatario=leiaute.Destinatario("52998224725", "Fulano"),
                           codigo_numerico="12345678")
    chave, xml = leiaute.montar(dados)
    assert chave[:-1] == f"522611{CNPJ}65101000044537112345678" and chave[-1] == leiaute.digito_chave(chave[:-1])
    xml = leiaute.com_qrcode(xml, chave, "1", "000001", "CSC")
    assinado = sefaz.assinar(xml, _pfx(CNPJ, "s"), "s", chave)
    assert sefaz.erros_de_leiaute(assinado) == []
    raiz = etree.fromstring(assinado.encode())
    assert raiz.find(".//n:qrCode", NS).text.startswith(f"https://nfe.sefaz.go.gov.br/nfeweb/sites/nfce/danfeNFCe?p={chave}|2|1|1|")
    assert raiz.find(".//n:cEAN", NS).text == "SEM GTIN"  # 123 não é GTIN válido
    assert raiz.find(".//n:ICMSSN500/n:CSOSN", NS).text == "500"
    assert raiz.find(".//n:dest/n:xNome", NS).text == "Fulano"
    assert [p.text for p in raiz.findall(".//n:detPag/n:xPag", NS)] == ["Vale"]
    assert raiz.find(".//n:vNF", NS).text == "35.00"


def test_emite_a_nfce_da_venda(banco, cliente, loja, falsa):
    url = _venda(cliente, loja, loja["davi"])
    # sem NCM: nem vai para a SEFAZ, e o número não é gasto
    r = cliente.post(f"{url}/nota", headers=loja["davi"])
    assert r.status_code == 422 and "Produto sem NCM: Lençol Ficticio Casal" in r.json()["detail"]
    assert falsa.enviados == []
    _com_ncm(banco, loja)

    r = cliente.post(f"{url}/nota", headers=loja["davi"])
    assert r.status_code == 200, r.text
    nota = r.json()
    assert (nota["situacao"], nota["ambiente"], nota["serie"], nota["numero"], nota["valor"], nota["protocolo"]) == (
        "autorizada", "2", 101, 1, "200.00", "152260000000123")
    enviado = etree.fromstring(falsa.enviados[0].encode())
    # homologação: a descrição do primeiro item é a exigida; o dinheiro vai com o que o cliente deu, e o troco
    assert enviado.find(".//n:xProd", NS).text == leiaute.HOMOLOGACAO
    assert enviado.find(".//n:cEAN", NS).text == "7891234567895"
    assert [(p.find("n:tPag", NS).text, p.find("n:vPag", NS).text) for p in enviado.findall(".//n:detPag", NS)] == [("01", "250.00")]
    assert enviado.find(".//n:vTroco", NS).text == "50.00"
    with banco() as db:
        guardada = db.get(NotaFiscal, nota["id"])
        assert guardada.xml.count("<nfeProc") == 1 and "<protNFe" in guardada.xml and "<Signature" in guardada.xml
        # os testes não gastam a numeração de produção
        producao = db.query(NumeracaoNota).filter_by(empresa_id=loja["empresa"], ambiente="1", serie=101).one()
        assert producao.ultimo == 500

    # de novo: já autorizada, não vai outra vez
    assert cliente.post(f"{url}/nota", headers=loja["davi"]).json()["id"] == nota["id"] and len(falsa.enviados) == 1
    assert cliente.get(f"{url}/nota", headers=loja["davi"]).json()["id"] == nota["id"]

    danfe = cliente.get(f"/notas/{nota['id']}/danfe", headers=loja["davi"]).json()
    assert (danfe["total"], danfe["troco"], danfe["protocolo"], danfe["numero"]) == ("200.00", "50.00", "152260000000123", 1)
    assert danfe["qrcode"].startswith("https://homolog.sefaz.go.gov.br/") and danfe["qrcode_svg"].startswith("<svg")
    r = cliente.get(f"/notas/{nota['id']}/xml", headers=loja["davi"])
    assert r.headers["content-type"].startswith("application/xml") and "procNFe.xml" in r.headers["content-disposition"]


def test_resposta_perdida_e_retransmissao(banco, cliente, loja, falsa):
    _com_ncm(banco, loja)
    url = _venda(cliente, loja, loja["davi"])
    falsa.resposta = "fora"
    r = cliente.post(f"{url}/nota", headers=loja["davi"])
    assert r.status_code == 503 and "ficou pendente" in r.json()["detail"]
    nota = cliente.get(f"{url}/nota", headers=loja["davi"]).json()
    assert nota["situacao"] == "pendente"

    # a SEFAZ tinha autorizado: o mesmo XML de novo dá duplicidade, e a consulta traz o protocolo
    falsa.resposta = "204"
    nota2 = cliente.post(f"{url}/nota", headers=loja["davi"]).json()
    assert (nota2["id"], nota2["situacao"], nota2["numero"]) == (nota["id"], "autorizada", 1)
    assert falsa.enviados[0] == falsa.enviados[1] and falsa.consultas == [nota["chave"]]


def test_rejeitada_e_transmitida_de_novo(banco, cliente, loja, falsa):
    _com_ncm(banco, loja)
    url = _venda(cliente, loja, loja["davi"])
    falsa.resposta = "778"
    nota = cliente.post(f"{url}/nota", headers=loja["davi"]).json()
    assert (nota["situacao"], nota["codigo_retorno"], nota["motivo_retorno"]) == ("rejeitada", "778", "Rejeicao: NCM inexistente")

    # corrigido, vai de novo com o mesmo número
    falsa.resposta = "100"
    nota2 = cliente.post(f"{url}/nota", headers=loja["davi"]).json()
    assert (nota2["id"], nota2["situacao"], nota2["numero"]) == (nota["id"], "autorizada", 1)
    # a próxima venda pega o número seguinte
    outra = cliente.post(f"{_venda(cliente, loja, loja['davi'])}/nota", headers=loja["davi"]).json()
    assert outra["numero"] == 2

    # a pendente que a SEFAZ não conhece (não chegou lá) vira rejeitada na consulta
    with banco() as db:
        db.get(NotaFiscal, outra["id"]).situacao = "pendente"
        db.commit()
    falsa.consulta = "217"
    assert cliente.post(f"/notas/{outra['id']}/consultar", headers=loja["davi"]).json()["situacao"] == "rejeitada"


def test_cancelar_nota(banco, cliente, loja, falsa):
    _com_ncm(banco, loja)
    url = _venda(cliente, loja, loja["davi"])
    nota = cliente.post(f"{url}/nota", headers=loja["davi"]).json()
    r = cliente.post(f"/notas/{nota['id']}/cancelar", headers=loja["davi"], json={"justificativa": "Cliente desistiu da compra"})
    assert r.status_code == 403  # o caixa emite, mas não cancela
    r = cliente.post(f"/notas/{nota['id']}/cancelar", headers=loja["admin"], json={"justificativa": "curta"})
    assert r.status_code == 422
    r = cliente.post(f"/notas/{nota['id']}/cancelar", headers=loja["admin"], json={"justificativa": "Cliente desistiu da compra"})
    assert r.status_code == 200, r.text
    cancelada = r.json()
    assert (cancelada["situacao"], cancelada["protocolo_cancelamento"], cancelada["cancelada_por"]["nome"]) == (
        "cancelada", "152260000000999", "Caio Admin")
    assert falsa.cancelamentos == [(nota["chave"], "152260000000123", "Cliente desistiu da compra", CNPJ)]
    r = cliente.post(f"/notas/{nota['id']}/cancelar", headers=loja["admin"], json={"justificativa": "Cliente desistiu da compra"})
    assert r.status_code == 422  # já cancelada

    lista = cliente.get("/notas", headers=loja["admin"], params={"situacao": "cancelada"}).json()
    assert [n["id"] for n in lista] == [nota["id"]]
    assert cliente.get("/notas", headers=loja["admin"], params={"situacao": "autorizada"}).json() == []


def test_sem_certificado_ou_sem_serie(banco, cliente, loja, falsa):
    _com_ncm(banco, loja)
    url = _venda(cliente, loja, loja["davi"])
    with banco() as db:
        db.get(Empresa, loja["empresa"]).certificado_arquivo = None
        db.commit()
    r = cliente.post(f"{url}/nota", headers=loja["davi"])
    assert r.status_code == 422 and "não tem certificado" in r.json()["detail"]
    assert cliente.post(f"/empresas/{loja['empresa']}/sefaz", headers=loja["admin"]).status_code == 422


def test_status_da_sefaz(cliente, loja, falsa):
    r = cliente.post(f"/empresas/{loja['empresa']}/sefaz", headers=loja["admin"])
    assert r.json() == {"codigo": "107", "motivo": "Servico em Operacao"}
    assert cliente.post(f"/empresas/{loja['empresa']}/sefaz", headers=loja["davi"]).status_code == 403


def test_inutiliza_as_lacunas_da_serie(banco, cliente, loja, falsa):
    """Notas 1 a 6 da série 101: a 2 e a 3 rejeitadas e largadas, a 5 pendente; a 7 e a 8 reservadas e não usadas."""
    _com_ncm(banco, loja)
    situacoes = {1: "autorizada", 2: "rejeitada", 3: "rejeitada", 4: "cancelada", 5: "pendente", 6: "autorizada"}
    with banco() as db:
        for numero, situacao in situacoes.items():
            db.add(NotaFiscal(empresa_id=loja["empresa"], ambiente="2", modelo="65", serie=101, numero=numero,
                              codigo_numerico="12345678", chave=f"{numero:044d}", situacao=situacao,
                              emitida_em=datetime(2026, 11, 3, 9), emitida_por_id=1, valor=Decimal("10.00"), xml="<NFe/>"))
        db.add(NumeracaoNota(empresa_id=loja["empresa"], ambiente="2", modelo="65", serie=101, ultimo=8))
        db.commit()
    admin = loja["admin"]
    assert cliente.get("/notas/series", headers=admin).json() == [{"modelo": "65", "serie": 101, "ultimo": 8}]
    r = cliente.get("/notas/lacunas", headers=admin, params={"serie": 101, "desde": "2026-11-01"})
    assert r.json() == {"faixas": [{"inicial": 2, "final": 3}, {"inicial": 7, "final": 8}], "pendentes": [5]}
    assert cliente.get("/notas/lacunas", headers=loja["davi"], params={"serie": 101, "desde": "2026-11-01"}).status_code == 403

    pedido = {"serie": 101, "inicial": 2, "final": 3, "justificativa": "Notas rejeitadas e nao reenviadas"}
    for faixa, erro in [((4, 5), "nota cancelada"), ((5, 5), "consulte-a na SEFAZ"), ((8, 9), "só chegou ao número 8")]:
        r = cliente.post("/notas/inutilizacoes", headers=admin, json=pedido | {"inicial": faixa[0], "final": faixa[1]})
        assert r.status_code == 422 and erro in r.json()["detail"], r.text
    assert falsa.inutilizacoes == []

    r = cliente.post("/notas/inutilizacoes", headers=admin, json=pedido)
    assert r.status_code == 201, r.text
    assert (r.json()["protocolo"], r.json()["feita_por"]["nome"]) == ("152260000000777", "Caio Admin")
    assert falsa.inutilizacoes == [(CNPJ, "65", 101, 2, 3, "Notas rejeitadas e nao reenviadas")]
    with banco() as db:
        assert {n.numero: n.situacao for n in db.query(NotaFiscal).filter(NotaFiscal.numero.in_([2, 3]))} == {
            2: "inutilizada", 3: "inutilizada"}
    r = cliente.get("/notas/lacunas", headers=admin, params={"serie": 101, "desde": "2026-11-01"})
    assert r.json()["faixas"] == [{"inicial": 7, "final": 8}]
    assert cliente.post("/notas/inutilizacoes", headers=admin, json=pedido).status_code == 422  # já inutilizada
    assert [i["inicial"] for i in cliente.get("/notas/inutilizacoes", headers=admin).json()] == [2]


    # a venda cuja nota rejeitada teve o número inutilizado ganha outro número
    url = _venda(cliente, loja, loja["davi"])
    falsa.resposta = "778"
    rejeitada = cliente.post(f"{url}/nota", headers=loja["davi"]).json()
    assert (rejeitada["numero"], rejeitada["situacao"]) == (9, "rejeitada")
    r = cliente.post("/notas/inutilizacoes", headers=admin, json=pedido | {"inicial": 7, "final": 9})
    assert r.status_code == 201, r.text
    falsa.resposta = "100"
    nova = cliente.post(f"{url}/nota", headers=loja["davi"]).json()
    assert (nova["numero"], nova["situacao"]) == (10, "autorizada") and nova["id"] != rejeitada["id"]
