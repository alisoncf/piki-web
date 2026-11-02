"""Importa fornecedores, com telefones e contatos, de um banco de filial do VB6 (D22).

Cada filial tem a sua tab_fornecedores, com os mesmos fornecedores em códigos
diferentes. O fornecedor é cadastro único (D9), então:

1. um código já importado desta filial (legado_mapa) continua apontando para
   o mesmo fornecedor;
2. senão, procura pelo CPF/CNPJ;
3. senão, cria.

Sem CPF/CNPJ válido, ou com nome sem sentido, o fornecedor não entra; se já
tinha entrado por esta filial, sai (a não ser que tenha vindo também de outra).

A tab_fornecedores não tem data de alteração, então quem manda nos dados é a
filial de menor código entre as que têm o fornecedor (a matriz, quando ela o
tem). As outras só preenchem os campos vazios e acrescentam telefones e
contatos que faltam.

O contato do VB6 (contato_for) é texto livre, quase sempre nome e telefone
juntos ("EBSON 9971-0002"): vira um contato com nome e telefone. Quando não
há nome ("FAX 15-3284-5809"), o número vai para os telefones do fornecedor.
"""
import re
from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import Connection, delete, inspect, select, text
from sqlalchemy.orm import Session

from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.empresas.modelos import Empresa
from app.dominios.fornecedores.modelos import ContatoFornecedor, Fornecedor, TelefoneFornecedor
from app.nucleo.documentos import TIPOS_TELEFONE, cpf_cnpj_valido, so_digitos
from app.nucleo.legado import MapaLegado
from etl import mapa
from etl.clientes import nome_sem_sentido
from etl.funcionarios import EmpresaNaoImportada

# tipo_ter 'F' = telefone de fornecedor; o cod_cli é o cod_for
_TELEFONES = text("SELECT CAST(cod_cli AS CHAR) cod, CAST(num_tel AS CHAR) num, CAST(tipo_tel AS CHAR) tipo"
                  "  FROM tab_telefones WHERE tipo_ter = 'F'")
# palavras que, sozinhas no contato, não são nome de pessoa
_SEM_NOME = {"FAX", "FONE", "TEL", "TELEFONE", "CEL", "CELULAR", "WHATS", "WHATSAPP", "ZAP"}
_TELEFONE_COMERCIAL = "2"
_FAX = "5"


@dataclass
class Resultado:
    criados: int = 0
    atualizados: int = 0
    ligados_por_documento: int = 0
    descartados: int = 0
    excluidos: int = 0
    telefones: int = 0
    contatos: int = 0
    avisos: list[str] = field(default_factory=list)


def _texto(valor: object) -> str | None:
    if valor is None:
        return None
    v = " ".join(str(valor).split())
    return v or None


def _corta(valor: object, tamanho: int) -> str | None:
    v = _texto(valor)
    return v[:tamanho] if v else None


def telefone(valor: object) -> str | None:
    """Só os dígitos, sem o 0 da operadora na frente ("(0..19)3807-7511" → 1938077511); None se curto demais."""
    digitos = so_digitos(valor).lstrip("0")
    return digitos[:15] if len(digitos) >= 8 else None


def separar_contato(valor: object) -> tuple[str | None, str | None]:
    """'EBSON 9971-0002' → ('EBSON', '99710002'); 'FAX15-3284-5809' → (None, '1532845809')."""
    v = _texto(valor) or ""
    nome = _texto(re.sub(r"[\d()\-./:]+", " ", v))
    if nome and (nome.upper() in _SEM_NOME or len(nome) < 2):
        nome = None
    return nome, telefone(v)


def converter(linha: dict) -> dict:
    """Uma linha da tab_fornecedores → campos do fornecedor (sem cidade, telefones e contatos)."""
    email = _corta(linha.get("email_for"), 200)
    return {
        "nome": _corta(linha.get("nome_for"), 100),
        "nome_fantasia": _corta(linha.get("fantasia_for"), 60),
        "inscricao_estadual": so_digitos(linha.get("ie_for"))[:20] or None,
        "cep": so_digitos(linha.get("cep_for")) if len(so_digitos(linha.get("cep_for"))) == 8 else None,
        "logradouro": _corta(linha.get("endereco_for"), 60) or _corta(linha.get("logradouro_for"), 60),
        "bairro": _corta(linha.get("bairro_for"), 60),
        "email": email.lower() if email else None,
        "observacao": _texto(linha.get("obs_for")),
    }


def _ler(origem: Connection) -> list[dict]:
    """Colunas em minúsculas e valores como texto (zerofill e datas inválidas quebram o conector)."""
    colunas = [f"CAST({c['name']} AS CHAR) AS {c['name'].lower()}" for c in inspect(origem).get_columns("tab_fornecedores")]
    return [dict(r) for r in origem.execute(text(f"SELECT {', '.join(colunas)} FROM tab_fornecedores ORDER BY cod_for")).mappings()]


_ABREVIACOES = {"sta": "santa", "sto": "santo", "sao": "sao", "s": "sao"}


def _chave_cidade(nome: object) -> str:
    """Só as letras, com as abreviações comuns por extenso: "STA BARBARA DOESTE" e "Santa Bárbara d'Oeste" batem."""
    palavras = re.split(r"[^a-z0-9]+", nome_de_busca(str(nome or "")))
    return "".join(_ABREVIACOES.get(p, p) for p in palavras if p)


