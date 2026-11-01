"""Importa as empresas a partir da tabela sped_empresa do VB6.

Cada banco de filial tem a sua sped_empresa, com uma linha por empresa
(codigo = cod_emp). A importação é repetível: a empresa é localizada pelo
código; se já existe, é atualizada; senão, é criada.

Colunas sensíveis NÃO são lidas: senha e caminho do certificado digital e
id/token do CSC da NFC-e. Onde guardar esses segredos no sistema novo é a
pendência P10 em docs/decisoes.md.

Também não são lidos o logo (caminho_logo) e o QR code do boleto
(caminho_qrcodedoc): são caminhos de arquivo no computador da loja. As imagens
são enviadas na ficha da empresa. O esquema de cores (D19) só existe no sistema novo.
"""
import re
from dataclasses import dataclass, field

from sqlalchemy import Connection, select, text
from sqlalchemy.orm import Session

from app.dominios.cidades.repositorio import cidade_por_codigo
from app.dominios.empresas.modelos import Empresa

# só as colunas que interessam; segredos ficam de fora da própria consulta
_CONSULTA = text(
    """
    SELECT codigo, cnpj, apelido, IE, nome, cod_mun, im, suframa, ind_perfil, ind_atv,
           fantasia, cep, endereco, numero, complemento, bairro, fone, email, crt
      FROM sped_empresa
     ORDER BY codigo
    """
)


class ConflitoEmpresa(Exception):
    """O mesmo código de empresa aparece com CNPJs diferentes."""


@dataclass
class Resultado:
    criadas: list[str] = field(default_factory=list)
    atualizadas: list[str] = field(default_factory=list)


def _texto(valor: object) -> str | None:
    if valor is None:
        return None
    v = str(valor).strip()
    return v or None


def _digitos(valor: object) -> str | None:
    v = re.sub(r"\D", "", str(valor or ""))
    return v or None


def converter(linha: dict) -> dict:
    """Uma linha da sped_empresa → campos da tabela empresa."""
    email = _texto(linha.get("email"))
    return {
        "codigo": _texto(linha["codigo"]),
        "cnpj": _digitos(linha.get("cnpj")),
        "nome": _texto(linha.get("apelido")) or _texto(linha.get("fantasia")) or _texto(linha["codigo"]),
        "razao_social": _texto(linha.get("nome")),
        "nome_fantasia": _texto(linha.get("fantasia")),
        "inscricao_estadual": _digitos(linha.get("IE")),
        "inscricao_municipal": _texto(linha.get("im")),
        "crt": _texto(linha.get("crt")),
        "sped_perfil": _texto(linha.get("ind_perfil")),
        "sped_atividade": _texto(linha.get("ind_atv")),
        "suframa": _texto(linha.get("suframa")),
        # o código do IBGE vira a cidade do banco novo na importação (a UF é a da cidade)
        "codigo_ibge": _digitos(linha.get("cod_mun")),
        "cep": _digitos(linha.get("cep")),
        "logradouro": _texto(linha.get("endereco")),
        "numero": _texto(linha.get("numero")),
        "complemento": _texto(linha.get("complemento")),
        "bairro": _texto(linha.get("bairro")),
        "telefone": _digitos(linha.get("fone")),
        "email": email.lower() if email else None,
    }


def importar_empresas(origem: Connection, db: Session) -> Resultado:
    """Lê a sped_empresa de um banco do VB6 e grava no banco novo."""
    resultado = Resultado()
    for linha in origem.execute(_CONSULTA).mappings():
        dados = converter(dict(linha))
        cidade = cidade_por_codigo(db, dados.pop("codigo_ibge") or "")
        dados["cidade_id"] = cidade.id if cidade else None
        empresa = db.scalar(select(Empresa).where(Empresa.codigo == dados["codigo"]))
        if empresa is None:
            db.add(Empresa(**dados))
            resultado.criadas.append(dados["codigo"])
            continue
        if empresa.cnpj and dados["cnpj"] and empresa.cnpj != dados["cnpj"]:
            db.rollback()
            raise ConflitoEmpresa(
                f"Empresa {dados['codigo']}: CNPJ {empresa.cnpj} no banco novo, {dados['cnpj']} na origem. "
                "Confira o cod_emp das filiais (pendência P2)."
            )
        for campo, valor in dados.items():
            setattr(empresa, campo, valor)
        resultado.atualizadas.append(dados["codigo"])
    db.commit()
    return resultado
