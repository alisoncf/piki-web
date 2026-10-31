"""Endereço pelo CEP, com o setor (bairro) adivinhado entre os setores da cidade."""
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominios.cidades import repositorio as cidades
from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.clientes.modelos import Setor
from app.dominios.enderecos import viacep
from app.nucleo.documentos import so_digitos

CepIndisponivel = viacep.CepIndisponivel


class CepInvalido(Exception):
    pass


class CepNaoEncontrado(Exception):
    pass


# abreviações comuns nos nomes dos setores (JD. GUANABARA, ST URIAS MAGALHAES)
_ABREVIACOES = {
    "jd": "jardim", "jard": "jardim", "vl": "vila", "st": "setor", "set": "setor", "res": "residencial",
    "resid": "residencial", "pq": "parque", "prq": "parque", "conj": "conjunto", "cj": "conjunto",
    "b": "bairro", "br": "bairro", "lot": "loteamento", "ch": "chacara", "chac": "chacara",
    "sta": "santa", "sto": "santo", "n": "nossa", "sra": "senhora", "dr": "doutor",
}
# palavras que só dizem o tipo do lugar: "Vila Jaiara" e "JAIARA" (tipo VILA) são o mesmo setor
_TIPOS = {"bairro", "vila", "jardim", "setor", "residencial", "parque", "conjunto", "loteamento", "chacara"}


def _palavras(texto: str | None) -> list[str]:
    return [_ABREVIACOES.get(p, p) for p in re.split(r"[^a-z0-9]+", nome_de_busca(texto)) if p]


def _sem_tipo(palavras: list[str]) -> list[str]:
    while palavras and palavras[0] in _TIPOS:
        palavras = palavras[1:]
    return palavras


def _nomes_do_setor(setor: Setor) -> set[str]:
    """O nome normalizado, também com o tipo na frente (tipo VILA + JAIARA = vila jaiara)."""
    nome = _palavras(setor.nome)
    nomes = {" ".join(nome)}
    tipo = _palavras(setor.tipo)
    if tipo and nome[: len(tipo)] != tipo:
        nomes.add(" ".join(tipo + nome))
    return nomes


def _contem(maior: list[str], menor: list[str]) -> bool:
    """`menor` aparece, palavra por palavra, dentro de `maior`."""
    n = len(menor)
    return any(maior[i:i + n] == menor for i in range(len(maior) - n + 1))


def setores_do_bairro(db: Session, bairro: str | None, cidade: Cidade) -> tuple[list[Setor], list[Setor]]:
    """Setores ativos da cidade iguais ao bairro e, à parte, os parecidos."""
    alvo = _palavras(bairro)
    if not alvo:
        return [], []
    nucleo = _sem_tipo(alvo) or alvo
    iguais: list[Setor] = []
    parecidos: list[Setor] = []
    setores = db.scalars(
        select(Setor).where(Setor.cidade_id == cidade.id, Setor.ativo.is_(True)).order_by(Setor.nome)
    )
    for setor in setores:
        if " ".join(alvo) in _nomes_do_setor(setor):
            iguais.append(setor)
            continue
        outro = _sem_tipo(_palavras(setor.nome)) or _palavras(setor.nome)
        # mesmo nome com outro tipo (Vila Jaiara x Jardim Jaiara) ou um nome dentro do outro
        # (Jundiaí x Jundiaí Industrial); nomes curtos demais pegariam qualquer coisa
        if outro == nucleo or (min(len(" ".join(outro)), len(" ".join(nucleo))) >= 4
                               and (_contem(outro, nucleo) or _contem(nucleo, outro))):
            parecidos.append(setor)
    return iguais, parecidos


def consultar_cep(db: Session, cep: str) -> dict:
    digitos = so_digitos(cep)
    if len(digitos) != 8:
        raise CepInvalido("O CEP tem 8 dígitos")
    dados = viacep.consultar(digitos)
    if dados is None:
        raise CepNaoEncontrado(f"CEP {digitos[:5]}-{digitos[5:]} não encontrado")
    cidade = cidades.cidade_por_codigo(db, dados.get("ibge") or "")
    bairro = (dados.get("bairro") or "").strip() or None
    iguais, parecidos = setores_do_bairro(db, bairro, cidade) if cidade else ([], [])
    # dois setores iguais (cadastro repetido): melhor a pessoa escolher
    unico = iguais[0] if len(iguais) == 1 else None
    return {
        "cep": digitos,
        "logradouro": (dados.get("logradouro") or "").strip() or None,
        "complemento": (dados.get("complemento") or "").strip() or None,
        "bairro": bairro,
        "cidade": cidade,
        "setor": unico,
        "sugestoes": ([] if unico else iguais) + parecidos[:10],
    }
