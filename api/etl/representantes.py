"""Importa os representantes do consignado de um banco de filial do VB6 (D30). Hoje só a matriz usa.

O representante é um cliente especializado: cada um é ligado ao cliente de mesmo CPF; quem
não é cliente vira um, com o nome, o CPF, o RG, o nascimento, o endereço e os telefones do
cadastro de representante. Os campos que não se usam mais (pai, mãe, cônjuge, naturalidade,
endereço dos pais) ficam de fora. O excluído do VB6 fica inativo, para o histórico.

- a senha (texto puro no VB6) vira hash, conferida sem diferenciar maiúsculas, como lá;
- as comissões próprias vêm da tab_reptip; as iguais à padrão do tipo não são gravadas;
- o código do VB6 vira o código do representante, e o legado_mapa liga cod_rep ao id novo
  (os dois cadastros do mesmo CPF no VB6 apontam para um representante só);
- rodar de novo atualiza o que veio do VB6, sem duplicar.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import Connection, select, text
from sqlalchemy.orm import Session

from app.dominios.clientes.modelos import Cliente, TelefoneCliente
from app.dominios.consignacao.modelos import COMISSOES_PADRAO, ComissaoRepresentante, Representante
from app.dominios.empresas.modelos import Empresa
from app.dominios.receber.modelos import TIPOS_COBRANCA
from app.nucleo.documentos import cpf_valido, so_digitos
from app.nucleo.seguranca import gerar_hash
from etl import mapa
from etl.funcionarios import EmpresaNaoImportada, _data, _texto, _tipo_telefone

_REPRESENTANTES = text("""
    SELECT CAST(cod_rep AS CHAR) AS cod_rep, nome_rep, limite_rep, endereco_rep, cep_rep, nasc_rep, rg_rep, cpf_rep,
           datacad_rep, obs_rep, status_rep, cod_set, senha_rep, excluido_rep, avalista_nome, avalista_cpf,
           avalista_rg, avalista_endereco, avalista_telefones, avalista_anotacoes, motivo_bloqueio, lembrete,
           lembreteAcerto AS lembrete_acerto, ultimaconferencia, bloqimpr, bloqdev
    FROM tab_representantes
