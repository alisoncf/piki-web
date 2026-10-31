"""Importa clientes, setores, órgãos e grupos de clientes de um banco de filial do VB6 (D15).

Cada filial criava os seus setores, órgãos e grupos, e os mesmos códigos
significam coisas diferentes em cada banco. Aqui eles viram uma lista só:

- grupos e órgãos são juntados pelo nome (sem acentos, sem diferenciar
  maiúsculas); setores, pelo nome e pela cidade;
- a cidade do setor é a do IBGE: o cod_mun da tab_cidades da loja ou, sem
  ele, o mesmo nome e UF na lista do IBGE (tabela cidade, da migração 0008),
  ou a única cidade da UF cujo nome começa assim ("CORUMBA" → Corumbá de Goiás);
- o cobrador do setor (cobrador_set) é o código de um funcionário da loja; ele
  é somado aos cobradores que o setor já tem, que valem para todas as lojas
  (D17). Rode antes: python -m etl funcionarios;
- o cliente não tem cidade: ela é a do setor.

O cliente é um só para todas as lojas (D9):

1. um código já importado desta filial (legado_mapa) continua apontando para
   o mesmo cliente;
2. senão, procura pelo CPF/CNPJ válido;
3. senão, cria. Sem documento válido não há como saber se é a mesma pessoa de
   outra loja, então o cliente fica como cadastro próprio desta filial.

Quem manda nos dados é o registro com a data de alteração mais recente
(dataalt_cli, ou data_cli se estiver vazia). Os outros só preenchem os campos
vazios. Telefones, referências e anotações de todas as lojas são somados.
A data de cadastro e a loja do cadastro são as do registro mais antigo.

As colunas da tab_clientes não são iguais em todas as filiais
(Logradouro_cli ou logradouro_cli, telefones só em algumas), por isso a
leitura usa as colunas que existirem.
"""
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Connection, inspect, select, text
from sqlalchemy.orm import Session, selectinload

from app.dominios.acesso.modelos import Empresa
from app.dominios.clientes.modelos import (
    AnotacaoCliente, Cliente, GrupoCliente, Orgao, Parentesco, ReferenciaCliente, Setor, TelefoneCliente,
)
from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.funcionarios.modelos import Funcionario
from app.nucleo.documentos import cpf_cnpj_valido, so_digitos
from app.nucleo.legado import MapaLegado
from etl import mapa
from etl.funcionarios import EmpresaNaoImportada, _data, _texto, _tipo_telefone, nome_comparavel

_LOTE = 1000

# cod_cli é int zerofill no VB6, e o conector da MariaDB quebra ao converter alguns valores: lido como texto.
# tipo_ter 'C' = telefone de cliente
_TELEFONES = text(
    "SELECT CAST(cod_cli AS CHAR) AS cod_cli, num_tel, tipo_tel FROM tab_telefones WHERE tipo_ter = 'C'"
)
_REFERENCIAS = text(
    "SELECT CAST(cod_cli AS CHAR) AS cod_cli, nome_ref, tel_ref, cod_tip FROM tab_referencias ORDER BY cod_cli, seq_ref"
)
_ANOTACOES = text(
    "SELECT id, CAST(cod_cli AS CHAR) AS cod_cli, anotacao, CAST(datahora AS CHAR) AS datahora, excluido"
    "  FROM tab_clientesanot ORDER BY id"
)
_GRUPOS = text("SELECT cod_gru, nome_gru FROM tab_grupocli")
_PARENTESCOS = text("SELECT CAST(cod_tip AS CHAR), nome_tip FROM tab_tipopar")
_SETORES = text("SELECT cod_set, nome_set, cobrador_set, cod_cid, tipo_set FROM tab_setores")

@dataclass
class Resultado:
    grupos_criados: int = 0
    parentescos_criados: int = 0
    setores_criados: int = 0
    setores_sem_cidade: int = 0
    orgaos_criados: int = 0
    cobradores: int = 0  # ligações setor-cobrador novas
    criados: int = 0
    atualizados: int = 0
    ligados_por_documento: int = 0
    sem_documento: int = 0
    telefones: int = 0
    referencias: int = 0
    anotacoes: int = 0
    avisos: list[str] = field(default_factory=list)


