"""Regras do cadastro de produtos, seções e marcas (D24)."""
import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominios.fornecedores.modelos import Fornecedor
from app.dominios.produtos import repositorio as repo
from app.dominios.produtos.esquemas import NomeDados, ProdutoDados, SubsecaoDados
from app.dominios.produtos.modelos import CodigoBarras, FotoProduto, Marca, Produto, ProdutoFornecedor, Secao, Subsecao
from app.nucleo.arquivos import Armazenamento

PERMISSAO_PRECOS = "produtos.precos"
_CAMPOS_DE_PRECO = ("custo", "margem", "preco_venda", "preco_queima")
FOTOS_POR_PRODUTO = 10
TAMANHO_MAXIMO_FOTO = 5 * 1024 * 1024
_FORMATOS = {b"\x89PNG\r\n\x1a\n": ("image/png", ".png"), b"\xff\xd8\xff": ("image/jpeg", ".jpg")}


class ErroProduto(Exception):
    """Erro de regra do cadastro; a mensagem vai para o usuário."""


class NaoEncontrado(ErroProduto):
    pass


class DadoInvalido(ErroProduto):
    pass


class Duplicado(ErroProduto):
    pass


class Proibido(ErroProduto):
    pass


# produtos

def obter_produto(db: Session, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise NaoEncontrado("Produto não encontrado")
    return produto


def _conferir(db: Session, dados: ProdutoDados, produto_id: int | None) -> None:
    subsecao = db.get(Subsecao, dados.subsecao_id)
    if subsecao is None:
        raise DadoInvalido("Subseção não encontrada")
    if dados.marca_id is not None and db.get(Marca, dados.marca_id) is None:
        raise DadoInvalido("Marca não encontrada")
    if dados.preco_queima is not None and dados.preco_queima >= dados.preco_venda:
        raise DadoInvalido("O preço de queima tem que ser menor que o preço de venda")

    barras = dados.codigos_barras
    if len(barras) != len(set(barras)):
        raise DadoInvalido("Código de barras repetido")
    for codigo in barras:
        if not 8 <= len(codigo) <= 14:
            raise DadoInvalido(f"Código de barras inválido: {codigo} (são de 8 a 14 dígitos)")
        dono = repo.dono_do_codigo_de_barras(db, codigo)
        if dono is not None and dono.id != produto_id:
            raise Duplicado(f"O código de barras {codigo} já é do produto {dono.codigo} - {dono.nome}")

    ids = [f.fornecedor_id for f in dados.fornecedores]
    if len(ids) != len(set(ids)):
        raise DadoInvalido("Fornecedor repetido")
    if ids and db.scalar(select(func.count()).select_from(Fornecedor).where(Fornecedor.id.in_(ids))) != len(ids):
        raise DadoInvalido("Fornecedor não encontrado")


def _aplicar(produto: Produto, dados: ProdutoDados, pode_precos: bool) -> None:
    campos = dados.model_dump(exclude={"codigos_barras", "fornecedores"})
    if not pode_precos:
        mudou = [c for c in _CAMPOS_DE_PRECO if _diferente(getattr(produto, c), campos[c])]
        if mudou:
            raise Proibido("Sem permissão para alterar custo e preços (produtos.precos)")
    for campo, valor in campos.items():
        setattr(produto, campo, valor)
    # mantém os registros que continuam, para não trocar o id à toa
    atuais = {c.codigo: c for c in produto.codigos_barras}
    produto.codigos_barras = [atuais.get(c) or CodigoBarras(codigo=c) for c in dados.codigos_barras]
    fornecedores = {f.fornecedor_id: f for f in produto.fornecedores}
    novos = []
    for f in dados.fornecedores:
        registro = fornecedores.get(f.fornecedor_id) or ProdutoFornecedor(fornecedor_id=f.fornecedor_id)
        registro.codigo = f.codigo
        novos.append(registro)
    produto.fornecedores = novos


def _diferente(atual: Decimal | None, novo: Decimal | None) -> bool:
    return (atual or Decimal(0)) != (novo or Decimal(0))


def criar_produto(db: Session, dados: ProdutoDados, pode_precos: bool) -> Produto:
    """O código é o seguinte ao maior que existe. Sem produtos.precos, custo e preços ficam zerados."""
    _conferir(db, dados, None)
    produto = Produto(codigo=repo.proximo_codigo(db), custo=0, margem=0, preco_venda=0, preco_queima=None)
    _aplicar(produto, dados, pode_precos)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def alterar_produto(db: Session, produto_id: int, dados: ProdutoDados, pode_precos: bool) -> Produto:
    """Os códigos de barras e fornecedores enviados substituem os que existiam."""
    produto = obter_produto(db, produto_id)
    _conferir(db, dados, produto_id)
    _aplicar(produto, dados, pode_precos)
    db.commit()
    db.refresh(produto)
    return produto


# fotos

def _foto(db: Session, produto_id: int, foto_id: int) -> FotoProduto:
    foto = db.get(FotoProduto, foto_id)
    if foto is None or foto.produto_id != produto_id:
        raise NaoEncontrado("Foto não encontrada")
    return foto


def enviar_foto(db: Session, arquivos: Armazenamento, produto_id: int, conteudo: bytes, usuario_id: int) -> FotoProduto:
    """A foto nova vai para o fim; a primeira é a principal."""
    produto = obter_produto(db, produto_id)
    if len(produto.fotos) >= FOTOS_POR_PRODUTO:
        raise DadoInvalido(f"O produto já tem {FOTOS_POR_PRODUTO} fotos")
    if not conteudo:
        raise DadoInvalido("Arquivo vazio")
    if len(conteudo) > TAMANHO_MAXIMO_FOTO:
        raise DadoInvalido("A foto passa de 5 MB")
    formato = next((f for inicio, f in _FORMATOS.items() if conteudo.startswith(inicio)), None)
    if formato is None:
        raise DadoInvalido("Envie uma imagem JPEG ou PNG")
    tipo_conteudo, extensao = formato
    chave = f"produtos/{produto.id}/{uuid.uuid4().hex}{extensao}"
    arquivos.gravar(chave, conteudo, tipo_conteudo)
    ordem = max((f.ordem for f in produto.fotos), default=-1) + 1
    foto = FotoProduto(produto_id=produto.id, ordem=ordem, chave=chave, tipo_conteudo=tipo_conteudo,
                       tamanho=len(conteudo), usuario_id=usuario_id)
    db.add(foto)
    db.commit()
    db.refresh(foto)
    return foto


def ler_foto(db: Session, arquivos: Armazenamento, produto_id: int, foto_id: int) -> tuple[FotoProduto, bytes]:
    foto = _foto(db, produto_id, foto_id)
    return foto, arquivos.ler(foto.chave)


def remover_foto(db: Session, produto_id: int, foto_id: int) -> None:
    """Tira a foto do produto. O arquivo fica no armazenamento."""
    db.delete(_foto(db, produto_id, foto_id))
    db.commit()


def tornar_principal(db: Session, produto_id: int, foto_id: int) -> Produto:
    foto = _foto(db, produto_id, foto_id)
    produto = obter_produto(db, produto_id)
    outras = [f for f in produto.fotos if f.id != foto.id]
    for ordem, f in enumerate([foto, *outras]):
        f.ordem = ordem
    db.commit()
    db.expire(produto, ["fotos"])
    return produto


# seções e subseções

def criar_secao(db: Session, dados: NomeDados) -> Secao:
    if repo.secao_por_nome(db, dados.nome):
        raise Duplicado("Já existe uma seção com este nome")
    secao = Secao(nome=dados.nome, ativo=dados.ativo)
    db.add(secao)
    db.commit()
    db.refresh(secao)
    return secao


def alterar_secao(db: Session, secao_id: int, dados: NomeDados) -> Secao:
    secao = db.get(Secao, secao_id)
    if secao is None:
        raise NaoEncontrado("Seção não encontrada")
    outra = repo.secao_por_nome(db, dados.nome)
    if outra and outra.id != secao_id:
        raise Duplicado("Já existe uma seção com este nome")
    secao.nome, secao.ativo = dados.nome, dados.ativo
    db.commit()
    db.refresh(secao)
    return secao


def _salvar_subsecao(db: Session, subsecao: Subsecao, dados: SubsecaoDados) -> Subsecao:
    if db.get(Secao, dados.secao_id) is None:
        raise DadoInvalido("Seção não encontrada")
    outra = repo.subsecao_por_nome(db, dados.secao_id, dados.nome)
    if outra and outra.id != subsecao.id:
        raise Duplicado("Já existe uma subseção com este nome nesta seção")
    subsecao.secao_id, subsecao.nome, subsecao.ativo = dados.secao_id, dados.nome, dados.ativo
    db.add(subsecao)
    db.commit()
    db.refresh(subsecao)
    db.expire_all()  # a lista de subseções da seção antiga e da nova
    return subsecao


def criar_subsecao(db: Session, dados: SubsecaoDados) -> Subsecao:
    return _salvar_subsecao(db, Subsecao(), dados)


def alterar_subsecao(db: Session, subsecao_id: int, dados: SubsecaoDados) -> Subsecao:
    subsecao = db.get(Subsecao, subsecao_id)
    if subsecao is None:
        raise NaoEncontrado("Subseção não encontrada")
    return _salvar_subsecao(db, subsecao, dados)


# marcas

def criar_marca(db: Session, dados: NomeDados) -> Marca:
    if repo.marca_por_nome(db, dados.nome):
        raise Duplicado("Já existe uma marca com este nome")
    marca = Marca(nome=dados.nome, ativo=dados.ativo)
    db.add(marca)
    db.commit()
    db.refresh(marca)
    return marca


def alterar_marca(db: Session, marca_id: int, dados: NomeDados) -> Marca:
    marca = db.get(Marca, marca_id)
    if marca is None:
        raise NaoEncontrado("Marca não encontrada")
    outra = repo.marca_por_nome(db, dados.nome)
    if outra and outra.id != marca_id:
        raise Duplicado("Já existe uma marca com este nome")
    marca.nome, marca.ativo = dados.nome, dados.ativo
    db.commit()
    db.refresh(marca)
    return marca
