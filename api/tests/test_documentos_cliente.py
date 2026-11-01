"""Documentos do cliente para o crediário. Arquivos fictícios, numa pasta temporária."""
from types import SimpleNamespace

import pytest

from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.empresas.modelos import Empresa
from app.main import app
from app.nucleo import arquivos
from app.nucleo.arquivos import ArquivoNaoEncontrado, MinIO, Pasta

PDF = b"%PDF-1.4\n" + b"0" * 50
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 50


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
def admin(cliente, cenario):
    return _auth(cliente, "caio", cenario["e1"])


@pytest.fixture
def maria(cliente, admin):
    r = cliente.post("/clientes", headers=admin, json={"nome": "Maria Teste", "cpf_cnpj": "529.982.247-25"})
    return r.json()["id"]


def _enviar(cliente, cabecalho, cliente_id, conteudo=PDF, **params):
    params = {"tipo": "identidade", **params}
    return cliente.post(f"/clientes/{cliente_id}/documentos", headers=cabecalho, params=params, content=conteudo)


def test_enviar_listar_e_baixar(cliente, cenario, admin, maria, pasta):
    r = _enviar(cliente, admin, maria, JPEG, descricao=" frente ", nome="C:\\fotos\\rg frente.jpg")
    assert r.status_code == 201, r.text
    doc = r.json()
    assert (doc["tipo"], doc["descricao"], doc["nome_arquivo"], doc["tipo_conteudo"], doc["tamanho"]) == (
        "identidade", "frente", "rg frente.jpg", "image/jpeg", len(JPEG))
    assert (doc["usuario"]["nome"], doc["empresa"]["codigo"]) == ("Caio Admin", "01")
    # o arquivo fica na pasta, fora do banco, com um nome que não diz de quem é
    gravados = list(pasta.rglob("*.jpg"))
    assert len(gravados) == 1 and gravados[0].parent.name == str(maria) and gravados[0].read_bytes() == JPEG

    _enviar(cliente, admin, maria, PDF, tipo="endereco")
    lista = cliente.get(f"/clientes/{maria}/documentos", headers=admin).json()
    assert [d["tipo"] for d in lista] == ["endereco", "identidade"]  # o mais novo primeiro

    r = cliente.get(f"/clientes/{maria}/documentos/{doc['id']}/arquivo", headers=admin)
    assert (r.status_code, r.content, r.headers["content-type"]) == (200, JPEG, "image/jpeg")
    assert r.headers["cache-control"] == "private, no-store"
    assert "rg%20frente.jpg" in r.headers["content-disposition"]


def test_arquivo_conferido(cliente, cenario, admin, maria, pasta):
    assert _enviar(cliente, admin, maria, b"<html>").json()["detail"] == "Envie um PDF ou uma imagem JPEG ou PNG"
    assert _enviar(cliente, admin, maria, b"").status_code == 422
    assert _enviar(cliente, admin, maria, PDF + b"0" * 5 * 1024 * 1024).json()["detail"] == "O arquivo passa de 5 MB"
    assert _enviar(cliente, admin, maria, tipo="selfie").status_code == 422
    assert _enviar(cliente, admin, 999).status_code == 404
    assert list(pasta.rglob("*.*")) == []


def test_so_quem_trabalha_com_crediario(cliente, cenario, admin, maria, pasta, banco):
    """clientes.ver não basta para ver documentos (LGPD); remover pede também clientes.editar."""
    doc = _enviar(cliente, admin, maria).json()
    with banco() as db:
        ana = repositorio.usuario_por_login(db, "ana")
        e1 = db.get(Empresa, cenario["e1"])
        balcao = acesso.criar_perfil(db, "Balcão", ["clientes.ver", "clientes.editar"])
        acesso.dar_acesso(db, ana, e1, balcao)
    ana = _auth(cliente, "ana", cenario["e1"])
    assert cliente.get(f"/clientes/{maria}", headers=ana).status_code == 200
    assert cliente.get(f"/clientes/{maria}/documentos", headers=ana).status_code == 403
    assert cliente.get(f"/clientes/{maria}/documentos/{doc['id']}/arquivo", headers=ana).status_code == 403
    assert _enviar(cliente, ana, maria).status_code == 403

    with banco() as db:
        crediario = acesso.criar_perfil(db, "Crediário", ["clientes.ver", "clientes.documentos"])
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "ana"), db.get(Empresa, cenario["e1"]), crediario)
    assert cliente.get(f"/clientes/{maria}/documentos", headers=ana).status_code == 200
    assert cliente.delete(f"/clientes/{maria}/documentos/{doc['id']}", headers=ana).status_code == 403


def test_remover_guarda_o_registro_e_o_arquivo(cliente, cenario, admin, maria, pasta, banco):
    from app.dominios.clientes.modelos import DocumentoCliente

    doc = _enviar(cliente, admin, maria).json()
    assert cliente.delete(f"/clientes/{maria}/documentos/{doc['id']}", headers=admin).status_code == 204
    assert cliente.get(f"/clientes/{maria}/documentos", headers=admin).json() == []
    assert cliente.get(f"/clientes/{maria}/documentos/{doc['id']}/arquivo", headers=admin).status_code == 404
    with banco() as db:
        registro = db.get(DocumentoCliente, doc["id"])
        assert registro.removido_em is not None and registro.removido_por_id is not None
    assert len(list(pasta.rglob("*.pdf"))) == 1


def test_pasta_nao_sai_da_raiz(tmp_path):
    p = Pasta(tmp_path / "arquivos")
    p.gravar("clientes/1/a.pdf", PDF, "application/pdf")
    assert p.ler("clientes/1/a.pdf") == PDF
    with pytest.raises(ArquivoNaoEncontrado):
        p.ler("clientes/1/b.pdf")
    with pytest.raises(ValueError):
        p.gravar("../fora.pdf", PDF, "application/pdf")


def test_minio_grava_e_le_no_bucket():
    guardados = {}

    class Resposta:
        def __init__(self, dados):
            self.dados = dados

        def read(self):
            return self.dados

        def close(self):
            pass

        def release_conn(self):
            pass

    falso = SimpleNamespace(
        put_object=lambda bucket, chave, dados, tamanho, content_type: guardados.update(
            {(bucket, chave): (dados.read(), tamanho, content_type)}),
        get_object=lambda bucket, chave: Resposta(guardados[(bucket, chave)][0]),
    )
    m = MinIO(falso, "piki")
    m.gravar("clientes/1/a.pdf", PDF, "application/pdf")
    assert guardados[("piki", "clientes/1/a.pdf")] == (PDF, len(PDF), "application/pdf")
    assert m.ler("clientes/1/a.pdf") == PDF
