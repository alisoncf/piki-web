-- 001 · Credenciais do sistema novo (decisão D7)
-- Aplicar uma vez no banco: mariadb -u USUARIO -p requinte < 001_web_credencial.sql
-- Não altera nenhuma tabela do VB6.

CREATE TABLE IF NOT EXISTS web_credencial (
  cod_fun       CHAR(3)      NOT NULL,
  hash_senha    VARCHAR(255) NOT NULL,
  marca_legado  CHAR(64)     NOT NULL,
  criado_em     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ultimo_login  DATETIME     NULL,
  PRIMARY KEY (cod_fun)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
