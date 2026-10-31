"""Importa cargos, funcionários e seus telefones de um banco de filial do VB6.

O cod_fun e o cod_car eram gerados com max()+1 em cada filial, então o mesmo
código aparece em filiais diferentes para pessoas diferentes. Por isso:

- cada código antigo é ligado ao registro novo pelo legado_mapa (tabela +
  empresa de origem + código), o que torna a importação repetível;
- um cargo que não está no mapa é procurado pelo nome.

A maior parte dos funcionários está cadastrada em mais de uma filial (e às
vezes duas vezes na mesma). Um funcionário que não está no mapa é procurado:

1. pelo CPF, desde que os nomes sejam compatíveis: há cadastros que não são
   de pessoas ("ESCRITORIO", nome de shopping) com o CPF do dono;
2. sem CPF que o identifique, pelo nome completo, entre os que vieram de
   outra filial;
3. se não achar, é criado, com a loja de origem como lotação.

Quem manda nos dados de uma pessoa cadastrada em várias filiais é a loja de
lotação (ou, se ela não tem o cadastro, a primeira filial importada). As
outras só preenchem o que está vazio e acrescentam telefones. A exceção é a
pessoa inativa na lotação e ativa em outra filial: ela passa para essa filial.

Na reimportação, os dados do VB6 (que segue oficial até a virada, D8)
atualizam o cadastro, menos a loja de lotação, que é do sistema novo.
"""
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Connection, func, select, text
from sqlalchemy.orm import Session

from app.dominios.acesso.modelos import Empresa
from app.dominios.funcionarios.modelos import Cargo, Funcionario, TelefoneFuncionario
from app.nucleo.documentos import TIPOS_TELEFONE, cpf_valido, so_digitos
from app.nucleo.legado import MapaLegado
from etl import mapa

# apelidos explícitos: o VB6 mistura maiúsculas nos nomes das colunas (COD_CAR, cod_Car...)
_CARGOS = text(
    "SELECT COD_CAR AS cod_car, NOME_CAR AS nome_car, venda_Car AS venda_car, cobranca_car AS cobranca_car"
    "  FROM tab_cargos"
)
_FUNCIONARIOS = text(
    """
    SELECT cod_fun, nome_fun, guerra_fun, endereco_fun, bairro_fun, cidade_fun, uf_fun, cep_fun, nasc_fun,
           natural_fun, rg_fun, cpf_fun, sexo_fun, conjuge_fun, pai_fun, mae_fun, endpais_fun, datacad_fun,
           obs_fun, status_fun, cod_Car AS cod_car, limite_fun, vale_fun
      FROM tab_funcionarios
     ORDER BY cod_fun
    """
)
# tipo_ter 'U' = telefone de funcionário (o 'C' é de cliente)
_TELEFONES = text("SELECT cod_cli, num_tel, tipo_tel FROM tab_telefones WHERE tipo_ter = 'U'")


class EmpresaNaoImportada(Exception):
    """A empresa de origem ainda não existe no banco novo."""


@dataclass
class Resultado:
    cargos_criados: int = 0
    criados: int = 0
    atualizados: int = 0
    ligados_por_cpf: int = 0
    ligados_por_nome: int = 0
    mudaram_de_loja: int = 0
    telefones: int = 0
    avisos: list[str] = field(default_factory=list)


def _texto(valor: object) -> str | None:
    if valor is None:
        return None
    v = str(valor).strip()
    return v or None


