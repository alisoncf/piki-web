# Decisões de arquitetura

Registro curto das decisões tomadas e do que ainda está em aberto. Quando uma decisão mudar, não apague: marque como substituída, diga por qual e anote a data. O histórico explica por que o código está como está.

## Vigentes

### D1. Repositório separado do legado (30/10/2026)

O VB6 continua em `alisoncf/piki_vb`, intacto. O sistema novo começa aqui, com histórico limpo. O legado tem senhas, logs e dumps no histórico, e o `piki_Simples.vbp` depende de caminhos relativos entre pastas que não podem ser reorganizadas.

### D5. Fiscal continua no ACBrMonitor PLUS (30/10/2026)

NF-e e NFC-e já são emitidas pelo ACBrMonitor. A API nova envia os mesmos comandos (por TCP, em vez de `ent.txt`/`sai.txt`) e não reimplementa a comunicação com a SEFAZ.

### D8. Esquema novo, alimentado por ETL a partir das filiais (30/10/2026)

O sistema novo tem banco e esquema próprios, desenhados para várias empresas desde o começo: InnoDB/transações, chaves estrangeiras, `DECIMAL` para valores, nomes claros. Não herdamos a estrutura do VB6.

Cada filial tem hoje seu próprio banco local. Os dados chegam ao banco novo assim:

1. **Agente em cada filial:** programa pequeno que faz o dump do banco local e envia para o servidor central por HTTPS (só conexão de saída, sem abrir porta na loja).
2. **Área de chegada:** cada dump é carregado como está, num esquema separado por filial (`legado_f01`, `legado_f02`...).
3. **ETL:** lê cada área de chegada e grava no esquema novo, deduplicando cadastros e mapeando (empresa, código antigo) → id novo. É repetível: rodar de novo atualiza o que existe e insere o que é novo.

Enquanto o VB6 estiver em uso, ele é o sistema oficial e o ETL roda todo dia, em mão única. O sistema novo já serve para consultas e relatórios consolidados. A virada é por filial: quando as telas que uma filial usa estiverem prontas, ela passa a gravar no sistema novo e deixa de enviar dumps.

As senhas antigas são reversíveis (`F_GeraPW`/`F_RetornaPW`), então o ETL as converte para hash argon2 na importação. A conferência de senha no formato antigo existe só no ETL (`api/etl/senha_legado.py`), nunca na API.

### D9. Escopo dos dados entre empresas (30/10/2026)

Cada filial é uma **empresa** (CNPJ próprio). Os dados se dividem em três escopos:

| Escopo | Exemplos | Regra |
|---|---|---|
| Global | clientes, produtos (cadastro), fornecedores, seções, formas de pagamento | Um cadastro só, visível em todas as empresas |
| Por empresa | estoque, ~~preço e custo do produto~~ (D24: são do produto), notas fiscais de entrada e saída, vendas, caixa, inventário | Cada registro pertence a uma empresa; só aparece nela |
| Por empresa, visível em todas | contas a receber (documentos e parcelas) | O documento pertence à empresa que vendeu, mas pode ser consultado e recebido em qualquer empresa. A baixa registra em qual empresa e em qual caixa o dinheiro entrou |

Na prática: o cliente pode pagar o boleto ou a parcela em qualquer loja, e o caixa de quem recebeu é que registra a entrada.

### D10. Acesso: usuário, empresa e perfil (30/10/2026)

- Um **usuário** pode ter acesso a uma ou várias empresas. A relação usuário–empresa diz também **o que ele pode fazer ali**, por meio de um **perfil** (conjunto de permissões, por exemplo "Caixa", "Gerente", "Financeiro").
- O mesmo usuário pode ter perfis diferentes em empresas diferentes (gerente na 01, só consulta na 02).
- No login, o usuário escolhe a empresa. Se só tem acesso a uma, ela é escolhida automaticamente. Ele pode **trocar de empresa** a qualquer momento sem sair do sistema.
- O token de login carrega o usuário e a empresa ativa. As permissões são conferidas no banco a cada requisição, então uma permissão retirada vale na hora.
- Usuário marcado como administrador tem acesso total a todas as empresas.
- As permissões são códigos no formato `area.acao` (por exemplo `clientes.editar`, `caixa.abrir`), definidos no código e cadastrados no banco.

### D11. Back-end organizado por domínio (30/10/2026)

Cada domínio (acesso, cadastros, financeiro...) tem sua pasta em `api/app/dominios/`, com:

- `modelos.py`: tabelas (SQLAlchemy)
- `esquemas.py`: formatos de entrada e saída da API (Pydantic)
- `repositorio.py`: consultas ao banco
- `servico.py`: regras de negócio, sem depender de HTTP
- `rotas.py`: endpoints, que só recebem, chamam o serviço e devolvem

O que é comum a todos (banco, segurança, dependências de login e empresa) fica em `api/app/nucleo/`. A estrutura do banco é versionada com Alembic (`api/alembic/`).

### D12. PostgreSQL no servidor central (30/10/2026)

O banco do sistema novo é PostgreSQL (16 ou mais recente). As filiais continuam com MariaDB enquanto o VB6 estiver em uso; o ETL lê do MariaDB e grava no PostgreSQL.

Motivos: *row-level security* para isolar as empresas no próprio banco (uma consulta que esqueça o filtro de empresa é barrada pelo banco), migrações de estrutura transacionais (uma migração que falha não deixa o banco pela metade), `INSERT ... ON CONFLICT` e consultas analíticas maduras para o ETL e os relatórios consolidados, e tipos rígidos que obrigam o ETL a tratar as datas `0000-00-00` e textos fora do tamanho do banco antigo.

Para desenvolver: `docker compose up -d` sobe o PostgreSQL com os bancos `piki` e `piki_teste`. Sem banco configurado, a API e os testes usam SQLite.

### D13. Front-end: Vue 3 + Quasar + Pinia, com Vite (30/10/2026)

O front fica em `web/` e chama a API em `/api`; em desenvolvimento o Vite repassa para a API, em produção o servidor web fará o mesmo (mesma origem, sem CORS). A sessão (usuário, empresa ativa, empresas e permissões) fica numa store Pinia. Rotas e itens de menu declaram a permissão que exigem, com os mesmos códigos da API. Ao trocar de empresa, a tela atual é recarregada com os dados da nova empresa.

O token de login fica no `localStorage`, para durar o turno mesmo fechando a aba. Ver P11.

### D14. Identidade visual: a marca da loja, com o Piki como assinatura (30/10/2026)

