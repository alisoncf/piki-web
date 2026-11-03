"""Preparação das notas fiscais (D29): certificado, CSC, série do caixa e numeração. Dados fictícios."""
import base64
from datetime import datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12
from cryptography.x509.oid import NameOID
from sqlalchemy import create_engine, text

from app.config import configuracao
from app.dominios.empresas.modelos import Empresa
from app.dominios.fiscal import servico as fiscal
from app.nucleo import segredos
from etl.notas import importar_numeracao

CNPJ = "11222333000181"  # fictício, com dígitos válidos


def _pfx(cnpj: str, senha: str, dias: int = 365) -> bytes:
    """Um certificado A1 de mentira, como os da ICP-Brasil: o CNPJ vai no nome do titular."""
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"LOJA FICTICIA LTDA:{cnpj}")])
    agora = datetime.now()
    cert = (x509.CertificateBuilder().subject_name(nome).issuer_name(nome).public_key(chave.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(agora - timedelta(days=1))
            .not_valid_after(agora + timedelta(days=dias)).sign(chave, hashes.SHA256()))
    return pkcs12.serialize_key_and_certificates(b"piki", chave, cert, None, BestAvailableEncryption(senha.encode()))


@pytest.fixture
def config(monkeypatch, tmp_path):
    c = configuracao()
    monkeypatch.setattr(c, "chave_segredos", segredos.nova_chave())
    monkeypatch.setattr(c, "certificados_pasta", str(tmp_path / "certificados"))
    return c


@pytest.fixture
def admin(cliente, cenario, banco):
    with banco() as db:
        db.get(Empresa, cenario["e1"]).cnpj = CNPJ
        db.commit()
    r = cliente.post("/auth/login", json={"login": "caio", "senha": "senha-caio", "empresa_id": cenario["e1"]})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_segredos_cifrados(config, monkeypatch):
    cifrado = segredos.cifrar("token-do-csc")
    assert cifrado != "token-do-csc" and segredos.decifrar(cifrado) == "token-do-csc"
    monkeypatch.setattr(config, "chave_segredos", segredos.nova_chave())  # trocaram a chave do .env
    with pytest.raises(segredos.SemChave):
        segredos.decifrar(cifrado)


def test_certificado_e_csc_da_empresa(banco, cliente, cenario, admin, config, tmp_path):
    url = f"/empresas/{cenario['e1']}"
    arquivo = base64.b64encode(_pfx(CNPJ, "senha-certa")).decode()
    r = cliente.put(f"{url}/certificado", headers=admin, json={"arquivo": arquivo, "senha": "errada"})
    assert r.status_code == 422 and "confira o arquivo e a senha" in r.json()["detail"]
    outro = base64.b64encode(_pfx("99888777000166", "senha-certa")).decode()
    r = cliente.put(f"{url}/certificado", headers=admin, json={"arquivo": outro, "senha": "senha-certa"})
    assert r.status_code == 422 and "não é do CNPJ da empresa" in r.json()["detail"]

    r = cliente.put(f"{url}/certificado", headers=admin, json={"arquivo": arquivo, "senha": "senha-certa"})
    assert r.status_code == 200, r.text
    certificado = r.json()["certificado"]
    assert CNPJ in certificado["titular"] and 363 <= certificado["dias_para_vencer"] <= 365
    assert (tmp_path / "certificados" / f"01-{CNPJ}.pfx").exists()  # na pasta do servidor, não no banco
    with banco() as db:
        empresa = db.get(Empresa, cenario["e1"])
        assert empresa.certificado_senha != "senha-certa" and segredos.decifrar(empresa.certificado_senha) == "senha-certa"

    # o CSC: o token é cifrado e nunca volta
    r = cliente.put(f"{url}/fiscal", headers=admin, json={"ambiente": "2", "csc_id": "000001", "csc_token": "ABC123"})
    assert r.json() | {"certificado": None} == {"ambiente": "2", "certificado": None, "csc_id": "000001", "tem_csc": True}
    assert "ABC123" not in r.text
    r = cliente.put(f"{url}/fiscal", headers=admin, json={"ambiente": "1", "csc_id": "000001"})  # sem token: fica o mesmo
    assert (r.json()["ambiente"], r.json()["tem_csc"]) == ("1", True)
    with banco() as db:
        assert segredos.decifrar(db.get(Empresa, cenario["e1"]).csc_token) == "ABC123"


def test_sem_chave_no_env_nao_cadastra(cliente, cenario, admin, config, monkeypatch):
    monkeypatch.setattr(config, "chave_segredos", "")
    arquivo = base64.b64encode(_pfx(CNPJ, "senha")).decode()
    r = cliente.put(f"/empresas/{cenario['e1']}/certificado", headers=admin, json={"arquivo": arquivo, "senha": "senha"})
    assert r.status_code == 422 and "PIKI_CHAVE_SEGREDOS" in r.json()["detail"]


def test_serie_do_caixa_e_numeracao(banco, cliente, cenario, admin, tmp_path):
    cx2 = cliente.post("/caixas", headers=admin, json={"nome": "Cx 02", "serie_nfe": 102}).json()
    assert cx2["serie_nfe"] == 102
    r = cliente.post("/caixas", headers=admin, json={"nome": "Cx 03", "serie_nfe": 102})
    assert r.status_code == 409 and "já é do caixa Cx 02" in r.json()["detail"]

    # a numeração continua de onde o VB6 parou, e só sobe
    eng = create_engine(f"sqlite:///{tmp_path / 'vb6.db'}")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE nfe (modelo TEXT, serie TEXT, nNF INTEGER)"))
        c.execute(text("INSERT INTO nfe VALUES ('65', '102', 44535), ('65', '102', 44536), ('55', '102', 69), ('65', '0', 14)"))
    with eng.connect() as c, banco() as db:
        r = importar_numeracao(c, db, "01")
        assert sorted(r.series) == ["NF-e série 102: 69", "NFC-e série 102: 44536"]
        assert "série '0'" in r.avisos[0]
        assert fiscal.proximo_numero(db, cenario["e1"], "65", 102) == 44537
        assert fiscal.proximo_numero(db, cenario["e1"], "65", 103) == 1  # série nova
        db.commit()
        fiscal.continuar_de(db, cenario["e1"], "65", 102, 44536)  # reimportar não volta para trás
        assert fiscal.proximo_numero(db, cenario["e1"], "65", 102) == 44538
    eng.dispose()
