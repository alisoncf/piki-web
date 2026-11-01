"""Onde ficam os arquivos enviados (documentos de clientes...), fora do banco.

O banco guarda só a chave de cada arquivo ("clientes/7/3f2a....jpg"). O lugar
vem do .env: uma pasta no servidor (padrão) ou um MinIO, que é compatível com
o S3. Para trocar de um para o outro, copie os arquivos mantendo as chaves.
"""
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Protocol

from app.config import configuracao


class ArquivoNaoEncontrado(Exception):
    pass


class Armazenamento(Protocol):
    def gravar(self, chave: str, conteudo: bytes, tipo_conteudo: str) -> None: ...

    def ler(self, chave: str) -> bytes: ...


class Pasta:
    """Arquivos numa pasta do servidor. Ela precisa entrar no backup."""

    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz.resolve()

    def _caminho(self, chave: str) -> Path:
        caminho = (self.raiz / chave).resolve()
        if not caminho.is_relative_to(self.raiz):  # chave com "..": nunca sai da pasta
            raise ValueError(f"Chave inválida: {chave}")
        return caminho

    def gravar(self, chave: str, conteudo: bytes, tipo_conteudo: str) -> None:
        caminho = self._caminho(chave)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(conteudo)

    def ler(self, chave: str) -> bytes:
        try:
            return self._caminho(chave).read_bytes()
        except FileNotFoundError as e:
            raise ArquivoNaoEncontrado(chave) from e


class MinIO:
    """Arquivos num bucket do MinIO (ou de outro serviço compatível com o S3)."""

    def __init__(self, cliente, bucket: str) -> None:
        self.cliente = cliente
        self.bucket = bucket

    def gravar(self, chave: str, conteudo: bytes, tipo_conteudo: str) -> None:
        self.cliente.put_object(self.bucket, chave, BytesIO(conteudo), len(conteudo), content_type=tipo_conteudo)

    def ler(self, chave: str) -> bytes:
        try:
            resposta = self.cliente.get_object(self.bucket, chave)
        except Exception as e:  # minio.error.S3Error; sem importar, o minio só é preciso com PIKI_ARQUIVOS=minio
            if getattr(e, "code", None) == "NoSuchKey":
                raise ArquivoNaoEncontrado(chave) from e
            raise
        try:
            return resposta.read()
        finally:
            resposta.close()
            resposta.release_conn()


@lru_cache
def armazenamento() -> Armazenamento:
    """O armazenamento configurado no .env. Dependência do FastAPI (os testes trocam por uma pasta temporária)."""
    c = configuracao()
    if c.arquivos == "minio":
        from minio import Minio  # instalado com: pip install -e ".[minio]"

        cliente = Minio(c.minio_endereco, access_key=c.minio_usuario, secret_key=c.minio_senha, secure=c.minio_https)
        return MinIO(cliente, c.minio_bucket)
    return Pasta(Path(c.arquivos_pasta))