Quem usa o sistema é a equipe da Requinte Enxovais, então a marca da loja aparece no login, no cabeçalho e na escolha de empresa, e as cores vêm do logo dela: ameixa `#941d70` como cor principal e o dourado do ícone do Piki (`#f2b01e`) como destaque. O Piki é o sistema: o ícone dele vai no favicon e como assinatura discreta ("Piki · gestão comercial") no login e no menu. Fonte Inter, instalada no próprio projeto (não depende de internet nas filiais).

Nome e logos ficam em `web/src/marca.js` e `web/public/`; as cores, só em `web/src/css/quasar.variables.scss` (os tons de apoio de `app.css` são derivados delas). Por enquanto a marca é fixa para todas as empresas (ver P12).

Cada empresa tem uma **cor de identificação**, para o funcionário saber em que loja está: aparece numa faixa no topo do cabeçalho, no selo da empresa, numa tintura leve do menu lateral, e o nome da loja vai para a aba do navegador. Botões e links continuam na cor da marca. ~~A cor sai de uma paleta fechada de 8; muda pela linha de comando (`cor-empresa`)~~. Substituído pela D19 em 01/11/2026.

### D15. Clientes, setores e órgãos unificados a partir dos bancos das lojas (30/10/2026)

Cliente é um só para todas as lojas (D9), e setores (bairros e regiões de cobrança), órgãos (onde o cliente trabalha) e grupos de clientes também passam a ser uma lista só. No VB6 cada loja criava os seus, e os mesmos códigos significam coisas diferentes em cada banco.

- **Fonte:** o ETL lê a `tab_clientes` e as tabelas ligadas de cada loja. O cadastro unificado que já existe no piki.app.br (sincronizado pelo VB6) não é usado: ele vai ser substituído pelo sistema novo.
- **Mesmo cliente:** mesmo CPF/CNPJ válido. Sem documento válido, o cliente fica como cadastro próprio daquela loja, sem juntar pelo nome, com aviso para conferência.
- **Quem manda nos dados:** o registro com a data de alteração mais recente (`dataalt_cli`, ou `data_cli` se estiver vazia). Os outros só preenchem campos vazios e acrescentam telefones e referências.
- **Setores e órgãos:** juntados pelo nome (setor: nome + cidade). ~~O cobrador do setor é escolhido por loja (`setor_cobrador`).~~ Substituído pela D16 em 31/10/2026.
- **Códigos antigos:** cada código de cada loja (`cod_cli`, `cod_set`, `cod_org`, `cod_gru`) fica no `legado_mapa`, apontando para o registro novo. É por ele que as vendas e contas antigas vão ser ligadas.
- **Listas fixas e tabelas:** vira tabela o que a loja pode aumentar (grupos, setores, órgãos, parentescos). O que o sistema usa para decidir fica fixo no código: a forma de cobrança (`domicilio`, `trabalho`, `loja`, que diz em qual setor cobrar) e o bloqueio do cliente (`bloqueado`), porque um valor novo numa tabela não ensinaria o programa o que fazer com ele.
- **Endereço:** o certo no VB6 é o `logradouro` (com `numero` e `complemento`); a `endereco_cli` é o campo antigo.
- **Sem documento válido:** depois que vendas e contas forem importadas, os clientes sem CPF/CNPJ válido e sem nenhum movimento serão excluídos.
- **Carga final:** as cópias locais servem para montar e testar. A carga de verdade será refeita direto nos bancos das lojas, por um túnel, antes da virada.

### D16. Setor numa cidade do IBGE, cobradores para todas as lojas (31/10/2026)

Correção do Alison sobre a D15.

- **Cidades:** tabela `cidade` com os 5.571 municípios do IBGE (código, nome com acentos, UF), carregada pela migração 0008 a partir de `api/alembic/referencia/municipios_ibge.csv` (API de localidades do IBGE). O setor aponta para uma cidade (`setor.cidade_id`), escolhida numa lista, não digitada. O nome que estava na `tab_cidades` de cada loja é cadastro antigo e não é usado: o ETL acha a cidade pelo `cod_mun` (código do IBGE) ou, sem ele, pelo nome. Setor novo ou alterado precisa de cidade; os antigos sem cidade ficam assim até alguém escolher uma.
- **Cobradores:** ~~tabela `cobrador` (a `tab_contacob` do VB6), uma lista só para todas as lojas~~. Substituído pela D17 em 31/10/2026.

### D17. Cobrador é funcionário; cliente sem cidade própria (31/10/2026)

Decisão do Alison.

- **Cobrador:** é um funcionário (o `cobrador_set` do VB6 guarda o código do funcionário). Não há tabela de cobradores. Um setor pode ter vários cobradores e um cobrador pode cobrar vários setores, sem loja (`setor_cobrador` com `setor_id` e `funcionario_id`). Setor sem cobrador não é problema.
- **Cidade do cliente:** o cliente não tem cidade nem UF digitadas. Ele está num setor, e a cidade é a do setor, que é sempre uma cidade do IBGE (D16). O mesmo vale para o órgão.
- **Bairro:** também é o setor. O campo de bairro do cliente era de antes dos setores e saiu.
- **Funcionário:** o endereço segue a mesma regra: logradouro e CEP digitados, bairro e cidade pelo setor (`funcionario.setor_id`). No VB6 o `cod_set` da `tab_funcionarios` existe, mas está vazio (`00000`) nos três bancos.

### D18. Endereço pelo CEP (31/10/2026)

Decisão do Alison.

- Nas fichas de cliente (casa e trabalho) e de funcionário, um botão ao lado do CEP busca o endereço no ViaCEP pela API (`GET /cep/{cep}`). O cadastro nunca depende do ViaCEP: CEP não encontrado ou serviço fora só gera um aviso.
- A rua vem do CEP. Se já havia uma rua digitada diferente, a tela pergunta antes de trocar.
- O setor é procurado entre os setores ativos da cidade do CEP (pelo código do IBGE), comparando o nome sem acentos, com as abreviações comuns (Jd, Vl, St, Res, Pq) e com o tipo do setor na frente. Um setor igual é escolhido sozinho; sem igual, a tela mostra os parecidos para escolher.
- O bairro do CEP que não existe como setor pode ser cadastrado ali mesmo como setor novo da cidade, por quem pode editar clientes.

### D19. Cadastro de empresas com esquema de cores (01/11/2026)

Decisão do Alison.

