from app.legado import senha


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
    armazenada = senha.codificar("D`AGUA")
    assert senha.conferir("d'agua", armazenada)


def test_conferir_sem_senha_gravada():
    assert not senha.conferir("qualquer", None)
    assert not senha.conferir("qualquer", "")
