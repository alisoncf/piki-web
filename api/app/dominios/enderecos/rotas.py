from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dominios.enderecos import servico
from app.dominios.enderecos.esquemas import EnderecoDoCep
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["endereços"])


@router.get("/cep/{cep}", response_model=EnderecoDoCep)
def consultar_cep(
    cep: str, ctx: Annotated[Contexto, Depends(exige("clientes.editar", "funcionarios.editar"))]
) -> EnderecoDoCep:
    """Endereço do CEP no ViaCEP e o setor da cidade que corresponde ao bairro (para as fichas de cliente e funcionário)."""
    try:
        return EnderecoDoCep.model_validate(servico.consultar_cep(ctx.db, cep), from_attributes=True)
    except servico.CepInvalido as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))
    except servico.CepNaoEncontrado as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except servico.CepIndisponivel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Serviço de CEP indisponível; preencha o endereço à mão")
