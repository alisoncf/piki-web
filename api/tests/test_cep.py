"""Endereço pelo CEP (ViaCEP) e o setor adivinhado pelo bairro. O ViaCEP é simulado: os testes não usam a rede."""
import httpx
import pytest

from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.clientes.modelos import Setor
from app.dominios.enderecos import viacep

JUNDIAI = {"cep": "75110-010", "logradouro": "Rua Amaro Pires", "complemento": "", "bairro": "Jundiaí",
           "localidade": "Anápolis", "uf": "GO", "ibge": "5201108"}


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    return _auth(cliente, "caio", cenario["e1"])


@pytest.fixture
def setores(banco):
    """Anápolis com setores escritos como vieram do VB6; Goiânia com outro Jundiaí."""
    with banco() as db:
        anapolis = Cidade(codigo_ibge="5201108", nome="Anápolis", uf="GO", nome_busca=nome_de_busca("Anápolis"))
        goiania = Cidade(codigo_ibge="5208707", nome="Goiânia", uf="GO", nome_busca=nome_de_busca("Goiânia"))
        lista = [
            Setor(nome="JUNDIAI", tipo="BAIRRO", cidade=anapolis),
            Setor(nome="JUNDIAI INDUSTRIAL", tipo="BAIRRO", cidade=anapolis),
            Setor(nome="NOVO JUNDIAI", tipo="BAIRRO", cidade=anapolis),
            Setor(nome="JAIARA", tipo="VILA", cidade=anapolis),
            Setor(nome="JD. GUANABARA", tipo="JARDIM", cidade=anapolis),
            Setor(nome="CENTRO", tipo="BAIRRO", cidade=anapolis, ativo=False),
            Setor(nome="JUNDIAI", tipo="BAIRRO", cidade=goiania),
        ]
        db.add_all(lista)
        db.commit()
        return {(s.nome, s.cidade.nome): s.id for s in lista}


@pytest.fixture
def via(monkeypatch):
    """Troca a consulta ao ViaCEP por um dicionário cep -> resposta."""
    respostas: dict = {}

    def consultar(cep):
        resposta = respostas.get(cep)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    monkeypatch.setattr(viacep, "consultar", consultar)
    return respostas


def test_cep_com_setor_igual(cliente, admin, setores, via):
    via["75110010"] = JUNDIAI
    r = cliente.get("/cep/75110-010", headers=admin)
    assert r.status_code == 200, r.text
    d = r.json()
    assert (d["cep"], d["logradouro"], d["complemento"], d["bairro"]) == ("75110010", "Rua Amaro Pires", None, "Jundiaí")
    assert d["cidade"]["codigo_ibge"] == "5201108"
    # o Jundiaí de Anápolis, não o de Goiânia; os parecidos não entram quando há um igual
    assert d["setor"]["id"] == setores[("JUNDIAI", "Anápolis")]
    assert {s["nome"] for s in d["sugestoes"]} == {"JUNDIAI INDUSTRIAL", "NOVO JUNDIAI"}


@pytest.mark.parametrize("bairro, esperado", [
    ("Vila Jaiara", "JAIARA"),  # o tipo do setor completa o nome
    ("Jardim Guanabara", "JD. GUANABARA"),  # abreviação
    ("Bairro Jundiaí", "JUNDIAI"),
])
def test_nomes_escritos_de_outro_jeito(cliente, admin, setores, via, bairro, esperado):
    via["75110010"] = {**JUNDIAI, "bairro": bairro}
    assert cliente.get("/cep/75110010", headers=admin).json()["setor"]["nome"] == esperado


def test_sem_setor_igual_sugere_os_parecidos(cliente, admin, setores, via):
    via["75110010"] = {**JUNDIAI, "bairro": "Jardim Jaiara"}
    d = cliente.get("/cep/75110010", headers=admin).json()
    assert d["setor"] is None
    assert [s["nome"] for s in d["sugestoes"]] == ["JAIARA"]
    # setor inativo não é sugerido; bairro sem nada parecido não sugere nada
    via["75110010"] = {**JUNDIAI, "bairro": "Centro"}
    d = cliente.get("/cep/75110010", headers=admin).json()
    assert (d["setor"], d["sugestoes"], d["bairro"]) == (None, [], "Centro")


def test_cep_geral_da_cidade(cliente, admin, setores, via):
    """Cidade pequena: um CEP só, sem rua nem bairro. Vem só a cidade."""
    via["75110000"] = {**JUNDIAI, "logradouro": "", "bairro": ""}
    d = cliente.get("/cep/75110000", headers=admin).json()
    assert (d["logradouro"], d["bairro"], d["setor"], d["sugestoes"]) == (None, None, None, [])
    assert d["cidade"]["nome"] == "Anápolis"


def test_cep_invalido_inexistente_ou_servico_fora(cliente, admin, cenario, via):
    assert cliente.get("/cep/1234", headers=admin).status_code == 422
    r = cliente.get("/cep/99999999", headers=admin)
    assert (r.status_code, r.json()["detail"]) == (404, "CEP 99999-999 não encontrado")
    via["75110010"] = viacep.CepIndisponivel("tempo esgotado")
    assert cliente.get("/cep/75110010", headers=admin).status_code == 503


def test_cep_exige_editar_cliente_ou_funcionario(cliente, cenario, via):
    ana = _auth(cliente, "ana", cenario["e1"])  # gerente só de acesso
    assert cliente.get("/cep/75110010", headers=ana).status_code == 403


def _cliente_http(responder):
    return httpx.Client(transport=httpx.MockTransport(responder))


def test_leitura_da_resposta_do_viacep():
    pedidos = []

    def responder(pedido):
        pedidos.append(str(pedido.url))
        if pedido.url.path == "/ws/75110010/json/":
            return httpx.Response(200, json=JUNDIAI)
        return httpx.Response(200, json={"erro": "true"})

    with _cliente_http(responder) as http:
        assert viacep.consultar("75110010", http)["bairro"] == "Jundiaí"
        assert viacep.consultar("99999999", http) is None
    assert pedidos[0] == "https://viacep.com.br/ws/75110010/json/"

    with _cliente_http(lambda p: httpx.Response(500)) as http, pytest.raises(viacep.CepIndisponivel):
        viacep.consultar("75110010", http)

    def cair(pedido):
        raise httpx.ConnectTimeout("tempo esgotado")

    with _cliente_http(cair) as http, pytest.raises(viacep.CepIndisponivel):
        viacep.consultar("75110010", http)
