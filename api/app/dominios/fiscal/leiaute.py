"""Monta o XML da NFC-e (modelo 65) e da NF-e (modelo 55), leiaute 4.00 (D29).

Só as regras do Simples Nacional, que é o caso de todas as lojas: ICMS pelo CSOSN
(102 ou 500, como no VB6), PIS e COFINS com CST 49 zerados. A natureza e o CFOP vêm de
quem chama. A NF-e leva o destinatário com o endereço; a NFC-e, o QR Code. A assinatura
e o envio ficam em sefaz.py. Funções puras: recebem os dados e devolvem o texto.
"""
import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from xml.sax.saxutils import escape

NS = "http://www.portalfiscal.inf.br/nfe"
UF_GO = "52"
HOMOLOGACAO = "NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"
DEST_HOMOLOGACAO = "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"
# QR Code versão 2 (com o CSC) e a consulta por chave, da SEFAZ de Goiás, por ambiente
QRCODE = {"1": "https://nfe.sefaz.go.gov.br/nfeweb/sites/nfce/danfeNFCe",
          "2": "https://homolog.sefaz.go.gov.br/nfeweb/sites/nfce/danfeNFCe"}
URL_CHAVE = {"1": "www.sefaz.go.gov.br/nfce/consulta", "2": "www.sefaz.go.gov.br/nfce/consulta"}
# os pagamentos que levam o grupo do cartão (sem integração com a maquininha: tpIntegra 2)
_CARTOES = {"03", "04"}


class NotaInvalida(Exception):
    """Falta um dado para montar a nota (o NCM do produto, o endereço da loja...)."""


def novo_codigo_numerico() -> str:
    """O cNF: oito dígitos ao acaso, que entram na chave para ela não ser adivinhada pelo número."""
    return f"{random.randint(1, 99999999):08d}"


@dataclass
class Emitente:
    cnpj: str
    razao_social: str
    nome_fantasia: str | None
    inscricao_estadual: str
    logradouro: str
    numero: str
    complemento: str | None
    bairro: str
    codigo_municipio: str  # IBGE, 7 dígitos
    municipio: str
    uf: str
    cep: str
    telefone: str | None
    crt: str = "1"


@dataclass
class ItemNota:
    codigo: str
    gtin: str | None
    descricao: str
    ncm: str | None
    cest: str | None
    cfop: str
    unidade: str
    quantidade: Decimal
    preco: Decimal
    bruto: Decimal
    desconto: Decimal
    origem: int
    csosn: str


@dataclass
class Destinatario:
    documento: str  # CPF ou CNPJ, só dígitos
    nome: str
    inscricao_estadual: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    codigo_municipio: str | None = None
    municipio: str | None = None
    uf: str | None = None
    cep: str | None = None
    telefone: str | None = None
    email: str | None = None


@dataclass
class PagamentoNota:
    tipo: str  # tPag: 01 dinheiro, 03 crédito, 04 débito, 05 crédito loja, 17 PIX...
    valor: Decimal
    descricao: str | None = None  # xPag, obrigatório no tPag 99 (outros)


@dataclass
class DadosNota:
    emitente: Emitente
    ambiente: str  # 1 produção, 2 homologação
    serie: int
    numero: int
    emissao: datetime
    itens: list[ItemNota]
    pagamentos: list[PagamentoNota]
    outros: Decimal = Decimal("0.00")  # a taxa de entrega
    troco: Decimal = Decimal("0.00")
    destinatario: Destinatario | None = None
    informacoes: str | None = None
    codigo_numerico: str = field(default_factory=novo_codigo_numerico)
    modelo: str = "65"
    natureza: str = "Venda de produtos"
    tipo: str = "1"  # tpNF: 0 entrada, 1 saída
    finalidade: str = "1"  # finNFe: 1 normal, 4 devolução
    destino: str = "1"  # idDest: 1 dentro do estado, 2 para fora


