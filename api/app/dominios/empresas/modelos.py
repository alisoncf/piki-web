"""Empresas (filiais com CNPJ próprio) e as suas imagens. No VB6: sped_empresa."""
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, LargeBinary, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.cidades.modelos import Cidade
from app.dominios.empresas.tema import tema_automatico
from app.nucleo.banco import Base, ComDatas


class Empresa(ComDatas, Base):
    """Uma filial, com CNPJ próprio."""

    __tablename__ = "empresa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # código usado no VB6 (cod_emp / sped_empresa.codigo); o ETL usa para saber de onde veio cada dado
    codigo: Mapped[str] = mapped_column(String(2), unique=True)
    # nome curto, mostrado na escolha e na troca de empresa (no VB6: apelido)
    nome: Mapped[str] = mapped_column(String(60))
    razao_social: Mapped[str | None] = mapped_column(String(100))
    nome_fantasia: Mapped[str | None] = mapped_column(String(60))
    cnpj: Mapped[str | None] = mapped_column(String(14), unique=True)
    inscricao_estadual: Mapped[str | None] = mapped_column(String(20))
    inscricao_municipal: Mapped[str | None] = mapped_column(String(20))
    suframa: Mapped[str | None] = mapped_column(String(19))
    # código de regime tributário da NF-e: 1 Simples Nacional, 2 Simples com excesso, 3 Regime normal
    crt: Mapped[str | None] = mapped_column(String(1))
    # perfil (A, B, C) e tipo de atividade (0 industrial, 1 outros) do SPED Fiscal
    sped_perfil: Mapped[str | None] = mapped_column(String(1))
    sped_atividade: Mapped[str | None] = mapped_column(String(1))

    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None] = mapped_column(String(60))
    numero: Mapped[str | None] = mapped_column(String(10))
    complemento: Mapped[str | None] = mapped_column(String(60))
    # texto: o setor é região de cobrança de clientes, não se aplica à empresa
    bairro: Mapped[str | None] = mapped_column(String(60))
    cidade_id: Mapped[int | None] = mapped_column(ForeignKey("cidade.id"), index=True)
    telefone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(200))

    ativa: Mapped[bool] = mapped_column(Boolean, server_default=true(), default=True)
    # esquema de cores na tela: {"principal", "fundo", "menu"} em #rrggbb; vazio = automático pelo código
    tema: Mapped[dict | None] = mapped_column(JSON)

    cidade: Mapped[Cidade | None] = relationship(lazy="joined")
    imagens: Mapped[list["ImagemEmpresa"]] = relationship(
        back_populates="empresa", lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def tema_efetivo(self) -> dict[str, str]:
        return self.tema or tema_automatico(self.codigo)

    @property
    def tipos_de_imagem(self) -> list[str]:
        return sorted(i.tipo for i in self.imagens)


class ImagemEmpresa(ComDatas, Base):
    """Logo dos relatórios e QR code do boleto de cobrança (no VB6, caminhos de arquivo na sped_empresa)."""

    __tablename__ = "empresa_imagem"

    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id", ondelete="CASCADE"), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10), primary_key=True)  # logo, qrcode
    tipo_conteudo: Mapped[str] = mapped_column(String(30))  # image/png, image/jpeg
    # carregado só quando pedido: a lista de imagens da empresa não precisa dos bytes
    conteudo: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)

    empresa: Mapped[Empresa] = relationship(back_populates="imagens")
