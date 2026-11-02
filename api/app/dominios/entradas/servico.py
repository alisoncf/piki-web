"""Regras da entrada de notas pelo XML (D25)."""
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominios.cidades.modelos import Cidade
from app.dominios.empresas.modelos import Empresa
from app.dominios.entradas import nfe
from app.dominios.entradas.esquemas import ItemDados
from app.dominios.entradas.modelos import ABERTA, CONFIRMADA, ItemNotaEntrada, NotaEntrada
from app.dominios.estoque import servico as estoque
from app.dominios.fornecedores.modelos import Fornecedor, TelefoneFornecedor
from app.dominios.produtos.modelos import CodigoBarras, Produto, ProdutoFornecedor
from app.nucleo.arquivos import Armazenamento
from app.nucleo.documentos import cpf_cnpj_valido
from app.nucleo.textos import nome_proprio

TAMANHO_MAXIMO_XML = 5 * 1024 * 1024
_TELEFONE_COMERCIAL = "2"


class ErroEntrada(Exception):
    """Erro de regra da entrada; a mensagem vai para o usuário."""


class NaoEncontrado(ErroEntrada):
    pass


class DadoInvalido(ErroEntrada):
    pass


class Duplicado(ErroEntrada):
    def __init__(self, mensagem: str, nota_id: int) -> None:
        super().__init__(mensagem)
        self.nota_id = nota_id


class Proibido(ErroEntrada):
    pass


def obter_nota(db: Session, empresa_id: int, nota_id: int) -> NotaEntrada:
    """A nota da loja; se ainda está aberta, tenta de novo ligar os itens sem produto (cadastrados depois)."""
    nota = db.get(NotaEntrada, nota_id)
    if nota is None or nota.empresa_id != empresa_id:
        raise NaoEncontrado("Nota não encontrada")
    if nota.situacao == ABERTA and any(i.produto_id is None for i in nota.itens):
        for item in nota.itens:
            if item.produto_id is None:
                _ligar_sozinho(db, nota.fornecedor_id, item)
        db.commit()
    return nota


def _ligar_sozinho(db: Session, fornecedor_id: int, item: ItemNotaEntrada) -> None:
    """Pelo código do produto no fornecedor; senão, pelo código de barras. A embalagem vem da ligação."""
    ligacao = db.scalar(select(ProdutoFornecedor).where(
        ProdutoFornecedor.fornecedor_id == fornecedor_id,
        func.lower(ProdutoFornecedor.codigo) == item.codigo.lower()))
    if ligacao is not None:
        item.produto_id, item.embalagem = ligacao.produto_id, ligacao.embalagem or 1
    elif item.ean:
        item.produto_id = db.scalar(select(CodigoBarras.produto_id).where(CodigoBarras.codigo == item.ean))
    if item.produto_id is not None:
        db.flush()
        db.refresh(item, ["produto"])


def _fornecedor(db: Session, emitente: nfe.Emitente) -> tuple[Fornecedor, bool]:
    """O fornecedor pelo CNPJ do emitente; se não existe, cadastrado com os dados do XML."""
    fornecedor = db.scalar(select(Fornecedor).where(Fornecedor.cpf_cnpj == emitente.cpf_cnpj))
    if fornecedor is not None:
        return fornecedor, False
    if not cpf_cnpj_valido(emitente.cpf_cnpj):
        raise DadoInvalido("O CNPJ do emitente da nota é inválido")
    cidade = db.scalar(select(Cidade.id).where(Cidade.codigo_ibge == emitente.codigo_municipio))
    fornecedor = Fornecedor(
        cpf_cnpj=emitente.cpf_cnpj, nome=nome_proprio(emitente.nome)[:100],
        nome_fantasia=nome_proprio(emitente.nome_fantasia)[:60] if emitente.nome_fantasia else None,
        inscricao_estadual=emitente.inscricao_estadual, cep=emitente.cep if emitente.cep and len(emitente.cep) == 8 else None,
        logradouro=nome_proprio(emitente.logradouro)[:60] if emitente.logradouro else None,
        numero=(emitente.numero or "")[:10] or None,
        complemento=nome_proprio(emitente.complemento)[:60] if emitente.complemento else None,
        bairro=nome_proprio(emitente.bairro)[:60] if emitente.bairro else None, cidade_id=cidade,
        observacao="Cadastrado pela entrada da nota.",
    )
    if emitente.telefone and len(emitente.telefone.lstrip("0")) >= 8:
        fornecedor.telefones.append(TelefoneFornecedor(numero=emitente.telefone.lstrip("0")[:15], tipo=_TELEFONE_COMERCIAL))
    db.add(fornecedor)
    db.flush()
    return fornecedor, True