def digito_chave(chave43: str) -> str:
    """Módulo 11 da chave de acesso, pesos de 2 a 9 da direita para a esquerda."""
    soma = sum(int(d) * (2 + i % 8) for i, d in enumerate(reversed(chave43)))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def chave_acesso(uf: str, emissao: datetime, cnpj: str, modelo: str, serie: int, numero: int, tipo_emissao: str,
                 codigo_numerico: str) -> str:
    base = f"{uf}{emissao:%y%m}{cnpj}{modelo}{serie:03d}{numero:09d}{tipo_emissao}{codigo_numerico}"
    return base + digito_chave(base)


def gtin_valido(codigo: str | None) -> bool:
    """GTIN-8, 12, 13 ou 14 com o dígito verificador certo (o que não for vai como "SEM GTIN")."""
    if not codigo or not codigo.isdigit() or len(codigo) not in (8, 12, 13, 14):
        return False
    corpo, digito = codigo[:-1], int(codigo[-1])
    soma = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(corpo)))
    return (10 - soma % 10) % 10 == digito


def _t(valor: object) -> str:
    return escape(" ".join(str(valor).split()))


def _d(valor: Decimal, casas: int = 2) -> str:
    return f"{Decimal(valor):.{casas}f}"


def _tag(nome: str, valor: object | None) -> str:
    return "" if valor is None or valor == "" else f"<{nome}>{_t(valor)}</{nome}>"


def _dest(d: Destinatario, modelo: str, homologacao: bool) -> str:
    tag = "CPF" if len(d.documento) == 11 else "CNPJ"
    nome = DEST_HOMOLOGACAO if homologacao else d.nome[:60]
    endereco = ""
    if modelo == "55":
        endereco = (f"<enderDest>{_tag('xLgr', d.logradouro)}{_tag('nro', d.numero)}{_tag('xCpl', d.complemento)}"
                    f"{_tag('xBairro', d.bairro)}<cMun>{d.codigo_municipio}</cMun>{_tag('xMun', d.municipio)}"
                    f"<UF>{d.uf}</UF><CEP>{d.cep}</CEP><cPais>1058</cPais><xPais>BRASIL</xPais>"
                    f"{_tag('fone', d.telefone)}</enderDest>")
    contribuinte = f"<indIEDest>1</indIEDest><IE>{d.inscricao_estadual}</IE>" if d.inscricao_estadual else "<indIEDest>9</indIEDest>"
    return f"<dest><{tag}>{d.documento}</{tag}>{_tag('xNome', nome)}{endereco}{contribuinte}{_tag('email', d.email)}</dest>"


