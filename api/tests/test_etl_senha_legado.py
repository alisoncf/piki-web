from app.nucleo.seguranca import conferir_hash
from etl import senha_legado as senha


def test_formato_do_vb6():
    # F_GeraPW: cada caractere sobe 1 + posição. "abc" -> c(+2) e(+3) g(+4)
    assert senha.codificar("abc") == "ceg"
    assert senha.decodificar("ceg") == "abc"


def test_ida_e_volta():
    for s in ["1234", "SENHA", "maria2018", "A'B[C]"]:
        assert senha.decodificar(senha.codificar(s)) == s


def test_conferir_ignora_maiusculas():
    armazenada = senha.codificar("SEGREDO")
    assert senha.conferir("segredo", armazenada)
    assert senha.conferir("SeGrEdO", armazenada)
    assert not senha.conferir("outra", armazenada)


def test_conferir_aplica_trocas_do_ajusta_texto():
    # o VB6 troca ' por ` antes de comparar, então a senha gravada já tem a crase
    assert senha.conferir("d'agua", senha.codificar("D`AGUA"))


def test_conferir_sem_senha_gravada():
    assert not senha.conferir("qualquer", None)
    assert not senha.conferir("qualquer", "")


def test_hash_importado_aceita_a_senha_como_no_vb6():
    h = senha.hash_para_importar(senha.codificar("SEGREDO"))
    assert h.startswith("$argon2")
    assert conferir_hash("segredo", h, sem_caixa=True)
    assert conferir_hash("SEGREDO", h, sem_caixa=True)
    assert not conferir_hash("outra", h, sem_caixa=True)


def test_hash_importado_sem_senha():
    assert senha.hash_para_importar(None) is None
    assert senha.hash_para_importar("   ") is None
