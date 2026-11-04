"""Regras da consignação (D30). Por enquanto, o cadastro de representantes."""
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.dominios.clientes.modelos import Cliente
from app.dominios.consignacao.esquemas import LimitesDados, RepresentanteDados
from app.dominios.consignacao.modelos import COMISSOES_PADRAO, ComissaoRepresentante, Representante
from app.dominios.receber.modelos import TIPOS_COBRANCA
from app.nucleo.documentos import cpf_valido, so_digitos
from app.nucleo.seguranca import conferir_hash, gerar_hash


class ErroConsignacao(Exception):
    """Erro de regra da consignação; a mensagem vai para o usuário."""


class NaoEncontrado(ErroConsignacao):
    pass


class DadoInvalido(ErroConsignacao):
    pass


class Duplicado(ErroConsignacao):
    pass


def listar(db: Session, busca: str | None = None, so_ativos: bool = False, limite: int = 200) -> list[Representante]:
    consulta = select(Representante).join(Representante.cliente).order_by(Cliente.nome)
    if busca and busca.strip():
        termo = busca.strip()
        condicoes = [func.lower(Cliente.nome).like(f"%{termo.lower()}%")]
        digitos = so_digitos(termo)
        if len(digitos) >= 5:
            condicoes.append(Cliente.cpf_cnpj.like(f"%{digitos}%"))
        if termo.isdigit() and len(termo) <= 6:  # só números, curto: o código
            condicoes.append(Representante.codigo == int(termo))
        consulta = consulta.where(or_(*condicoes))
    if so_ativos:
        consulta = consulta.where(Representante.ativo.is_(True))
    return list(db.scalars(consulta.limit(limite)))


def obter(db: Session, representante_id: int) -> Representante:
    representante = db.get(Representante, representante_id)
    if representante is None:
        raise NaoEncontrado("Representante não encontrado")
    return representante


def comissoes(representante: Representante) -> list[dict]:
    """As comissões de todos os tipos de cobrança: a do representante, ou a padrão."""
    proprias = {c.tipo_cobranca for c in representante.comissoes}
    return [{"tipo_cobranca": tipo, "nome": nome, "percentual": representante.comissao(tipo), "padrao": tipo not in proprias}
            for tipo, (nome, _) in TIPOS_COBRANCA.items()]


def _aplicar(representante: Representante, dados: RepresentanteDados) -> None:
    if dados.avalista_cpf and not cpf_valido(dados.avalista_cpf):
        raise DadoInvalido("CPF do avalista inválido")
    for campo, valor in dados.model_dump().items():
        setattr(representante, campo, valor.strip() or None if isinstance(valor, str) else valor)


def criar(db: Session, cliente_id: int, dados: RepresentanteDados) -> Representante:
    """O cliente passa a ser representante, com o próximo código."""
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise DadoInvalido("Cliente não encontrado")
    outro = db.scalar(select(Representante).where(Representante.cliente_id == cliente_id))
    if outro is not None:
        raise Duplicado(f"{cliente.nome} já é o representante {outro.codigo}")
    codigo = (db.scalar(select(func.max(Representante.codigo))) or 0) + 1
    representante = Representante(codigo=codigo, cliente=cliente)
    _aplicar(representante, dados)
    db.add(representante)
    db.commit()
    return representante


def alterar(db: Session, representante_id: int, dados: RepresentanteDados) -> Representante:
    representante = obter(db, representante_id)
    _aplicar(representante, dados)
    db.commit()
    return representante


def alterar_limites(db: Session, representante_id: int, dados: LimitesDados) -> Representante:
    """Limite, bloqueio e comissões (permissão própria, como no VB6). Comissão vazia volta para a padrão."""
    representante = obter(db, representante_id)
    motivo = (dados.motivo_bloqueio or "").strip() or None
    if dados.bloqueado and not motivo:
        raise DadoInvalido("Informe o motivo do bloqueio")
    desconhecidos = [c.tipo_cobranca for c in dados.comissoes if c.tipo_cobranca not in COMISSOES_PADRAO]
    if desconhecidos:
        raise DadoInvalido(f"Tipo de cobrança desconhecido: {', '.join(desconhecidos)}")
    representante.limite, representante.bloqueado = dados.limite, dados.bloqueado
    representante.motivo_bloqueio = motivo if dados.bloqueado else None
    representante.bloqueia_impressao, representante.bloqueia_devolucao = dados.bloqueia_impressao, dados.bloqueia_devolucao
    representante.comissoes = [ComissaoRepresentante(tipo_cobranca=c.tipo_cobranca, percentual=c.percentual.quantize(Decimal("0.01")))
                               for c in dados.comissoes if c.percentual is not None]
    db.commit()
    return representante


def trocar_senha(db: Session, representante_id: int, senha: str) -> Representante:
    representante = obter(db, representante_id)
    representante.senha_hash = gerar_hash(senha, sem_caixa=True)
    db.commit()
    return representante


def conferir_senha(representante: Representante, senha: str) -> bool:
    """A senha que o representante digita no balcão para confirmar a transferência. Como no VB6, sem diferenciar
    maiúsculas."""
    return conferir_hash(senha, representante.senha_hash, sem_caixa=True)