def _codigo(valor: object) -> str | None:
    """Códigos vazios ou só de zeros ('000', '00000') querem dizer 'nenhum'."""
    v = _texto(valor)
    return None if not v or not v.strip("0") else v


def _int(valor: object) -> int | None:
    v = _texto(valor)
    return int(v) if v and v.isdigit() else None


def _corta(valor: object, tamanho: int) -> str | None:
    v = _texto(valor)
    return v[:tamanho] if v else None


def _digitos(valor: object, tamanho: int) -> str | None:
    return so_digitos(valor)[:tamanho] or None


# cadastros de apoio

def _importar_lista(origem: Connection, db: Session, empresa: Empresa, consulta, modelo: type,
                    tabela: str, tamanho: int) -> int:
    """Grupos e parentescos: código e nome, juntados pelo nome. Devolve quantos foram criados."""
    por_nome = {nome_comparavel(item.nome): item for item in db.scalars(select(modelo))}
    criados = 0
    for codigo, nome in origem.execute(consulta).all():
        codigo, nome = _texto(codigo), _corta(nome, tamanho)
        if codigo is None or not nome or mapa.buscar(db, tabela, empresa.id, codigo):
            continue
        item = por_nome.get(nome_comparavel(nome))
        if item is None:
            item = modelo(nome=nome)
            db.add(item)
            db.flush()
            por_nome[nome_comparavel(nome)] = item
            criados += 1
        mapa.gravar(db, tabela, empresa.id, codigo, item.id)
    return criados


def _cidades_da_loja(origem: Connection, db: Session, r: Resultado) -> dict[str, int]:
    """cod_cid da tab_cidades da loja → id da cidade do IBGE. As que não forem achadas viram aviso."""
    ibge = {c.codigo_ibge: c.id for c in db.scalars(select(Cidade))}
    if not ibge:
        r.avisos.append("a lista de cidades do IBGE está vazia (rode alembic upgrade head): setores ficam sem cidade")
        return {}
    lista = [(c.nome_busca, c.uf, c.id) for c in db.scalars(select(Cidade))]
    por_nome = {(nome, uf): id_ for nome, uf, id_ in lista}

    def pelo_nome(nome: str, uf: str) -> int | None:
        # o nome exato; ou o começo do nome, se só uma cidade da UF começar assim ("CORUMBA" → Corumbá de Goiás)
        if not nome:
            return None
        if (nome, uf) in por_nome:
            return por_nome[(nome, uf)]
        parecidas = [id_ for n, u, id_ in lista if u == uf and n.startswith(nome + " ")]
        return parecidas[0] if len(parecidas) == 1 else None

    cidades = {}
    for linha in _ler(origem, "tab_cidades"):
        codigo = _texto(linha["cod_cid"])
        cidade_id = ibge.get(so_digitos(linha.get("cod_mun"))) or pelo_nome(
            nome_de_busca(linha.get("nome_cid")), (_texto(linha.get("uf_cid")) or "").upper())
        if codigo and cidade_id:
            cidades[codigo] = cidade_id
        elif codigo:
            r.avisos.append(f"cidade {codigo} ({_texto(linha.get('nome_cid'))}/{_texto(linha.get('uf_cid'))}) "
                            "não encontrada no IBGE: os setores dela ficam sem cidade")
    return cidades


def _importar_setores(origem: Connection, db: Session, empresa: Empresa, r: Resultado) -> None:
    cidades = _cidades_da_loja(origem, db, r)
    chave = lambda nome, cidade_id: (nome_comparavel(nome), cidade_id)  # noqa: E731
    por_nome = {chave(s.nome, s.cidade_id): s for s in db.scalars(select(Setor))}
    for linha in origem.execute(_SETORES).mappings():
        codigo, nome = _texto(linha["cod_set"]), _corta(linha["nome_set"], 40)
        if not codigo or not nome:
            continue
        cidade_id = cidades.get(_texto(linha["cod_cid"]) or "")
        setor_id = mapa.buscar(db, "tab_setores", empresa.id, codigo)
        if setor_id is not None:
            setor = db.get(Setor, setor_id)
            # importado antes de as cidades existirem: ganha a cidade, se o nome ainda estiver livre nela
            if setor.cidade_id is None and cidade_id and chave(nome, cidade_id) not in por_nome:
                setor.cidade_id = cidade_id
                por_nome[chave(nome, cidade_id)] = setor
        else:
            setor = por_nome.get(chave(nome, cidade_id))
            if setor is None:
                setor = Setor(nome=nome, cidade_id=cidade_id, tipo=_corta(linha["tipo_set"], 20))
                db.add(setor)
                db.flush()
                por_nome[chave(nome, cidade_id)] = setor
                r.setores_criados += 1
            mapa.gravar(db, "tab_setores", empresa.id, codigo, setor.id)
        if setor.cidade_id is None:
            r.setores_sem_cidade += 1

        codigo_cobrador = _codigo(linha["cobrador_set"])
        if not codigo_cobrador:
            continue
        cobrador_id = mapa.buscar(db, "tab_funcionarios", empresa.id, codigo_cobrador)
        if cobrador_id is None:
            r.avisos.append(f"setor {codigo} ({nome}): cobrador {codigo_cobrador} não encontrado entre os funcionários")
            continue
        if all(c.id != cobrador_id for c in setor.cobradores):
            setor.cobradores.append(db.get(Funcionario, cobrador_id))
            r.cobradores += 1
    db.flush()