def montar(dados: DadosNota) -> tuple[str, str]:
    """Devolve a chave de acesso e o XML da nota (sem assinatura e, na NFC-e, sem o grupo do QR Code)."""
    e = dados.emitente
    faltas = [nome for nome, valor in (("o CNPJ", e.cnpj), ("a inscrição estadual", e.inscricao_estadual),
                                       ("a rua", e.logradouro), ("o número", e.numero), ("o bairro", e.bairro),
                                       ("a cidade", e.codigo_municipio), ("o CEP", e.cep)) if not valor]
    if faltas:
        raise NotaInvalida(f"Falta no cadastro da loja: {', '.join(faltas)}")
    sem_ncm = [i.descricao for i in dados.itens if not i.ncm or len(i.ncm) != 8]
    if sem_ncm:
        raise NotaInvalida(f"Produto sem NCM: {', '.join(sem_ncm)}")
    if not dados.itens:
        raise NotaInvalida("A nota não tem itens")
    d = dados.destinatario
    if dados.modelo == "55":
        if d is None:
            raise NotaInvalida("A NF-e precisa do destinatário: escolha o cliente na venda")
        faltas = [nome for nome, valor in (("o CPF ou CNPJ", d.documento), ("a rua", d.logradouro), ("o bairro", d.bairro),
                                           ("a cidade", d.codigo_municipio), ("o CEP", d.cep)) if not valor]
        if faltas:
            raise NotaInvalida(f"Falta no cadastro do cliente {d.nome}: {', '.join(faltas)}")

    chave = chave_acesso(UF_GO, dados.emissao, e.cnpj, dados.modelo, dados.serie, dados.numero, "1", dados.codigo_numerico)
    homologacao = dados.ambiente == "2"
    emissao = dados.emissao.strftime("%Y-%m-%dT%H:%M:%S-03:00")

    nfce = dados.modelo == "65"
    ide = (f"<ide><cUF>{UF_GO}</cUF><cNF>{dados.codigo_numerico}</cNF>{_tag('natOp', dados.natureza[:60])}"
           f"<mod>{dados.modelo}</mod><serie>{dados.serie}</serie><nNF>{dados.numero}</nNF><dhEmi>{emissao}</dhEmi>"
           f"{'' if nfce else f'<dhSaiEnt>{emissao}</dhSaiEnt>'}<tpNF>{dados.tipo}</tpNF>"
           f"<idDest>{dados.destino}</idDest><cMunFG>{e.codigo_municipio}</cMunFG><tpImp>{4 if nfce else 1}</tpImp>"
           f"<tpEmis>1</tpEmis><cDV>{chave[-1]}</cDV><tpAmb>{dados.ambiente}</tpAmb><finNFe>{dados.finalidade}</finNFe>"
           f"<indFinal>1</indFinal>"
           f"<indPres>1</indPres><indIntermed>0</indIntermed><procEmi>0</procEmi><verProc>Piki 1.0</verProc></ide>")
    endereco = (f"<enderEmit>{_tag('xLgr', e.logradouro)}{_tag('nro', e.numero)}{_tag('xCpl', e.complemento)}"
                f"{_tag('xBairro', e.bairro)}<cMun>{e.codigo_municipio}</cMun>{_tag('xMun', e.municipio)}"
                f"<UF>{e.uf}</UF><CEP>{e.cep}</CEP><cPais>1058</cPais><xPais>BRASIL</xPais>"
                f"{_tag('fone', e.telefone)}</enderEmit>")
    emit = (f"<emit><CNPJ>{e.cnpj}</CNPJ>{_tag('xNome', e.razao_social[:60])}{_tag('xFant', (e.nome_fantasia or '')[:60])}"
            f"{endereco}<IE>{e.inscricao_estadual}</IE><CRT>{e.crt}</CRT></emit>")
    dest = _dest(d, dados.modelo, homologacao) if d else ""

    # a taxa de entrega entra como outras despesas, no primeiro item
    dets = []
    for n, item in enumerate(dados.itens, start=1):
        descricao = HOMOLOGACAO if homologacao and nfce and n == 1 else item.descricao[:120]
        gtin = item.gtin if gtin_valido(item.gtin) else "SEM GTIN"
        outros = dados.outros if n == 1 and dados.outros else None
        prod = (f"<prod><cProd>{_t(item.codigo)}</cProd><cEAN>{gtin}</cEAN>{_tag('xProd', descricao)}"
                f"<NCM>{item.ncm}</NCM>{_tag('CEST', item.cest)}<CFOP>{item.cfop}</CFOP>{_tag('uCom', item.unidade)}"
                f"<qCom>{_d(item.quantidade, 4)}</qCom><vUnCom>{_d(item.preco, 4)}</vUnCom><vProd>{_d(item.bruto)}</vProd>"
                f"<cEANTrib>{gtin}</cEANTrib>{_tag('uTrib', item.unidade)}<qTrib>{_d(item.quantidade, 4)}</qTrib>"
                f"<vUnTrib>{_d(item.preco, 4)}</vUnTrib>"
                f"{f'<vDesc>{_d(item.desconto)}</vDesc>' if item.desconto else ''}"
                f"{f'<vOutro>{_d(outros)}</vOutro>' if outros else ''}<indTot>1</indTot></prod>")
        icms = (f"<ICMSSN500><orig>{item.origem}</orig><CSOSN>500</CSOSN></ICMSSN500>" if item.csosn == "500"
                else f"<ICMSSN102><orig>{item.origem}</orig><CSOSN>{item.csosn}</CSOSN></ICMSSN102>")
        zerado = "<CST>49</CST><vBC>0.00</vBC><p{0}>0.0000</p{0}><v{0}>0.00</v{0}>"
        imposto = (f"<imposto><ICMS>{icms}</ICMS><PIS><PISOutr>{zerado.format('PIS')}</PISOutr></PIS>"
                   f"<COFINS><COFINSOutr>{zerado.format('COFINS')}</COFINSOutr></COFINS></imposto>")
        dets.append(f'<det nItem="{n}">{prod}{imposto}</det>')

    produtos = sum((i.bruto for i in dados.itens), Decimal(0))
    descontos = sum((i.desconto for i in dados.itens), Decimal(0))
    total_nota = produtos - descontos + dados.outros
    total = (f"<total><ICMSTot><vBC>0.00</vBC><vICMS>0.00</vICMS><vICMSDeson>0.00</vICMSDeson><vFCP>0.00</vFCP>"
             f"<vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST><vFCPSTRet>0.00</vFCPSTRet>"
             f"<vProd>{_d(produtos)}</vProd><vFrete>0.00</vFrete><vSeg>0.00</vSeg><vDesc>{_d(descontos)}</vDesc>"
             f"<vII>0.00</vII><vIPI>0.00</vIPI><vIPIDevol>0.00</vIPIDevol><vPIS>0.00</vPIS><vCOFINS>0.00</vCOFINS>"
             f"<vOutro>{_d(dados.outros)}</vOutro><vNF>{_d(total_nota)}</vNF></ICMSTot></total>")
    pagamentos = "".join(
        f"<detPag><tPag>{p.tipo}</tPag>{_tag('xPag', (p.descricao or 'Outros')[:60]) if p.tipo == '99' else ''}"
        f"<vPag>{_d(p.valor)}</vPag>"
        f"{'<card><tpIntegra>2</tpIntegra></card>' if p.tipo in _CARTOES else ''}</detPag>"
        for p in dados.pagamentos)
    pag = f"<pag>{pagamentos}{f'<vTroco>{_d(dados.troco)}</vTroco>' if dados.troco else ''}</pag>"
    adicionais = f"<infAdic>{_tag('infCpl', dados.informacoes[:5000])}</infAdic>" if dados.informacoes else ""

    xml = (f'<NFe xmlns="{NS}"><infNFe versao="4.00" Id="NFe{chave}">{ide}{emit}{dest}{"".join(dets)}{total}'
           f"<transp><modFrete>9</modFrete></transp>{pag}{adicionais}</infNFe></NFe>")
    return chave, xml


