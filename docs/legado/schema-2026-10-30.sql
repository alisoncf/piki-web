/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.6.2-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: requinte
-- ------------------------------------------------------
-- Server version	11.6.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `abrecaixa`
--

DROP TABLE IF EXISTS `abrecaixa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `abrecaixa` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cod_cai` char(3) DEFAULT NULL,
  `data` date NOT NULL DEFAULT '0000-00-00',
  `hora` char(5) DEFAULT NULL,
  `cod_usu` char(3) DEFAULT NULL,
  `valor_inicial` double(14,2) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `atualizacao_produtos`
--

DROP TABLE IF EXISTS `atualizacao_produtos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `atualizacao_produtos` (
  `cod_pro` char(8) NOT NULL,
  `atualizacao` datetime NOT NULL,
  PRIMARY KEY (`cod_pro`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bases`
--

DROP TABLE IF EXISTS `bases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bases` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `banco` char(60) NOT NULL DEFAULT '',
  `descricao` char(200) NOT NULL DEFAULT '',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cartao_movimento`
--

DROP TABLE IF EXISTS `cartao_movimento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cartao_movimento` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dia` date NOT NULL DEFAULT '0000-00-00',
  `usuario` int(11) NOT NULL DEFAULT 0,
  `coo` char(10) DEFAULT NULL,
  `doc` char(10) DEFAULT NULL,
  `autorizacao` char(10) DEFAULT NULL,
  `valor` double(14,2) NOT NULL DEFAULT 0.00,
  `parcelas` int(11) NOT NULL DEFAULT 1,
  `conferido` char(1) NOT NULL DEFAULT 'N',
  `financeira` char(3) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cartao_presente`
--

DROP TABLE IF EXISTS `cartao_presente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cartao_presente` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` char(60) DEFAULT NULL,
  `cpf` char(20) DEFAULT NULL,
  `contato` char(200) DEFAULT NULL,
  `presenteado` char(60) DEFAULT NULL,
  `obs` char(200) DEFAULT NULL,
  `DATA` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `vencimento` date DEFAULT NULL,
  `numero` char(10) DEFAULT NULL,
  `valor` double NOT NULL DEFAULT 0,
  `utilizado` double NOT NULL DEFAULT 0,
  `cod_usu` char(3) DEFAULT NULL,
  `num_ven` char(7) DEFAULT NULL,
  `cod_for` char(2) NOT NULL DEFAULT '',
  `STATUS` char(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=87 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chequepresente`
--

DROP TABLE IF EXISTS `chequepresente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `chequepresente` (
  `codigo` int(11) NOT NULL DEFAULT 0,
  `data` date DEFAULT NULL,
  `cod_cli` char(6) DEFAULT NULL,
  `historico` char(250) DEFAULT NULL,
  `status` char(1) DEFAULT NULL,
  `baixa` date DEFAULT NULL,
  `caixa` char(2) DEFAULT NULL,
  `cod_usu` char(3) DEFAULT NULL,
  `usuariobaixa` char(3) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cidades`
--

DROP TABLE IF EXISTS `cidades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cidades` (
  `cod_cid` char(7) NOT NULL DEFAULT '',
  `nome_cid` char(100) DEFAULT NULL,
  `uf_cid` char(2) DEFAULT NULL,
  `estado_cid` char(60) DEFAULT NULL,
  PRIMARY KEY (`cod_cid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `contagem`
--

DROP TABLE IF EXISTS `contagem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contagem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_ant` double(14,2) DEFAULT 0.00,
  `qtd` double(14,2) DEFAULT 0.00,
  `data` date NOT NULL DEFAULT '0000-00-00',
  `hora` char(8) NOT NULL DEFAULT '',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `cod_emp` char(2) NOT NULL DEFAULT '01',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=247 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `contato`
--

DROP TABLE IF EXISTS `contato`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contato` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` char(200) NOT NULL DEFAULT '',
  `telefone` char(250) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=362 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `doc_quitacao`
--

DROP TABLE IF EXISTS `doc_quitacao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `doc_quitacao` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `seq_doc` varchar(7) DEFAULT NULL,
  `cod_emp` char(2) NOT NULL,
  `id_doc` int(11) DEFAULT NULL,
  `valor_doc` double(14,2) DEFAULT NULL,
  `parcelas` int(2) NOT NULL,
  `vencimento_inicial` date NOT NULL,
  `vencimento_final` date NOT NULL,
  `data_quitacao` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `seq_doc` (`seq_doc`,`cod_emp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `documentos_contrato`
--

DROP TABLE IF EXISTS `documentos_contrato`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `documentos_contrato` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `seq_doc` char(7) DEFAULT NULL,
  `descricao` varchar(256) DEFAULT NULL,
  `caminho` varchar(256) DEFAULT NULL,
  `data` datetime DEFAULT NULL,
  `cod_usu` char(3) DEFAULT NULL,
  `hash` varchar(256) DEFAULT NULL,
  `excluido` varchar(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `seq_doc` (`seq_doc`),
  KEY `cod_usu` (`cod_usu`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fecha_caixa`
--

DROP TABLE IF EXISTS `fecha_caixa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fecha_caixa` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `DATA` date NOT NULL DEFAULT '0000-00-00',
  `caixa` char(2) NOT NULL DEFAULT '',
  `dinheiro_total` double(14,2) DEFAULT 0.00,
  `dinheiro_info` double(14,2) DEFAULT 0.00,
  `cheque_total` double(14,2) DEFAULT 0.00,
  `cheque_info` double(14,2) DEFAULT 0.00,
  `cartao_total` double(14,2) DEFAULT 0.00,
  `cartao_info` double(14,2) DEFAULT 0.00,
  `quem_fechou` char(3) DEFAULT NULL,
  `quando` datetime DEFAULT NULL,
  `obs` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fechacaixa`
--

DROP TABLE IF EXISTS `fechacaixa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fechacaixa` (
  `id` int(11) NOT NULL DEFAULT 0,
  `data_fechamento` date NOT NULL DEFAULT '0000-00-00',
  `hora_fechamento` char(5) DEFAULT NULL,
  `fecha_usu` char(3) DEFAULT NULL,
  `valor_final` double(14,2) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fila_transferencia`
--

DROP TABLE IF EXISTS `fila_transferencia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fila_transferencia` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(30) NOT NULL,
  `tipo` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`,`tipo`)
) ENGINE=InnoDB AUTO_INCREMENT=142819 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `inventario`
--

DROP TABLE IF EXISTS `inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inventario` (
  `id` int(11) NOT NULL DEFAULT 0,
  `data` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `de` date DEFAULT NULL,
  `ate` date DEFAULT NULL,
  `cod_emp` char(2) NOT NULL DEFAULT '01',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `inventario_it`
--

DROP TABLE IF EXISTS `inventario_it`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inventario_it` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `inventario` int(11) NOT NULL DEFAULT 0,
  `codigo` char(8) NOT NULL DEFAULT '',
  `nome` char(60) NOT NULL DEFAULT '',
  `custo` double(14,2) NOT NULL DEFAULT 0.00,
  `preco` double(14,2) NOT NULL DEFAULT 0.00,
  `q1` double(14,2) NOT NULL DEFAULT 0.00,
  `q2` double(14,2) NOT NULL DEFAULT 0.00,
  `r` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_emp` char(2) NOT NULL DEFAULT '01',
  PRIMARY KEY (`id`),
  KEY `inv` (`inventario`)
) ENGINE=MyISAM AUTO_INCREMENT=506063 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mensagem`
--

DROP TABLE IF EXISTS `mensagem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mensagem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `remetente` char(3) NOT NULL DEFAULT '',
  `destinatario` char(3) NOT NULL DEFAULT '',
  `mensagem` text DEFAULT NULL,
  `lido` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mensagens`
--

DROP TABLE IF EXISTS `mensagens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mensagens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `de` char(3) NOT NULL DEFAULT '',
  `para` char(3) NOT NULL DEFAULT '',
  `mensagem` text DEFAULT NULL,
  `status` char(1) DEFAULT NULL,
  `data` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe`
--

DROP TABLE IF EXISTS `nfe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cUF` char(2) NOT NULL DEFAULT '',
  `cNF` varchar(8) NOT NULL DEFAULT '',
  `natOp` varchar(60) NOT NULL DEFAULT '',
  `indPag` char(1) NOT NULL DEFAULT '',
  `modelo` char(2) NOT NULL DEFAULT '',
  `serie` char(3) NOT NULL DEFAULT '',
  `nNF` int(9) NOT NULL DEFAULT 0,
  `dhEmi` varchar(26) NOT NULL DEFAULT '',
  `dhSaiEnt` varchar(26) NOT NULL DEFAULT '',
  `tpNF` char(1) NOT NULL DEFAULT '',
  `idDest` char(1) NOT NULL DEFAULT '',
  `cMunFG` varchar(7) DEFAULT NULL,
  `tpImp` char(1) DEFAULT NULL,
  `tpEmis` char(1) DEFAULT NULL,
  `cDV` char(1) DEFAULT NULL,
  `tpAmb` char(1) DEFAULT NULL,
  `finNFe` char(1) DEFAULT NULL,
  `indFinal` char(1) DEFAULT NULL,
  `indPres` char(1) DEFAULT NULL,
  `procEmi` char(1) DEFAULT NULL,
  `verProc` varchar(20) DEFAULT NULL,
  `dhCont` varchar(26) DEFAULT NULL,
  `xJust` varchar(255) DEFAULT NULL,
  `status` int(3) DEFAULT NULL,
  `num_ven` varchar(7) DEFAULT NULL,
  `chave` varchar(200) DEFAULT NULL,
  `caminhoXML` text DEFAULT NULL,
  `protocolo` varchar(255) DEFAULT NULL,
  `recibo` varchar(255) DEFAULT NULL,
  `DigestValue` varchar(255) DEFAULT NULL,
  `cod_usu` char(3) DEFAULT NULL,
  `refNfe` varchar(44) DEFAULT NULL,
  `indIntermed` int(11) NOT NULL DEFAULT 0,
  `cod_emp` char(2) NOT NULL DEFAULT '01',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=95574 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_cobr_dup`
--

DROP TABLE IF EXISTS `nfe_cobr_dup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_cobr_dup` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `nDup` char(60) DEFAULT NULL,
  `dVenc` date DEFAULT NULL,
  `vDup` double(14,2) DEFAULT NULL,
  PRIMARY KEY (`id_nfe`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_cobr_fat`
--

DROP TABLE IF EXISTS `nfe_cobr_fat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_cobr_fat` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `nFat` char(60) DEFAULT NULL,
  `vOrig` double(14,2) DEFAULT NULL,
  `vDesc` double(14,2) DEFAULT NULL,
  `vLiq` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_crt`
--

DROP TABLE IF EXISTS `nfe_crt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_crt` (
  `id` int(11) NOT NULL DEFAULT 0,
  `nome` char(60) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_cst`
--

DROP TABLE IF EXISTS `nfe_cst`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_cst` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `nome` char(80) NOT NULL DEFAULT '',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_dest`
--

DROP TABLE IF EXISTS `nfe_dest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_dest` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CNPJ` char(14) DEFAULT NULL,
  `CPF` char(11) DEFAULT NULL,
  `idEstrangeiro` char(20) DEFAULT NULL,
  `xNome` char(50) DEFAULT NULL,
  PRIMARY KEY (`id_nfe`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_emit`
--

DROP TABLE IF EXISTS `nfe_emit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_emit` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CNPJ` char(14) DEFAULT NULL,
  `CPF` char(11) DEFAULT NULL,
  `xNome` char(60) DEFAULT NULL,
  `xFant` char(60) DEFAULT NULL,
  `IdEstrangeiro` char(20) DEFAULT NULL,
  PRIMARY KEY (`id_nfe`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_enderdest`
--

DROP TABLE IF EXISTS `nfe_enderdest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_enderdest` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `xLgr` char(60) DEFAULT NULL,
  `nro` char(60) DEFAULT NULL,
  `xCpl` char(60) DEFAULT NULL,
  `xBairro` char(60) DEFAULT NULL,
  `cMun` char(7) DEFAULT NULL,
  `xMun` char(60) DEFAULT NULL,
  `UF` char(2) DEFAULT NULL,
  `CEP` char(8) DEFAULT NULL,
  `cPais` char(4) DEFAULT NULL,
  `xPais` char(60) DEFAULT NULL,
  `fone` char(60) DEFAULT NULL,
  `IE` char(14) DEFAULT NULL,
  `indIEDest` char(1) DEFAULT NULL,
  `IEST` char(14) DEFAULT NULL,
  `ISUF` char(9) DEFAULT NULL,
  `IM` char(15) DEFAULT NULL,
  `email` char(60) DEFAULT NULL,
  PRIMARY KEY (`id_nfe`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_enderemit`
--

DROP TABLE IF EXISTS `nfe_enderemit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_enderemit` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `xLgr` char(60) DEFAULT NULL,
  `nro` char(60) DEFAULT NULL,
  `xCpl` char(60) DEFAULT NULL,
  `xBairro` char(60) DEFAULT NULL,
  `cMun` char(7) DEFAULT NULL,
  `xMun` char(60) DEFAULT NULL,
  `UF` char(2) DEFAULT NULL,
  `CEP` char(8) DEFAULT NULL,
  `cPais` char(4) DEFAULT NULL,
  `xPais` char(60) DEFAULT NULL,
  `fone` char(60) DEFAULT NULL,
  `IE` char(14) DEFAULT NULL,
  `IEST` char(14) DEFAULT NULL,
  `IM` char(15) DEFAULT NULL,
  `CNAE` char(7) DEFAULT NULL,
  `CRT` char(1) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_icmstot`
--

DROP TABLE IF EXISTS `nfe_icmstot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_icmstot` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `vBC` double(14,2) DEFAULT NULL,
  `vICMS` double(14,2) DEFAULT NULL,
  `vICMSDeson` double(14,2) DEFAULT NULL,
  `vBCST` double(14,2) DEFAULT NULL,
  `vST` double(14,2) DEFAULT NULL,
  `vProd` double(14,2) DEFAULT NULL,
  `vFrete` double(14,2) DEFAULT NULL,
  `vSeg` double(14,2) DEFAULT NULL,
  `vDesc` double(14,2) DEFAULT NULL,
  `vII` double(14,2) DEFAULT NULL,
  `vIPI` double(14,2) DEFAULT NULL,
  `vPIS` double(14,2) DEFAULT NULL,
  `vCOFINS` double(14,2) DEFAULT NULL,
  `vOutro` double(14,2) DEFAULT NULL,
  `vNF` double(14,2) DEFAULT NULL,
  `vTotTrib` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_infaddpadrao`
--

DROP TABLE IF EXISTS `nfe_infaddpadrao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_infaddpadrao` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `texto` text DEFAULT NULL,
  `cfop` varchar(4) DEFAULT NULL,
  `tipo_icms` char(3) DEFAULT NULL,
  `credicms` double(14,2) DEFAULT NULL,
  `cod_emp` char(2) NOT NULL DEFAULT '01',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_infadic`
--

DROP TABLE IF EXISTS `nfe_infadic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_infadic` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `infAdFisco` text DEFAULT NULL,
  `infCpl` text DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item`
--

DROP TABLE IF EXISTS `nfe_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `cProd` varchar(60) NOT NULL DEFAULT '',
  `cEAN` varchar(14) DEFAULT NULL,
  `xProd` varchar(120) DEFAULT NULL,
  `NCM` varchar(8) DEFAULT NULL,
  `NVE` varchar(6) DEFAULT NULL,
  `EXTIPI` char(3) DEFAULT NULL,
  `CFOP` varchar(4) DEFAULT NULL,
  `uCom` varchar(6) DEFAULT NULL,
  `qCom` double(14,4) DEFAULT NULL,
  `vUnCom` double(14,4) DEFAULT NULL,
  `vProd` double(14,4) DEFAULT NULL,
  `cEANTrib` varchar(14) DEFAULT NULL,
  `uTrib` varchar(6) DEFAULT NULL,
  `qTrib` double(14,4) DEFAULT NULL,
  `vUnTrib` double(14,4) DEFAULT NULL,
  `vFrete` double(14,4) DEFAULT NULL,
  `vSeg` double(14,4) DEFAULT NULL,
  `vDesc` double(14,4) DEFAULT NULL,
  `vOutro` double(14,4) DEFAULT NULL,
  `indTot` char(1) DEFAULT NULL,
  `CEST` varchar(7) DEFAULT NULL,
  `infAdProd` text DEFAULT NULL,
  `cod_emp` char(2) DEFAULT '01',
  PRIMARY KEY (`id`),
  KEY `cProd` (`cProd`)
) ENGINE=MyISAM AUTO_INCREMENT=293389 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_comb`
--

DROP TABLE IF EXISTS `nfe_item_comb`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_comb` (
  `id_item` int(11) NOT NULL,
  `id_nfe` int(11) NOT NULL,
  `cProdANP` varchar(9) NOT NULL,
  `descANP` varchar(95) NOT NULL,
  `UFCons` char(2) NOT NULL,
  PRIMARY KEY (`id_item`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_icms`
--

DROP TABLE IF EXISTS `nfe_item_icms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_icms` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `tag` char(12) NOT NULL DEFAULT '',
  `csosn` char(4) NOT NULL DEFAULT '',
  `orig` char(1) NOT NULL DEFAULT '0',
  `vBC` double(14,2) DEFAULT NULL,
  `vicms` double(14,2) DEFAULT NULL,
  `vpcms` double(14,2) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto`
--

DROP TABLE IF EXISTS `nfe_item_imposto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `vTotTrib` double(14,2) DEFAULT NULL,
  `tipo_icms` char(14) DEFAULT NULL,
  `tipo_pis` char(14) DEFAULT NULL,
  `tipo_cofins` char(14) DEFAULT NULL,
  `tipo_ipi` char(14) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_cofinsaliq`
--

DROP TABLE IF EXISTS `nfe_item_imposto_cofinsaliq`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_cofinsaliq` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pCOFINS` double(14,4) DEFAULT NULL,
  `VCOFINS` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_cofinsnt`
--

DROP TABLE IF EXISTS `nfe_item_imposto_cofinsnt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_cofinsnt` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_cofinsoutr`
--

DROP TABLE IF EXISTS `nfe_item_imposto_cofinsoutr`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_cofinsoutr` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pCOFINS` double(14,4) DEFAULT NULL,
  `qBCProd` double(14,2) DEFAULT NULL,
  `vAliqProd` double(14,4) DEFAULT NULL,
  `vCOFINS` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_cofinsqtde`
--

DROP TABLE IF EXISTS `nfe_item_imposto_cofinsqtde`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_cofinsqtde` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL,
  `qBCProd` double(14,2) DEFAULT NULL,
  `vAliqProd` double(14,4) DEFAULT NULL,
  `pCOFINS` double(14,4) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_cofinsst`
--

DROP TABLE IF EXISTS `nfe_item_imposto_cofinsst`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_cofinsst` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `vBC` double(14,2) DEFAULT NULL,
  `pCOFINS` double(14,4) DEFAULT NULL,
  `qBCProd` double(14,2) DEFAULT NULL,
  `vAliqProd` double(14,4) DEFAULT NULL,
  `vCOFINS` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icms00`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icms00`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icms00` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL,
  `orig` char(1) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pICMS` double(14,4) DEFAULT NULL,
  `vICMS` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icms10`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icms10`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icms10` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL,
  `orig` char(1) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pICMS` double(14,4) DEFAULT NULL,
  `vICMS` double(14,2) DEFAULT NULL,
  `modBCST` char(1) DEFAULT NULL,
  `pMVAST` double(14,2) DEFAULT NULL,
  `pRedBCST` double(14,4) DEFAULT NULL,
  `vBCST` double(14,2) DEFAULT NULL,
  `pICMSST` double(14,4) DEFAULT NULL,
  `vICMSST` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icms20`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icms20`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icms20` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CST` char(2) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  `pRedBC` double(14,4) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pICMS` double(14,4) DEFAULT NULL,
  `vICMS` double(14,2) DEFAULT NULL,
  `vICMSDeson` double(14,2) DEFAULT NULL,
  `motDesICMS` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icms30`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icms30`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icms30` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CST` char(2) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  `pMVAST` double(14,4) DEFAULT NULL,
  `pRedBC` double(14,4) DEFAULT NULL,
  `pRedBCST` double(14,4) DEFAULT NULL,
  `vBCST` double(14,2) DEFAULT NULL,
  `pICMSST` double(14,4) DEFAULT NULL,
  `vICMSST` double(14,2) DEFAULT NULL,
  `vICMSDeson` double(14,2) DEFAULT NULL,
  `motDesICMS` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icms40`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icms40`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icms40` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CST` char(2) DEFAULT NULL,
  `vICMSDeson` double(14,2) DEFAULT NULL,
  `motDesICMS` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icms51`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icms51`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icms51` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CST` char(2) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  `pRedBC` double(14,4) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pICMS` double(14,4) DEFAULT NULL,
  `vICMSOp` double(14,2) DEFAULT NULL,
  `vICMSDif` double(14,2) DEFAULT NULL,
  `vICMS` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icms60`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icms60`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icms60` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CST` char(2) DEFAULT NULL,
  `vBCSTRet` double(14,2) DEFAULT NULL,
  `vICMSSTRet` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icms70`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icms70`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icms70` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CST` char(2) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  `pRedBC` double(14,4) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pICMS` double(14,4) DEFAULT NULL,
  `vICMS` double(14,2) DEFAULT NULL,
  `modBCST` char(1) DEFAULT NULL,
  `pMVAST` double(14,4) DEFAULT NULL,
  `pRedBCST` double(14,4) DEFAULT NULL,
  `vBCST` double(14,2) DEFAULT NULL,
  `pICMSST` double(14,4) DEFAULT NULL,
  `vICMSST` double(14,2) DEFAULT NULL,
  `vICMSDeson` double(14,2) DEFAULT NULL,
  `motDesICMS` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icms90`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icms90`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icms90` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CST` char(2) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pRedBC` double(14,4) DEFAULT NULL,
  `pICMS` double(14,4) DEFAULT NULL,
  `vICMS` double(14,2) DEFAULT NULL,
  `modBCST` char(1) DEFAULT NULL,
  `pMVAST` double(14,4) DEFAULT NULL,
  `pRedBCST` double(14,4) DEFAULT NULL,
  `vBCST` double(14,2) DEFAULT NULL,
  `pICMSST` double(14,4) DEFAULT NULL,
  `vICMSST` double(14,2) DEFAULT NULL,
  `vICMSDeson` double(14,2) DEFAULT NULL,
  `motDesICMS` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icmspart`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icmspart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icmspart` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CST` char(2) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pRedBC` double(14,4) DEFAULT NULL,
  `pICMS` double(14,4) DEFAULT NULL,
  `vICMS` double(14,2) DEFAULT NULL,
  `modBCST` char(1) DEFAULT NULL,
  `pMVAST` double(14,4) DEFAULT NULL,
  `pRedBCST` double(14,4) DEFAULT NULL,
  `vBCST` double(14,2) DEFAULT NULL,
  `pICMSST` double(14,4) DEFAULT NULL,
  `vICMSST` double(14,2) DEFAULT NULL,
  `pBCOp` double(14,2) DEFAULT NULL,
  `UFST` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icmssn101`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icmssn101`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icmssn101` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CSOSN` char(3) DEFAULT NULL,
  `pCredSN` double(14,4) DEFAULT NULL,
  `vCredICMSSN` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icmssn102`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icmssn102`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icmssn102` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CSOSN` char(3) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icmssn201`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icmssn201`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icmssn201` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CSOSN` char(3) DEFAULT NULL,
  `modBCST` char(1) DEFAULT NULL,
  `pMVAST` double(14,4) DEFAULT NULL,
  `pRedBCST` double(14,4) DEFAULT NULL,
  `vBCST` double(14,2) DEFAULT NULL,
  `pICMSST` double(14,4) DEFAULT NULL,
  `vICMSST` double(14,2) DEFAULT NULL,
  `pCredSN` double(14,4) DEFAULT NULL,
  `vCredICMSSN` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icmssn202`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icmssn202`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icmssn202` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CSOSN` char(3) DEFAULT NULL,
  `modBCST` char(1) DEFAULT NULL,
  `pMVAST` double(14,4) DEFAULT NULL,
  `pRedBCST` double(14,4) DEFAULT NULL,
  `vBCST` double(14,2) DEFAULT NULL,
  `pICMSST` double(14,4) DEFAULT NULL,
  `vICMSST` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icmssn500`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icmssn500`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icmssn500` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CSOSN` char(3) DEFAULT NULL,
  `vBCSTRet` double(14,2) DEFAULT NULL,
  `vICMSSTRet` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icmssn900`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icmssn900`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icmssn900` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CSOSN` char(3) DEFAULT NULL,
  `modBC` char(1) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pRedBC` double(14,4) DEFAULT NULL,
  `pICMS` double(14,4) DEFAULT NULL,
  `vICMS` double(14,2) DEFAULT NULL,
  `modBCST` char(1) DEFAULT NULL,
  `pMVAST` double(14,4) DEFAULT NULL,
  `pRedBCST` double(14,4) DEFAULT NULL,
  `vBCST` double(14,2) DEFAULT NULL,
  `pICMSST` double(14,4) DEFAULT NULL,
  `vICMSST` double(14,2) DEFAULT NULL,
  `pCredSN` double(14,4) DEFAULT NULL,
  `vCredICMSSN` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_icmsst`
--

DROP TABLE IF EXISTS `nfe_item_imposto_icmsst`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_icmsst` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `orig` char(1) DEFAULT NULL,
  `CST` char(2) DEFAULT NULL,
  `vBCSTRet` double(14,2) DEFAULT NULL,
  `vICMSSTRet` double(14,2) DEFAULT NULL,
  `vBCSTDest` double(14,2) DEFAULT NULL,
  `vICMSSTDest` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_ipi`
--

DROP TABLE IF EXISTS `nfe_item_imposto_ipi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_ipi` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `clEnq` char(5) DEFAULT NULL,
  `CNPJProd` char(14) DEFAULT NULL,
  `cSelo` char(60) DEFAULT NULL,
  `qSelo` char(2) DEFAULT NULL,
  `cEnq` char(3) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_ipiint`
--

DROP TABLE IF EXISTS `nfe_item_imposto_ipiint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_ipiint` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_ipint`
--

DROP TABLE IF EXISTS `nfe_item_imposto_ipint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_ipint` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_ipitrib`
--

DROP TABLE IF EXISTS `nfe_item_imposto_ipitrib`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_ipitrib` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pIPI` double(14,4) DEFAULT NULL,
  `qUnid` int(11) DEFAULT NULL,
  `vUnid` double(14,4) DEFAULT NULL,
  `vIPI` double(14,4) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_pisaliq`
--

DROP TABLE IF EXISTS `nfe_item_imposto_pisaliq`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_pisaliq` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pPIS` double(14,4) DEFAULT NULL,
  `vPIS` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_pisnt`
--

DROP TABLE IF EXISTS `nfe_item_imposto_pisnt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_pisnt` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_pisoutr`
--

DROP TABLE IF EXISTS `nfe_item_imposto_pisoutr`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_pisoutr` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL,
  `vBC` double(14,2) DEFAULT NULL,
  `pPIS` double(14,4) DEFAULT NULL,
  `qBCProd` double(14,2) DEFAULT NULL,
  `vAliqProd` double(14,4) DEFAULT NULL,
  `vPIS` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_pisqtde`
--

DROP TABLE IF EXISTS `nfe_item_imposto_pisqtde`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_pisqtde` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CST` char(2) DEFAULT NULL,
  `qBCProd` double(14,4) DEFAULT NULL,
  `vAliqProd` double(14,4) DEFAULT NULL,
  `vPIS` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_imposto_pisst`
--

DROP TABLE IF EXISTS `nfe_item_imposto_pisst`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_imposto_pisst` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `vBC` double(14,2) DEFAULT NULL,
  `pPIS` double(14,4) DEFAULT NULL,
  `qBCProd` double(14,2) DEFAULT NULL,
  `vAliqProd` double(14,4) DEFAULT NULL,
  `vPIS` double(14,2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_item_ipi`
--

DROP TABLE IF EXISTS `nfe_item_ipi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_item_ipi` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_nfe` int(11) NOT NULL,
  `id_nfe_item` int(11) NOT NULL,
  `CST` char(2) DEFAULT NULL,
  `clEnq` char(5) DEFAULT NULL,
  `CNPJProd` char(14) DEFAULT NULL,
  `cSelo` char(60) DEFAULT NULL,
  `qSelo` char(2) DEFAULT NULL,
  `cEnq` char(3) DEFAULT NULL,
  `vBC` decimal(15,2) DEFAULT NULL,
  `pIPI` decimal(15,4) DEFAULT NULL,
  `qUnid` decimal(15,4) DEFAULT NULL,
  `vUnid` decimal(15,4) DEFAULT NULL,
  `vIPI` decimal(15,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_nfe` (`id_nfe`),
  KEY `idx_id_nfe_item` (`id_nfe_item`),
  KEY `idx_cst` (`CST`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_lote`
--

DROP TABLE IF EXISTS `nfe_lote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_lote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `horario` datetime DEFAULT NULL,
  `id_nfe` char(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=81078 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_pag`
--

DROP TABLE IF EXISTS `nfe_pag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_pag` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `tPag` char(2) DEFAULT NULL,
  `vPag` double(14,2) DEFAULT NULL,
  `card` char(1) DEFAULT NULL,
  `CNPJ` char(14) DEFAULT NULL,
  `tBand` char(2) DEFAULT NULL,
  `cAut` char(20) DEFAULT NULL,
  `tpIntegra` char(1) DEFAULT NULL,
  `vTroco` double(14,2) DEFAULT 0.00,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=111565 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_pedidoinut`
--

DROP TABLE IF EXISTS `nfe_pedidoinut`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_pedidoinut` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `inicial` varchar(9) NOT NULL DEFAULT '',
  `final` varchar(9) NOT NULL DEFAULT '',
  `datahora` datetime DEFAULT NULL,
  `status` char(1) NOT NULL DEFAULT '1',
  `cod_usu` char(3) DEFAULT NULL,
  `justificativa` text DEFAULT NULL,
  `modelo` char(2) DEFAULT NULL,
  `serie` char(3) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=689 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_procref`
--

DROP TABLE IF EXISTS `nfe_procref`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_procref` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `nProc` char(60) DEFAULT NULL,
  `indProc` char(1) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_ref`
--

DROP TABLE IF EXISTS `nfe_ref`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_ref` (
  `id` int(11) NOT NULL DEFAULT 0,
  `refNfe` char(44) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`,`refNfe`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_tipo_icms`
--

DROP TABLE IF EXISTS `nfe_tipo_icms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_tipo_icms` (
  `codigo` char(3) NOT NULL DEFAULT '',
  `descricao` char(200) DEFAULT NULL,
  `tabela` char(100) DEFAULT NULL,
  `tipo` char(1) DEFAULT '1',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_tpag`
--

DROP TABLE IF EXISTS `nfe_tpag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_tpag` (
  `tpag` char(2) NOT NULL DEFAULT '',
  `nome` char(60) DEFAULT NULL,
  PRIMARY KEY (`tpag`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_transp`
--

DROP TABLE IF EXISTS `nfe_transp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_transp` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `modFrete` char(1) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_transp_reboque`
--

DROP TABLE IF EXISTS `nfe_transp_reboque`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_transp_reboque` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `placa` char(7) DEFAULT NULL,
  `UF` char(2) DEFAULT NULL,
  `RNTC` char(20) DEFAULT NULL,
  `vagao` char(20) DEFAULT NULL,
  `balsa` char(20) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_transp_rettransp`
--

DROP TABLE IF EXISTS `nfe_transp_rettransp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_transp_rettransp` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `vServ` double(14,2) DEFAULT NULL,
  `vBCRet` double(14,2) DEFAULT NULL,
  `pICMSRet` double(14,4) DEFAULT NULL,
  `vICMSRet` double(14,2) DEFAULT NULL,
  `CFOP` char(4) DEFAULT NULL,
  `cMunFG` char(7) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_transp_transportadora`
--

DROP TABLE IF EXISTS `nfe_transp_transportadora`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_transp_transportadora` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `CNPJ` char(14) DEFAULT NULL,
  `CPF` char(11) DEFAULT NULL,
  `xNome` char(60) DEFAULT NULL,
  `IE` char(14) DEFAULT NULL,
  `xEnder` char(60) DEFAULT NULL,
  `xMun` char(60) DEFAULT NULL,
  `UF` char(2) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_transp_veictransp`
--

DROP TABLE IF EXISTS `nfe_transp_veictransp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_transp_veictransp` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `placa` char(7) DEFAULT NULL,
  `UF` char(2) DEFAULT NULL,
  `RNTC` char(20) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nfe_transp_vol`
--

DROP TABLE IF EXISTS `nfe_transp_vol`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nfe_transp_vol` (
  `id_nfe` int(11) NOT NULL DEFAULT 0,
  `qVol` int(11) DEFAULT NULL,
  `esp` char(60) DEFAULT NULL,
  `marca` char(60) DEFAULT NULL,
  `nVol` char(60) DEFAULT NULL,
  `pesoL` double(14,3) DEFAULT NULL,
  `pesoB` double(14,3) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `parametro_estrutura`
--

DROP TABLE IF EXISTS `parametro_estrutura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `parametro_estrutura` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `regra` varchar(100) NOT NULL DEFAULT '',
  `valor` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `parcelas_baixadas_desktop`
--

DROP TABLE IF EXISTS `parcelas_baixadas_desktop`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `parcelas_baixadas_desktop` (
  `id` int(11) NOT NULL,
  `id_doc` int(11) NOT NULL,
  `id_parcela` int(11) NOT NULL,
  `cod_emp` char(2) NOT NULL,
  `seq_doc` char(7) NOT NULL,
  `seq_itd` char(7) NOT NULL,
  `valor_baixado` double(14,2) DEFAULT NULL,
  `data_baixa` datetime DEFAULT NULL,
  `cod_usu` char(3) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `parcelas_online_baixadas`
--

DROP TABLE IF EXISTS `parcelas_online_baixadas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `parcelas_online_baixadas` (
  `id` int(11) NOT NULL,
  `id_doc` int(11) NOT NULL,
  `cod_emp` char(2) NOT NULL,
  `seq_doc` char(7) NOT NULL,
  `seq_itd` char(7) NOT NULL,
  `valor_baixado` double(14,2) DEFAULT NULL,
  `data_baixa` datetime DEFAULT NULL,
  `cod_usu` char(3) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `produtos_comb`
--

DROP TABLE IF EXISTS `produtos_comb`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `produtos_comb` (
  `cod_pro` char(8) NOT NULL,
  `cProdAnp` varchar(9) NOT NULL,
  `descAnp` varchar(95) NOT NULL,
  PRIMARY KEY (`cod_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `quitacao_debitos`
--

DROP TABLE IF EXISTS `quitacao_debitos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `quitacao_debitos` (
  `id` int(11) NOT NULL DEFAULT 0,
  `cod_cli` varchar(6) NOT NULL DEFAULT '',
  `data` date DEFAULT NULL,
  `obs` text DEFAULT NULL,
  `status` char(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sendmail`
--

DROP TABLE IF EXISTS `sendmail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sendmail` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` text DEFAULT NULL,
  `email` varchar(100) NOT NULL DEFAULT '',
  `sch` text DEFAULT NULL,
  `sendusing` char(1) DEFAULT NULL,
  `smtpserver` varchar(255) DEFAULT NULL,
  `smtpserverport` int(11) DEFAULT NULL,
  `smtpauthenticate` char(1) DEFAULT NULL,
  `sendusername` text DEFAULT NULL,
  `sendpassword` text DEFAULT NULL,
  `smtpusessl` char(1) DEFAULT NULL,
  `subject` text DEFAULT NULL,
  `body` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_cfop`
--

DROP TABLE IF EXISTS `sped_cfop`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_cfop` (
  `codigo` char(4) NOT NULL,
  `Descricao` text DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_cst_cofins`
--

DROP TABLE IF EXISTS `sped_cst_cofins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_cst_cofins` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `descricao` char(200) DEFAULT NULL,
  `tipo` char(20) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_cst_ipi`
--

DROP TABLE IF EXISTS `sped_cst_ipi`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_cst_ipi` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `descricao` char(100) NOT NULL DEFAULT '',
  `tipo` char(50) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_cst_pis`
--

DROP TABLE IF EXISTS `sped_cst_pis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_cst_pis` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `descricao` char(200) NOT NULL DEFAULT '',
  `tipo` char(20) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_cupom`
--

DROP TABLE IF EXISTS `sped_cupom`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_cupom` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `caixa` char(2) DEFAULT NULL,
  `num_ven` char(7) DEFAULT NULL,
  `data` date DEFAULT NULL,
  `hora` char(8) DEFAULT NULL,
  `cod_mod` char(2) DEFAULT NULL,
  `cod_sit` char(2) DEFAULT NULL,
  `num_doc` char(6) DEFAULT NULL,
  `vl_doc` double(14,2) NOT NULL DEFAULT 0.00,
  `vl_pis` double(14,2) NOT NULL DEFAULT 0.00,
  `vl_cofins` double(14,2) NOT NULL DEFAULT 0.00,
  `cpf_adq` char(14) DEFAULT NULL,
  `nom_adq` char(60) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_cupom_itens`
--

DROP TABLE IF EXISTS `sped_cupom_itens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_cupom_itens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_cupom` int(11) DEFAULT NULL,
  `cod_item` char(60) DEFAULT NULL,
  `qtd` double(14,2) NOT NULL DEFAULT 0.00,
  `qtd_canc` double(14,2) NOT NULL DEFAULT 0.00,
  `unid` char(6) DEFAULT NULL,
  `vl_item` double(14,2) NOT NULL DEFAULT 0.00,
  `cst_icms` char(3) DEFAULT NULL,
  `cfop` char(4) DEFAULT NULL,
  `aliq_icms` double(14,2) NOT NULL DEFAULT 0.00,
  `vl_pis` double(14,2) NOT NULL DEFAULT 0.00,
  `vl_cofins` double(14,2) NOT NULL DEFAULT 0.00,
  `vl_icms` double(14,2) DEFAULT 0.00,
  `vl_desconto` double(14,2) DEFAULT 0.00,
  `vl_ipi` double(14,2) DEFAULT 0.00,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_cupom_referenciado`
--

DROP TABLE IF EXISTS `sped_cupom_referenciado`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_cupom_referenciado` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_nf` int(11) NOT NULL DEFAULT 0,
  `cod_mod` char(2) NOT NULL DEFAULT '',
  `ecf_fab` char(21) NOT NULL DEFAULT '',
  `ecf_cx` char(3) NOT NULL DEFAULT '',
  `num_doc` char(8) NOT NULL DEFAULT '',
  `dt_doc` date NOT NULL DEFAULT '0000-00-00',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_ecf`
--

DROP TABLE IF EXISTS `sped_ecf`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_ecf` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cod_mod` char(2) NOT NULL DEFAULT '',
  `ecf_mod` char(20) NOT NULL DEFAULT '',
  `ecf_fab` char(21) NOT NULL DEFAULT '',
  `ecf_cx` char(3) DEFAULT NULL,
  `ativa` char(1) NOT NULL DEFAULT 'S',
  `fim` date DEFAULT NULL,
  `inicio` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_empresa`
--

DROP TABLE IF EXISTS `sped_empresa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_empresa` (
  `codigo` char(2) NOT NULL,
  `cnpj` char(14) NOT NULL,
  `apelido` char(10) NOT NULL,
  `cpf` char(11) DEFAULT NULL,
  `UF` char(2) DEFAULT NULL,
  `IE` char(16) DEFAULT NULL,
  `nome` char(80) DEFAULT NULL,
  `cod_mun` char(7) DEFAULT NULL,
  `im` char(16) DEFAULT NULL,
  `suframa` char(19) DEFAULT NULL,
  `ind_perfil` char(1) NOT NULL DEFAULT 'A',
  `ind_atv` char(1) NOT NULL DEFAULT '0',
  `fantasia` char(60) NOT NULL,
  `cep` char(8) DEFAULT NULL,
  `endereco` char(60) DEFAULT NULL,
  `numero` char(10) DEFAULT NULL,
  `complemento` char(60) DEFAULT NULL,
  `bairro` char(60) DEFAULT NULL,
  `fone` char(11) DEFAULT NULL,
  `fax` char(11) DEFAULT NULL,
  `email` char(200) DEFAULT NULL,
  `caminho_certificado` varchar(250) DEFAULT NULL,
  `senha_certificado` varchar(50) DEFAULT NULL,
  `idcsc` varchar(10) DEFAULT NULL,
  `token` varchar(50) DEFAULT NULL,
  `caminho_logo` varchar(255) DEFAULT NULL,
  `caminho_qrcodedoc` varchar(255) DEFAULT NULL,
  `cor` char(20) DEFAULT NULL,
  `crt` char(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_evento`
--

DROP TABLE IF EXISTS `sped_evento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_evento` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `descricao` mediumtext DEFAULT NULL,
  `periodicidade` char(1) NOT NULL DEFAULT 'E',
  `limite` varchar(5) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_evento_registros`
--

DROP TABLE IF EXISTS `sped_evento_registros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_evento_registros` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_evento` int(11) NOT NULL DEFAULT 0,
  `registro` char(4) NOT NULL DEFAULT '',
  `nivel` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_genero`
--

DROP TABLE IF EXISTS `sped_genero`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_genero` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `descricao` mediumtext NOT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_ind_frt`
--

DROP TABLE IF EXISTS `sped_ind_frt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_ind_frt` (
  `codigo` int(11) NOT NULL DEFAULT 0,
  `descricao` char(60) NOT NULL DEFAULT '',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_informacao_complementar`
--

DROP TABLE IF EXISTS `sped_informacao_complementar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_informacao_complementar` (
  `codigo` int(11) NOT NULL AUTO_INCREMENT,
  `texto` mediumtext DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_nat400`
--

DROP TABLE IF EXISTS `sped_nat400`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_nat400` (
  `codigo` char(4) NOT NULL DEFAULT '',
  `descricao` char(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_nf`
--

DROP TABLE IF EXISTS `sped_nf`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_nf` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `IND_OPER` char(1) NOT NULL DEFAULT '',
  `IND_EMIT` char(1) NOT NULL DEFAULT '',
  `COD_PART` char(60) DEFAULT NULL,
  `COD_MOD` char(2) DEFAULT NULL,
  `COD_SIT` char(2) DEFAULT NULL,
  `SER` char(2) DEFAULT NULL,
  `NUM_DOC` char(12) DEFAULT NULL,
  `CHV_NFE` char(44) DEFAULT NULL,
  `DT_DOC` char(30) DEFAULT NULL,
  `DT_E_S` char(30) DEFAULT NULL,
  `VL_DOC` double(14,2) NOT NULL DEFAULT 0.00,
  `IND_PGTO` char(1) DEFAULT NULL,
  `VL_DESC` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_ABAT_NT` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_MERC` double(14,2) NOT NULL DEFAULT 0.00,
  `IND_FRT` char(1) NOT NULL DEFAULT '9',
  `VL_FRT` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_SEG` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_OUT_DA` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_BC_ICMS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_ICMS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_BC_ICMS_ST` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_ICMS_ST` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_IPI` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_PIS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_COFINS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_PIS_ST` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_COFINS_ST` double(14,2) NOT NULL DEFAULT 0.00,
  `status` int(1) NOT NULL DEFAULT 1,
  `num_ven` char(7) DEFAULT NULL,
  `Data` date DEFAULT NULL,
  `cod_emp` char(2) DEFAULT '01',
  `tipo_entrada` char(10) DEFAULT '01',
  `cod_usu` char(3) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `COD_PART` (`COD_PART`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_nf_c300`
--

DROP TABLE IF EXISTS `sped_nf_c300`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_nf_c300` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cod_mod` char(2) NOT NULL DEFAULT '',
  `ser` char(4) DEFAULT NULL,
  `sub` char(3) DEFAULT NULL,
  `num_doc_ini` char(6) DEFAULT NULL,
  `num_doc_fin` char(6) DEFAULT NULL,
  `dt_doc` date DEFAULT NULL,
  `vl_doc` double(14,2) DEFAULT NULL,
  `vl_pis` double(14,2) DEFAULT NULL,
  `vl_cofins` double(14,2) DEFAULT NULL,
  `cod_cta` char(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_nf_c310`
--

DROP TABLE IF EXISTS `sped_nf_c310`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_nf_c310` (
  `id` int(11) NOT NULL DEFAULT 0,
  `num_doc_canc` char(6) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`,`num_doc_canc`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_nf_energia`
--

DROP TABLE IF EXISTS `sped_nf_energia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_nf_energia` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `IND_OPER` char(1) NOT NULL DEFAULT '0',
  `IND_EMIT` char(60) DEFAULT NULL,
  `COD_MOD` char(2) DEFAULT NULL,
  `cod_part` char(60) DEFAULT NULL,
  `COD_SIT` char(2) DEFAULT NULL,
  `SER` char(4) DEFAULT NULL,
  `SUB` char(3) DEFAULT NULL,
  `COD_CONS` char(2) DEFAULT NULL,
  `NUM_DOC` char(9) DEFAULT NULL,
  `DT_DOC` date DEFAULT NULL,
  `DT_E_S` date DEFAULT NULL,
  `VL_DESC` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_FORN` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_SERV_NT` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_TERC` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_DA` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_BC_ICMS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_ICMS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_ICMS_ST` double(14,2) NOT NULL DEFAULT 0.00,
  `COD_INF` char(6) DEFAULT NULL,
  `VL_PIS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_COFINS` double(14,2) NOT NULL DEFAULT 0.00,
  `TP_LIGACAO` int(11) NOT NULL DEFAULT 1,
  `COD_GRUPO_TENSAO` char(2) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_nf_ic`
--

DROP TABLE IF EXISTS `sped_nf_ic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_nf_ic` (
  `id_nf` int(11) NOT NULL DEFAULT 0,
  `codigo` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id_nf`,`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_nf_itens`
--

DROP TABLE IF EXISTS `sped_nf_itens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_nf_itens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_nf` int(11) NOT NULL DEFAULT 0,
  `NUM_ITEM` int(11) NOT NULL DEFAULT 0,
  `COD_ITEM` char(60) NOT NULL DEFAULT '',
  `DESCR_COMPL` char(150) DEFAULT NULL,
  `QTD` double(14,2) NOT NULL DEFAULT 0.00,
  `UNID` char(60) NOT NULL DEFAULT '',
  `VL_ITEM` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_DESC` double(14,2) NOT NULL DEFAULT 0.00,
  `IND_MOV` char(1) NOT NULL DEFAULT '0',
  `CST_ICMS` char(3) NOT NULL DEFAULT '',
  `CFOP` char(4) NOT NULL DEFAULT '',
  `COD_NAT` char(10) DEFAULT NULL,
  `VL_BC_ICMS` double(14,2) DEFAULT NULL,
  `ALIQ_ICMS` double(14,2) DEFAULT NULL,
  `VL_ICMS` double(14,2) DEFAULT NULL,
  `VL_BC_ICMS_ST` double(14,2) DEFAULT NULL,
  `ALIQ_ST` double(14,2) DEFAULT NULL,
  `VL_ICMS_ST` double(14,2) DEFAULT NULL,
  `IND_APUR` char(1) NOT NULL DEFAULT '0',
  `CST_IPI` char(2) DEFAULT NULL,
  `COD_ENQ` char(3) DEFAULT NULL,
  `VL_BC_IPI` double(14,2) DEFAULT NULL,
  `ALIQ_IPI` double(14,2) DEFAULT NULL,
  `VL_IPI` double(14,2) DEFAULT NULL,
  `CST_PIS` char(2) DEFAULT NULL,
  `VL_BC_PIS` double(14,2) DEFAULT NULL,
  `ALIQ_PIS` double(14,2) DEFAULT NULL,
  `QUANT_BC_PIS` double(14,2) DEFAULT NULL,
  `ALIQ_PIS_r` double(14,2) DEFAULT NULL,
  `VL_PIS` double(14,2) DEFAULT NULL,
  `CST_COFINS` char(2) DEFAULT NULL,
  `VL_BC_COFINS` double(14,2) DEFAULT NULL,
  `ALIQ_COFINS` double(14,2) DEFAULT NULL,
  `QUANT_BC_COFINS` double(14,2) DEFAULT NULL,
  `ALIQ_COFINS_r` double(14,2) DEFAULT NULL,
  `VL_COFINS` double(14,2) DEFAULT NULL,
  `COD_CTA` char(20) DEFAULT NULL,
  `Qtd_Saida` double(14,2) unsigned DEFAULT NULL,
  `Unid_Saida` char(4) DEFAULT 'UN',
  `cod_pro` char(8) DEFAULT 'UN',
  `cEAN` char(20) DEFAULT 'UN',
  `qtd_convert` double(14,2) DEFAULT 0.00,
  `cNCM` char(20) DEFAULT '0.00',
  `custo` double(14,4) NOT NULL DEFAULT 0.0000,
  `Preco` double(14,2) DEFAULT NULL,
  `alterapreco` char(1) DEFAULT 'N',
  PRIMARY KEY (`id`),
  KEY `COD_ITEM` (`COD_ITEM`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_nfc510`
--

DROP TABLE IF EXISTS `sped_nfc510`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_nfc510` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_nf` int(11) NOT NULL DEFAULT 0,
  `NUM_ITEM` int(11) NOT NULL DEFAULT 0,
  `COD_CLASS` char(4) DEFAULT NULL,
  `QTD` double(14,2) NOT NULL DEFAULT 0.00,
  `UNID` char(6) DEFAULT NULL,
  `VL_ITEM` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_DESC` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_DA` double(14,2) NOT NULL DEFAULT 0.00,
  `CST_ICMS` char(3) DEFAULT NULL,
  `CFOP` char(4) DEFAULT NULL,
  `VL_BC_ICMS` double(14,2) NOT NULL DEFAULT 0.00,
  `ALIQ_ICMS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_ICMS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_BC_ICMS_ST` double(14,2) NOT NULL DEFAULT 0.00,
  `ALIQ_ST` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_ICMS_ST` double(14,2) NOT NULL DEFAULT 0.00,
  `IND_REC` char(1) NOT NULL DEFAULT '1',
  `COD_PART` char(10) DEFAULT NULL,
  `VL_PIS` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_COFINS` double(14,2) NOT NULL DEFAULT 0.00,
  `COD_CTA` char(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_nfc600`
--

DROP TABLE IF EXISTS `sped_nfc600`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_nfc600` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `COD_MOD` char(2) NOT NULL DEFAULT '',
  `cod_mun` char(7) NOT NULL DEFAULT '',
  `ser` char(4) DEFAULT NULL,
  `sub` char(3) DEFAULT NULL,
  `cod_cons` char(2) DEFAULT NULL,
  `qtd_cons` int(11) DEFAULT NULL,
  `qtd_canc` int(11) DEFAULT NULL,
  `dt_doc` date DEFAULT NULL,
  `vl_doc` double(14,2) DEFAULT NULL,
  `vl_desc` double(14,2) DEFAULT NULL,
  `cons` double(14,2) DEFAULT NULL,
  `vl_forn` double(14,2) DEFAULT NULL,
  `vl_serv_nt` double(14,2) DEFAULT NULL,
  `vl_terc` double(14,2) DEFAULT NULL,
  `vl_da` double(14,2) DEFAULT NULL,
  `vl_bc_icms` double(14,2) DEFAULT NULL,
  `vl_icms` double(14,2) DEFAULT NULL,
  `vl_bc_icms_st` double(14,2) DEFAULT NULL,
  `vl_icms_st` double(14,2) DEFAULT NULL,
  `vl_pis` double(14,2) DEFAULT NULL,
  `vl_cofins` double(14,2) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_observacoes_nf`
--

DROP TABLE IF EXISTS `sped_observacoes_nf`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_observacoes_nf` (
  `codigo` int(11) NOT NULL AUTO_INCREMENT,
  `texto` mediumtext DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_origem`
--

DROP TABLE IF EXISTS `sped_origem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_origem` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `descricao` text DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_participante`
--

DROP TABLE IF EXISTS `sped_participante`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_participante` (
  `codigo` int(11) NOT NULL AUTO_INCREMENT,
  `NOME` char(100) NOT NULL DEFAULT '',
  `COD_PAIS` char(5) DEFAULT NULL,
  `CNPJ` char(14) DEFAULT NULL,
  `CPF` char(11) DEFAULT NULL,
  `IE` char(14) DEFAULT NULL,
  `COD_MUN` char(7) DEFAULT NULL,
  `SUFRAMA` char(9) DEFAULT NULL,
  `ENDERECO` char(60) DEFAULT NULL,
  `NUMERO` char(10) DEFAULT NULL,
  `COMPLEMENTO` char(60) DEFAULT NULL,
  `BAIRRO` char(60) DEFAULT NULL,
  `cod_cli` char(7) DEFAULT NULL,
  `cod_for` char(7) DEFAULT NULL,
  `cep` char(8) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_pc_contabil`
--

DROP TABLE IF EXISTS `sped_pc_contabil`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_pc_contabil` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dt_alt` date NOT NULL DEFAULT '0000-00-00',
  `cod_nat_cc` char(2) NOT NULL DEFAULT '',
  `ind_cta` char(1) NOT NULL DEFAULT '',
  `nivel` int(11) NOT NULL DEFAULT 0,
  `cod_cta` char(60) DEFAULT NULL,
  `nome_cta` char(60) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_redz`
--

DROP TABLE IF EXISTS `sped_redz`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_redz` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `caixa` char(2) NOT NULL DEFAULT '',
  `dt_doc` date NOT NULL DEFAULT '0000-00-00',
  `cro` int(11) NOT NULL DEFAULT 0,
  `crz` int(11) NOT NULL DEFAULT 0,
  `NUM_COO_FIN` int(11) NOT NULL DEFAULT 0,
  `GT_FIN` double(14,2) NOT NULL DEFAULT 0.00,
  `VL_BRT` double(14,2) NOT NULL DEFAULT 0.00,
  `vl_pis` double(14,2) NOT NULL DEFAULT 0.00,
  `vl_cofins` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_redz_tot`
--

DROP TABLE IF EXISTS `sped_redz_tot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_redz_tot` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_red` int(11) NOT NULL DEFAULT 0,
  `id_tot` int(11) DEFAULT NULL,
  `valor` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_imp` char(3) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_registros`
--

DROP TABLE IF EXISTS `sped_registros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_registros` (
  `registro` char(4) NOT NULL DEFAULT '',
  `descricao` char(200) NOT NULL DEFAULT '',
  `pai` char(4) NOT NULL DEFAULT '',
  PRIMARY KEY (`registro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_situacao_doc`
--

DROP TABLE IF EXISTS `sped_situacao_doc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_situacao_doc` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `descricao` char(200) NOT NULL DEFAULT '',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_tipo_consumo_agua`
--

DROP TABLE IF EXISTS `sped_tipo_consumo_agua`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_tipo_consumo_agua` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `nome` char(200) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_tipo_consumo_energia`
--

DROP TABLE IF EXISTS `sped_tipo_consumo_energia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_tipo_consumo_energia` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `nome` char(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_tipo_doc_icms`
--

DROP TABLE IF EXISTS `sped_tipo_doc_icms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_tipo_doc_icms` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `descricao` char(60) NOT NULL DEFAULT '',
  `modelo` char(20) DEFAULT NULL,
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_tipo_item`
--

DROP TABLE IF EXISTS `sped_tipo_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_tipo_item` (
  `codigo` char(2) NOT NULL DEFAULT '',
  `descricao` char(80) NOT NULL DEFAULT '',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_tiponf_energia`
--

DROP TABLE IF EXISTS `sped_tiponf_energia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_tiponf_energia` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` char(80) DEFAULT NULL,
  `cfop` char(4) DEFAULT NULL,
  `cst` char(3) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_totalizador_redz`
--

DROP TABLE IF EXISTS `sped_totalizador_redz`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_totalizador_redz` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(10) DEFAULT NULL,
  `nome` varchar(100) DEFAULT NULL,
  `descricao` text DEFAULT NULL,
  `cod_imp` char(3) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sped_unidades`
--

DROP TABLE IF EXISTS `sped_unidades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sped_unidades` (
  `unidade` char(4) NOT NULL DEFAULT '',
  `descricao` char(80) NOT NULL DEFAULT '',
  PRIMARY KEY (`unidade`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_acertofin`
--

DROP TABLE IF EXISTS `tab_acertofin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_acertofin` (
  `seq_FIN` char(7) NOT NULL DEFAULT '',
  `seq_ace` char(7) NOT NULL DEFAULT '',
  `tipo_fin` char(1) NOT NULL DEFAULT 'C',
  PRIMARY KEY (`seq_ace`,`seq_FIN`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_acertos`
--

DROP TABLE IF EXISTS `tab_acertos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_acertos` (
  `seq_ace` char(7) NOT NULL DEFAULT '',
  `data_ace` date DEFAULT '0000-00-00',
  `hora_ace` char(5) DEFAULT NULL,
  `cod_cli` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `cod_for` char(3) NOT NULL DEFAULT '',
  `valor_ace` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `cobranca_ace` char(1) NOT NULL DEFAULT 'L',
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `tipo_ter` char(1) NOT NULL DEFAULT 'C',
  `comissao_ace` double(14,2) NOT NULL DEFAULT 0.00,
  `diferenca_ace` double(14,2) NOT NULL DEFAULT 0.00,
  `entrada_ace` double(14,2) NOT NULL DEFAULT 0.00,
  `tipo_cai` char(1) DEFAULT NULL,
  `status_ace` char(1) NOT NULL DEFAULT '2',
  `ipusu_ace` char(20) DEFAULT NULL,
  `queima` char(1) DEFAULT 'N',
  PRIMARY KEY (`seq_ace`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_acertosabertos`
--

DROP TABLE IF EXISTS `tab_acertosabertos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_acertosabertos` (
  `seq_ace` char(7) NOT NULL DEFAULT '',
  `data_ace` date NOT NULL DEFAULT '0000-00-00',
  `hora_ace` char(5) NOT NULL DEFAULT '',
  `cod_cli` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `cod_for` char(3) NOT NULL DEFAULT '',
  `valor_ace` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `cobranca_ace` char(1) NOT NULL DEFAULT 'L',
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `tipo_ter` char(1) NOT NULL DEFAULT 'C',
  `comissao_ace` double(14,2) NOT NULL DEFAULT 0.00,
  `diferenca_ace` double(14,2) NOT NULL DEFAULT 0.00,
  `entrada_ace` double(14,2) NOT NULL DEFAULT 0.00,
  `tipo_cai` char(1) NOT NULL DEFAULT '',
  `status_ace` char(1) NOT NULL DEFAULT '1',
  `ipusu_ace` char(20) NOT NULL DEFAULT '',
  `queima` char(1) DEFAULT 'N',
  PRIMARY KEY (`seq_ace`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_acertoscanc`
--

DROP TABLE IF EXISTS `tab_acertoscanc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_acertoscanc` (
  `seq_ace` char(7) NOT NULL DEFAULT '',
  `data_can` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_ace`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_altpreco`
--

DROP TABLE IF EXISTS `tab_altpreco`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_altpreco` (
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `antigo_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `novo_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `data_alt` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `status_alt` char(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`cod_pro`,`data_alt`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_autorizados`
--

DROP TABLE IF EXISTS `tab_autorizados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_autorizados` (
  `cod_cli` char(5) NOT NULL DEFAULT '',
  `seq_aut` int(11) NOT NULL DEFAULT 0,
  `nome_aut` char(40) NOT NULL DEFAULT '',
  `status_aut` char(1) NOT NULL DEFAULT '1',
  `cod_tip` char(2) NOT NULL DEFAULT '00',
  PRIMARY KEY (`cod_cli`,`seq_aut`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_baixafin`
--

DROP TABLE IF EXISTS `tab_baixafin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_baixafin` (
  `seq_bai` int(11) NOT NULL DEFAULT 0,
  `seq_fin` char(7) NOT NULL DEFAULT '',
  `seq_cab` char(7) NOT NULL DEFAULT '',
  `esp_bai` char(3) NOT NULL DEFAULT 'DFI',
  `valor_bai` double(14,2) NOT NULL DEFAULT 0.00,
  `desconto_bai` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`seq_bai`,`seq_cab`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_baixaitd`
--

DROP TABLE IF EXISTS `tab_baixaitd`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_baixaitd` (
  `seq_itd` char(7) NOT NULL DEFAULT '',
  `seq_bai` int(11) NOT NULL DEFAULT 0,
  `valor_bai` double(14,2) NOT NULL DEFAULT 0.00,
  `esp_bai` char(3) NOT NULL DEFAULT '',
  `data_bai` date NOT NULL DEFAULT '0000-00-00',
  `seq_fin` char(7) NOT NULL DEFAULT '',
  `cod_usu` char(3) NOT NULL DEFAULT '001',
  PRIMARY KEY (`seq_itd`,`seq_bai`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_baixaitd2`
--

DROP TABLE IF EXISTS `tab_baixaitd2`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_baixaitd2` (
  `seq_itd` char(7) NOT NULL DEFAULT '',
  `seq_bai` int(11) NOT NULL DEFAULT 0,
  `valor_bai` double(14,2) NOT NULL DEFAULT 0.00,
  `esp_bai` char(3) NOT NULL DEFAULT '',
  `data_bai` date NOT NULL DEFAULT '0000-00-00',
  `seq_fin` char(7) NOT NULL DEFAULT '',
  `cod_usu` char(3) NOT NULL DEFAULT '001',
  `seq_cab` char(7) NOT NULL DEFAULT '0',
  `cod_cob` char(3) NOT NULL DEFAULT '',
  `hora_bai` char(5) DEFAULT '08:00',
  `desconto_bai` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_cai` char(3) DEFAULT NULL,
  PRIMARY KEY (`seq_itd`,`seq_cab`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_baixavenfin`
--

DROP TABLE IF EXISTS `tab_baixavenfin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_baixavenfin` (
  `num_ven` char(7) NOT NULL DEFAULT '',
  `seq_bai` int(11) NOT NULL DEFAULT 0,
  `valor_bai` double(14,2) NOT NULL DEFAULT 0.00,
  `esp_bai` char(3) NOT NULL DEFAULT '',
  `data_bai` date NOT NULL DEFAULT '0000-00-00',
  `seq_fin` char(7) NOT NULL DEFAULT '',
  `cod_usu` char(3) NOT NULL DEFAULT '001',
  PRIMARY KEY (`num_ven`,`seq_bai`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_bancos`
--

DROP TABLE IF EXISTS `tab_bancos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_bancos` (
  `COD_BCO` char(3) NOT NULL DEFAULT '',
  `NOME_BCO` char(50) NOT NULL DEFAULT '',
  PRIMARY KEY (`COD_BCO`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_caixa`
--

DROP TABLE IF EXISTS `tab_caixa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_caixa` (
  `SEQ_CAI` char(7) NOT NULL DEFAULT '',
  `DATA_CAI` date NOT NULL DEFAULT '0000-00-00',
  `VALOR_CAI` double(14,2) NOT NULL DEFAULT 0.00,
  `entrada_CAI` double(14,2) NOT NULL DEFAULT 0.00,
  `troco_CAI` double(14,2) NOT NULL DEFAULT 0.00,
  `HISTORICO_CAI` char(50) NOT NULL DEFAULT '',
  `TIPO_CAI` char(1) NOT NULL DEFAULT '',
  `esp_cai` char(3) NOT NULL DEFAULT '',
  `NUM_VEN` char(7) DEFAULT NULL,
  `cod_con` char(2) NOT NULL DEFAULT '01',
  `cod_cai` char(2) NOT NULL DEFAULT '01',
  `ip_cai` char(11) NOT NULL DEFAULT '00000000000',
  `cod_usu` char(3) NOT NULL DEFAULT '001',
  `saldo_Cai` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_tur` char(1) NOT NULL DEFAULT '1',
  `cod_pla` char(3) NOT NULL DEFAULT '000',
  `visivel_cai` char(1) NOT NULL DEFAULT 'S',
  `desconto_cai` double(14,2) NOT NULL DEFAULT 0.00,
  `hora_cai` datetime DEFAULT NULL,
  `saida_cai` double(14,2) DEFAULT 0.00,
  `excluido_cai` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`SEQ_CAI`),
  KEY `tipocai` (`cod_cai`,`esp_cai`,`SEQ_CAI`),
  KEY `ccai` (`cod_cai`,`SEQ_CAI`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_caixas`
--

DROP TABLE IF EXISTS `tab_caixas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_caixas` (
  `cod_cai` char(2) NOT NULL DEFAULT '',
  `nome_cai` char(20) NOT NULL DEFAULT '',
  `ip_cai` char(20) NOT NULL DEFAULT '',
  `COD_CON` char(3) DEFAULT NULL,
  `status_Cai` char(1) NOT NULL DEFAULT 'A',
  `cod_tur` char(1) NOT NULL DEFAULT '1',
  `impressora_cai` char(1) NOT NULL DEFAULT 'B',
  `modo_cai` char(1) NOT NULL DEFAULT '0',
  `bloqueado_cai` char(1) NOT NULL DEFAULT 'N',
  `serie_nfe` char(4) DEFAULT NULL,
  PRIMARY KEY (`cod_cai`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_caixasip`
--

DROP TABLE IF EXISTS `tab_caixasip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_caixasip` (
  `cod_cai` char(2) NOT NULL DEFAULT '',
  `ip_cai` char(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_cai`,`ip_cai`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_cancelamentos`
--

DROP TABLE IF EXISTS `tab_cancelamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_cancelamentos` (
  `num_ven` char(7) NOT NULL DEFAULT '',
  `data_can` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `valor_ven` double(14,2) NOT NULL DEFAULT 0.00,
  `tipo_ven` char(1) NOT NULL DEFAULT 'R',
  `cod_cai` char(2) NOT NULL DEFAULT '',
  `cod_tur` char(2) NOT NULL DEFAULT '',
  PRIMARY KEY (`num_ven`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_cargos`
--

DROP TABLE IF EXISTS `tab_cargos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_cargos` (
  `COD_CAR` char(3) NOT NULL DEFAULT '',
  `NOME_CAR` char(20) NOT NULL DEFAULT '',
  `venda_Car` char(1) NOT NULL DEFAULT 'N',
  `cobranca_car` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`COD_CAR`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_cargoscomiss`
--

DROP TABLE IF EXISTS `tab_cargoscomiss`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_cargoscomiss` (
  `cod_car` char(3) NOT NULL DEFAULT '',
  `tipo_cai` char(3) NOT NULL DEFAULT '',
  `comiss_car` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`cod_car`,`tipo_cai`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_cat`
--

DROP TABLE IF EXISTS `tab_cat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_cat` (
  `cod_cat` char(3) NOT NULL DEFAULT '',
  `nome_cat` char(50) DEFAULT NULL,
  PRIMARY KEY (`cod_cat`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_categorias`
--

DROP TABLE IF EXISTS `tab_categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_categorias` (
  `cod_cat` char(3) NOT NULL DEFAULT '',
  `nome_cat` char(50) DEFAULT NULL,
  `atacado_cat` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`cod_cat`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_chequedep`
--

DROP TABLE IF EXISTS `tab_chequedep`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_chequedep` (
  `seq_che` char(7) NOT NULL DEFAULT '',
  `data_dep` date NOT NULL DEFAULT '0000-00-00',
  `cod_con` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_che`,`data_dep`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_chequedev`
--

DROP TABLE IF EXISTS `tab_chequedev`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_chequedev` (
  `seq_che` char(7) NOT NULL DEFAULT '',
  `seq_dev` int(11) NOT NULL DEFAULT 0,
  `data_dev` date NOT NULL DEFAULT '0000-00-00',
  `motivo_dev` char(30) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_che`,`seq_dev`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_chequepag`
--

DROP TABLE IF EXISTS `tab_chequepag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_chequepag` (
  `seq_che` char(7) NOT NULL DEFAULT '',
  `num_che` char(12) NOT NULL DEFAULT '',
  `cod_con` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_che`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_chequerec`
--

DROP TABLE IF EXISTS `tab_chequerec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_chequerec` (
  `seq_che` char(7) NOT NULL DEFAULT '',
  `num_che` char(12) NOT NULL DEFAULT '',
  `cod_bco` char(3) NOT NULL DEFAULT '',
  `age_che` char(8) NOT NULL DEFAULT '',
  `cco_che` char(12) NOT NULL DEFAULT '',
  `cpf_che` char(18) NOT NULL DEFAULT '',
  `nome_che` char(50) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_che`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_cheques`
--

DROP TABLE IF EXISTS `tab_cheques`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_cheques` (
  `seq_che` char(7) NOT NULL DEFAULT '',
  `num_che` char(12) DEFAULT NULL,
  `cod_bco` char(3) DEFAULT NULL,
  `age_che` char(8) DEFAULT NULL,
  `cco_che` char(12) DEFAULT NULL,
  `nome_che` char(50) DEFAULT NULL,
  `cpf_che` char(18) DEFAULT NULL,
  `valor_che` double(14,2) DEFAULT NULL,
  `venc_che` date DEFAULT '0000-00-00',
  `cod_ter` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `tipo_che` char(1) DEFAULT NULL,
  `seq_doc` char(7) DEFAULT NULL,
  `parc_che` int(11) DEFAULT 0,
  `num_ven` char(7) DEFAULT NULL,
  `dep_che` date DEFAULT '0000-00-00',
  `cod_usu` char(3) DEFAULT NULL,
  `cod_con` char(3) NOT NULL DEFAULT '001',
  `status_Che` char(1) NOT NULL DEFAULT '1',
  `hora_che` char(5) NOT NULL DEFAULT '00:00',
  `cod_loc` char(2) DEFAULT NULL,
  PRIMARY KEY (`seq_che`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_chequesback`
--

DROP TABLE IF EXISTS `tab_chequesback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_chequesback` (
  `seq_che` char(7) NOT NULL DEFAULT '',
  `num_che` char(12) NOT NULL DEFAULT '',
  `cod_bco` char(3) NOT NULL DEFAULT '',
  `age_che` char(8) DEFAULT NULL,
  `cco_che` char(12) DEFAULT NULL,
  `nome_che` char(50) DEFAULT NULL,
  `cpf_che` char(18) NOT NULL DEFAULT '',
  `valor_che` double(14,2) DEFAULT NULL,
  `venc_che` date NOT NULL DEFAULT '0000-00-00',
  `cod_ter` char(5) NOT NULL DEFAULT '',
  `tipo_che` char(1) NOT NULL DEFAULT '',
  `seq_doc` char(7) DEFAULT NULL,
  `parc_che` int(11) NOT NULL DEFAULT 0,
  `num_ven` char(7) DEFAULT NULL,
  `dep_che` date NOT NULL DEFAULT '0000-00-00',
  `cod_usu` char(3) DEFAULT NULL,
  `cod_con` char(3) NOT NULL DEFAULT '001',
  `status_Che` char(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`seq_che`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_chv`
--

DROP TABLE IF EXISTS `tab_chv`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_chv` (
  `seq_cai` char(7) NOT NULL DEFAULT '',
  `num_che` char(12) NOT NULL DEFAULT '',
  `cod_bco` char(3) NOT NULL DEFAULT '',
  `age_che` char(8) NOT NULL DEFAULT '',
  `cco_che` char(12) NOT NULL DEFAULT '',
  `cpf_che` char(18) NOT NULL DEFAULT '',
  `nome_che` char(50) NOT NULL DEFAULT '',
  `valor_che` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`seq_cai`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_cidades`
--

DROP TABLE IF EXISTS `tab_cidades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_cidades` (
  `cod_cid` char(7) NOT NULL DEFAULT '',
  `nome_cid` char(40) DEFAULT NULL,
  `uf_cid` char(2) DEFAULT NULL,
  `cod_mun` char(7) DEFAULT NULL,
  PRIMARY KEY (`cod_cid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_clausulas`
--

DROP TABLE IF EXISTS `tab_clausulas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_clausulas` (
  `seq_con` int(11) NOT NULL DEFAULT 0,
  `seq_cla` int(11) NOT NULL DEFAULT 0,
  `cab_cla` varchar(250) NOT NULL DEFAULT '',
  `texto_cla` text NOT NULL,
  PRIMARY KEY (`seq_con`,`seq_cla`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_clientes`
--

DROP TABLE IF EXISTS `tab_clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_clientes` (
  `cod_cli` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `nome_cli` varchar(50) NOT NULL DEFAULT '',
  `datanasc_cli` date DEFAULT '0000-00-00',
  `cpf_cli` varchar(18) DEFAULT NULL,
  `endereco_cli` varchar(60) DEFAULT NULL,
  `bairro_cli` varchar(30) DEFAULT NULL,
  `cep_cli` varchar(10) DEFAULT NULL,
  `referencia_cli` varchar(30) DEFAULT NULL,
  `cidade_cli` varchar(30) DEFAULT NULL,
  `uf_cli` char(2) DEFAULT NULL,
  `data_cli` date DEFAULT '0000-00-00',
  `obs_cli` text DEFAULT NULL,
  `status_cli` char(1) DEFAULT '1',
  `rg_cli` varchar(18) DEFAULT NULL,
  `mae_cli` varchar(40) DEFAULT NULL,
  `pai_cli` varchar(40) DEFAULT NULL,
  `cod_old` varchar(10) DEFAULT NULL,
  `mens_cli` char(1) DEFAULT 'N',
  `limite_cli` double(14,2) NOT NULL DEFAULT 0.00,
  `endcom_cli` varchar(60) DEFAULT NULL,
  `usucad_cli` char(3) DEFAULT '001',
  `prazo_cli` int(10) unsigned NOT NULL DEFAULT 0,
  `tipo_cli` char(1) DEFAULT 'F',
  `credito_cli` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_set` varchar(5) DEFAULT '00000',
  `cod_gru` char(3) DEFAULT '000',
  `cobranca_cli` char(1) DEFAULT '1',
  `localtrab_cli` varchar(60) DEFAULT NULL,
  `endtrab_cli` varchar(40) DEFAULT NULL,
  `setortrab_cli` varchar(5) DEFAULT NULL,
  `teltrab_cli` varchar(16) DEFAULT NULL,
  `ceptrab_cli` varchar(10) DEFAULT NULL,
  `cod_org` varchar(5) DEFAULT NULL,
  `dataalt_cli` date DEFAULT '0000-00-00',
  `sexo_cli` char(1) DEFAULT 'F',
  `email_cli` varchar(100) DEFAULT NULL,
  `logradouro` varchar(100) DEFAULT NULL,
  `complemento` varchar(100) DEFAULT NULL,
  `numero` varchar(10) DEFAULT NULL,
  `creditosuspenso_cli` char(1) DEFAULT 'N',
  `ie_cli` varchar(20) DEFAULT NULL,
  `cod_cid` varchar(20) DEFAULT '5201108',
  `telefone_cli` varchar(20) DEFAULT NULL,
  `Logradouro_cli` varchar(60) DEFAULT '',
  `numero_cli` varchar(60) DEFAULT '',
  `complemento_cli` varchar(60) DEFAULT '',
  `indiedest_cli` char(1) NOT NULL DEFAULT '9',
  `cfop_cli` varchar(4) DEFAULT '5102',
  `tipoicms_cli` varchar(4) DEFAULT '102',
  `especial_cli` char(1) NOT NULL DEFAULT 'N',
  `telefones` char(200) DEFAULT NULL,
  PRIMARY KEY (`cod_cli`),
  KEY `codold` (`cod_old`),
  KEY `fbairro` (`bairro_cli`),
  KEY `fCodSet` (`cod_set`),
  KEY `ind_nome` (`nome_cli`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_clientes_`
--

DROP TABLE IF EXISTS `tab_clientes_`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_clientes_` (
  `cod_cli` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `nome_cli` varchar(50) NOT NULL DEFAULT '',
  `datanasc_cli` date DEFAULT '0000-00-00',
  `cpf_cli` varchar(18) DEFAULT NULL,
  `endereco_cli` varchar(60) DEFAULT NULL,
  `bairro_cli` varchar(30) DEFAULT NULL,
  `cep_cli` varchar(10) DEFAULT NULL,
  `referencia_cli` varchar(30) DEFAULT NULL,
  `cidade_cli` varchar(30) DEFAULT NULL,
  `uf_cli` char(2) DEFAULT NULL,
  `data_cli` date DEFAULT '0000-00-00',
  `obs_cli` text DEFAULT NULL,
  `status_cli` char(1) DEFAULT '1',
  `rg_cli` varchar(18) DEFAULT NULL,
  `mae_cli` varchar(40) DEFAULT NULL,
  `pai_cli` varchar(40) DEFAULT NULL,
  `cod_old` varchar(10) DEFAULT NULL,
  `mens_cli` char(1) DEFAULT 'N',
  `limite_cli` double(14,2) NOT NULL DEFAULT 0.00,
  `endcom_cli` varchar(60) DEFAULT NULL,
  `usucad_cli` char(3) DEFAULT '001',
  `prazo_cli` int(10) unsigned NOT NULL DEFAULT 0,
  `tipo_cli` char(1) DEFAULT 'F',
  `credito_cli` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_set` varchar(5) DEFAULT '00000',
  `cod_gru` char(3) DEFAULT '000',
  `cobranca_cli` char(1) DEFAULT '1',
  `localtrab_cli` varchar(60) DEFAULT NULL,
  `endtrab_cli` varchar(40) DEFAULT NULL,
  `setortrab_cli` varchar(5) DEFAULT NULL,
  `teltrab_cli` varchar(16) DEFAULT NULL,
  `ceptrab_cli` varchar(10) DEFAULT NULL,
  `cod_org` varchar(5) DEFAULT NULL,
  `dataalt_cli` date DEFAULT '0000-00-00',
  `sexo_cli` char(1) DEFAULT 'F',
  `email_cli` varchar(100) DEFAULT NULL,
  `logradouro` varchar(100) DEFAULT NULL,
  `complemento` varchar(100) DEFAULT NULL,
  `numero` varchar(10) DEFAULT NULL,
  `creditosuspenso_cli` char(1) DEFAULT 'N',
  `ie_cli` varchar(20) DEFAULT NULL,
  `cod_cid` varchar(20) DEFAULT '5201108',
  `telefone_cli` varchar(20) DEFAULT NULL,
  `Logradouro_cli` varchar(60) DEFAULT '',
  `numero_cli` varchar(60) DEFAULT '',
  `complemento_cli` varchar(60) DEFAULT '',
  `indiedest_cli` char(1) NOT NULL DEFAULT '9',
  `cfop_cli` varchar(4) DEFAULT '5102',
  `tipoicms_cli` varchar(4) DEFAULT '102',
  `cpf` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`cod_cli`),
  KEY `codold` (`cod_old`),
  KEY `fbairro` (`bairro_cli`),
  KEY `fCodSet` (`cod_set`),
  KEY `ind_nome` (`nome_cli`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_clientes_copy`
--

DROP TABLE IF EXISTS `tab_clientes_copy`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_clientes_copy` (
  `cod_cli` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `nome_cli` char(50) NOT NULL DEFAULT '',
  `datanasc_cli` date DEFAULT '0000-00-00',
  `cpf_cli` char(18) DEFAULT NULL,
  `endereco_cli` char(40) DEFAULT NULL,
  `bairro_cli` char(30) DEFAULT NULL,
  `cep_cli` char(10) DEFAULT NULL,
  `referencia_cli` char(30) DEFAULT NULL,
  `cidade_cli` char(30) DEFAULT NULL,
  `uf_cli` char(2) DEFAULT NULL,
  `data_cli` date DEFAULT '0000-00-00',
  `obs_cli` char(250) DEFAULT NULL,
  `status_cli` char(1) NOT NULL DEFAULT '1',
  `rg_cli` char(18) DEFAULT NULL,
  `mae_cli` char(40) DEFAULT NULL,
  `pai_cli` char(40) DEFAULT NULL,
  `cod_old` char(10) DEFAULT NULL,
  `mens_cli` char(1) DEFAULT 'N',
  `limite_cli` double(14,2) NOT NULL DEFAULT 0.00,
  `endcom_cli` char(60) DEFAULT NULL,
  `usucad_cli` char(3) NOT NULL DEFAULT '001',
  `prazo_cli` int(10) unsigned NOT NULL DEFAULT 0,
  `tipo_cli` char(1) NOT NULL DEFAULT 'F',
  `credito_cli` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_set` char(5) NOT NULL DEFAULT '00000',
  `cod_gru` char(3) NOT NULL DEFAULT '000',
  `cobranca_cli` char(1) NOT NULL DEFAULT '1',
  `localtrab_cli` char(60) NOT NULL DEFAULT '',
  `endtrab_cli` char(40) NOT NULL DEFAULT '',
  `setortrab_cli` char(5) NOT NULL DEFAULT '',
  `teltrab_cli` char(16) NOT NULL DEFAULT '',
  `ceptrab_cli` char(10) NOT NULL DEFAULT '',
  `cod_org` char(5) NOT NULL DEFAULT '',
  `dataalt_cli` date NOT NULL DEFAULT '0000-00-00',
  `sexo_cli` char(1) NOT NULL DEFAULT 'F',
  `email_cli` char(100) DEFAULT NULL,
  PRIMARY KEY (`cod_cli`),
  KEY `codold` (`cod_old`),
  KEY `fbairro` (`bairro_cli`),
  KEY `fCodSet` (`cod_set`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_clientesanot`
--

DROP TABLE IF EXISTS `tab_clientesanot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_clientesanot` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cod_cli` int(6) unsigned zerofill DEFAULT NULL,
  `anotacao` text DEFAULT NULL,
  `datahora` datetime DEFAULT NULL,
  `cod_usu` char(3) DEFAULT NULL,
  `excluido` char(1) DEFAULT 'N',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=46 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_clientespc`
--

DROP TABLE IF EXISTS `tab_clientespc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_clientespc` (
  `seq_spc` int(11) NOT NULL AUTO_INCREMENT,
  `cod_cli` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `data_spc` date NOT NULL DEFAULT '0000-00-00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `baixa_spc` date NOT NULL DEFAULT '0000-00-00',
  `valor_spc` double(14,2) NOT NULL DEFAULT 0.00,
  `doc_spc` char(10) NOT NULL DEFAULT '',
  `dataacao_spc` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `tipo_ter` char(1) NOT NULL DEFAULT 'C',
  `tipo_doc` char(1) NOT NULL DEFAULT 'P',
  PRIMARY KEY (`seq_spc`)
) ENGINE=MyISAM AUTO_INCREMENT=908 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_clientetrab`
--

DROP TABLE IF EXISTS `tab_clientetrab`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_clientetrab` (
  `cod_cli` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `seq_tra` int(11) NOT NULL DEFAULT 0,
  `nome_tra` char(50) NOT NULL DEFAULT '',
  `endereco_tra` char(50) NOT NULL DEFAULT '',
  `cod_set` char(5) NOT NULL DEFAULT '',
  `fone_tra` char(16) NOT NULL DEFAULT '',
  `obs_tra` char(40) NOT NULL DEFAULT '',
  `cargo_tra` char(20) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_cli`,`seq_tra`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_cmp`
--

DROP TABLE IF EXISTS `tab_cmp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_cmp` (
  `COD_FOR` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `NUM_NOT` char(16) DEFAULT NULL,
  `SERIE_NOT` char(4) DEFAULT NULL,
  `VALOR_NOT` double(14,2) NOT NULL DEFAULT 0.00,
  `BC_NOT` double(14,2) DEFAULT NULL,
  `FRETE_NOT` double(14,2) DEFAULT NULL,
  `ICMS_NOT` double(14,2) DEFAULT NULL,
  `IPI_NOT` double(14,2) DEFAULT NULL,
  `DESPESAS_NOT` double(14,2) DEFAULT NULL,
  `OPERACAO_NOT` char(6) DEFAULT NULL,
  `EMISSAO_NOT` date DEFAULT '0000-00-00',
  `ENTRADA_NOT` date DEFAULT '0000-00-00',
  `COD_USU` char(3) DEFAULT NULL,
  `STATUS_NOT` char(1) NOT NULL DEFAULT '',
  `valorprod_not` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_not` char(7) NOT NULL DEFAULT '0000001',
  `desconto_not` double(14,2) NOT NULL DEFAULT 0.00,
  `data_not` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `seq_ent` char(7) NOT NULL DEFAULT '0000001',
  PRIMARY KEY (`seq_not`),
  KEY `codfor` (`COD_FOR`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_cobrancas`
--

DROP TABLE IF EXISTS `tab_cobrancas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_cobrancas` (
  `seq_cob` char(7) NOT NULL DEFAULT '',
  `data_cob` date NOT NULL DEFAULT '0000-00-00',
  `hora_cob` char(5) NOT NULL DEFAULT '',
  `entra_con` char(3) NOT NULL DEFAULT '',
  `datasai_cob` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `seq_itd` char(7) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_cob`),
  KEY `fkSeqIte` (`seq_itd`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_codbarras`
--

DROP TABLE IF EXISTS `tab_codbarras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_codbarras` (
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `cod_bar` char(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_pro`,`cod_bar`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_codigos`
--

DROP TABLE IF EXISTS `tab_codigos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_codigos` (
  `table_cod` char(30) NOT NULL DEFAULT '',
  `field_cod` char(30) NOT NULL DEFAULT '',
  `value_cod` char(15) NOT NULL DEFAULT '',
  PRIMARY KEY (`table_cod`,`field_cod`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_comisscons`
--

DROP TABLE IF EXISTS `tab_comisscons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_comisscons` (
  `gerado_com` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_itd` char(7) NOT NULL DEFAULT '',
  `seq_com` char(7) NOT NULL DEFAULT '',
  `status_com` char(1) NOT NULL DEFAULT '1',
  `data_com` date NOT NULL DEFAULT '0000-00-00',
  `seq_cai` char(7) NOT NULL DEFAULT '',
  `valor_bai` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_per` int(10) unsigned NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`seq_per`)
) ENGINE=MyISAM AUTO_INCREMENT=121 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_comissparc`
--

DROP TABLE IF EXISTS `tab_comissparc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_comissparc` (
  `seq_itd` char(7) NOT NULL DEFAULT '',
  `seq_ace` char(7) NOT NULL DEFAULT '',
  `valor_com` double(14,2) NOT NULL DEFAULT 0.00,
  `venc_com` date NOT NULL DEFAULT '0000-00-00',
  `status_com` char(1) NOT NULL DEFAULT '1',
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `tipo_com` char(1) NOT NULL DEFAULT '1',
  `SEQ_CAI` char(7) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_itd`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_comissparccai`
--

DROP TABLE IF EXISTS `tab_comissparccai`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_comissparccai` (
  `seq_cai` char(7) NOT NULL DEFAULT '',
  `seq_itd` char(7) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_cai`,`seq_itd`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_comissprov`
--

DROP TABLE IF EXISTS `tab_comissprov`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_comissprov` (
  `seq_com` char(7) NOT NULL DEFAULT '',
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `seq_ace` char(7) NOT NULL DEFAULT '',
  `valor_com` double(14,2) NOT NULL DEFAULT 0.00,
  `reman_com` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_doc` char(7) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_rep`,`seq_com`,`seq_doc`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_compras`
--

DROP TABLE IF EXISTS `tab_compras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_compras` (
  `COD_FOR` int(6) unsigned zerofill DEFAULT 000000,
  `NUM_NOT` char(16) DEFAULT NULL,
  `SERIE_NOT` char(4) DEFAULT NULL,
  `VALOR_NOT` double(14,2) NOT NULL DEFAULT 0.00,
  `BC_NOT` double(14,2) DEFAULT NULL,
  `FRETE_NOT` double(14,2) DEFAULT NULL,
  `ICMS_NOT` double(14,2) DEFAULT NULL,
  `IPI_NOT` double(14,2) DEFAULT NULL,
  `DESPESAS_NOT` double(14,2) DEFAULT NULL,
  `OPERACAO_NOT` char(6) NOT NULL DEFAULT '',
  `EMISSAO_NOT` date DEFAULT '0000-00-00',
  `ENTRADA_NOT` date DEFAULT '0000-00-00',
  `COD_USU` char(3) DEFAULT NULL,
  `STATUS_NOT` char(1) DEFAULT NULL,
  `valorprod_not` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_not` char(7) NOT NULL DEFAULT '0000001',
  `desconto_not` double(14,2) NOT NULL DEFAULT 0.00,
  `data_not` datetime DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`seq_not`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_consignabertas`
--

DROP TABLE IF EXISTS `tab_consignabertas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_consignabertas` (
  `seq_con` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `data_con` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `qtd_con` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `unit_con` double(14,2) NOT NULL DEFAULT 0.00,
  `RETIF_CON` char(1) NOT NULL DEFAULT 'N',
  `reservado_con` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`seq_con`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_consignacoes`
--

DROP TABLE IF EXISTS `tab_consignacoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_consignacoes` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `seq_con` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `data_con` datetime DEFAULT '0000-00-00 00:00:00',
  `qtd_con` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `reman_con` double(14,2) NOT NULL DEFAULT 0.00,
  `unit_con` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_cab` char(7) DEFAULT NULL,
  `RETIF_CON` char(1) NOT NULL DEFAULT 'N',
  `reservado_con` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `f_codrep` (`cod_rep`),
  KEY `cod_pro` (`cod_pro`)
) ENGINE=MyISAM AUTO_INCREMENT=623927 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_consignacoes_backup`
--

DROP TABLE IF EXISTS `tab_consignacoes_backup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_consignacoes_backup` (
  `seq_con` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `data_con` datetime DEFAULT '0000-00-00 00:00:00',
  `qtd_con` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `reman_con` double(14,2) NOT NULL DEFAULT 0.00,
  `unit_con` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_cab` char(7) DEFAULT NULL,
  `RETIF_CON` char(1) NOT NULL DEFAULT 'N',
  `reservado_con` double(14,2) NOT NULL DEFAULT 0.00
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_consigncab`
--

DROP TABLE IF EXISTS `tab_consigncab`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_consigncab` (
  `seq_cab` char(7) NOT NULL DEFAULT '',
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `data_con` date NOT NULL DEFAULT '0000-00-00',
  `hora_con` char(5) NOT NULL DEFAULT '',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `valor_con` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`seq_cab`),
  KEY `cod_rep` (`cod_rep`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_contacob`
--

DROP TABLE IF EXISTS `tab_contacob`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_contacob` (
  `cod_cob` char(3) NOT NULL DEFAULT '',
  `nome_cob` char(40) DEFAULT NULL,
  `excluido_cob` char(1) DEFAULT 'N',
  PRIMARY KEY (`cod_cob`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_contagens`
--

DROP TABLE IF EXISTS `tab_contagens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_contagens` (
  `seq_cnt` char(5) NOT NULL DEFAULT '',
  `data_cnt` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `status_cnt` char(1) NOT NULL DEFAULT 'N',
  `tipo_con` char(1) NOT NULL DEFAULT 'R',
  PRIMARY KEY (`seq_cnt`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_contas`
--

DROP TABLE IF EXISTS `tab_contas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_contas` (
  `cod_con` char(3) NOT NULL DEFAULT '',
  `nome_con` char(20) NOT NULL DEFAULT '',
  `num_con` char(12) DEFAULT NULL,
  `cod_bco` char(3) DEFAULT NULL,
  `age_con` char(12) DEFAULT NULL,
  `tit_con` char(30) DEFAULT NULL,
  `status_con` char(1) NOT NULL DEFAULT 'H',
  PRIMARY KEY (`cod_con`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_contratos`
--

DROP TABLE IF EXISTS `tab_contratos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_contratos` (
  `seq_con` int(11) NOT NULL DEFAULT 0,
  `cab_con` varchar(250) NOT NULL DEFAULT '',
  `preambulo_con` text NOT NULL,
  PRIMARY KEY (`seq_con`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_controles`
--

DROP TABLE IF EXISTS `tab_controles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_controles` (
  `cod_con` char(3) NOT NULL DEFAULT '',
  `nome_con` char(30) NOT NULL DEFAULT '',
  `descricao_con` char(60) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_con`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_conveniados`
--

DROP TABLE IF EXISTS `tab_conveniados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_conveniados` (
  `cod_cli` char(5) NOT NULL DEFAULT '',
  `seq_con` int(11) NOT NULL DEFAULT 0,
  `nome_con` char(60) NOT NULL DEFAULT '',
  `cpf_con` char(16) NOT NULL DEFAULT '',
  `endereco_con` char(40) NOT NULL DEFAULT '',
  `bairro_con` char(40) NOT NULL DEFAULT '',
  `cidade_con` char(40) NOT NULL DEFAULT '',
  `uf_con` char(2) NOT NULL DEFAULT '',
  `fone_con` char(14) NOT NULL DEFAULT '',
  `matricula_con` char(20) NOT NULL DEFAULT '',
  `cep_con` char(10) NOT NULL DEFAULT '',
  `status_con` char(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`seq_con`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_convenios`
--

DROP TABLE IF EXISTS `tab_convenios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_convenios` (
  `data_con` date NOT NULL DEFAULT '0000-00-00',
  `cod_cli` char(5) NOT NULL DEFAULT '',
  `status_con` char(1) NOT NULL DEFAULT '1',
  `desconto_con` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`cod_cli`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_correcaorep`
--

DROP TABLE IF EXISTS `tab_correcaorep`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_correcaorep` (
  `seq_cor` char(7) NOT NULL DEFAULT '',
  `data_cor` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_cor`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_crediarioven`
--

DROP TABLE IF EXISTS `tab_crediarioven`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_crediarioven` (
  `num_ven` char(7) NOT NULL DEFAULT '',
  `cod_usu` char(3) DEFAULT NULL,
  `status_cre` char(1) NOT NULL DEFAULT '1',
  `avaliacao_cre` char(40) DEFAULT NULL,
  `data_cre` datetime DEFAULT '0000-00-00 00:00:00',
  `fechamento_cre` datetime DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`num_ven`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_defusu`
--

DROP TABLE IF EXISTS `tab_defusu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_defusu` (
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `abrevenda_usu` char(1) NOT NULL DEFAULT 'N',
  `abrenota_usu` char(1) NOT NULL DEFAULT 'N',
  `efetnota_usu` char(1) NOT NULL DEFAULT 'N',
  `abresaida_usu` char(1) NOT NULL DEFAULT 'N',
  `lancaixa_usu` char(1) NOT NULL DEFAULT 'N',
  `landoc_usu` char(1) NOT NULL DEFAULT 'N',
  `lanche_usu` char(1) NOT NULL DEFAULT 'N',
  `baixadoc_usu` char(1) NOT NULL DEFAULT 'N',
  `baixache_usu` char(1) NOT NULL DEFAULT 'N',
  `edicai_usu` char(1) NOT NULL DEFAULT 'N',
  `exclcai_usu` char(1) NOT NULL DEFAULT 'N',
  `excldoc_usu` char(1) NOT NULL DEFAULT 'N',
  `cadprod_usu` char(1) NOT NULL DEFAULT 'N',
  `altprod_usu` char(1) NOT NULL DEFAULT 'N',
  `altpreco_usu` char(1) NOT NULL DEFAULT 'N',
  `cadusu_usu` char(1) NOT NULL DEFAULT 'N',
  `cadcli_usu` char(1) NOT NULL DEFAULT 'N',
  `cadcco_usu` char(1) NOT NULL DEFAULT 'N',
  `cadformaspag_usu` char(1) NOT NULL DEFAULT 'N',
  `altformaspag_usu` char(1) NOT NULL DEFAULT 'N',
  `viscusto_usu` char(1) NOT NULL DEFAULT 'N',
  `visrelest_usu` char(1) NOT NULL DEFAULT 'N',
  `visrelfin_usu` char(1) NOT NULL DEFAULT 'N',
  `fechacai_usu` char(1) NOT NULL DEFAULT 'N',
  `fechames_usu` char(1) NOT NULL DEFAULT 'N',
  `desconto_usu` double(14,2) NOT NULL DEFAULT 0.00,
  `contrpre_usu` char(1) NOT NULL DEFAULT 'N',
  `exclvenda_usu` char(1) NOT NULL DEFAULT 'N',
  `alterarvlrparcela_usu` char(1) NOT NULL DEFAULT 'N',
  `prorrogarparcela_usu` char(1) NOT NULL DEFAULT 'N',
  `alterarterceirodoc_usu` char(1) NOT NULL DEFAULT 'N',
  `baixarcheque_usu` char(1) NOT NULL DEFAULT 'N',
  `excluircheque_usu` char(1) NOT NULL DEFAULT 'N',
  `efetivarvenda_usu` char(1) NOT NULL DEFAULT 'N',
  `crediario_usu` char(1) NOT NULL DEFAULT 'N',
  `visualizarvenda_usu` char(1) NOT NULL DEFAULT 'N',
  `lancarfin_usu` char(1) NOT NULL DEFAULT 'N',
  `editarfin_usu` char(1) NOT NULL DEFAULT 'N',
  `excluirfin_usu` char(1) NOT NULL DEFAULT 'N',
  `transfinterna_usu` char(1) NOT NULL DEFAULT 'N',
  `abrirtransfint_usu` char(1) NOT NULL DEFAULT 'N',
  `fechartransfint_usu` char(1) NOT NULL DEFAULT 'N',
  `efetuardevcons_usu` char(1) NOT NULL DEFAULT 'N',
  `efetuartransfcons_usu` char(1) NOT NULL DEFAULT 'N',
  `efetuaracerto_usu` char(1) NOT NULL DEFAULT 'N',
  `excluiracerto_usu` char(1) NOT NULL DEFAULT 'N',
  `alterarcomrepr_usu` char(1) NOT NULL DEFAULT 'N',
  `baixarcomrepr_usu` char(1) NOT NULL DEFAULT 'N',
  `cadastrarrepr_usu` char(1) NOT NULL DEFAULT 'N',
  `cadastrarfun_usu` char(1) NOT NULL DEFAULT 'N',
  `cadastrarfor_usu` char(1) NOT NULL DEFAULT 'N',
  `descontobaixa_usu` double(14,2) NOT NULL DEFAULT 0.00,
  `corrigeestcons_usu` char(1) NOT NULL DEFAULT 'N',
  `visaocaixa_usu` char(1) NOT NULL DEFAULT 'N',
  `visaoconsignado_usu` char(1) NOT NULL DEFAULT 'N',
  `visaocrediario_usu` char(1) NOT NULL DEFAULT 'N',
  `visaovendas_usu` char(1) NOT NULL DEFAULT 'N',
  `visaogeral_usu` char(1) NOT NULL DEFAULT 'N',
  `visaopacote_usu` char(1) NOT NULL DEFAULT 'N',
  `visaofinanceiro_usu` char(1) NOT NULL DEFAULT 'N',
  `visaoestoque_usu` char(1) NOT NULL DEFAULT 'N',
  `liberarcliente_usu` char(1) NOT NULL DEFAULT 'N',
  `desbloquearvenda_usu` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`cod_usu`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_descontos`
--

DROP TABLE IF EXISTS `tab_descontos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_descontos` (
  `cod_car` char(3) NOT NULL DEFAULT '',
  `cod_for` char(2) NOT NULL DEFAULT '',
  `cod_sub` char(3) NOT NULL DEFAULT '',
  `valor_des` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`cod_car`,`cod_for`,`cod_sub`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_destmovint`
--

DROP TABLE IF EXISTS `tab_destmovint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_destmovint` (
  `cod_des` int(11) NOT NULL DEFAULT 0,
  `nome_des` char(50) NOT NULL DEFAULT '',
  `cnpj_des` char(20) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_des`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_devconsign`
--

DROP TABLE IF EXISTS `tab_devconsign`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_devconsign` (
  `seq_dev` char(7) NOT NULL DEFAULT '',
  `data_dev` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `cod_usu` char(3) NOT NULL DEFAULT '000',
  `retif_dev` char(1) NOT NULL DEFAULT 'N',
  `confirmacorrecao_usu` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_dev`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_devconsignabertas`
--

DROP TABLE IF EXISTS `tab_devconsignabertas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_devconsignabertas` (
  `seq_dev` char(7) NOT NULL DEFAULT '',
  `data_dev` date NOT NULL DEFAULT '0000-00-00',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_dev` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `seq_con` char(7) NOT NULL DEFAULT '',
  `cod_usu` char(3) DEFAULT NULL,
  PRIMARY KEY (`seq_dev`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_devolucoes`
--

DROP TABLE IF EXISTS `tab_devolucoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_devolucoes` (
  `num_ven` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_ite` double(14,2) DEFAULT NULL,
  `qtd_dev` double(14,2) DEFAULT NULL,
  `data_dev` datetime DEFAULT NULL,
  `gerado_dev` double(14,2) DEFAULT NULL,
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `tipo_dev` char(1) NOT NULL DEFAULT 'I',
  `SEQEFET_DEV` char(7) DEFAULT NULL,
  `cod_cli` char(6) DEFAULT NULL,
  `desconto_dev` double(14,2) DEFAULT 0.00,
  `cod_tip` char(2) DEFAULT NULL,
  `situacao_dev` char(1) DEFAULT NULL,
  `seq_pro` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`num_ven`,`cod_pro`,`tipo_dev`,`seq_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_doc`
--

DROP TABLE IF EXISTS `tab_doc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_doc` (
  `seq_doc` char(9) NOT NULL,
  `num_doc` char(12) NOT NULL DEFAULT '',
  `tipo_doc` char(1) NOT NULL DEFAULT '',
  `cod_ter` int(6) unsigned zerofill DEFAULT 000000,
  `valor_doc` double(14,2) NOT NULL DEFAULT 0.00,
  `parcelas_doc` int(11) NOT NULL DEFAULT 0,
  `data_doc` date DEFAULT '0000-00-00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `excluido_doc` char(1) NOT NULL DEFAULT 'N',
  `historico_doc` char(80) NOT NULL DEFAULT '',
  `num_ven` char(7) NOT NULL DEFAULT '',
  `esp_doc` char(1) NOT NULL DEFAULT 'F',
  `tipo_ter` char(1) NOT NULL DEFAULT 'C',
  `cod_pla` char(3) NOT NULL DEFAULT '000',
  `id_doc_web` int(11) DEFAULT NULL,
  PRIMARY KEY (`seq_doc`),
  KEY `ind_num_doc` (`num_doc`),
  KEY `ind_cod_ter` (`cod_ter`),
  KEY `ind_num_ven` (`num_ven`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_dochist`
--

DROP TABLE IF EXISTS `tab_dochist`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_dochist` (
  `seq_his` int(11) NOT NULL AUTO_INCREMENT,
  `seq_doc` char(7) NOT NULL DEFAULT '',
  `cobout_doc` char(3) NOT NULL DEFAULT '',
  `cobin_doc` char(3) NOT NULL DEFAULT '',
  `data_doc` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `tipocobin_doc` char(1) NOT NULL DEFAULT '',
  `tipocobout_doc` char(1) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_his`)
) ENGINE=MyISAM AUTO_INCREMENT=2982273 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_dochistusu`
--

DROP TABLE IF EXISTS `tab_dochistusu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_dochistusu` (
  `seq_his` int(11) NOT NULL AUTO_INCREMENT,
  `seq_doc` char(7) NOT NULL DEFAULT '',
  `usuin_doc` char(3) NOT NULL DEFAULT '',
  `data_doc` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_his`)
) ENGINE=MyISAM AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_docimpress`
--

DROP TABLE IF EXISTS `tab_docimpress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_docimpress` (
  `seq_imp` int(11) NOT NULL AUTO_INCREMENT,
  `seq_doc` char(7) NOT NULL DEFAULT '',
  `data_imp` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_imp`)
) ENGINE=MyISAM AUTO_INCREMENT=65622 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_ecfimp`
--

DROP TABLE IF EXISTS `tab_ecfimp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_ecfimp` (
  `cod_imp` char(3) NOT NULL DEFAULT '',
  `ecf_imp` char(3) NOT NULL DEFAULT '',
  `impressora_imp` char(1) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_imp`,`impressora_imp`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_embalagens`
--

DROP TABLE IF EXISTS `tab_embalagens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_embalagens` (
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_emb` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`cod_pro`,`qtd_emb`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_espcai`
--

DROP TABLE IF EXISTS `tab_espcai`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_espcai` (
  `sigla_cai` char(3) NOT NULL DEFAULT '',
  `descricao_cai` char(50) NOT NULL DEFAULT '',
  `efetivo` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`sigla_cai`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_estcons`
--

DROP TABLE IF EXISTS `tab_estcons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_estcons` (
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `estoque_pro` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`cod_pro`,`cod_rep`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_etiquetas`
--

DROP TABLE IF EXISTS `tab_etiquetas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_etiquetas` (
  `cod_eti` int(11) NOT NULL DEFAULT 0,
  `nome_eti` char(50) NOT NULL DEFAULT '',
  `altura_eti` double(14,2) NOT NULL DEFAULT 0.00,
  `disth_eti` double(14,2) NOT NULL DEFAULT 0.00,
  `distv_eti` double(14,2) NOT NULL DEFAULT 0.00,
  `largura_eti` double(14,2) NOT NULL DEFAULT 0.00,
  `mesq_eti` double(14,2) NOT NULL DEFAULT 0.00,
  `msup_eti` double(14,2) NOT NULL DEFAULT 0.00,
  `qtdcol_eti` double(14,2) NOT NULL DEFAULT 0.00,
  `qtdlinha_eti` double(14,2) NOT NULL DEFAULT 0.00,
  `padrao_eti` char(1) NOT NULL DEFAULT 'N',
  `fonte_eti` char(50) NOT NULL DEFAULT 'arial',
  `tamfonte_eti` double(14,2) NOT NULL DEFAULT 10.00,
  `tambar_eti` int(11) NOT NULL DEFAULT 1800,
  `altbar_eti` int(11) NOT NULL DEFAULT 495,
  PRIMARY KEY (`cod_eti`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_fabricantes`
--

DROP TABLE IF EXISTS `tab_fabricantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_fabricantes` (
  `cod_fab` char(5) NOT NULL DEFAULT '',
  `nome_fab` char(60) NOT NULL DEFAULT '',
  `telefone_fab` char(20) NOT NULL DEFAULT '',
  `cidade_fab` char(40) NOT NULL DEFAULT '',
  `uf_fab` char(20) NOT NULL DEFAULT '',
  `pais_fab` char(40) NOT NULL DEFAULT '',
  `web_fab` char(100) NOT NULL DEFAULT '',
  `email_fab` char(100) NOT NULL DEFAULT '',
  `endereco_fab` char(100) NOT NULL DEFAULT '',
  `etico_fab` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`cod_fab`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_fechacaixa`
--

DROP TABLE IF EXISTS `tab_fechacaixa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_fechacaixa` (
  `DATA_CAI` date NOT NULL DEFAULT '0000-00-00',
  `VALOR_FEC` double(14,2) NOT NULL DEFAULT 0.00,
  `COD_USU` char(10) NOT NULL DEFAULT '',
  `cod_cai` char(2) NOT NULL DEFAULT '',
  `fundo_cai` double(14,2) NOT NULL DEFAULT 0.00,
  `turno_cai` char(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`DATA_CAI`,`cod_cai`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_financeiras`
--

DROP TABLE IF EXISTS `tab_financeiras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_financeiras` (
  `COD_FIN` char(3) NOT NULL DEFAULT '',
  `COD_TIP` char(2) NOT NULL DEFAULT '',
  `TIPO_FIN` char(1) NOT NULL DEFAULT '',
  `NOME_FIN` char(20) NOT NULL DEFAULT '',
  `TEL_FIN` char(30) DEFAULT NULL,
  `SIGLA_FIN` char(30) NOT NULL DEFAULT '',
  `operacao_fin` char(1) NOT NULL DEFAULT 'C',
  `CNPJ` char(50) DEFAULT NULL,
  `tBand` char(2) DEFAULT NULL,
  `cpf_fin` char(20) DEFAULT NULL,
  `tpintegra` char(1) DEFAULT '1',
  PRIMARY KEY (`COD_FIN`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_financeiro`
--

DROP TABLE IF EXISTS `tab_financeiro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_financeiro` (
  `seq_fin` char(7) NOT NULL DEFAULT '',
  `data_fin` date NOT NULL DEFAULT '0000-00-00',
  `historico_fin` char(50) NOT NULL DEFAULT '',
  `cod_con` char(3) NOT NULL DEFAULT '',
  `valor_fin` double(14,2) NOT NULL DEFAULT 0.00,
  `saldo_fin` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `vinculado_fin` char(1) NOT NULL DEFAULT 'N',
  `tipo_fin` char(1) NOT NULL DEFAULT '',
  `esp_fin` char(3) NOT NULL DEFAULT 'DIN',
  `cod_pla` char(3) NOT NULL DEFAULT '000',
  `hora_fin` char(5) NOT NULL DEFAULT '00:00',
  PRIMARY KEY (`seq_fin`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_formaspag`
--

DROP TABLE IF EXISTS `tab_formaspag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_formaspag` (
  `cod_for` char(2) NOT NULL DEFAULT '',
  `nome_for` char(20) NOT NULL DEFAULT '',
  `desconto_for` double(14,2) NOT NULL DEFAULT 0.00,
  `tipo_cai` char(3) NOT NULL DEFAULT '',
  `avista_for` char(1) NOT NULL DEFAULT 'N',
  `parcelas_for` int(3) NOT NULL DEFAULT 1,
  `intervalo_for` int(3) unsigned NOT NULL DEFAULT 30,
  `cod_tip` char(2) NOT NULL DEFAULT '01',
  `gerencial_for` char(1) NOT NULL DEFAULT 'N',
  `tpag` char(2) DEFAULT '01',
  `visivel_for` char(1) DEFAULT 'S',
  PRIMARY KEY (`cod_for`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_fornecedores`
--

DROP TABLE IF EXISTS `tab_fornecedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_fornecedores` (
  `COD_FOR` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `NOME_FOR` char(50) NOT NULL DEFAULT '',
  `FANTASIA_FOR` char(50) DEFAULT NULL,
  `CNPJ_FOR` char(18) NOT NULL DEFAULT '',
  `ie_for` varchar(14) DEFAULT NULL,
  `ENDERECO_FOR` char(30) DEFAULT NULL,
  `BAIRRO_FOR` char(20) DEFAULT NULL,
  `CIDADE_FOR` char(30) DEFAULT NULL,
  `UF_FOR` char(2) DEFAULT NULL,
  `CEP_FOR` char(8) DEFAULT NULL,
  `TELEFONE_FOR` char(16) DEFAULT NULL,
  `FAX_FOR` char(16) DEFAULT NULL,
  `CONTATO_FOR` char(30) DEFAULT NULL,
  `EMAIL_FOR` char(64) DEFAULT NULL,
  `codantigo_for` char(5) DEFAULT NULL,
  `obs_for` char(60) DEFAULT NULL,
  `logradouro_for` char(40) DEFAULT NULL,
  PRIMARY KEY (`COD_FOR`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_fotofun`
--

DROP TABLE IF EXISTS `tab_fotofun`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_fotofun` (
  `cod_fun` char(3) NOT NULL DEFAULT '',
  `seq_fot` int(11) NOT NULL DEFAULT 0,
  `foto_fot` mediumblob NOT NULL,
  `tipo_fot` char(1) NOT NULL DEFAULT '',
  `data_fot` date NOT NULL DEFAULT '0000-00-00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_fot`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_fotorep`
--

DROP TABLE IF EXISTS `tab_fotorep`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_fotorep` (
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `seq_fot` int(11) NOT NULL DEFAULT 0,
  `foto_fot` mediumblob NOT NULL,
  `tipo_fot` char(1) NOT NULL DEFAULT '',
  `data_fot` date NOT NULL DEFAULT '0000-00-00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_fot`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_funcionarios`
--

DROP TABLE IF EXISTS `tab_funcionarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_funcionarios` (
  `cod_fun` char(3) NOT NULL DEFAULT '',
  `nome_fun` char(50) DEFAULT NULL,
  `endereco_fun` char(40) DEFAULT NULL,
  `bairro_fun` char(40) DEFAULT NULL,
  `cidade_fun` char(40) DEFAULT NULL,
  `uf_fun` char(2) DEFAULT NULL,
  `cep_fun` char(10) DEFAULT NULL,
  `nasc_fun` date DEFAULT '0000-00-00',
  `natural_fun` char(30) DEFAULT NULL,
  `rg_fun` char(16) DEFAULT NULL,
  `cpf_fun` char(18) DEFAULT NULL,
  `sexo_fun` char(1) DEFAULT NULL,
  `conjuge_fun` char(40) DEFAULT NULL,
  `pai_fun` char(40) DEFAULT NULL,
  `mae_fun` char(40) DEFAULT NULL,
  `endpais_fun` char(60) DEFAULT NULL,
  `datacad_fun` date DEFAULT '0000-00-00',
  `obs_fun` char(250) DEFAULT NULL,
  `status_rep` char(1) NOT NULL DEFAULT '1',
  `cod_old` char(7) DEFAULT NULL,
  `status_fun` char(1) NOT NULL DEFAULT '1',
  `cod_Car` char(3) NOT NULL DEFAULT '001',
  `guerra_fun` char(20) DEFAULT NULL,
  `limite_fun` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_set` char(5) NOT NULL DEFAULT '00000',
  `vale_fun` char(1) NOT NULL DEFAULT 'S',
  PRIMARY KEY (`cod_fun`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_grupocli`
--

DROP TABLE IF EXISTS `tab_grupocli`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_grupocli` (
  `cod_gru` char(3) NOT NULL DEFAULT '',
  `nome_gru` char(20) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_gru`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_impostos`
--

DROP TABLE IF EXISTS `tab_impostos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_impostos` (
  `cod_imp` char(3) NOT NULL DEFAULT '',
  `desc_imp` char(16) NOT NULL DEFAULT '',
  `perc_imp` double(14,2) NOT NULL DEFAULT 0.00,
  `ecf_imp` char(2) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_imp`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itacertos`
--

DROP TABLE IF EXISTS `tab_itacertos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itacertos` (
  `seq_ace` char(7) NOT NULL DEFAULT '',
  `seq_ite` int(11) NOT NULL DEFAULT 0,
  `seq_con` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `unit_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `qtd_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `dif_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `ajuste_ite` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`seq_ace`,`seq_ite`),
  KEY `fSeqCon` (`seq_con`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itacertosabertos`
--

DROP TABLE IF EXISTS `tab_itacertosabertos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itacertosabertos` (
  `seq_ace` char(7) NOT NULL DEFAULT '',
  `seq_ite` int(11) NOT NULL DEFAULT 0,
  `seq_con` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `unit_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `qtd_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `dif_ite` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`seq_ace`,`seq_ite`),
  KEY `fSeqCon` (`seq_con`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itcmp`
--

DROP TABLE IF EXISTS `tab_itcmp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itcmp` (
  `COD_PRO` char(8) NOT NULL DEFAULT '',
  `UNIT_ITE` double(14,4) NOT NULL DEFAULT 0.0000,
  `QTD_ITE` double(14,2) NOT NULL DEFAULT 0.00,
  `IPI_ITE` double(14,4) DEFAULT NULL,
  `GASTOS_ITE` double(14,4) DEFAULT NULL,
  `CUSTO_ITE` double(14,4) DEFAULT NULL,
  `SEQ_ITE` int(11) NOT NULL DEFAULT 0,
  `sujerido_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `precofuturo_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `lucrosuj_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `lucroliq_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `desconto_ite` double(14,4) NOT NULL DEFAULT 0.0000,
  `seq_not` char(7) NOT NULL DEFAULT '',
  `custosai_ite` double(14,4) NOT NULL DEFAULT 0.0000,
  `icms_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `qtd_emb` int(10) unsigned NOT NULL DEFAULT 1,
  PRIMARY KEY (`seq_not`,`SEQ_ITE`),
  KEY `COD_PRO` (`COD_PRO`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itcompras`
--

DROP TABLE IF EXISTS `tab_itcompras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itcompras` (
  `COD_PRO` char(8) NOT NULL DEFAULT '',
  `UNIT_ITE` double(14,4) NOT NULL DEFAULT 0.0000,
  `QTD_ITE` double(14,2) NOT NULL DEFAULT 0.00,
  `IPI_ITE` double(14,4) DEFAULT NULL,
  `GASTOS_ITE` double(14,4) DEFAULT NULL,
  `CUSTO_ITE` double(14,4) DEFAULT NULL,
  `SEQ_ITE` int(11) NOT NULL DEFAULT 0,
  `sujerido_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `precofuturo_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `lucrosuj_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `lucroliq_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `desconto_ite` double(14,4) NOT NULL DEFAULT 0.0000,
  `seq_not` char(7) NOT NULL DEFAULT '',
  `custosai_ite` double(14,4) NOT NULL DEFAULT 0.0000,
  `icms_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `qtd_emb` int(10) unsigned NOT NULL DEFAULT 1,
  PRIMARY KEY (`seq_not`,`SEQ_ITE`),
  KEY `COD_PRO` (`COD_PRO`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itcont`
--

DROP TABLE IF EXISTS `tab_itcont`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itcont` (
  `seq_cnt` char(5) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_itc` double(14,2) NOT NULL DEFAULT 0.00,
  `data_itc` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `anterior_itc` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`seq_cnt`,`cod_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itcorr`
--

DROP TABLE IF EXISTS `tab_itcorr`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itcorr` (
  `seq_cor` char(7) NOT NULL DEFAULT '',
  `cod_pro` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `qtd_ite` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`seq_cor`,`cod_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itdev`
--

DROP TABLE IF EXISTS `tab_itdev`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itdev` (
  `NUM_DEV` char(7) NOT NULL DEFAULT '',
  `COD_PRO` char(8) NOT NULL DEFAULT '',
  `UNIT_ITE` double(14,2) NOT NULL DEFAULT 0.00,
  `QTD_ITE` double(14,2) NOT NULL DEFAULT 0.00,
  `SEQ_ITE` int(11) NOT NULL DEFAULT 0,
  `seq_pro` char(1) NOT NULL DEFAULT '',
  PRIMARY KEY (`NUM_DEV`,`COD_PRO`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itdevconsign`
--

DROP TABLE IF EXISTS `tab_itdevconsign`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itdevconsign` (
  `seq_dev` char(7) NOT NULL DEFAULT '',
  `seq_ite` int(11) NOT NULL DEFAULT 0,
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_dev` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_con` char(7) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_dev`,`seq_ite`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itdoc`
--

DROP TABLE IF EXISTS `tab_itdoc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itdoc` (
  `seq_itd` char(7) NOT NULL DEFAULT '',
  `seq_doc` char(9) NOT NULL,
  `valor_itd` double(14,2) NOT NULL DEFAULT 0.00,
  `reman_itd` double(14,2) NOT NULL DEFAULT 0.00,
  `vencini_itd` date DEFAULT '0000-00-00',
  `venc_itd` date DEFAULT '0000-00-00',
  `parcela_itd` int(11) DEFAULT 0,
  `juros_itd` double(14,2) NOT NULL DEFAULT 0.00,
  `desconto_itd` double(14,2) NOT NULL DEFAULT 0.00,
  `baixa_itd` date DEFAULT '0000-00-00',
  `boleto_itd` char(20) DEFAULT NULL,
  `operacao_itd` char(1) DEFAULT 'V',
  `cod_cob` char(3) DEFAULT '000',
  `cod_tip` char(2) DEFAULT '1',
  `impressao_itd` int(3) unsigned DEFAULT 1,
  `prejuizo_itd` char(1) DEFAULT 'N',
  `marcado_itd` char(14) DEFAULT NULL,
  `atualizacao_itd` datetime DEFAULT NULL,
  PRIMARY KEY (`seq_itd`),
  KEY `ind_seq_doc` (`seq_doc`),
  KEY `idx_venc_itd` (`venc_itd`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itdocpre`
--

DROP TABLE IF EXISTS `tab_itdocpre`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itdocpre` (
  `seq_pre` int(11) NOT NULL AUTO_INCREMENT,
  `seq_itd` varchar(7) DEFAULT NULL,
  `hora_pre` char(20) DEFAULT NULL,
  `data_pre` date DEFAULT '0000-00-00',
  `anterior_pre` date DEFAULT '0000-00-00',
  `atual_pre` date DEFAULT '0000-00-00',
  `cod_usu` char(3) DEFAULT NULL,
  `anotacao_pre` text DEFAULT NULL,
  PRIMARY KEY (`seq_pre`),
  UNIQUE KEY `seq_pre` (`seq_pre`),
  KEY `seqitd` (`seq_itd`)
) ENGINE=MyISAM AUTO_INCREMENT=282851 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itmov`
--

DROP TABLE IF EXISTS `tab_itmov`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itmov` (
  `num_mov` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `custo_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `unit_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_ite` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`num_mov`,`seq_ite`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itmovext`
--

DROP TABLE IF EXISTS `tab_itmovext`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itmovext` (
  `num_mov` char(7) NOT NULL DEFAULT '',
  `seq_ite` int(11) NOT NULL DEFAULT 0,
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `cr_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `cf_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `cb_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `pv_pro` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`num_mov`,`seq_ite`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itperdas`
--

DROP TABLE IF EXISTS `tab_itperdas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itperdas` (
  `seq_per` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `unit_itp` double(14,2) DEFAULT NULL,
  `item_itp` int(11) NOT NULL DEFAULT 0,
  `qtd_itp` double(14,2) NOT NULL DEFAULT 0.00
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itrep`
--

DROP TABLE IF EXISTS `tab_itrep`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itrep` (
  `seq_rep` char(7) NOT NULL DEFAULT '',
  `seq_ite` int(11) NOT NULL DEFAULT 0,
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_ite` int(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`seq_rep`,`seq_ite`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itsai`
--

DROP TABLE IF EXISTS `tab_itsai`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itsai` (
  `NOTA_SAI` char(12) NOT NULL DEFAULT '',
  `SERIE_SAI` char(4) NOT NULL DEFAULT '',
  `UNIT_ITS` double(14,2) DEFAULT NULL,
  `QTD_ITS` double(14,2) DEFAULT NULL,
  `COD_PRO` char(8) NOT NULL DEFAULT '',
  `SEQ_ITS` int(11) NOT NULL DEFAULT 0,
  `cod_cai` char(2) NOT NULL DEFAULT '01',
  `icms_its` char(1) NOT NULL DEFAULT 'N',
  `seq_pro` int(10) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`NOTA_SAI`,`SERIE_SAI`,`SEQ_ITS`,`cod_cai`,`COD_PRO`),
  KEY `fst` (`COD_PRO`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_ittrocas`
--

DROP TABLE IF EXISTS `tab_ittrocas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_ittrocas` (
  `seq_tro` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtdant_itt` double(14,2) NOT NULL DEFAULT 0.00,
  `qtdatual_itt` double(14,2) NOT NULL DEFAULT 0.00,
  `unit_itt` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_pro` int(10) unsigned NOT NULL DEFAULT 0,
  `final_itt` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`seq_tro`,`cod_pro`,`seq_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_itvendas`
--

DROP TABLE IF EXISTS `tab_itvendas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_itvendas` (
  `num_ven` char(7) NOT NULL DEFAULT '',
  `seq_ite` int(11) NOT NULL DEFAULT 0,
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `seq_pro` int(11) NOT NULL DEFAULT 0,
  `qtd_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `unit_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `desconto_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `final_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `desc_ite` char(60) DEFAULT NULL,
  `lote_ite` char(20) DEFAULT NULL,
  `venc_ite` date DEFAULT '0000-00-00',
  `pq_itd` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_tro` char(7) DEFAULT NULL,
  `devolvido_ite` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_emp` char(2) NOT NULL DEFAULT '01',
  PRIMARY KEY (`num_ven`,`seq_ite`),
  KEY `codpro` (`cod_pro`),
  KEY `numvem` (`num_ven`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_juridica`
--

DROP TABLE IF EXISTS `tab_juridica`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_juridica` (
  `cod_cli` char(6) NOT NULL DEFAULT '',
  `cnpj_cli` char(20) NOT NULL DEFAULT '',
  `ie_cli` char(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_cli`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_listaprod`
--

DROP TABLE IF EXISTS `tab_listaprod`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_listaprod` (
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `qtd_pro` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`cod_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_localche`
--

DROP TABLE IF EXISTS `tab_localche`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_localche` (
  `cod_loc` char(2) NOT NULL DEFAULT '',
  `nome_loc` char(20) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_loc`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_log`
--

DROP TABLE IF EXISTS `tab_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_log` (
  `seq_log` int(11) NOT NULL AUTO_INCREMENT,
  `data_log` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `expressao_log` text NOT NULL,
  `tab_log` varchar(60) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_log`)
) ENGINE=MyISAM AUTO_INCREMENT=4310 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_marcas`
--

DROP TABLE IF EXISTS `tab_marcas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_marcas` (
  `cod_mar` char(3) NOT NULL DEFAULT '',
  `nome_mar` char(50) DEFAULT NULL,
  PRIMARY KEY (`cod_mar`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_movext`
--

DROP TABLE IF EXISTS `tab_movext`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_movext` (
  `num_mov` char(7) NOT NULL DEFAULT '',
  `protocolo_mov` char(20) NOT NULL DEFAULT '',
  `cnpj_mov` char(20) NOT NULL DEFAULT '',
  `data_mov` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `protocolorec_mov` char(20) NOT NULL DEFAULT '',
  PRIMARY KEY (`num_mov`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_movint`
--

DROP TABLE IF EXISTS `tab_movint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_movint` (
  `num_mov` char(7) NOT NULL DEFAULT '',
  `tipo_mov` char(1) DEFAULT NULL,
  `desc_mov` char(40) DEFAULT NULL,
  `valor_mov` double(14,2) NOT NULL DEFAULT 0.00,
  `data_mov` date DEFAULT '0000-00-00',
  `situacao_mov` char(1) DEFAULT NULL,
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `dataefet_mov` date DEFAULT '0000-00-00',
  `cod_des` int(11) NOT NULL DEFAULT 0,
  `protocolo_mov` char(20) DEFAULT NULL,
  `confirmacao_mov` char(20) DEFAULT NULL,
  `obs_mov` tinyint(3) unsigned DEFAULT NULL,
  `numero_mov` char(20) DEFAULT NULL,
  PRIMARY KEY (`num_mov`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_orgaos`
--

DROP TABLE IF EXISTS `tab_orgaos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_orgaos` (
  `cod_org` char(5) NOT NULL DEFAULT '',
  `nome_org` char(50) NOT NULL DEFAULT '',
  `cod_gru` char(3) NOT NULL DEFAULT '',
  `endereco_org` char(50) NOT NULL DEFAULT '',
  `cod_set` char(5) NOT NULL DEFAULT '',
  `fone_org` char(20) NOT NULL DEFAULT '',
  `cep_org` char(10) NOT NULL DEFAULT '',
  `cobrador_org` char(3) DEFAULT '000',
  `data_org` date DEFAULT NULL,
  `Obs` char(200) DEFAULT NULL,
  PRIMARY KEY (`cod_org`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_pacotes`
--

DROP TABLE IF EXISTS `tab_pacotes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_pacotes` (
  `seq_pac` char(7) NOT NULL DEFAULT '',
  `num_ven` char(7) NOT NULL DEFAULT '',
  `data_pac` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `enviou_pac` char(3) NOT NULL DEFAULT '',
  `despachou_pac` char(3) NOT NULL DEFAULT '',
  `status_pac` char(1) NOT NULL DEFAULT '1',
  `retirada_pac` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`seq_pac`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_pagfun`
--

DROP TABLE IF EXISTS `tab_pagfun`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_pagfun` (
  `seq_fin` char(7) NOT NULL DEFAULT '',
  `tipo_pag` char(1) NOT NULL DEFAULT '',
  `cod_fun` char(3) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_fin`),
  KEY `fCodFun` (`cod_fun`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_parametros`
--

DROP TABLE IF EXISTS `tab_parametros`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_parametros` (
  `NOME_EMP` char(40) DEFAULT NULL,
  `ENDERECO_EMP` char(40) DEFAULT NULL,
  `BAIRRO_EMP` char(20) DEFAULT NULL,
  `CIDADE_EMP` char(20) DEFAULT NULL,
  `UF_EMP` char(2) DEFAULT NULL,
  `CEP_EMP` char(10) DEFAULT NULL,
  `FONE_EMP` char(16) DEFAULT NULL,
  `FAX_EMP` char(14) DEFAULT NULL,
  `CNPJ_EMP` char(18) DEFAULT NULL,
  `IE_EMP` char(12) DEFAULT NULL,
  `NOMERESP_EMP` char(40) DEFAULT NULL,
  `CPFRESP_EMP` char(14) DEFAULT NULL,
  `RGRESP_EMP` char(14) DEFAULT NULL,
  `NOMEMOEDA_PAR` char(10) DEFAULT NULL,
  `SIMBMOEDA_PAR` char(3) DEFAULT NULL,
  `PLURALMOEDA_PAR` char(14) DEFAULT NULL,
  `TXFEDERATIVA_PAR` double(14,2) DEFAULT NULL,
  `TXADM_PAR` double(14,2) DEFAULT NULL,
  `TXDIVERSAS_PAR` double(14,2) DEFAULT NULL,
  `MARGEMSEG_PAR` double(14,2) DEFAULT NULL,
  `cod_loj` char(3) DEFAULT '001',
  `msgecf_par` char(48) DEFAULT NULL,
  `tipomsgecf_par` char(1) DEFAULT NULL,
  `msgvenda_par` char(200) DEFAULT NULL,
  `juros_par` double(14,2) NOT NULL DEFAULT 0.00,
  `comissven_par` double(14,2) NOT NULL DEFAULT 0.00,
  `fantasia_emp` char(40) DEFAULT NULL,
  `IMPRESSORA_PAR` char(1) DEFAULT 'B',
  `ipserver_par` char(20) DEFAULT '10.10.0.100',
  `tipodoc_par` char(1) DEFAULT 'C',
  `caminhoexec_par` char(200) DEFAULT NULL,
  `fototemp_par` char(255) DEFAULT NULL,
  `gravafototemp_par` char(255) DEFAULT NULL,
  `descontofun_par` double(14,2) NOT NULL DEFAULT 20.00,
  `txdescontoavista_par` double NOT NULL DEFAULT 25,
  `usacrediario_par` char(1) DEFAULT 'S',
  `usacomissaoacerto_par` char(1) DEFAULT 'S',
  `logradouro_emp` char(35) DEFAULT NULL,
  `numero_emp` char(35) DEFAULT NULL,
  `complemento_emp` char(35) DEFAULT NULL,
  `ambiente_nfe` char(60) DEFAULT '1',
  `tipoicms_nfe` char(60) DEFAULT 'ICMSSN102',
  `usavendasupermarcado` char(1) DEFAULT 'N',
  `formapagamentopadrao` char(2) DEFAULT '06',
  `usavendasupermercado` char(1) DEFAULT 'N',
  `CaminhoCopiaXML` char(200) DEFAULT NULL,
  `versao_nfe` char(10) DEFAULT '3.10',
  `UsaVendaRestaurante` char(1) DEFAULT 'N',
  `UsaImpedirVendaDeProdutoSemEstoque` char(1) DEFAULT 'N',
  `infaddnfe55` char(250) DEFAULT NULL,
  `crt` char(1) DEFAULT '1',
  `cod_emp` char(2) NOT NULL DEFAULT '02'
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_perdas`
--

DROP TABLE IF EXISTS `tab_perdas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_perdas` (
  `seq_per` char(7) NOT NULL DEFAULT '',
  `data_per` date NOT NULL DEFAULT '0000-00-00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `situacao_per` char(1) NOT NULL DEFAULT '1',
  `cod_for` char(5) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_per`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_permissoes`
--

DROP TABLE IF EXISTS `tab_permissoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_permissoes` (
  `cod_per` char(5) NOT NULL DEFAULT '',
  `nome_per` char(40) NOT NULL DEFAULT '',
  `obs_per` char(200) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_per`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_permusu`
--

DROP TABLE IF EXISTS `tab_permusu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_permusu` (
  `cod_per` char(3) NOT NULL DEFAULT '',
  `Cod_fun` char(3) NOT NULL DEFAULT '',
  `valor_per` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`cod_per`,`Cod_fun`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_planocontas`
--

DROP TABLE IF EXISTS `tab_planocontas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_planocontas` (
  `cod_pla` char(5) NOT NULL DEFAULT '',
  `nome_pla` char(50) NOT NULL DEFAULT '',
  `tipo_pla` char(1) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_pla`,`tipo_pla`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_principios`
--

DROP TABLE IF EXISTS `tab_principios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_principios` (
  `cod_pri` char(5) NOT NULL DEFAULT '',
  `nome_pri` char(80) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_pri`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_prodacerto`
--

DROP TABLE IF EXISTS `tab_prodacerto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_prodacerto` (
  `seq_ace` char(7) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `ordem_ace` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`seq_ace`,`ordem_ace`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_prodfrac`
--

DROP TABLE IF EXISTS `tab_prodfrac`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_prodfrac` (
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `matriz_pro` char(8) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_pro`,`matriz_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_produtos`
--

DROP TABLE IF EXISTS `tab_produtos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_produtos` (
  `cod_pro` varchar(8) NOT NULL DEFAULT '',
  `nome_pro` varchar(100) DEFAULT NULL,
  `cod_sub` char(3) DEFAULT NULL,
  `cod_pri` varchar(5) DEFAULT '00001',
  `cr_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `cf_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `pv_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `pa_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `cm_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `ref_pro` varchar(20) DEFAULT NULL,
  `codbar_pro` varchar(20) DEFAULT '0',
  `fracionado_pro` char(1) DEFAULT 'N',
  `lucro_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `st_pro` char(1) DEFAULT 'R',
  `unidade_pro` varchar(5) NOT NULL DEFAULT 'UN',
  `complemento_pro` varchar(40) NOT NULL DEFAULT '0',
  `pfab_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_fab` int(6) NOT NULL DEFAULT 0,
  `cod_con` char(3) NOT NULL DEFAULT '000',
  `lista_pro` char(1) DEFAULT '0',
  `cod_imp` char(2) NOT NULL DEFAULT '01',
  `qtdfra_pro` int(11) NOT NULL DEFAULT 1,
  `matriz_pro` varchar(8) DEFAULT '0',
  `bonificado_pro` char(1) DEFAULT 'N',
  `pb_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `endereco_pro` varchar(30) DEFAULT '',
  `icms_pro` varchar(5) DEFAULT 'FF',
  `er_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `ef_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `r_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `pq_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `cb_pro` double(14,2) NOT NULL DEFAULT 0.00,
  `principal_pro` varchar(8) DEFAULT NULL,
  `ncm_pro` varchar(10) DEFAULT NULL,
  `cfop_pro` varchar(4) DEFAULT '5102',
  `cst_ipi` char(2) DEFAULT '49',
  `cst_pis` char(2) DEFAULT '49',
  `cst_cofins` char(2) DEFAULT '49',
  `ean_pro` varchar(20) DEFAULT NULL,
  `fpm_pro` date DEFAULT NULL,
  `ipm_pro` date DEFAULT NULL,
  `uc_pro` double(14,2) DEFAULT NULL,
  `cod_ori` char(1) DEFAULT '0',
  `cest_pro` varchar(10) DEFAULT NULL,
  `cst_icms` char(3) DEFAULT '102',
  `controlaestoque_pro` char(1) DEFAULT 'S',
  `comercializavel_pro` char(1) NOT NULL DEFAULT 'S',
  `balanca_pro` char(1) DEFAULT 'N',
  `dataalt_pro` date DEFAULT NULL,
  `cod_mar` char(3) DEFAULT NULL,
  `cod_cat` char(3) DEFAULT NULL,
  `codbarra_pro` varchar(20) DEFAULT NULL,
  `codfab_pro` varchar(20) DEFAULT NULL,
  `cod_gen` char(2) DEFAULT NULL,
  `qconv` int(11) NOT NULL DEFAULT 1,
  `cfop_revenda` char(5) DEFAULT NULL,
  `cst_revenda` char(5) DEFAULT NULL,
  PRIMARY KEY (`cod_pro`),
  KEY `cod_sub` (`cod_sub`),
  KEY `codfab` (`cod_con`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_promocoes`
--

DROP TABLE IF EXISTS `tab_promocoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_promocoes` (
  `seq_pro` char(7) NOT NULL DEFAULT '',
  `data_pro` date NOT NULL DEFAULT '0000-00-00',
  `venc_pro` date NOT NULL DEFAULT '0000-00-00',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `desc_pro` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`seq_pro`,`cod_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_recados`
--

DROP TABLE IF EXISTS `tab_recados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_recados` (
  `seq_rec` int(11) NOT NULL AUTO_INCREMENT,
  `de_rec` char(20) NOT NULL DEFAULT '',
  `para_rec` char(5) NOT NULL DEFAULT '',
  `tipo_ter` char(1) NOT NULL DEFAULT '',
  `mensagem_rec` char(200) NOT NULL DEFAULT '',
  `status_rec` char(1) NOT NULL DEFAULT '1',
  `data_rec` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`seq_rec`)
) ENGINE=MyISAM AUTO_INCREMENT=5118 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_referencias`
--

DROP TABLE IF EXISTS `tab_referencias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_referencias` (
  `cod_cli` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `seq_ref` int(11) NOT NULL DEFAULT 0,
  `nome_ref` char(50) NOT NULL DEFAULT '',
  `cod_tip` int(2) NOT NULL DEFAULT 0,
  `tel_ref` char(20) NOT NULL DEFAULT '',
  `tipo_ref` char(2) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_cli`,`seq_ref`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_reposicao`
--

DROP TABLE IF EXISTS `tab_reposicao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_reposicao` (
  `seq_rep` char(7) NOT NULL DEFAULT '',
  `solicitante_rep` char(3) NOT NULL DEFAULT '',
  `abertura_rep` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `fechamento_Rep` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `atendente_rep` char(3) NOT NULL DEFAULT '',
  `atendimento_rep` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `status_rep` char(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`seq_rep`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_representantes`
--

DROP TABLE IF EXISTS `tab_representantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_representantes` (
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `nome_rep` varchar(50) DEFAULT NULL,
  `limite_rep` double(14,2) NOT NULL DEFAULT 0.00,
  `endereco_rep` varchar(40) DEFAULT NULL,
  `bairro_rep` varchar(40) DEFAULT NULL,
  `cidade_rep` varchar(40) DEFAULT NULL,
  `uf_rep` char(2) DEFAULT NULL,
  `cep_rep` varchar(10) DEFAULT NULL,
  `nasc_rep` date DEFAULT '0000-00-00',
  `natural_rep` varchar(30) DEFAULT NULL,
  `rg_rep` varchar(16) DEFAULT NULL,
  `cpf_rep` varchar(18) DEFAULT NULL,
  `sexo_rep` char(1) DEFAULT NULL,
  `conjuge_rep` varchar(40) DEFAULT NULL,
  `pai_rep` varchar(40) DEFAULT NULL,
  `mae_rep` varchar(40) DEFAULT NULL,
  `endpais_rep` varchar(60) DEFAULT NULL,
  `datacad_rep` date DEFAULT '0000-00-00',
  `obs_rep` varchar(250) DEFAULT NULL,
  `status_rep` char(1) DEFAULT '1',
  `cod_old` varchar(7) DEFAULT NULL,
  `cod_tip` char(2) DEFAULT '01',
  `cod_set` varchar(5) DEFAULT NULL,
  `cobranca_cli` char(1) DEFAULT '1',
  `setortrab_CLI` varchar(5) DEFAULT '00000',
  `senha_rep` varchar(10) DEFAULT NULL,
  `excluido_rep` char(1) DEFAULT 'N',
  `avalista_nome` varchar(100) DEFAULT NULL,
  `avalista_cpf` varchar(20) DEFAULT NULL,
  `avalista_rg` varchar(20) DEFAULT NULL,
  `avalista_endereco` varchar(200) DEFAULT NULL,
  `avalista_telefones` varchar(200) DEFAULT NULL,
  `avalista_anotacoes` text DEFAULT NULL,
  `motivo_bloqueio` text DEFAULT NULL,
  `lembrete` text DEFAULT NULL,
  `lembreteAcerto` text DEFAULT NULL,
  `ultimaconferencia` date DEFAULT NULL,
  `bloqimpr` char(1) NOT NULL DEFAULT 'N',
  `bloqdev` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`cod_rep`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_reptip`
--

DROP TABLE IF EXISTS `tab_reptip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_reptip` (
  `cod_tip` char(2) NOT NULL DEFAULT '',
  `cod_rep` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `comissao_tip` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`cod_tip`,`cod_rep`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_resumotmp`
--

DROP TABLE IF EXISTS `tab_resumotmp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_resumotmp` (
  `cod_rep` char(5) NOT NULL DEFAULT '',
  `valor` double(14,2) NOT NULL DEFAULT 0.00,
  `qtd` int(11) NOT NULL DEFAULT 0,
  `tipo` char(1) NOT NULL DEFAULT ''
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_resumotmpresult`
--

DROP TABLE IF EXISTS `tab_resumotmpresult`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_resumotmpresult` (
  `cod` char(5) NOT NULL DEFAULT '',
  `nome` char(60) NOT NULL DEFAULT '',
  `a` double(14,2) DEFAULT NULL,
  `qa` int(11) DEFAULT NULL,
  `d` double(14,2) DEFAULT NULL,
  `qd` int(11) DEFAULT NULL,
  `t` double(14,2) DEFAULT NULL,
  `qt` int(11) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_saidas`
--

DROP TABLE IF EXISTS `tab_saidas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_saidas` (
  `COD_CLI` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `NOTA_SAI` char(12) NOT NULL DEFAULT '',
  `SERIE_SAI` char(4) NOT NULL DEFAULT '',
  `VALOR_SAI` double(14,2) DEFAULT NULL,
  `DESCONTO_SAI` double(14,2) DEFAULT NULL,
  `ICMS_SAI` double(14,2) DEFAULT NULL,
  `NUM_VEN` char(7) NOT NULL DEFAULT '',
  `COD_USU` char(3) NOT NULL DEFAULT '',
  `EMISSAO_SAI` date NOT NULL DEFAULT '0000-00-00',
  `cod_cai` char(2) NOT NULL DEFAULT '01',
  `hora_sai` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_tur` char(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`NOTA_SAI`,`SERIE_SAI`,`cod_cai`,`EMISSAO_SAI`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_secoes`
--

DROP TABLE IF EXISTS `tab_secoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_secoes` (
  `cod_sec` char(3) NOT NULL DEFAULT '',
  `nome_sec` char(40) DEFAULT NULL,
  PRIMARY KEY (`cod_sec`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_setores`
--

DROP TABLE IF EXISTS `tab_setores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_setores` (
  `cod_set` char(5) NOT NULL DEFAULT '',
  `nome_set` char(40) DEFAULT NULL,
  `cobrador_set` char(3) DEFAULT NULL,
  `cod_cid` char(5) DEFAULT NULL,
  `cod_old` char(3) DEFAULT NULL,
  `tipo_set` char(20) DEFAULT 'BAIRRO',
  PRIMARY KEY (`cod_set`),
  KEY `fCodCid` (`cod_cid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_similares`
--

DROP TABLE IF EXISTS `tab_similares`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_similares` (
  `seq_sim` int(11) NOT NULL DEFAULT 0,
  `cod_pro` char(8) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_sim`,`cod_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_subsec`
--

DROP TABLE IF EXISTS `tab_subsec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_subsec` (
  `cod_sub` char(3) NOT NULL DEFAULT '',
  `nome_sub` char(50) DEFAULT NULL,
  `descmax_sub` double(14,2) NOT NULL DEFAULT 0.00,
  `comiss_sub` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_sec` char(3) DEFAULT NULL,
  PRIMARY KEY (`cod_sub`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_suspensao`
--

DROP TABLE IF EXISTS `tab_suspensao`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_suspensao` (
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `data_pro` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `motivo_sus` char(40) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_pro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_telefones`
--

DROP TABLE IF EXISTS `tab_telefones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_telefones` (
  `cod_cli` int(6) unsigned zerofill NOT NULL DEFAULT 000000,
  `num_tel` char(16) NOT NULL DEFAULT '',
  `tipo_tel` char(1) NOT NULL DEFAULT '',
  `tipo_ter` char(1) NOT NULL DEFAULT 'C',
  KEY `cod_cli` (`cod_cli`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_tipocai`
--

DROP TABLE IF EXISTS `tab_tipocai`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_tipocai` (
  `cod_tip` char(2) NOT NULL DEFAULT '',
  `nome_tip` char(20) DEFAULT '',
  PRIMARY KEY (`cod_tip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_tipocob`
--

DROP TABLE IF EXISTS `tab_tipocob`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_tipocob` (
  `cod_tip` char(2) NOT NULL DEFAULT '',
  `nome_tip` char(20) DEFAULT '',
  `comiss_tip` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`cod_tip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_tipopag`
--

DROP TABLE IF EXISTS `tab_tipopag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_tipopag` (
  `cod_tip` char(2) NOT NULL DEFAULT '',
  `nome_tip` char(20) DEFAULT '',
  PRIMARY KEY (`cod_tip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_tipopar`
--

DROP TABLE IF EXISTS `tab_tipopar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_tipopar` (
  `cod_tip` int(2) NOT NULL DEFAULT 0,
  `nome_tip` char(20) DEFAULT '',
  PRIMARY KEY (`cod_tip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_tiporef`
--

DROP TABLE IF EXISTS `tab_tiporef`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_tiporef` (
  `cod_tip` char(2) NOT NULL DEFAULT '',
  `nome_tip` char(20) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_tip`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_tipoven`
--

DROP TABLE IF EXISTS `tab_tipoven`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_tipoven` (
  `COD_TIP` char(2) NOT NULL DEFAULT '',
  `PARCELAS_TIP` int(11) NOT NULL DEFAULT 0,
  `JUROS_TIP` double(14,4) NOT NULL DEFAULT 0.0000,
  `DESCRICAO_TIP` char(20) DEFAULT '',
  `ENTRADA_TIP` char(1) DEFAULT '',
  `INTERVALO_TIP` int(11) NOT NULL DEFAULT 0,
  `tipo_tip` char(1) DEFAULT 'C',
  `fator_tip` double(14,2) NOT NULL DEFAULT 1.00,
  PRIMARY KEY (`COD_TIP`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_trocaavulsa`
--

DROP TABLE IF EXISTS `tab_trocaavulsa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_trocaavulsa` (
  `data` date NOT NULL DEFAULT '0000-00-00',
  `cod_usu` char(3) NOT NULL DEFAULT '000',
  `qtd_in` double(14,2) NOT NULL DEFAULT 0.00,
  `valor_in` double(14,2) NOT NULL DEFAULT 0.00,
  `valor_out` double(14,2) NOT NULL DEFAULT 0.00,
  `desconto` double(14,2) NOT NULL DEFAULT 0.00,
  `cliente` char(40) DEFAULT NULL,
  `vendedor` char(3) DEFAULT NULL,
  `obs` char(200) NOT NULL DEFAULT '',
  `id` int(11) unsigned NOT NULL DEFAULT 0,
  `telefone` char(30) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_trocaavulsait`
--

DROP TABLE IF EXISTS `tab_trocaavulsait`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_trocaavulsait` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_tro` int(11) NOT NULL DEFAULT 0,
  `codigo` char(8) NOT NULL DEFAULT '',
  `qtd` double(14,2) NOT NULL DEFAULT 0.00,
  `unit` double(14,2) NOT NULL DEFAULT 0.00,
  `total` double(14,2) NOT NULL DEFAULT 0.00,
  `tipo` char(1) NOT NULL DEFAULT 'I',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=15803 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_trocas`
--

DROP TABLE IF EXISTS `tab_trocas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_trocas` (
  `num_ven` char(7) NOT NULL DEFAULT '',
  `data_tro` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `seq_tro` char(7) NOT NULL DEFAULT '',
  `abat_tro` double(14,2) NOT NULL DEFAULT 0.00,
  `acres_tro` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_ven` char(3) NOT NULL DEFAULT '',
  `desconto_tro` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`seq_tro`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_turncai`
--

DROP TABLE IF EXISTS `tab_turncai`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_turncai` (
  `cod_tur` char(1) NOT NULL DEFAULT '',
  `cod_cai` char(2) NOT NULL DEFAULT '',
  `data_tur` date NOT NULL DEFAULT '0000-00-00',
  `login_usu` char(3) NOT NULL DEFAULT '',
  `logout_usu` char(3) NOT NULL DEFAULT '',
  `abertura_tur` char(5) NOT NULL DEFAULT '',
  `fechamento_tur` char(5) NOT NULL DEFAULT '',
  `valorabertura_tur` double(14,2) NOT NULL DEFAULT 0.00,
  `valorfechamento_tur` double(14,2) NOT NULL DEFAULT 0.00,
  `status_tur` char(1) NOT NULL DEFAULT 'A',
  `fundo_tur` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`cod_tur`,`cod_cai`,`data_tur`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_turnos`
--

DROP TABLE IF EXISTS `tab_turnos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_turnos` (
  `cod_tur` char(1) NOT NULL DEFAULT '',
  `horaini_tur` char(5) DEFAULT '',
  `horafin_tur` char(5) DEFAULT '',
  PRIMARY KEY (`cod_tur`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_usuarios`
--

DROP TABLE IF EXISTS `tab_usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_usuarios` (
  `COD_FUN` char(3) NOT NULL DEFAULT '',
  `ULTACESSO_USU` datetime DEFAULT NULL,
  `NIVEL_USU` char(1) DEFAULT '1',
  `SENHA_USU` char(10) DEFAULT NULL,
  `Status_USU` char(1) DEFAULT '1',
  `corfundo_usu` char(20) DEFAULT NULL,
  PRIMARY KEY (`COD_FUN`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_valescai`
--

DROP TABLE IF EXISTS `tab_valescai`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_valescai` (
  `seq_cai` char(7) NOT NULL DEFAULT '',
  `cod_fun` char(3) DEFAULT '',
  PRIMARY KEY (`seq_cai`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_vendaaberta`
--

DROP TABLE IF EXISTS `tab_vendaaberta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_vendaaberta` (
  `num_ven` char(7) NOT NULL DEFAULT '',
  `ip_ven` char(16) NOT NULL DEFAULT '',
  PRIMARY KEY (`num_ven`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_vendas`
--

DROP TABLE IF EXISTS `tab_vendas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_vendas` (
  `num_ven` varchar(7) NOT NULL DEFAULT '',
  `cod_cli` int(6) NOT NULL DEFAULT 0,
  `seq_con` varchar(5) DEFAULT NULL,
  `data_ven` datetime DEFAULT '0000-00-00 00:00:00',
  `dataefet_ven` date DEFAULT '0000-00-00',
  `ip_ven` varchar(20) DEFAULT NULL,
  `valor_ven` double(14,2) NOT NULL DEFAULT 0.00,
  `abrevenda_usu` char(3) NOT NULL DEFAULT '',
  `fechavenda_usu` char(3) DEFAULT NULL,
  `situacao_ven` char(1) NOT NULL DEFAULT '1',
  `desconto_ven` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_for` char(2) NOT NULL DEFAULT '01',
  `nomecli_ven` varchar(50) DEFAULT NULL,
  `cancelavenda_usu` char(3) DEFAULT NULL,
  `entrega_ven` char(1) DEFAULT NULL,
  `endereco_ven` varchar(80) DEFAULT NULL,
  `bairro_ven` varchar(60) DEFAULT NULL,
  `fone_ven` varchar(40) DEFAULT NULL,
  `crediario_ven` char(1) NOT NULL DEFAULT '0',
  `status_ven` char(1) NOT NULL DEFAULT '0',
  `autorizadesconto_ven` char(3) DEFAULT NULL,
  `tipocli_ven` char(1) NOT NULL DEFAULT 'C',
  `telefonecli_ven` varchar(60) DEFAULT NULL,
  `cpfcli_ven` varchar(11) NOT NULL DEFAULT '',
  `tipo_ven` char(1) DEFAULT 'V',
  `valorentrega_ven` double(14,2) DEFAULT 0.00,
  `enderecoentrega_ven` varchar(200) DEFAULT NULL,
  `cod_emp` char(2) NOT NULL DEFAULT '01',
  `email_ven` char(255) DEFAULT NULL,
  `aniversario_ven` char(5) DEFAULT NULL,
  `cod_cai` char(2) NOT NULL DEFAULT '01',
  `tipo_operacao` char(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`num_ven`),
  KEY `codcli` (`cod_cli`),
  KEY `codfor` (`cod_for`),
  KEY `abrevenda_usu` (`abrevenda_usu`),
  KEY `fechavenda_usu` (`fechavenda_usu`),
  KEY `status_ven` (`status_ven`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_venfec`
--

DROP TABLE IF EXISTS `tab_venfec`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_venfec` (
  `num_ven` char(7) NOT NULL DEFAULT '',
  `valor_ven` double(14,2) NOT NULL DEFAULT 0.00,
  `cod_for` char(2) NOT NULL DEFAULT '',
  `cod_fin` char(2) NOT NULL DEFAULT '',
  `cod_cai` char(2) NOT NULL DEFAULT '01',
  `cod_tur` char(1) NOT NULL DEFAULT '1',
  `esp_cai` char(3) NOT NULL DEFAULT 'DIN',
  PRIMARY KEY (`num_ven`,`cod_for`),
  KEY `fk_caixa` (`cod_cai`),
  KEY `ccai` (`cod_cai`,`num_ven`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_venfin`
--

DROP TABLE IF EXISTS `tab_venfin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_venfin` (
  `num_ven` varchar(7) NOT NULL DEFAULT '',
  `cod_fin` char(3) NOT NULL DEFAULT '',
  `valor_fin` double(14,2) NOT NULL DEFAULT 0.00,
  `reman_fin` double(14,2) NOT NULL DEFAULT 0.00,
  `data_fin` date DEFAULT '0000-00-00',
  `autorizacao_fin` varchar(60) DEFAULT '',
  `parcelas_fin` int(2) unsigned NOT NULL DEFAULT 1,
  `cod_usu` char(3) DEFAULT '',
  `tipo_fin` char(1) DEFAULT 'V',
  `operacao_fin` char(1) DEFAULT '0',
  `hora_fin` varchar(20) DEFAULT '00:00',
  `mensagem` text DEFAULT NULL,
  `cnpj_fin` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`num_ven`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tab_vinc`
--

DROP TABLE IF EXISTS `tab_vinc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tab_vinc` (
  `seq_vin` char(7) NOT NULL DEFAULT '',
  `seq_itd` char(7) NOT NULL DEFAULT '',
  `data_vin` date NOT NULL DEFAULT '0000-00-00',
  `valor_vin` double(14,2) NOT NULL DEFAULT 0.00,
  `acres_vin` double(14,2) NOT NULL DEFAULT 0.00,
  `decres_vin` double(14,2) NOT NULL DEFAULT 0.00,
  `venc_vin` double(14,2) NOT NULL DEFAULT 0.00,
  `parc_vin` double(14,2) NOT NULL DEFAULT 0.00,
  `seq_doc` char(7) NOT NULL DEFAULT '',
  PRIMARY KEY (`seq_vin`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tad_descprod`
--

DROP TABLE IF EXISTS `tad_descprod`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tad_descprod` (
  `cod_car` char(3) NOT NULL DEFAULT '',
  `cod_pro` char(8) NOT NULL DEFAULT '',
  `desc_pro` double(14,2) DEFAULT NULL,
  PRIMARY KEY (`cod_pro`,`cod_car`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tipoven`
--

DROP TABLE IF EXISTS `tipoven`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tipoven` (
  `codigo` char(1) NOT NULL DEFAULT '',
  `descricao` char(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`codigo`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `turncai`
--

DROP TABLE IF EXISTS `turncai`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `turncai` (
  `cod_tur` char(1) NOT NULL DEFAULT '',
  `cod_cai` char(2) NOT NULL DEFAULT '',
  `data_tur` date NOT NULL DEFAULT '0000-00-00',
  `login_usu` char(3) DEFAULT NULL,
  `logout_usu` char(3) DEFAULT NULL,
  `abertura_tur` char(5) DEFAULT NULL,
  `fechamento_tur` char(5) DEFAULT NULL,
  `valorabertura_tur` double(14,2) NOT NULL DEFAULT 0.00,
  `valorfechamento_tur` double(14,2) NOT NULL DEFAULT 0.00,
  `status_tur` char(1) NOT NULL DEFAULT 'A',
  `fundo_tur` double(14,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`cod_tur`,`cod_cai`,`data_tur`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `turnos`
--

DROP TABLE IF EXISTS `turnos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `turnos` (
  `cod_tur` char(1) NOT NULL DEFAULT '',
  `horaini_tur` char(5) NOT NULL DEFAULT '',
  `horafin_tur` char(5) NOT NULL DEFAULT '',
  PRIMARY KEY (`cod_tur`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vales`
--

DROP TABLE IF EXISTS `vales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vales` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cod_fun` char(3) NOT NULL DEFAULT '',
  `historico` char(200) DEFAULT NULL,
  `valor` double DEFAULT NULL,
  `referencia` date DEFAULT NULL,
  `data` date DEFAULT NULL,
  `cod_usu` char(3) NOT NULL DEFAULT '',
  `parcela` char(10) DEFAULT NULL,
  `num_ven` char(8) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=38336 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping events for database 'requinte'
--

--
-- Dumping routines for database 'requinte'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-10-30 11:19:30