def _importar_orgaos(origem: Connection, db: Session, empresa: Empresa, r: Resultado) -> None:
    por_nome = {nome_comparavel(o.nome): o for o in db.scalars(select(Orgao))}
    for linha in _ler(origem, "tab_orgaos"):
        codigo, nome = _texto(linha["cod_org"]), _corta(linha["nome_org"], 60)
        if not codigo or not nome:
            continue
        dados = {
            "grupo_id": _mapeado(db, "tab_grupocli", empresa.id, linha["cod_gru"]),
            "setor_id": _mapeado(db, "tab_setores", empresa.id, linha["cod_set"]),
            "endereco": _corta(linha["endereco_org"], 60),
            "cep": _digitos(linha["cep_org"], 8),
            "telefone": _digitos(linha["fone_org"], 15),
            "observacao": _texto(linha.get("obs")),
        }
        orgao_id = mapa.buscar(db, "tab_orgaos", empresa.id, codigo)
        orgao = db.get(Orgao, orgao_id) if orgao_id is not None else por_nome.get(nome_comparavel(nome))
        if orgao is None:
            orgao = Orgao(nome=nome, **dados)
            db.add(orgao)
            db.flush()
            por_nome[nome_comparavel(nome)] = orgao
            r.orgaos_criados += 1
        else:
            for campo, valor in dados.items():
                if getattr(orgao, campo) in (None, "") and valor is not None:
                    setattr(orgao, campo, valor)
        if orgao_id is None:
            mapa.gravar(db, "tab_orgaos", empresa.id, codigo, orgao.id)


def _mapeado(db: Session, tabela: str, empresa_id: int, codigo: object) -> int | None:
    codigo = _codigo(codigo)
    return mapa.buscar(db, tabela, empresa_id, codigo) if codigo else None


# clientes

def _ler(origem: Connection, tabela: str, ordem: str | None = None) -> Iterator[dict]:
    """Todas as colunas da tabela, com nomes em minúsculas e valores como texto.

    As colunas não são iguais em todas as filiais (Logradouro_cli ou
    logradouro_cli, Obs só em algumas), então a leitura usa as que existirem;
    quem lê usa .get(). Datas inválidas do MySQL (dia 31 de fevereiro) e
    inteiros zerofill quebram a conversão do conector da MariaDB, por isso
    tudo vem como texto e é convertido aqui (_data, Decimal...).
    """
    colunas = [f"CAST({c['name']} AS CHAR) AS {c['name'].lower()}" for c in inspect(origem).get_columns(tabela)]
    sql = f"SELECT {', '.join(colunas)} FROM {tabela}" + (f" ORDER BY {ordem}" if ordem else "")
    for linha in origem.execute(text(sql)).mappings():
        yield dict(linha)


def _documento(linha: dict, r: Resultado) -> str | None:
    bruto = _texto(linha.get("cpf_cli"))
    doc = so_digitos(bruto)
    if len(doc) in (11, 14) and cpf_cnpj_valido(doc):
        return doc
    if bruto and doc.strip("0"):
        r.avisos.append(f"cliente {linha['cod_cli']} ({_texto(linha.get('nome_cli'))}): "
                        f"CPF/CNPJ inválido ignorado: {bruto}")
    return None


