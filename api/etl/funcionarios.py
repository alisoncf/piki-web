"""Importa cargos, funcionários e seus telefones de um banco de filial do VB6.

O cod_fun e o cod_car eram gerados com max()+1 em cada filial, então o mesmo
código aparece em filiais diferentes para pessoas diferentes. Por isso:

- cada código antigo é ligado ao registro novo pelo legado_mapa (tabela +
  empresa de origem + código), o que torna a importação repetível;
- um funcionário que não está no mapa é procurado pelo CPF, porque a mesma
  pessoa pode estar cadastrada em mais de uma filial; se não houver, é criado
  com a loja de origem como lotação;
- um cargo que não está no mapa é procurado pelo nome.

Na reimportação, os dados do VB6 (que segue oficial até a virada, D8)
atualizam o cadastro, menos a loja de lotação, que é do sistema novo.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Connection, func, select, text
from sqlalchemy.orm import Session

from app.dominios.acesso.modelos import Empresa
from app.dominios.funcionarios.modelos import Cargo, Funcionario, TelefoneFuncionario
from app.nucleo.documentos import TIPOS_TELEFONE, cpf_valido, so_digitos
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
    uf = (_texto(linha.get("uf_fun")) or "").upper()
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
        "bairro": _texto(linha.get("bairro_fun")),
        "cidade": _texto(linha.get("cidade_fun")),
        "uf": uf if len(uf) == 2 else None,
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
            for campo, valor in dados.items():
                setattr(funcionario, campo, valor)
            if cpf and cpf != funcionario.cpf:
                dono = db.scalar(select(Funcionario).where(Funcionario.cpf == cpf))
                if dono is None:
                    funcionario.cpf = cpf
                else:
                    r.avisos.append(f"funcionário {codigo} ({dados['nome']}): CPF {cpf} já é de {dono.nome}; mantido o anterior")
            r.atualizados += 1
        else:
            funcionario = db.scalar(select(Funcionario).where(Funcionario.cpf == cpf)) if cpf else None
            if funcionario is not None:
                # a mesma pessoa já veio de outra filial: só liga o código, sem sobrescrever
                r.ligados_por_cpf += 1
            else:
                funcionario = Funcionario(**dados, cpf=cpf, empresa_id=empresa.id)
                if criado := _data(linha.get("datacad_fun")):
                    funcionario.criado_em = datetime.combine(criado, datetime.min.time())
                db.add(funcionario)
                db.flush()
                r.criados += 1
            mapa.gravar(db, "tab_funcionarios", empresa.id, codigo, funcionario.id)

        existentes = {t.numero for t in funcionario.telefones}
        for numero, tipo in telefones.get(int(codigo), []) if codigo.isdigit() else []:
            if numero not in existentes:
                funcionario.telefones.append(TelefoneFuncionario(numero=numero, tipo=_tipo_telefone(tipo, numero)))
                existentes.add(numero)
                r.telefones += 1

    db.commit()
    return r