def carregar_xml(db: Session, arquivos: Armazenamento, empresa_id: int, conteudo: bytes,
                 usuario_id: int) -> tuple[NotaEntrada, bool]:
    """Lê o XML e guarda a nota aberta, com os itens já ligados aos produtos que o sistema achou.

    Devolve a nota e se o fornecedor foi cadastrado agora.
    """
    if not conteudo:
        raise DadoInvalido("Arquivo vazio")
    if len(conteudo) > TAMANHO_MAXIMO_XML:
        raise DadoInvalido("O arquivo passa de 5 MB")
    try:
        lida = nfe.ler(conteudo)
    except nfe.XmlInvalido as e:
        raise DadoInvalido(str(e)) from e

    empresa = db.get(Empresa, empresa_id)
    if not empresa.cnpj or lida.destinatario_cpf_cnpj != empresa.cnpj:
        raise DadoInvalido(f"Esta nota não é para {empresa.nome}: o destinatário é outro CNPJ")
    existente = db.scalar(select(NotaEntrada).where(NotaEntrada.chave == lida.chave))
    if existente is not None:
        raise Duplicado(f"Esta nota já foi carregada (nº {existente.numero}, {existente.situacao})", existente.id)

    fornecedor, novo = _fornecedor(db, lida.emitente)
    chave_arquivo = f"notas-entrada/{empresa_id}/{lida.chave}-{uuid.uuid4().hex[:8]}.xml"
    arquivos.gravar(chave_arquivo, conteudo, "application/xml")
    nota = NotaEntrada(
        empresa_id=empresa_id, fornecedor_id=fornecedor.id, chave=lida.chave, numero=lida.numero, serie=lida.serie,
        data_emissao=lida.data_emissao, valor_total=lida.valor_total, situacao=ABERTA, arquivo=chave_arquivo,
        usuario_id=usuario_id,
    )
    for i in lida.itens:
        nota.itens.append(ItemNotaEntrada(
            numero=i.numero, codigo=i.codigo[:60], ean=i.ean, descricao=i.descricao[:120], ncm=i.ncm,
            cest=i.cest, cfop=i.cfop, unidade=i.unidade, quantidade=i.quantidade, valor_unitario=i.valor_unitario,
            valor_produtos=i.valor_produtos, valor_desconto=i.valor_desconto, valor_frete=i.valor_frete,
            valor_seguro=i.valor_seguro, valor_outras=i.valor_outras, valor_ipi=i.valor_ipi, valor_st=i.valor_st,
            embalagem=1,
        ))
    db.add(nota)
    db.flush()
    for item in nota.itens:
        _ligar_sozinho(db, fornecedor.id, item)
    db.commit()
    db.refresh(nota)
    return nota, novo


def _item(nota: NotaEntrada, item_id: int) -> ItemNotaEntrada:
    item = next((i for i in nota.itens if i.id == item_id), None)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    return item


def _aberta(db: Session, empresa_id: int, nota_id: int) -> NotaEntrada:
    nota = obter_nota(db, empresa_id, nota_id)
    if nota.situacao != ABERTA:
        raise DadoInvalido("A entrada desta nota já foi confirmada")
    return nota


def alterar_item(db: Session, empresa_id: int, nota_id: int, item_id: int, dados: ItemDados,
                 pode_precos: bool) -> ItemNotaEntrada:
    nota = _aberta(db, empresa_id, nota_id)
    item = _item(nota, item_id)
    if dados.produto_id is not None and db.get(Produto, dados.produto_id) is None:
        raise DadoInvalido("Produto não encontrado")
    if dados.preco_venda is not None and dados.preco_venda != item.preco_venda and not pode_precos:
        raise Proibido("Sem permissão para alterar preços (produtos.precos)")
    item.produto_id, item.embalagem, item.preco_venda = dados.produto_id, dados.embalagem, dados.preco_venda
    db.commit()
    db.refresh(item)
    return item


def confirmar(db: Session, empresa_id: int, nota_id: int, usuario_id: int, pode_precos: bool) -> NotaEntrada:
    """Dá entrada no estoque da loja, grava o custo da nota no produto e, se pedido, o preço novo.

    A ligação item → produto fica na ficha do produto (código e embalagem do
    fornecedor), e a próxima nota desse fornecedor já vem ligada.
    """
    nota = _aberta(db, empresa_id, nota_id)
    sem_produto = [i.numero for i in nota.itens if i.produto_id is None]
    if sem_produto:
        raise DadoInvalido(f"Ligue todos os itens a um produto antes de confirmar (faltam os itens {', '.join(map(str, sem_produto))})")
    if not pode_precos and any(i.preco_venda is not None for i in nota.itens):
        raise Proibido("Sem permissão para alterar preços (produtos.precos)")
    documento = f"NF {nota.numero}/{nota.serie}"
    for item in nota.itens:
        produto = item.produto
        try:
            estoque.movimentar(db, empresa_id, produto.id, "entrada", item.unidades, usuario_id=usuario_id,
                               documento=documento, observacao=nota.fornecedor.nome_fantasia or nota.fornecedor.nome)
        except estoque.DadoInvalido as e:
            raise DadoInvalido(f"Item {item.numero}: {e}. Confira a embalagem.") from e
        if item.custo_unitario is not None:
            produto.custo = item.custo_unitario
        if item.preco_venda is not None:
            produto.preco_venda = item.preco_venda
            if produto.preco_queima is not None and produto.preco_queima >= item.preco_venda:
                produto.preco_queima = None
        ligacao = next((f for f in produto.fornecedores if f.fornecedor_id == nota.fornecedor_id), None)
        if ligacao is None:
            produto.fornecedores.append(ProdutoFornecedor(
                fornecedor_id=nota.fornecedor_id, codigo=item.codigo, embalagem=item.embalagem))
        else:
            ligacao.codigo, ligacao.embalagem = item.codigo, item.embalagem
        if item.ean and not any(c.codigo == item.ean for c in produto.codigos_barras) and db.scalar(
                select(CodigoBarras.id).where(CodigoBarras.codigo == item.ean)) is None:
            produto.codigos_barras.append(CodigoBarras(codigo=item.ean))
    nota.situacao = CONFIRMADA
    nota.confirmada_em = datetime.now()
    nota.confirmada_por_id = usuario_id
    db.commit()
    db.refresh(nota)
    return nota


def descartar(db: Session, empresa_id: int, nota_id: int) -> None:
    """Apaga a nota aberta (carregada por engano). O XML fica no armazenamento."""
    db.delete(_aberta(db, empresa_id, nota_id))
    db.commit()


def ler_xml(db: Session, arquivos: Armazenamento, empresa_id: int, nota_id: int) -> tuple[NotaEntrada, bytes]:
    nota = obter_nota(db, empresa_id, nota_id)
    return nota, arquivos.ler(nota.arquivo)