# cobranca_cli do VB6 → FORMAS_COBRANCA
_COBRANCA = {"1": "domicilio", "2": "trabalho", "3": "loja"}


def converter(linha: dict) -> dict:
    """Uma linha da tab_clientes → campos do cliente (sem documento, setores, órgão e grupo, tratados à parte)."""
    sexo = (_texto(linha.get("sexo_cli")) or "").upper()
    sim = lambda campo: (_texto(linha.get(campo)) or "").upper() == "S"  # noqa: E731
    # o endereço certo é o logradouro; endereco_cli é o campo antigo, usado só quando os outros estão vazios
    if _texto(linha.get("logradouro")):
        endereco = (linha.get("logradouro"), linha.get("numero"), linha.get("complemento"))
    elif _texto(linha.get("logradouro_cli")):
        endereco = (linha.get("logradouro_cli"), linha.get("numero_cli"), linha.get("complemento_cli"))
    else:
        endereco = (linha.get("endereco_cli"), linha.get("numero_cli") or linha.get("numero"),
                    linha.get("complemento_cli") or linha.get("complemento"))
    return {
        "nome": _corta(linha.get("nome_cli"), 60),
        "rg": _corta(linha.get("rg_cli"), 20),
        "inscricao_estadual": _corta(linha.get("ie_cli"), 20),
        "data_nascimento": _data(linha.get("datanasc_cli")),
        "sexo": sexo if sexo in ("M", "F") else None,
        "pai": _corta(linha.get("pai_cli"), 60),
        "mae": _corta(linha.get("mae_cli"), 60),
        "email": _corta(linha.get("email_cli"), 100),
        "cep": _digitos(linha.get("cep_cli"), 8),
        "logradouro": _corta(endereco[0], 100),
        "numero": _corta(endereco[1], 20),
        "complemento": _corta(endereco[2], 60),
        "bairro": _corta(linha.get("bairro_cli"), 40),
        "ponto_referencia": _corta(linha.get("referencia_cli"), 60),
        "local_trabalho": _corta(linha.get("localtrab_cli"), 60),
        "endereco_trabalho": _corta(linha.get("endtrab_cli") or linha.get("endcom_cli"), 60),
        "telefone_trabalho": _digitos(linha.get("teltrab_cli"), 15),
        "cep_trabalho": _digitos(linha.get("ceptrab_cli"), 8),
        "bloqueado": _texto(linha.get("status_cli")) == "2",
        "forma_cobranca": _COBRANCA.get(_texto(linha.get("cobranca_cli")), "domicilio"),
        "limite_credito": Decimal(str(linha.get("limite_cli") or 0)).quantize(Decimal("0.01")),
        "credito_suspenso": sim("creditosuspenso_cli"),
        "recebe_mensagens": sim("mens_cli"),
        "especial": sim("especial_cli"),
        "observacao": _texto(linha.get("obs_cli")),
    }


def _aplicar(cliente: Cliente, dados: dict, completo: bool) -> None:
    """Completo: os dados desta loja (os mais recentes) substituem os atuais. Senão, só preenchem o que está vazio."""
    for campo, valor in dados.items():
        if valor in (None, ""):
            continue
        if completo or getattr(cliente, campo) in (None, ""):
            setattr(cliente, campo, valor)


@dataclass
class _Extras:
    """Telefones, referências e anotações desta filial, por cod_cli."""

    telefones: dict[int, list[tuple[str, object]]] = field(default_factory=lambda: defaultdict(list))
    referencias: dict[int, list[dict]] = field(default_factory=lambda: defaultdict(list))
    anotacoes: dict[int, list[dict]] = field(default_factory=lambda: defaultdict(list))
    parentescos: dict[str, int] = field(default_factory=dict)  # cod_tip → parentesco novo


def _ler_extras(origem: Connection) -> _Extras:
    e = _Extras()
    for t in origem.execute(_TELEFONES).mappings():
        numero, cod = so_digitos(t["num_tel"]), _int(t["cod_cli"])
        if len(numero) >= 8 and cod is not None:
            e.telefones[cod].append((numero[:15], t["tipo_tel"]))
    for ref in origem.execute(_REFERENCIAS).mappings():
        cod = _int(ref["cod_cli"])
        if cod is not None and _texto(ref["nome_ref"]):
            e.referencias[cod].append(dict(ref))
    for a in origem.execute(_ANOTACOES).mappings():
        cod = _int(a["cod_cli"])
        if cod is not None and _texto(a["anotacao"]) and (_texto(a["excluido"]) or "N").upper() != "S":
            e.anotacoes[cod].append(dict(a))
    return e