def qrcode(chave: str, ambiente: str, csc_id: str, csc_token: str) -> str:
    """QR Code da NFC-e emitida on-line, versão 2: chave|2|ambiente|id do CSC|SHA-1 disso com o token do CSC."""
    base = f"{chave}|2|{ambiente}|{int(csc_id)}"
    return f"{QRCODE[ambiente]}?p={base}|{hashlib.sha1((base + csc_token).encode()).hexdigest().upper()}"


def com_qrcode(xml: str, chave: str, ambiente: str, csc_id: str, csc_token: str) -> str:
    """Põe o grupo infNFeSupl (QR Code e endereço da consulta), que vai depois da infNFe e antes da assinatura."""
    supl = f"<infNFeSupl><qrCode>{escape(qrcode(chave, ambiente, csc_id, csc_token))}</qrCode><urlChave>{URL_CHAVE[ambiente]}</urlChave></infNFeSupl>"
    return xml.replace("</infNFe></NFe>", f"</infNFe>{supl}</NFe>")


def danfe_pdf(xml: str, logo: bytes | None = None, cancelada: bool = False) -> bytes:
    """O DANFE da NF-e em folha A4, em PDF (para imprimir e mandar por e-mail)."""
    from brazilfiscalreport.danfe import Danfe, DanfeConfig

    return bytes(Danfe(xml=xml.encode(), config=DanfeConfig(logo=logo, watermark_cancelled=cancelada)).output())


