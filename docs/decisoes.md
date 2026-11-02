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
| Por empresa | estoque, preço e custo do produto, notas fiscais de entrada e saída, vendas, caixa, inventário | Cada registro pertence a uma empresa; só aparece nela |
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
- **P9.** Durante a transição, produtos cadastrados no sistema novo precisam chegar aos VB6 das filiais que ainda não viraram? Se o cadastro de produtos é feito por uma só pessoa ou pela matriz, pode ser preciso uma sincronização de volta só para produtos.
- **P13.** ~~Códigos do cliente no VB6~~. `status_cli`: 1 liberado, 2 bloqueado. `cobranca_cli`: 1 em domicílio, 2 no trabalho, 3 na loja. O tipo da referência é o parentesco (`tab_tipopar`). Resolvido na D15 em 30/10/2026.