def _data(valor: object) -> date | None:
    """Datas do VB6 vêm como date, string ou '0000-00-00'."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    v = _texto(valor)
    if not v or v.startswith("0000"):
        return None
    try:
        return date.fromisoformat(v[:10])
    except ValueError:
        return None


def converter(linha: dict) -> dict:
    """Uma linha da tab_funcionarios → campos do funcionário (sem loja, cargo e CPF, tratados à parte)."""
    sexo = (_texto(linha.get("sexo_fun")) or "").upper()
    return {
        "nome": _texto(linha.get("nome_fun")),
        "apelido": _texto(linha.get("guerra_fun")),
        "rg": _texto(linha.get("rg_fun")),
        "data_nascimento": _data(linha.get("nasc_fun")),
        "sexo": sexo if sexo in ("M", "F") else None,
        "naturalidade": _texto(linha.get("natural_fun")),
        "ativo": _texto(linha.get("status_fun")) == "1",
        "pode_tirar_vale": (_texto(linha.get("vale_fun")) or "S").upper() == "S",
        "limite_vale": Decimal(str(linha.get("limite_fun") or 0)).quantize(Decimal("0.01")),
        "cep": so_digitos(linha.get("cep_fun"))[:8] or None,
        "logradouro": _texto(linha.get("endereco_fun")),
        "conjuge": _texto(linha.get("conjuge_fun")),
        "pai": _texto(linha.get("pai_fun")),
        "mae": _texto(linha.get("mae_fun")),
        "endereco_pais": _texto(linha.get("endpais_fun")),
        "observacao": _texto(linha.get("obs_fun")),
    }


def _tipo_telefone(tipo: object, numero: str) -> str:
    t = _texto(tipo)
    if t in TIPOS_TELEFONE:
        return t
    return "3" if len(numero) == 11 else "1"


def _importar_cargos(origem: Connection, db: Session, empresa: Empresa, r: Resultado) -> None:
    for linha in origem.execute(_CARGOS).mappings():
        codigo, nome = _texto(linha["cod_car"]), _texto(linha["nome_car"])
        if not codigo or not nome:
            continue
        vende = (_texto(linha["venda_car"]) or "").upper() == "S"
        cobra = (_texto(linha["cobranca_car"]) or "").upper() == "S"
        cargo_id = mapa.buscar(db, "tab_cargos", empresa.id, codigo)
        if cargo_id is not None:
            cargo = db.get(Cargo, cargo_id)
            cargo.vende, cargo.cobra = vende, cobra
            continue
        cargo = db.scalar(select(Cargo).where(func.lower(Cargo.nome) == nome.lower()))
        if cargo is None:
            cargo = Cargo(nome=nome[:40], vende=vende, cobra=cobra)
            db.add(cargo)
            db.flush()
            r.cargos_criados += 1
        mapa.gravar(db, "tab_cargos", empresa.id, codigo, cargo.id)


def _cpf(linha: dict, r: Resultado) -> str | None:
    bruto = _texto(linha.get("cpf_fun"))
    cpf = so_digitos(bruto)
    if cpf and cpf_valido(cpf):
        return cpf
    if bruto:
        r.avisos.append(f"funcionário {linha['cod_fun']} ({_texto(linha.get('nome_fun'))}): CPF inválido ignorado: {bruto}")
    return None


def nome_comparavel(nome: str | None) -> str:
    """Maiúsculas, sem acentos e sem espaços repetidos."""
    sem_acento = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode()
    return " ".join(sem_acento.upper().split())


_LIGACOES = {"DE", "DA", "DO", "DAS", "DOS", "E"}


def nomes_compativeis(a: str | None, b: str | None) -> bool:
    """Se dois nomes com o mesmo CPF podem ser da mesma pessoa.

    Aceita nomes incompletos ou abreviados ("ANA" e "ANA PAULA SOUZA", "ANAS"
    e "ANA S LIMA") e um nome a mais na frente ("MARIA ANA SOUZA LIMA" e
    "ANA SOUZA LIMA").
    """
    pa, pb = nome_comparavel(a).split(), nome_comparavel(b).split()
    if not pa or not pb:
        return False
    if pa[0].startswith(pb[0]) or pb[0].startswith(pa[0]):
        return True
    return len((set(pa) & set(pb)) - _LIGACOES) >= 2


class _Indice:
    """Funcionários já gravados, por CPF e por nome, para achar a mesma pessoa vinda de outra filial."""

    def __init__(self, db: Session, empresa_id: int):
        self.por_cpf: dict[str, Funcionario] = {}
        self.por_nome: dict[str, list[Funcionario]] = defaultdict(list)
        for f in db.scalars(select(Funcionario)):
            self.incluir(f)
        # já ligados a um código desta filial: outro código com o mesmo nome é outra pessoa
        self.desta_filial = set(db.scalars(select(MapaLegado.novo_id).where(
            MapaLegado.tabela == "tab_funcionarios", MapaLegado.empresa_id == empresa_id)))

    def incluir(self, f: Funcionario) -> None:
        if f.cpf:
            self.por_cpf[f.cpf] = f
        self.por_nome[nome_comparavel(f.nome)].append(f)

    def procurar(self, codigo: str, nome: str, cpf: str | None, r: Resultado) -> tuple[Funcionario | None, str | None]:
        """Devolve o funcionário (ou None) e o CPF a usar, que vira None se já for de outra pessoa."""
        if cpf and (dono := self.por_cpf.get(cpf)):
            if nomes_compativeis(dono.nome, nome):
                if nome_comparavel(dono.nome) != nome_comparavel(nome):
                    r.avisos.append(f"funcionário {codigo} ({nome}): ligado pelo CPF a {dono.nome}")
                r.ligados_por_cpf += 1
                return dono, cpf
            r.avisos.append(f"funcionário {codigo} ({nome}): o CPF {cpf} já é de {dono.nome}; cadastrado à parte, sem CPF")
            cpf = None
        mesmo_nome = [f for f in self.por_nome[nome_comparavel(nome)] if f.id not in self.desta_filial]
        candidatos = [f for f in mesmo_nome if not cpf or not f.cpf or f.cpf == cpf]
        if len(candidatos) == 1:
            r.ligados_por_nome += 1
            return candidatos[0], cpf
        if mesmo_nome:
            r.avisos.append(f"funcionário {codigo} ({nome}): há outro cadastro com o mesmo nome e outro CPF; "
                            "cadastrado à parte")
        return None, cpf


def _manda_nos_dados(db: Session, funcionario: Funcionario, empresa_id: int) -> bool:
    """A lotação manda; se ela não tem o cadastro no VB6, manda a filial de menor id."""
    if funcionario.empresa_id == empresa_id:
        return True
    origens = db.scalars(select(MapaLegado.empresa_id).where(
        MapaLegado.tabela == "tab_funcionarios", MapaLegado.novo_id == funcionario.id)).all()
    return funcionario.empresa_id not in origens and empresa_id == min(origens)


def _aplicar(funcionario: Funcionario, dados: dict, completo: bool) -> None:
    """Completo: os dados desta filial substituem os atuais. Senão, só preenchem o que está vazio."""
    for campo, valor in dados.items():
        if completo or (getattr(funcionario, campo) in (None, "") and valor not in (None, "")):
            setattr(funcionario, campo, valor)


def _aplicar_cpf(indice: _Indice, funcionario: Funcionario, cpf: str | None, codigo: str,
                 completo: bool, r: Resultado) -> None:
    if not cpf or cpf == funcionario.cpf or (funcionario.cpf and not completo):
        return
    dono = indice.por_cpf.get(cpf)
    if dono is None:
        funcionario.cpf = cpf
        indice.por_cpf[cpf] = funcionario
    else:
        r.avisos.append(f"funcionário {codigo} ({funcionario.nome}): CPF {cpf} já é de {dono.nome}; mantido o anterior")


def importar_funcionarios(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    """Lê cargos, funcionários e telefones de um banco do VB6 e grava no banco novo."""
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")

    r = Resultado()
    _importar_cargos(origem, db, empresa, r)

    telefones: dict[int, list[tuple[str, object]]] = {}
    for t in origem.execute(_TELEFONES).mappings():
        numero = so_digitos(t["num_tel"])
        if len(numero) >= 8 and str(t["cod_cli"]).strip().isdigit():
            telefones.setdefault(int(t["cod_cli"]), []).append((numero[:15], t["tipo_tel"]))

    indice = _Indice(db, empresa.id)
    vistos: set[int] = set()  # já gravados nesta importação: a mesma pessoa com dois códigos na filial
    for linha in origem.execute(_FUNCIONARIOS).mappings():
        linha = dict(linha)
        codigo = _texto(linha["cod_fun"])
        dados = converter(linha)
        if not codigo or not dados["nome"]:
            r.avisos.append(f"funcionário {codigo!r} sem nome: ignorado")
            continue
        cpf = _cpf(linha, r)
        codigo_cargo = _texto(linha.get("cod_car"))
        dados["cargo_id"] = mapa.buscar(db, "tab_cargos", empresa.id, codigo_cargo) if codigo_cargo else None

        funcionario_id = mapa.buscar(db, "tab_funcionarios", empresa.id, codigo)
        if funcionario_id is not None:
            funcionario = db.get(Funcionario, funcionario_id)
            r.atualizados += 1
        else:
            funcionario, cpf = indice.procurar(codigo, dados["nome"], cpf, r)
            if funcionario is None:
                funcionario = Funcionario(**dados, cpf=cpf, empresa_id=empresa.id)
                if criado := _data(linha.get("datacad_fun")):
                    funcionario.criado_em = datetime.combine(criado, datetime.min.time())
                db.add(funcionario)
                db.flush()
                indice.incluir(funcionario)
                vistos.add(funcionario.id)
                r.criados += 1
            mapa.gravar(db, "tab_funcionarios", empresa.id, codigo, funcionario.id)
            indice.desta_filial.add(funcionario.id)

        completo = funcionario.id not in vistos and _manda_nos_dados(db, funcionario, empresa.id)
        if not completo and dados["ativo"] and not funcionario.ativo:
            # inativo onde estava e ativo aqui: a pessoa trabalha nesta loja
            if funcionario.empresa_id != empresa.id:
                funcionario.empresa_id = empresa.id
                r.mudaram_de_loja += 1
            completo = True
        _aplicar(funcionario, dados, completo)
        _aplicar_cpf(indice, funcionario, cpf, codigo, completo, r)
        vistos.add(funcionario.id)

        existentes = {t.numero for t in funcionario.telefones}
        for numero, tipo in telefones.get(int(codigo), []) if codigo.isdigit() else []:
            if numero not in existentes:
                funcionario.telefones.append(TelefoneFuncionario(numero=numero, tipo=_tipo_telefone(tipo, numero)))
                existentes.add(numero)
                r.telefones += 1

    db.commit()
    return r