def _texto(elemento, caminho: str) -> str | None:
    achado = elemento.find(caminho, {"n": NS})
    return None if achado is None else achado.text


def danfe(xml: str) -> dict:
    """O que vai no DANFE NFC-e, lido do XML da nota (o que a SEFAZ autorizou, não o que está no banco hoje)."""
    import qrcode
    import qrcode.image.svg
    from lxml import etree

    raiz = etree.fromstring(xml.encode())
    inf = raiz.find(".//n:infNFe", {"n": NS})
    endereco = inf.find("n:emit/n:enderEmit", {"n": NS})
    dest = inf.find("n:dest", {"n": NS})
    texto_qr = _texto(raiz, ".//n:infNFeSupl/n:qrCode")
    svg = (qrcode.make(texto_qr, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=0).to_string(encoding="unicode")
           if texto_qr else None)
    return {
        "emitente": {
            "razao_social": _texto(inf, "n:emit/n:xNome"), "cnpj": _texto(inf, "n:emit/n:CNPJ"),
            "inscricao_estadual": _texto(inf, "n:emit/n:IE"),
            "endereco": ", ".join(t for t in (_texto(endereco, "n:xLgr"), _texto(endereco, "n:nro"),
                                              _texto(endereco, "n:xBairro"), _texto(endereco, "n:xMun"),
                                              _texto(endereco, "n:UF")) if t),
        },
        "itens": [{
            "codigo": _texto(det, "n:prod/n:cProd"), "descricao": _texto(det, "n:prod/n:xProd"),
            "quantidade": _texto(det, "n:prod/n:qCom"), "unidade": _texto(det, "n:prod/n:uCom"),
            "preco": _texto(det, "n:prod/n:vUnCom"), "total": _texto(det, "n:prod/n:vProd"),
        } for det in inf.findall("n:det", {"n": NS})],
        "produtos": _texto(inf, "n:total/n:ICMSTot/n:vProd"), "descontos": _texto(inf, "n:total/n:ICMSTot/n:vDesc"),
        "outros": _texto(inf, "n:total/n:ICMSTot/n:vOutro"), "total": _texto(inf, "n:total/n:ICMSTot/n:vNF"),
        "pagamentos": [{"tipo": _texto(p, "n:tPag"), "descricao": _texto(p, "n:xPag"), "valor": _texto(p, "n:vPag")}
                       for p in inf.findall("n:pag/n:detPag", {"n": NS})],
        "troco": _texto(inf, "n:pag/n:vTroco"),
        "consumidor": None if dest is None else {
            "documento": _texto(dest, "n:CPF") or _texto(dest, "n:CNPJ"), "nome": _texto(dest, "n:xNome")},
        "numero": _texto(inf, "n:ide/n:nNF"), "serie": _texto(inf, "n:ide/n:serie"),
        "emissao": _texto(inf, "n:ide/n:dhEmi"), "ambiente": _texto(inf, "n:ide/n:tpAmb"),
        "chave": inf.get("Id", "")[3:], "url_consulta": _texto(raiz, ".//n:infNFeSupl/n:urlChave"),
        "protocolo": _texto(raiz, ".//n:protNFe/n:infProt/n:nProt"),
        "autorizada_em": _texto(raiz, ".//n:protNFe/n:infProt/n:dhRecbto"),
        "qrcode": texto_qr, "qrcode_svg": svg,
        "informacoes": _texto(inf, "n:infAdic/n:infCpl"),
    }