- **Tela:** Acesso › Empresas (permissão `acesso.empresas`), com lista e ficha. Os dados vêm da `sped_empresa` pelo ETL; as empresas 04 e 05 serão cadastradas pela tela. O código (01 matriz, 02 Jundiaí Casa, 03 La Viva) é dado na criação e não muda depois, porque o ETL usa o código para saber de onde veio cada dado. As empresas são um domínio próprio (`app/dominios/empresas`), separado do acesso.
- **Esquema de cores:** cada empresa tem um `tema` com três cores, que o administrador escolhe na ficha: `principal` (faixa do cabeçalho, selo, troca de empresa), `fundo` (fundo das telas) e `menu` (menu lateral). O esquema é aplicado ao entrar ou trocar de empresa. Botões e links continuam na cor da marca (D14). A ficha tem prévia e um botão que gera fundo e menu a partir da cor principal. Empresa sem esquema recebe um automático pelo código.
- **Endereço:** a cidade é uma cidade do IBGE (lista, como no setor); o bairro é texto, porque setor é região de cobrança de clientes. O CEP busca rua, bairro e cidade (D18).
- **Imagens:** o logo dos relatórios e o QR code do boleto de cobrança (no VB6, `caminho_logo` e `caminho_qrcodedoc`, caminhos de arquivo na loja) são enviados na ficha e guardados no banco (`empresa_imagem`), em PNG ou JPEG de até 1 MB. Qualquer usuário logado pode lê-los, porque saem em relatórios e boletos.
- **Fica de fora:** certificado digital, senha, CSC e token da NFC-e (P10). `cpf` e `fax` da `sped_empresa` não são usados.

### D20. Documentos digitais do cliente para o crediário (01/11/2026)

Decisão do Alison.

- Na ficha do cliente, a seção **Documentos** recebe arquivos (PDF, JPEG ou PNG, até 5 MB) ou fotos tiradas na hora pela câmera do celular ou tablet. As fotos são reduzidas no navegador (1600 px, JPEG) antes de enviar.
- Tipos: identidade (RG ou CNH), CPF, comprovante de endereço, comprovante de renda, ficha ou contrato de crediário assinado, foto do cliente e outro. Cada um com descrição opcional (frente, verso...) e vários arquivos por tipo. Documento não vence.
- **LGPD:** só quem trabalha com crediário vê e envia, pela permissão `clientes.documentos`, separada de `clientes.ver`. Remover pede também `clientes.editar`, e só tira da lista: o arquivo e o registro ficam, com quem removeu e quando. O navegador não guarda cópia dos arquivos (`Cache-Control: no-store`).
- O documento é do cliente (cadastro global): todas as lojas veem; fica registrado quem enviou e de qual loja.
- A falta de documentos não bloqueia a venda a prazo.
- **Onde ficam os arquivos:** fora do banco, numa pasta do servidor (padrão) ou num MinIO, escolhidos no `.env` (`PIKI_ARQUIVOS`); o banco guarda só a chave (`app/nucleo/arquivos.py`). A pasta precisa entrar no backup.

### D21. Clientes sem CPF/CNPJ válido ou com nome sem sentido ficam de fora (01/11/2026)

Decisão do Alison.

- Na importação do VB6, não entram clientes sem CPF/CNPJ válido nem com nome sem sentido (vazio, sem letras, "TESTE", um endereço no lugar do nome). Vale para todas as lojas e continua valendo nas reimportações.
- A exceção é quem tem parcela de crediário em aberto na loja (`tab_itdoc.reman_itd` > 0): fica, para não perder a dívida, e a ficha avisa que o CPF precisa ser corrigido.
- Os que já tinham sido importados foram excluídos. Fica o cliente que veio também de outra loja ou que já tem documentos enviados no sistema novo.
- Erros de digitação no nome são corrigidos na importação: zero no lugar da letra O ("D0S SANTOS") e pedaços de endereço no fim ("N.470", "Q 3 L 2").
- Continua mandando o cadastro alterado por último, de qualquer loja (D15). A exceção é o cadastro repetido com nome sem sentido (o "+" que marcava o cadastro velho de quem foi recadastrado com o mesmo CPF): ele nunca manda, mesmo sendo o alterado por último, e fica só o cadastro bom (02/11/2026).
- Na importação de vendas, parcelas e documentos, o cliente é procurado pelo CPF do cadastro do VB6 quando o código dele não estiver no mapa (caso dos cadastros descartados que tinham o mesmo CPF de outro).
- Resultado em 01/11/2026, com o `requinte` atualizado: de 80.657 clientes ficaram 56.000. Saíram 921 da matriz, 1.125 da Jundiaí e 23.272 da La Viva (quase nenhum cliente de lá tem CPF). Ficaram 184 sem CPF válido, todos da matriz, por terem parcela em aberto.

### D22. Cadastro de fornecedores (02/11/2026)

Decisão do Alison.

- O nome é "fornecedores" (e não "participantes", que é o termo do SPED). É um cadastro só para todas as lojas (D9), e serve também para transportadoras, sem marcação: os dados são os mesmos.
- Todo fornecedor tem CPF ou CNPJ válido, que não se repete. Quem não tem fica de fora da importação; pessoa física (com CPF) é aceita.
- O endereço é como o da empresa: CEP com busca, cidade da lista do IBGE e bairro digitado (o setor é região de cobrança de clientes).
- A ficha tem os telefones da empresa e uma lista de contatos (nome, função, telefone e e-mail), porque o representante e o financeiro costumam ser pessoas diferentes.
- Na ficha, a lupa do CNPJ busca na BrasilAPI (pública, sem chave) a razão social, o fantasia, o endereço, o telefone e o e-mail. Com maiúscula só nas iniciais, porque a Receita escreve tudo em maiúsculas. O que já estava preenchido só é trocado se a pessoa confirmar; se o CNPJ já é de um fornecedor, a ficha oferece abrir o cadastro dele.
- Na importação, a `tab_fornecedores` não tem data de alteração: manda a loja de menor código que tem o fornecedor (a matriz, quando ela tem). As outras só preenchem o vazio e somam telefones e contatos.
- A ficha é de página única com índice, como a do cliente.
- Resultado em 02/11/2026: 267 fornecedores, a partir de 338 (matriz), 325 (Jundiaí) e 319 (La Viva) cadastros; 193 descartados por não terem CPF/CNPJ válido (ou nome). 214 ficaram com cidade; os outros têm a cidade escrita de um jeito que não deu para reconhecer.

### D23. Usuários, perfis e senhas (02/11/2026)

Decisão do Alison.