def _somar_extras(db: Session, cliente: Cliente, cod: int, extras: _Extras, anotacoes_importadas: set[str],
                  empresa_id: int, r: Resultado) -> None:
    numeros = {t.numero for t in cliente.telefones}
    for numero, tipo in extras.telefones.get(cod, []):
        if numero not in numeros:
            cliente.telefones.append(TelefoneCliente(numero=numero, tipo=_tipo_telefone(tipo, numero)))
            numeros.add(numero)
            r.telefones += 1

    existentes = {(nome_comparavel(f.nome), f.telefone) for f in cliente.referencias}
    for ref in extras.referencias.get(cod, []):
        nome, telefone = _corta(ref["nome_ref"], 60), _digitos(ref["tel_ref"], 20)
        if (nome_comparavel(nome), telefone) not in existentes:
            cliente.referencias.append(ReferenciaCliente(
                nome=nome, telefone=telefone, parentesco_id=extras.parentescos.get(_texto(ref["cod_tip"]) or "")))
            existentes.add((nome_comparavel(nome), telefone))
            r.referencias += 1

    for a in extras.anotacoes.get(cod, []):
        codigo = str(a["id"])
        if codigo in anotacoes_importadas:
            continue
        data_hora = _data_hora(a["datahora"])
        anotacao = AnotacaoCliente(texto=_texto(a["anotacao"]), empresa_id=empresa_id, **(
            {"data_hora": data_hora} if data_hora else {}))
        cliente.anotacoes.append(anotacao)
        db.flush()
        db.add(MapaLegado(tabela="tab_clientesanot", empresa_id=empresa_id, codigo=codigo, novo_id=anotacao.id))
        anotacoes_importadas.add(codigo)
        r.anotacoes += 1


def _data_hora(valor: object) -> datetime | None:
    v = _texto(valor)
    if not v or v.startswith("0000"):
        return None
    try:
        return datetime.fromisoformat(v[:19])
    except ValueError:
        return None


def _mapa_da_empresa(db: Session, tabela: str, empresa_id: int) -> dict[str, int]:
    return dict(db.execute(select(MapaLegado.codigo, MapaLegado.novo_id).where(
        MapaLegado.tabela == tabela, MapaLegado.empresa_id == empresa_id)).all())


def _importar_clientes(origem: Connection, db: Session, empresa: Empresa, r: Resultado) -> None:
    extras = _ler_extras(origem)
    extras.parentescos = _mapa_da_empresa(db, "tab_tipopar", empresa.id)
    # índices em memória: com dezenas de milhares de clientes, uma consulta por linha seria lenta demais
    por_codigo = _mapa_da_empresa(db, "tab_clientes", empresa.id)
    por_documento = dict(db.execute(select(Cliente.cpf_cnpj, Cliente.id).where(Cliente.cpf_cnpj.is_not(None))).all())
    anotacoes_importadas = set(_mapa_da_empresa(db, "tab_clientesanot", empresa.id))
    setores = _mapa_da_empresa(db, "tab_setores", empresa.id)
    orgaos = _mapa_da_empresa(db, "tab_orgaos", empresa.id)
    grupos = _mapa_da_empresa(db, "tab_grupocli", empresa.id)

    lote: list[dict] = []
    for linha in _ler(origem, "tab_clientes", "cod_cli"):
        lote.append(linha)
        if len(lote) == _LOTE:
            _importar_lote(db, empresa, lote, extras, por_codigo, por_documento, anotacoes_importadas,
                           setores, orgaos, grupos, r)
            lote = []
    if lote:
        _importar_lote(db, empresa, lote, extras, por_codigo, por_documento, anotacoes_importadas,
                       setores, orgaos, grupos, r)