""")
_COMISSOES = text("SELECT CAST(cod_rep AS CHAR) AS cod_rep, cod_tip, comissao_tip FROM tab_reptip")
_TELEFONES = text("SELECT CAST(cod_cli AS CHAR) AS cod_rep, num_tel, tipo_tel FROM tab_telefones WHERE tipo_ter = 'R'")
_TIPOS = {codigo: tipo for tipo, (_, codigo) in TIPOS_COBRANCA.items()}  # cod_tip do VB6 → tipo de cobrança


@dataclass
class Resultado:
    representantes: int = 0  # novos
    ja_clientes: int = 0  # ligados a um cliente que já existia
    clientes_criados: int = 0
    inativos: int = 0
    comissoes: int = 0
    avisos: list[str] = field(default_factory=list)


def _sim(valor: object) -> bool:
    return (_texto(valor) or "N").upper() == "S"


def _dinheiro(valor: object) -> Decimal:
    return Decimal(str(valor or 0)).quantize(Decimal("0.01"))


def _cliente(db: Session, empresa: Empresa, linha, cpf: str | None, telefones: list) -> tuple[Cliente, bool]:
    """O cliente do representante: o de mesmo CPF, ou um novo com os dados do cadastro de representante."""
    cliente = db.scalar(select(Cliente).where(Cliente.cpf_cnpj == cpf)) if cpf else None
    if cliente is not None:
        return cliente, False
    setor_id = mapa.buscar(db, "tab_setores", empresa.id, _texto(linha["cod_set"]) or "")
    cliente = Cliente(
        nome=" ".join((_texto(linha["nome_rep"]) or "Sem nome").split())[:60], cpf_cnpj=cpf,
        rg=(_texto(linha["rg_rep"]) or "")[:20] or None, data_nascimento=_data(linha["nasc_rep"]),
        logradouro=(_texto(linha["endereco_rep"]) or "")[:100] or None, cep=so_digitos(linha["cep_rep"] or "")[:8] or None,
        setor_id=setor_id, data_cadastro=_data(linha["datacad_rep"]) or date(2000, 1, 1),
        empresa_cadastro_id=empresa.id)
    for numero, tipo in telefones:
        cliente.telefones.append(TelefoneCliente(numero=numero, tipo=_tipo_telefone(tipo, numero)))
    db.add(cliente)
    db.flush()
    return cliente, True


def importar_representantes(origem: Connection, db: Session, codigo_empresa: str) -> Resultado:
    empresa = db.scalar(select(Empresa).where(Empresa.codigo == codigo_empresa))
    if empresa is None:
        raise EmpresaNaoImportada(f"Empresa {codigo_empresa} não existe no banco novo. Rode antes: python -m etl empresas")
    r = Resultado()

    telefones: dict[str, list] = {}
    for t in origem.execute(_TELEFONES).mappings():
        numero = so_digitos(t["num_tel"] or "")
        if 8 <= len(numero) <= 11:
            telefones.setdefault(_texto(t["cod_rep"]) or "", []).append((numero, t["tipo_tel"]))
    comissoes: dict[str, dict[str, Decimal]] = {}
    for c in origem.execute(_COMISSOES).mappings():
        tipo = _TIPOS.get((_texto(c["cod_tip"]) or "").lstrip("0"))
        if tipo:
            comissoes.setdefault(_texto(c["cod_rep"]) or "", {})[tipo] = _dinheiro(c["comissao_tip"])

    importados: dict[int, bool] = {}  # id → ativo
    # em ordem de código (o cod_rep vem como texto); no mesmo CPF, o cadastro mais novo é o que vale
    for linha in sorted(origem.execute(_REPRESENTANTES).mappings(), key=lambda l: int(_texto(l["cod_rep"]) or 0)):
        cod = _texto(linha["cod_rep"]) or ""
        if not cod.isdigit():
            continue
        cpf = so_digitos(linha["cpf_rep"] or "")
        if not cpf_valido(cpf):
            r.avisos.append(f"representante {cod} ({_texto(linha['nome_rep'])}): CPF inválido, o cliente fica sem CPF")
            cpf = None
        ativo = not _sim(linha["excluido_rep"])

        representante = db.get(Representante, mapa.buscar(db, "tab_representantes", empresa.id, cod) or 0)
        if representante is None:
            cliente, criado = _cliente(db, empresa, linha, cpf, telefones.get(cod, []))
            representante = db.scalar(select(Representante).where(Representante.cliente_id == cliente.id))
            if representante is not None:  # o mesmo CPF em dois cadastros do VB6: vale o ativo
                r.avisos.append(f"representante {cod}: mesmo CPF do representante {representante.codigo}, ligados")
                if not ativo or representante.ativo:
                    mapa.gravar(db, "tab_representantes", empresa.id, cod, representante.id)
                    continue
                representante.codigo = int(cod)  # este é o ativo: fica com o código dele
            else:
                representante = Representante(codigo=int(cod), cliente=cliente)
                db.add(representante)
                r.representantes += 1
                r.clientes_criados += criado
                r.ja_clientes += not criado

        bloqueado = (_texto(linha["status_rep"]) or "1") == "2"
        representante.ativo, representante.bloqueado = ativo, bloqueado
        representante.motivo_bloqueio = _texto(linha["motivo_bloqueio"]) if bloqueado else None
        if bloqueado and not representante.motivo_bloqueio:
            representante.motivo_bloqueio = "Bloqueado no sistema antigo"
        representante.limite = _dinheiro(linha["limite_rep"])
        senha = _texto(linha["senha_rep"])
        representante.senha_hash = gerar_hash(senha, sem_caixa=True) if senha else None
        representante.bloqueia_impressao = _sim(linha["bloqimpr"])
        representante.bloqueia_devolucao = _sim(linha["bloqdev"])
        representante.lembrete, representante.lembrete_acerto = _texto(linha["lembrete"]), _texto(linha["lembrete_acerto"])
        representante.observacao = _texto(linha["obs_rep"])
        representante.ultima_conferencia = _data(linha["ultimaconferencia"])
        representante.data_cadastro = _data(linha["datacad_rep"]) or representante.data_cadastro or date(2000, 1, 1)
        avalista_cpf = so_digitos(linha["avalista_cpf"] or "")
        representante.avalista_nome = (_texto(linha["avalista_nome"]) or "")[:100] or None
        representante.avalista_cpf = avalista_cpf if cpf_valido(avalista_cpf) else None
        representante.avalista_rg = (_texto(linha["avalista_rg"]) or "")[:20] or None
        representante.avalista_endereco = (_texto(linha["avalista_endereco"]) or "")[:200] or None
        representante.avalista_telefones = (_texto(linha["avalista_telefones"]) or "")[:200] or None
        representante.avalista_anotacoes = _texto(linha["avalista_anotacoes"])
        representante.comissoes = [ComissaoRepresentante(tipo_cobranca=tipo, percentual=percentual)
                                   for tipo, percentual in comissoes.get(cod, {}).items()
                                   if percentual != COMISSOES_PADRAO[tipo]]
        r.comissoes += len(representante.comissoes)
        db.flush()
        importados[representante.id] = ativo
        mapa.gravar(db, "tab_representantes", empresa.id, cod, representante.id)

    r.inativos = sum(not ativo for ativo in importados.values())
    db.commit()
    return r