- O usuário pode ser ligado a um funcionário (no VB6 todo usuário era um funcionário). A ligação é opcional, para caber o administrador e quem é de fora, como o contador. Na ficha do usuário, o nome e o login vêm do funcionário escolhido.
- As permissões são só por perfil, sem exceções por usuário: quem precisa de algo diferente ganha outro perfil. Os níveis do VB6 viraram os perfis Operador, Supervisor, Gerente e Gestor, criados sem permissões; elas são marcadas na tela de perfis. As marcações por usuário da `tab_defusu` não foram importadas. Os limites de desconto vão para o perfil quando chegarem as vendas.
- O administrador mexe em tudo. Quem cuida de usuários sem ser administrador (o gerente da loja):
  - só dá acesso à empresa em que está;
  - só dá perfis que não tenham permissões que ele mesmo não tem (como o "não dar nível maior que o seu" do VB6);
  - não mexe em administradores, em usuários só de outras empresas nem no próprio acesso;
  - num perfil, não acrescenta permissões que não tem (tirar pode).
- Quem cadastra define uma senha provisória, e o usuário é obrigado a trocar no primeiro login: até trocar, a API só aceita a troca de senha. Para quem esqueceu, o administrador ou o gerente define outra provisória. A senha tem no mínimo 8 caracteres. Depois de trocada, diferencia maiúsculas de minúsculas, mesmo a de quem veio do VB6.
- Na quinta senha errada seguida, o login fica bloqueado por 15 minutos. O administrador ou o gerente pode desbloquear antes (a senha provisória também desbloqueia).
- Na importação, entram só os usuários ativos de funcionários ativos, com a senha do VB6 como provisória. Vendas e outros movimentos de quem não está mais ativo continuam ligados ao funcionário.
- O usuário ganhou e-mail, para a recuperação de senha por e-mail, que vai ser feita depois. A autenticação em dois fatores também fica para depois.
- Resultado em 02/11/2026: 50 usuários novos (40 da matriz, 4 a mais da Jundiaí e 6 a mais da La Viva) e o administrador, que foi ligado ao funcionário dele; 74 acessos. 7 estavam sem senha no VB6 e precisam de uma provisória.

### D24. Produtos e estoque (02/11/2026)

Decisão do Alison. Substitui o trecho da D9 que punha preço e custo por empresa.

- **Cadastro único, mantido pela matriz.** Já é assim no VB6: as outras lojas recebem os produtos da matriz, com os mesmos códigos. O código do VB6 (`cod_pro`) continua sendo o código do produto e o código de barras interno (impresso com 8 dígitos).
- **Preço e custo são do produto**, iguais em todas as lojas. Mudar custo, margem e preços pede a permissão `produtos.precos` (no VB6, a marcação "altera preço" do usuário).
- **Sem grade.** Cada tamanho ou cor é um produto, com o nome completo e o seu código de barras, como as lojas trabalham hoje.
- **Classificação:** seção › subseção, como no VB6. A **marca** (quem fabrica) é separada do **fornecedor** (de quem a loja compra). O produto pode ter vários fornecedores, cada um com o código que ele usa para o produto, para ligar o item da nota de entrada ao produto.
- **Unidade e fração:** a marcação "aceita fração" diz se o produto pode ser vendido com quantidade quebrada (passadeira por m²).
- **Fotos:** várias por produto; a primeira é a principal.
- **Preço de queima** continua como um campo do produto. O preço de atacado sai (não há venda em atacado). A sugestão de preço pela margem será revista na entrada de notas.
- **Estoque por loja**, numa tabela própria (próximo passo): quantidade, reservado (consignação) e localização. Só um estoque: o fiscal passa a ser o real. Os movimentos (venda, entrada, envio e devolução de consignação, acerto, ajuste, inventário) ficam registrados; estoque negativo é permitido, com aviso.
- **Impostos:** NCM, CEST e origem ficam no produto; o que depende do regime de cada empresa (CST/CSOSN, CFOP, alíquota de ICMS) fica no estoque de cada loja.
- **Transferência entre lojas** não existe: tem que ser por nota, como uma remessa (fica para o fiscal).
- **Saldo inicial:** o estoque de cada loja vai ser montado a partir do último inventário (31/12/2025), com as notas de saída e as entradas desde então. Fica para o passo do estoque.
- **Importação:** só do banco da matriz. Inativo o produto sem venda, compra, cadastro ou alteração no último ano (em qualquer loja). Restos de farmácia do VB6 (princípio ativo, controle, fabricante, gênero, combustível, balança) e o preço de atacado não vêm.
- Resultado em 02/11/2026: 13.474 produtos (6.689 ativos), 11 seções, 67 subseções, 1.703 códigos de barras de fábrica, 11.609 com fornecedor. 1.379 produtos ficaram sem fornecedor porque o fornecedor do VB6 não tem CNPJ válido (Karsten, Coteminas, Buchara...); o Alison vai corrigir os CNPJs no VB6 para reimportar.
- **Estoque na ficha do produto** (02/11/2026): a ficha mostra o estoque da loja ativa (em estoque, com representantes e disponível), a localização e os impostos da loja, o ajuste de quantidade (com motivo) e o histórico. Quantidade é tudo o que é da loja, inclusive o que está com os representantes; o reservado é a parte que está com eles. As permissões são `estoque.ver`, `estoque.editar` (localização e impostos) e `estoque.ajustar`.
- **Saldo importado:** o fiscal do VB6 (`ef_pro`) e, como reservado, o que falta acertar das consignações (a mesma conta que o VB6 usa para refazer o `r_pro`). Resultado em 02/11/2026: matriz com 7.648 produtos com saldo (2.337 negativos), Jundiaí com 3 (o estoque dela está zerado na cópia) e La Viva com 3.685 (1.337 negativos; 120 códigos que lá são outro produto ficaram de fora). As cópias da Jundiaí e da La Viva estão antigas e serão importadas de novo.

### D25. Entrada de notas pelo XML (02/11/2026)

Decisão do Alison: a entrada é pelo XML da NF-e, e a nota tem que ser da empresa. Os demais pontos foram propostos e ficam valendo até os XMLs reais mostrarem outra coisa.