def _importar_lote(db: Session, empresa: Empresa, lote: list[dict], extras: _Extras, por_codigo: dict[str, int],
                   por_documento: dict[str, int], anotacoes_importadas: set[str], setores: dict[str, int],
                   orgaos: dict[str, int], grupos: dict[str, int], r: Resultado) -> None:
    preparados = []
    for linha in lote:
        # zerofill ou não, o código vai para o mapa sem os zeros à esquerda
        codigo = str(_int(linha["cod_cli"]) if _int(linha["cod_cli"]) is not None else linha["cod_cli"]).strip()
        dados = converter(linha)
        if not dados["nome"]:
            r.avisos.append(f"cliente {codigo} sem nome: ignorado")
            continue
        documento = _documento(linha, r)
        preparados.append((codigo, linha, dados, documento))

    # carrega de uma vez os clientes já existentes que este lote vai alterar
    ids = {por_codigo.get(c) or (d and por_documento.get(d)) for c, _, _, d in preparados} - {None}
    carregados = {c.id: c for c in db.scalars(select(Cliente).where(Cliente.id.in_(ids)).options(
        selectinload(Cliente.telefones), selectinload(Cliente.referencias)))} if ids else {}
    novos_por_documento: dict[str, Cliente] = {}
    ligados: list[tuple[str, Cliente]] = []

    for codigo, linha, dados, documento in preparados:
        data_linha = _data(linha.get("dataalt_cli")) or _data(linha.get("data_cli"))
        cadastro = _data(linha.get("data_cli"))
        dados["tipo"] = "J" if documento and len(documento) == 14 else "F"
        dados["setor_id"] = setores.get(_codigo(linha.get("cod_set")) or "")
        dados["setor_trabalho_id"] = setores.get(_codigo(linha.get("setortrab_cli")) or "")
        dados["orgao_id"] = orgaos.get(_codigo(linha.get("cod_org")) or "")
        dados["grupo_id"] = grupos.get(_texto(linha.get("cod_gru")) or "")

        ja_importado = codigo in por_codigo
        if ja_importado:
            cliente = carregados[por_codigo[codigo]]
        elif documento and documento in por_documento:
            cliente = carregados[por_documento[documento]]
        else:
            cliente = novos_por_documento.get(documento or "")

        if cliente is None:
            cliente = Cliente(cpf_cnpj=documento, data_cadastro=cadastro or date.today(),
                              data_alteracao=data_linha, empresa_cadastro_id=empresa.id)
            _aplicar(cliente, dados, completo=True)
            db.add(cliente)
            if documento:
                novos_por_documento[documento] = cliente
            else:
                r.sem_documento += 1
            r.criados += 1
        else:
            if ja_importado:
                r.atualizados += 1
            else:
                r.ligados_por_documento += 1
            completo = cliente.data_alteracao is None or (data_linha is not None and data_linha >= cliente.data_alteracao)
            _aplicar(cliente, dados, completo)
            if completo and data_linha:
                cliente.data_alteracao = data_linha
            if documento and not cliente.cpf_cnpj and documento not in por_documento:
                cliente.cpf_cnpj = documento
            if cadastro and cadastro < cliente.data_cadastro:
                cliente.data_cadastro, cliente.empresa_cadastro_id = cadastro, empresa.id

        cod_int = int(codigo) if codigo.isdigit() else None
        if cod_int is not None:
            _somar_extras(db, cliente, cod_int, extras, anotacoes_importadas, empresa.id, r)
        ligados.append((codigo, cliente))

    # os clientes novos só ganham id aqui; gravar o mapa linha a linha seria lento demais
    db.flush()
    for codigo, cliente in ligados:
        if codigo not in por_codigo:
            db.add(MapaLegado(tabela="tab_clientes", empresa_id=empresa.id, codigo=codigo, novo_id=cliente.id))
            por_codigo[codigo] = cliente.id
        if cliente.cpf_cnpj:
            por_documento[cliente.cpf_cnpj] = cliente.id
    db.flush()
    db.expunge_all()


def importar_clientes(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    """Lê grupos, setores, órgãos, clientes, telefones, referências e anotações de um banco do VB6."""
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    empresa_id = empresa.id

    r = Resultado()
    r.grupos_criados = _importar_lista(origem, db, empresa, _GRUPOS, GrupoCliente, "tab_grupocli", 40)
    r.parentescos_criados = _importar_lista(origem, db, empresa, _PARENTESCOS, Parentesco, "tab_tipopar", 30)
    _importar_setores(origem, db, empresa, r)
    _importar_orgaos(origem, db, empresa, r)
    db.flush()
    _importar_clientes(origem, db, db.get(Empresa, empresa_id), r)
    db.commit()
    return r