class _Cidades:
    """Cidades do IBGE pelo nome digitado no VB6: igual, ou o começo de uma só cidade da UF ("SAO BERNARDO DO CAMP")."""

    def __init__(self, db: Session) -> None:
        self.lista = [(_chave_cidade(c.nome), c.uf, c.id) for c in db.scalars(select(Cidade))]
        self.exatas = {(chave, uf): id_ for chave, uf, id_ in self.lista}

    def buscar(self, nome: object, uf: str) -> int | None:
        chave = _chave_cidade(nome)
        if not chave:
            return None
        if (chave, uf) in self.exatas:
            return self.exatas[(chave, uf)]
        parecidas = [id_ for c, u, id_ in self.lista if u == uf and len(chave) >= 6 and c.startswith(chave)]
        return parecidas[0] if len(parecidas) == 1 else None


def _excluir(db: Session, empresa: Empresa, codigo: str, fornecedor_id: int, r: Resultado) -> None:
    """O fornecedor descartado que já tinha vindo desta filial sai, se não veio também de outra."""
    db.execute(delete(MapaLegado).where(MapaLegado.tabela == "tab_fornecedores", MapaLegado.empresa_id == empresa.id,
                                        MapaLegado.codigo == codigo))
    de_outra = db.scalar(select(MapaLegado.novo_id).where(
        MapaLegado.tabela == "tab_fornecedores", MapaLegado.novo_id == fornecedor_id).limit(1))
    if de_outra is None and (fornecedor := db.get(Fornecedor, fornecedor_id)) is not None:
        db.delete(fornecedor)
        r.excluidos += 1
    db.flush()


def _dona(db: Session, fornecedor_id: int) -> str | None:
    """O menor código de filial entre as que já trouxeram este fornecedor."""
    return db.scalar(select(Empresa.codigo).join(MapaLegado, MapaLegado.empresa_id == Empresa.id).where(
        MapaLegado.tabela == "tab_fornecedores", MapaLegado.novo_id == fornecedor_id).order_by(Empresa.codigo).limit(1))


def importar_fornecedores(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()
    cidades = _Cidades(db)
    telefones_extras: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for t in origem.execute(_TELEFONES).mappings():
        if (numero := telefone(t["num"])) and (t["cod"] or "").strip().isdigit():
            tipo = t["tipo"] if t["tipo"] in TIPOS_TELEFONE else _TELEFONE_COMERCIAL
            telefones_extras[str(int(t["cod"]))].append((numero, tipo))

    for linha in _ler(origem):
        codigo = str(int(linha["cod_for"])) if (linha["cod_for"] or "").strip().isdigit() else _texto(linha["cod_for"])
        dados = converter(linha)
        documento = so_digitos(linha.get("cnpj_for"))
        ja_importado = mapa.buscar(db, "tab_fornecedores", empresa.id, codigo)
        motivo = ("nome sem sentido" if nome_sem_sentido(dados["nome"])
                  else None if len(documento) in (11, 14) and cpf_cnpj_valido(documento) else "sem CPF/CNPJ válido")
        if motivo:
            r.descartados += 1
            r.avisos.append(f"fornecedor {codigo} ({dados['nome']}): {motivo}, não importado")
            if ja_importado:
                _excluir(db, empresa, codigo, ja_importado, r)
            continue

        dados["cidade_id"] = cidades.buscar(linha.get("cidade_for"), (_texto(linha.get("uf_for")) or "").upper())
        if _texto(linha.get("cidade_for")) and not dados["cidade_id"]:
            r.avisos.append(f"fornecedor {codigo} ({dados['nome']}): cidade {_texto(linha.get('cidade_for'))}/"
                            f"{_texto(linha.get('uf_for'))} não encontrada no IBGE")

        telefones = [(n, _TELEFONE_COMERCIAL) for n in (telefone(linha.get("telefone_for")),) if n]
        telefones += [(n, _FAX) for n in (telefone(linha.get("fax_for")),) if n]
        telefones += telefones_extras.get(codigo, [])
        contatos = []
        nome_contato, fone_contato = separar_contato(linha.get("contato_for"))
        if nome_contato:
            contatos.append((nome_contato[:60], fone_contato))
        elif fone_contato:
            tipo = _FAX if "FAX" in (_texto(linha.get("contato_for")) or "").upper() else _TELEFONE_COMERCIAL
            telefones.append((fone_contato, tipo))

        fornecedor = db.get(Fornecedor, ja_importado) if ja_importado else None
        if fornecedor is None:
            fornecedor = db.scalar(select(Fornecedor).where(Fornecedor.cpf_cnpj == documento))
            if fornecedor is not None:
                r.ligados_por_documento += 1
        else:
            r.atualizados += 1
        if fornecedor is None:
            fornecedor = Fornecedor(cpf_cnpj=documento, **{k: v for k, v in dados.items()})
            db.add(fornecedor)
            r.criados += 1
        else:
            dona = _dona(db, fornecedor.id)
            completo = dona is None or empresa.codigo <= dona
            for campo, valor in dados.items():
                if valor is not None and (completo or getattr(fornecedor, campo) in (None, "")):
                    setattr(fornecedor, campo, valor)

        numeros = {t.numero for t in fornecedor.telefones}
        for numero, tipo in telefones:
            if numero not in numeros:
                fornecedor.telefones.append(TelefoneFornecedor(numero=numero, tipo=tipo))
                numeros.add(numero)
                r.telefones += 1
        nomes = {c.nome.upper() for c in fornecedor.contatos}
        for nome, fone in contatos:
            if nome.upper() not in nomes:
                fornecedor.contatos.append(ContatoFornecedor(nome=nome, telefone=fone))
                nomes.add(nome.upper())
                r.contatos += 1
        db.flush()
        mapa.gravar(db, "tab_fornecedores", empresa.id, codigo, fornecedor.id)

    db.commit()
    return r