- **Carregar:** o XML (NF-e modelo 55) só entra na empresa do destinatário, e uma nota (pela chave) só entra uma vez; a repetida abre a que já existe. O XML fica guardado no armazenamento de arquivos.
- **Fornecedor:** achado pelo CNPJ do emitente; se não existe, é cadastrado com os dados do XML (a tela avisa).
- **Itens:** cada item é ligado sozinho a um produto, pelo código do produto no fornecedor ou pelo código de barras. Enquanto a nota está aberta, isso é refeito toda vez que ela é aberta, então o produto cadastrado antes da entrada (como a pessoa do estoque costuma fazer) aparece ligado. O item sem produto tem um atalho que abre a ficha de produto nova já preenchida (nome, NCM, CEST, EAN, fornecedor e código) e volta para a nota ao salvar; ou pode ser ligado a um produto existente.
- **Embalagem:** quantas unidades do produto vêm em cada unidade da nota (caixa com 12). Fica na ligação do produto com o fornecedor e é lembrada na próxima nota.
- **Custo:** produtos − desconto + frete, seguro, outras despesas, IPI e ST do item, dividido pelas unidades. Ao confirmar, passa a ser o custo do produto (o custo da última nota, como no VB6).
- **Preço:** a tela mostra o preço pela margem do produto; o preço novo é opcional, item por item, e pede `produtos.precos`.
- **Confirmar:** de uma vez, só com todos os itens ligados. Cada item vira um movimento "Entrada" no estoque da loja, com o número da nota; a ligação (código e embalagem do fornecedor) e o código de barras da nota ficam na ficha do produto. A nota aberta pode ser descartada.
- Permissões: `entradas.ver` e `entradas.lancar`.
- Ficam para depois: buscar as notas direto na SEFAZ (com o certificado), devolução ao fornecedor e o SPED.

### D26. Vendas, formas de pagamento e caixa (02/11/2026)

Decisão do Alison. Vendas vão em etapas: (1) formas de pagamento e caixa, (2) venda, (3) crediário, (4) NFC-e, (5) trocas, cancelamento, entrega e cartão presente, (6) importação do histórico.

**Venda (regras para a etapa 2)**
- O vendedor monta a venda no balcão e o caixa recebe.
- O desconto vem da forma de pagamento escolhida (os 5% à vista), até o limite do perfil; acima, pede a senha de quem pode mais, e fica registrado quem autorizou. Parcelas acima do limite da forma também pedem a gerência.
- O desconto pode ser dado no item ou no total, mas é a mesma coisa: o do total é rateado entre os itens, e cada item guarda por quanto foi vendido de fato.
- A venda aberta vence em 10 dias.
- Cartão: registra o número de parcelas; a baixa vem depois, pelo extrato da financeira. O pagamento integrado (TEF, por um intermediário) fica para uma etapa própria.
- Crediário: cliente cadastrado, sem bloqueio e dentro do limite; o carnê sai na hora.
- Toda venda gera a NFC-e e um canhoto para retirar o produto no pacote; há impressora térmica e impressora comum. A impressão usa a janela de impressão do navegador (sem programa instalado no caixa).
- Histórico: importar todas as vendas do VB6 (ou os últimos 10 anos, se ficar lento).

**Como a venda ficou (etapa 2, 02/11/2026)**
- Cada perfil tem o seu "desconto máximo na venda" (%), na tela de perfis; o administrador vai até 100%. No VB6 o limite era por usuário (`tab_defusu.desconto_usu`); não foi importado: os valores vão ser dados nos perfis.
- O desconto permitido é o maior entre o da forma de pagamento, o do perfil de quem está vendendo e o de quem já autorizou na venda. Acima disso, a tela pede o login e a senha de alguém com limite maior, e a venda guarda quem autorizou. Parcelas acima do "sem autorização" da forma pedem alguém com a permissão `vendas.autorizar`.
- Ao escolher (ou trocar) a forma, o desconto dela vale para todos os itens, substituindo o que havia. O desconto no total, em % ou em reais, é rateado pelo valor de cada item (os centavos que sobram vão no maior); o item que entra depois leva o mesmo %. O desconto também pode ser dado direto no item.
- O preço do item é o de queima, quando o produto tem; senão, o de venda.
- ~~Uma forma de pagamento por venda~~. Substituído em 02/11/2026: a venda tem a forma que dá o desconto, e no caixa o cliente paga em uma ou mais formas (ver "Recebimento no caixa").
- A venda aberta não reserva estoque; a baixa acontece quando o caixa recebe, e o estoque pode ficar negativo, com aviso. O recebimento lança a entrada no caixa (motivo "venda"), que só é desfeita pela venda.
- Numeração própria por loja. A venda aberta pode ser cancelada com o motivo; a recebida, só pela devolução (etapa 5).
- Permissões: `vendas.ver`, `vendas.vender` e `vendas.autorizar`; quem recebe precisa de `caixa.operar`.

**Recebimento no caixa (02/11/2026)**
- Pedido do Alison. O computador fica no caixa: quem entra num caixa aberto (ou o abre) deixa aquele computador nele, e as vendas são recebidas ali sem escolher o caixa. O caixa aparece no cabeçalho, com "Sair do caixa neste computador"; fechar o caixa tira o computador dele. Fica guardado no navegador, por loja.
- A tela de recebimento é própria (o "troco" do VB6). O caixa da loja abre as vendas fechadas direto nela.
- **Trocar a forma no caixa:** o cliente pode mudar de ideia (era crédito, vai no débito ou no PIX). Se o desconto da forma nova é outro, ele vale para todos os itens e o desconto que tinha sido dado sai, com aviso (o VB6 também cancelava o desconto); se é o mesmo, o desconto fica. As parcelas do crediário também podem mudar ali, com as mesmas autorizações.
- **Várias formas:** o cliente paga em uma ou mais formas (um pouco no PIX, um pouco no cartão), e cada uma entra no caixa na sua forma. Fora do crediário, o lançado tem de fechar o total; o troco é só do dinheiro (o que o cliente deu menos o que ficou no dinheiro). No cartão de crédito, cada pagamento tem suas parcelas, com a autorização acima do limite da forma.
- **Nota:** o caixa escolhe NFC-e (modelo 65, o normal) ou NF-e (modelo 55, pede o cliente cadastrado com CPF ou CNPJ). Por enquanto só fica guardado na venda; a emissão é a etapa 4.
- Do troco do VB6, respondido pelo Alison em 02/11/2026: o desconto gerencial (acima do limite do funcionário e da forma) é o da tela da venda, com autorização, e não vai para o recebimento. O "cliente promocional" (venda sem nota) não precisa. Reorganizar as parcelas do carnê e o tipo de cobrança são possíveis, mas em outra tela, depois. Ficam para depois também o vale de funcionário e o cartão presente (etapa 5).
- NF-e e NFC-e: o Alison vai mostrar a tela de hoje (lista das notas transmitidas e não transmitidas, com as configurações). As tabelas do VB6 para notas são complexas; a ideia é simplificar no sistema novo. Fica para a etapa 4, com cuidado próprio.

