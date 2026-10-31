from pydantic import BaseModel, Field

from app.dominios.cidades.esquemas import Cidade, SetorResumo


class EnderecoDoCep(BaseModel):
    """O endereço do CEP e o setor que corresponde ao bairro, quando dá para saber."""

    cep: str
    logradouro: str | None
    complemento: str | None
    bairro: str | None = Field(description="Como o ViaCEP escreve; o cliente guarda o setor, não este texto")
    cidade: Cidade | None = Field(description="Pelo código do IBGE; vazia se o município não está na lista")
    setor: SetorResumo | None = Field(description="O único setor da cidade com o mesmo nome do bairro")
    sugestoes: list[SetorResumo] = Field(description="Sem setor igual: setores da cidade com nome parecido")