**Tela de contas a receber (02/11/2026, primeira parte)**
- Pedido do Alison: a tela do VB6 (`frmEditaMov`, "Movimentações") filtra as parcelas, e a lista que sai é o que se baixa. Menu Financeiro › Contas a receber, com a permissão `receber.ver`; mostra as parcelas de todas as lojas (D9).
- Filtros que já existem: em aberto, já pagas ou todas; cliente (nome ou CPF); documento (01-0000777 ou só o número); loja; espécie (venda, acerto de consignação, avulsa); data de vencimento, de vencimento inicial (o de antes das prorrogações) ou de emissão, de/até; valor exato do que falta; histórico; cidade, setor, órgão e grupo do cliente; cliente bloqueado ou liberado; crédito suspenso. Ordena por vencimento, cliente, documento ou valor. Mostra quantas são, o valor e o que falta da consulta toda, e a soma das selecionadas.
- **Baixar:** as selecionadas, de um cliente só (como na baixa do VB6), vão para a tela "Receber crediário" já marcadas. Lá dá para **distribuir um valor**: o que o cliente trouxe paga as parcelas da mais antiga para a mais nova, e os juros sugeridos somam à parte (como o "Distribuir" do VB6).
- Desconto na baixa (Alison, 03/11/2026): é só nos juros, e os juros já são só sugeridos (o caixa muda). Não há desconto no valor da parcela.
- Ficam para depois: tipo de cobrança, baixa para o financeiro (conta bancária) em vez do caixa, boleto, SPC, prorrogação, editar e criar parcela, excluir documento, histórico de baixas da parcela, recibo, exportar e imprimir a lista, representantes e funcionários.

**Prejuízo (03/11/2026)**
- Explicação do Alison: o prejuízo marca a parcela que não se vai mais receber (o cliente morreu, não foi achado, a cobrança tentou de todo jeito e desistiu). Ela deve ser esquecida como algo que se pode receber.
- A parcela guarda quando caiu no prejuízo, quem pôs e o motivo (obrigatório). Pôr e tirar pede a permissão `receber.prejuizo` (no VB6 era a de excluir documento, com senha); vale para várias selecionadas de uma vez.
- Sai da lista do contas a receber e das somas, como no VB6; o filtro "Prejuízo" mostra só elas, ou junto com as outras.
- O cliente continua devendo: se pagar um dia, a parcela aparece (marcada) na tela de receber e é recebida normalmente. Também continua contando no limite do crediário, como no VB6, e a venda mostra quanto do em aberto está no prejuízo. Confirmado pelo Alison em 03/11/2026; o cliente que atrasa um tempo é bloqueado, mas à mão (não há bloqueio automático).
- No VB6 a marca `prejuizo_itd` quase não foi usada (8 parcelas na matriz). O prejuízo de verdade é a conta de cobrança chamada PREJUIZO (na matriz, 14.269 parcelas, R$ 1,21 milhão; na 03, 717; na 02, 38). O ETL trata as duas como prejuízo, com o motivo dizendo de onde veio; a reimportação só marca, e tirar é pela tela.

**Importação das contas a receber do VB6 (02/11/2026)**
- `python -m etl receber`, por loja, depois dos clientes e usuários. Entram os documentos a receber de clientes com alguma parcela em aberto, com todas as parcelas (as pagas também, para o carnê continuar "3 de 5"). Os de representantes e de funcionários ficam para a consignação e os vales; o ETL só mostra o total deles.
- **Números repetidos entre as lojas** (pedido do Alison): o seq_doc, o seq_itd e o num_doc do VB6 são sequências de cada loja. A ligação com o VB6 fica no `legado_mapa` por loja (`tab_doc` e `tab_itdoc`), e a conta guarda o num_doc, sempre mostrado com o código da loja: 01-0000777 e 02-0000777 são contas diferentes.
- A origem vem do `esp_doc`: venda (V), acerto de consignação (A) ou avulsa. Todas contam no limite do cliente, como no VB6.
- Reimportar atualiza o que falta, o vencimento e o valor das parcelas já importadas (inclusive as quitadas depois no VB6), menos as que já tiveram recebimento no sistema novo. A matriz está atualizada; as filiais vão ser atualizadas pelo Alison e reimportadas.
- Rodado nas três cópias em 02/11/2026: 01 com 44.022 parcelas em aberto (R$ 6,09 milhões, das quais R$ 2,67 milhões de acertos de consignação), 02 com 3.437 (R$ 727 mil) e 03 com 7.447 (R$ 999 mil). Ficaram de fora 11 documentos da matriz (R$ 1.553,50) de clientes que não existem mais na `tab_clientes`.
- O que apareceu: 9.520 clientes devem algo; 199 em mais de uma loja; R$ 4,77 milhões estão vencidos, R$ 3,04 milhões há mais de um ano (4.997 clientes). Como quase ninguém tem limite, 9.160 desses clientes já estão acima do limite e o crediário deles vai pedir a gerência.
- Ficam para as operações do contas a receber que o Alison vai mostrar: mudança de carnês para a cobrança em lote, baixa de vários carnês, cobrador e tipo de cobrança das parcelas.

**Recebimento das parcelas do crediário (02/11/2026)**
- Regra do Alison: os juros de atraso são só **sugeridos**, contados por dia: % ao mês ÷ 30 × dias de atraso, sobre o que falta pagar da parcela (como o `F_CalculaJuros` do VB6). Hoje é 5% ao mês; fica na forma Crediário (tela de formas de pagamento), e o ETL traz o `juros_par` da loja. Não há multa nem carência.
- Tela "Receber crediário" (menu Caixa): o caixa escolhe o cliente e vê as parcelas em aberto de **todas as lojas**, com a loja, a venda, o vencimento, os dias de atraso e os juros sugeridos. Marca as que vai receber; pode mudar os juros e pagar só uma parte da parcela.
- O cliente paga em uma ou mais formas (não no crediário), com troco do dinheiro, como na venda. O recebimento é da loja e do caixa deste computador (D9); cada forma entra no caixa como "Recebimento de crediário", que só se desfaz pelo estorno do recebimento.
- Recebimento errado é estornado enquanto o caixa estiver aberto: as parcelas voltam a dever o que deviam e os lançamentos saem do caixa.
- Permissão: `caixa.operar`. Ficam para depois: o recibo impresso e a consulta dos recebimentos.

**Ajustes da venda (02/11/2026)**
- Pedido do Alison. O vendedor **fecha** a venda com o cliente, e só a venda fechada vai para o caixa, que a acha pelo nome de quem comprou (a lista do caixa começa nas fechadas). Para fechar: itens, forma de pagamento e o nome de quem compra (o crediário pede o cliente cadastrado; a entrega, o endereço). A venda fechada não muda; o vendedor ou o caixa reabre, e ela sai da fila do caixa. Fechada também vence em 10 dias.
- **Venda a consumidor** (o cliente 0 do VB6): sem cliente cadastrado, o nome de quem compra é obrigatório, mas pode ser só o primeiro nome. CPF, aniversário (dia e mês), telefone e e-mail são opcionais. Com algum deles, a pessoa entra num cadastro curto de consumidores (global); o CPF acha quem já comprou e preenche o resto, e o CPF de um cliente cadastrado troca o consumidor pelo cliente. Só com o nome, fica só na venda (como o `nomecli_ven` do VB6).
- **Entrega:** a venda pode ter entrega, com a taxa (entra no total, sem desconto) e o endereço (rua, número, bairro e cidade obrigatórios para fechar; CEP, complemento, referência e telefone de quem recebe). Com cliente cadastrado, o endereço dele vem preenchido. O controle da entrega em si fica na etapa 5.
- **Queima:** o produto vendido pelo preço de queima aparece marcado e não tem desconto nenhum: nem o da forma de pagamento, nem o do total (rateado só entre os outros itens), nem o do item. O limite de desconto é conferido sobre os itens que aceitam desconto.

**Crediário (etapa 3, 02/11/2026)**
- Regras do Alison: o limite restante do cliente é o limite de crédito menos todas as parcelas em aberto (em todas as lojas). O carnê não tem entrada; se o cliente pagar uma parte na hora, o caixa informa a entrada ao receber. Não há juros no crediário; pode haver juros de atraso ao receber a parcela.
- O crediário pede o cliente cadastrado. Cliente bloqueado ou com o crédito suspenso não compra no crediário, nem com autorização.
- Ao escolher o crediário, a venda mostra o limite do cliente, o que está em aberto e o disponível. Acima do disponível, o caixa pede o login e a senha de quem tem `vendas.autorizar` (ou uma entrada maior), e a venda guarda quem autorizou. No VB6 o limite só aparecia na tela, sem bloquear.
- A entrada é paga em uma ou mais formas que não sejam o crediário (com troco, se tiver dinheiro). O resto é dividido nas parcelas escolhidas na venda, iguais e sem juros; os centavos que sobram vão na última, como no VB6.
- ~~O primeiro vencimento é escolhido pelo caixa~~ (substituído em 02/11/2026). O caixa escolhe a **data base** (hoje, se não mudar; até um mês atrás, como no VB6), e a 1ª parcela vence um intervalo depois dela (um mês, com o intervalo de 30 dias da forma). As outras vencem no mesmo dia dos meses seguintes; se o dia não existe no mês, no último dia dele.
- No caixa entram a entrada, em cada forma em que foi paga, e o valor a prazo, na forma Crediário (como o DUP do VB6).
- O carnê é uma conta a receber da loja que vendeu, com as parcelas (o que falta pagar de cada uma). Sai na janela de impressão do navegador logo depois de receber, e pode ser impresso de novo pela venda. Cada parcela tem o canhoto, que fica na loja, e a parte do cliente.
- Ficam para depois: a baixa das parcelas (em qualquer loja, com os juros de atraso), o contrato impresso. (A baixa e a importação do VB6 foram feitas em 02/11/2026.)

**Formas de pagamento** (lista única para todas as lojas)
- Uma forma por tipo (dinheiro, PIX, cartão de crédito, de débito, crediário, cartão presente, depósito, vale): as "1X DUP" a "10X DUP" do VB6 viram o "Crediário" com até 10 parcelas, e a parcela é escolhida na venda. Cada forma tem desconto, máximo de parcelas, até quantas não pedem autorização, intervalo e ordem na tela. O cheque deixou de existir (entra desativado, só para as vendas antigas). Confirmado pelo Alison em 02/11/2026: o cartão de crédito continua com os 5% de desconto do VB6 e vai até 12x sem autorização.

**Caixa**
- O caixa é o ponto de recebimento (Cx 02, Consignado, Crediário...), não a pessoa: várias pessoas lançam no mesmo caixa, e cada lançamento guarda quem fez. Os nomes do VB6 continuam.
- Abre com o fundo de troco e fecha com conferência cega: quem fecha informa o que contou em dinheiro e em cada forma que teve lançamento, sem ver o esperado; a diferença aparece depois de fechar. Quem tem `caixa.conferir` vê o saldo esperado e os fechamentos.
- Lançamentos avulsos de entrada e saída: troco (entrada e retirada), despesa, vale de funcionário e comissão de cobrador. O controle dos vales por funcionário fica para depois. Lançamento errado é estornado (continua na lista, com quem estornou).
- Permissões: `caixa.operar`, `caixa.conferir` e `caixa.configurar`.

### D27. Contas de cobrança (03/11/2026)

Explicação do Alison. A conta de cobrança (`tab_contacob` do VB6) diz onde o carnê está para ser cobrado: a **Geral** é a padrão, quando está na loja e não foi entregue a ninguém; as outras são os cobradores, o advogado e os balanços (que marcam que o carnê está num processo).

- É diferente do cobrador do setor (D17), que continua sendo funcionário: a conta de cobrança é uma lista própria, uma só para todas as lojas, juntada pelo nome (o mesmo código é outra conta em cada loja no VB6). Toda parcela está numa conta; o carnê novo nasce na Geral.
- Na tela de contas a receber: filtro por conta de cobrança, a conta na lista (quando não é a Geral) e **Mudar cobrança**, em lote, para as selecionadas. Cadastro em Financeiro › Contas de cobrança (a Geral não pode ser desativada). Mudar e cadastrar pedem a permissão `receber.cobranca`.
- Depois da baixa, como no VB6: o caixa pode devolver os carnês recebidos para a Geral, e a tela avisa quando o cliente quitou todos os débitos, para repassar ao vendedor.
- ETL: a conta é achada pelo nome do VB6 (sem acentos nem maiúsculas); 000 e GERAL são a Geral. A conta PREJUIZO também vai para a Geral, porque o prejuízo virou a marca da parcela (D26). Os códigos são outros em cada loja porque cada banco cadastrou as contas num momento (confirmado pelo Alison em 03/11/2026).
- **Tipo de cobrança** (Alison, 03/11/2026): é escolha do cliente quando a venda é efetivada: pagamento na loja, cobrança no cliente, representante recebe, depósito ou boleto. Fica em cada parcela; a tela de receber a venda sugere pela ficha do cliente (pagamento na loja, ou cobrança no cliente em casa ou no trabalho) e o cliente escolhe. Lista fixa no código (a `tab_tipocob` do VB6 é a mesma nas três lojas); filtro na tela de contas a receber; o ETL traz o `cod_tip`.
- **Comissão:** a do vendedor é calculada pela venda efetivada, sem depender do recebimento das parcelas; a comissão da `tab_tipocob` não é usada para isso. A dos representantes (consignado) fica para a onda 5.
- **Prorrogar e editar** (regras do Alison, 03/11/2026), na tela de contas a receber, com a permissão `receber.editar`:
  - Prorrogar muda só o vencimento; o vencimento inicial fica. Em lote, para uma data só (o "dia 30" do VB6) ou tantos dias depois do vencimento de cada uma, com a anotação do contato.
  - Na parcela (clicando na linha): o tipo e a conta de cobrança. **O que falta pagar não se edita: só muda com a baixa.**
  - No documento: o cabeçalho (histórico e número), para todas as parcelas dele.
  - Toda mudança vai para o histórico da parcela, com o que era, o que ficou, quem, quando e a anotação, como a `frmEdiLan` do VB6: prorrogação, conta e tipo de cobrança, prejuízo e documento.
- **Cobrança em lote** (a tela "Cobrança" do VB6 fica como ações da mesma tela de contas a receber): mudar as selecionadas de conta de cobrança, e bloquear ou liberar os clientes delas (o bloqueio por atraso é à mão); cada bloqueio fica anotado na ficha do cliente. Bloquear pede `receber.cobranca` ou `clientes.editar`.

### Próximas etapas da venda (respostas do Alison, 03/11/2026)

- **Troca:** é uma funcionalidade à parte e complexa; o Alison vai mostrar.
- **Cancelamento:** a venda é marcada como cancelada, e também os registros que vieram dela. O cancelamento da NFC-e não é automático: o usuário faz.
- **Entrega:** sai um canhoto para fazer a entrega, no endereço que o vendedor informou; a taxa de entrega entra no caixa com a venda (já é assim).
- **Cartão presente:** existe, com um processo simples; o Alison vai mostrar.
- **Cartão de crédito:** a venda no cartão vai para a `tab_venfin` (ligada às financeiras); o financeiro tira o extrato todo dia e baixa, dizendo em que conta entrou. A ideia é automatizar depois. Na importação das vendas é importante ter o registro, podendo simplificar. (Na matriz, nenhuma linha da `tab_venfin` aparece baixada desde 2024: falta saber onde a baixa do extrato é gravada.)
- **Notas:** o Alison mostra a tela de notas (NF-e e NFC-e) quando for a hora da etapa 4.

## Substituídas

- **D2.** ~~FastAPI + Vue/Quasar sobre o banco atual~~. A stack continua, mas o banco passou a ser novo. Substituída pela D8 em 30/10/2026.
- **D3.** ~~Filial na chave das tabelas do banco atual~~. Com esquema novo, as tabelas já nascem com a empresa. Substituída pelas D8 e D9 em 30/10/2026.
- **D4.** ~~VB6 e sistema novo no mesmo banco, com sincronização~~. Substituída pela D8 (ETL de mão única e virada por filial) em 30/10/2026.
- **D6.** ~~Converter o banco atual para InnoDB e criar chaves~~. Desnecessário com esquema novo. Substituída pela D8 em 30/10/2026.
- **D7.** ~~Login conferindo a senha do VB6 e migrando para hash no primeiro acesso~~. Com o ETL, as senhas são convertidas na importação. Substituída pela D8 em 30/10/2026.

## Em aberto

- **P1.** ~~O servidor da API web que o VB6 já usa (piki.app.br)~~. É mantido pelo Alison e vai ser substituído pelo `piki-web`; os clientes não vêm dele (D15).
- **P2.** Códigos das empresas (`sped_empresa.codigo`, o `cod_emp` do VB6). Conhecidos em 30/10/2026: **01** (matriz, Requinte Enxovais, banco `requinte`), **02** (Jundiaí Casa, nome fantasia Requinte Enxovais, banco `requintejun`) e **03** (La Viva Enxovais, banco `requintebps`). Falta saber se existem outras e conferir se os registros já gravados em cada banco estão com o código certo. O ETL recusa importar quando o mesmo código aparece com CNPJs diferentes.
- **P3.** ~~Clientes e produtos globais ou por loja?~~ Resolvido na D9.
- **P4.** As lojas ainda usam ECF, ou só NFC-e? Se só NFC-e, o código e as tabelas de ECF são descartados.
- **P6.** O login do VB6 monta o SQL concatenando o texto digitado (`frmLogin`), o que permite injeção de SQL. Vale corrigir no legado enquanto ele estiver em uso.
- **P7.** ~~PostgreSQL ou MariaDB?~~ Resolvido na D12.
- **P8.** Infraestrutura das filiais: quantas são, se o computador do banco fica ligado e com internet, e o tamanho de cada banco. Define a frequência do agente.
- **P10.** Segredos fiscais por empresa: certificado digital A1 (`.pfx` e senha) e CSC da NFC-e (id e token). No VB6 ficam em texto puro na `sped_empresa`; o ETL não os lê. Proposta: os arquivos `.pfx` ficam no servidor, fora do repositório e do banco, e senhas e tokens ficam cifrados no banco com uma chave que só existe no `.env` do servidor (ou num cofre de segredos). Decidir antes da onda 6.
- **P11.** Token no `localStorage` é simples, mas fica exposto se algum dia o front tiver uma falha de XSS. Antes de ir para produção, avaliar trocar por cookie `HttpOnly` emitido pela API, com renovação automática.
- **P12.** Todas as filiais usam a marca Requinte Enxovais? Se alguma tiver outra marca, o logo e as cores passam para o cadastro da empresa e o visual muda ao trocar de empresa. Em 30/10/2026: a 03 tem nome fantasia La Viva Enxovais na `sped_empresa`; falta confirmar se ela usa outra marca na loja.
- **P9.** (02/11/2026: hoje as lojas recebem os produtos da matriz por uma API na internet; D24.) Durante a transição, produtos cadastrados no sistema novo precisam chegar aos VB6 das filiais que ainda não viraram? Se o cadastro de produtos é feito por uma só pessoa ou pela matriz, pode ser preciso uma sincronização de volta só para produtos.
- **P13.** ~~Códigos do cliente no VB6~~. `status_cli`: 1 liberado, 2 bloqueado. `cobranca_cli`: 1 em domicílio, 2 no trabalho, 3 na loja. O tipo da referência é o parentesco (`tab_tipopar`). Resolvido na D15 em 30/10/2026.
