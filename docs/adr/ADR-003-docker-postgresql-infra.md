# ADR-003: Infraestrutura com Docker e PostgreSQL (Fase 2)

| Status   | Aceito     |
|----------|------------|
| Data     | 21-08-2026 |
| Área     | Infraestrutura / Banco de Dados |

## Contexto

Na Fase 2 do CineLake AI, necessitamos configurar a base da nossa infraestrutura de banco de dados relacional e preparar as ferramentas de migração de schema e testes de integração de forma automatizada e replicável.

## Problema

Como estruturar o banco de dados PostgreSQL utilizando Docker Compose, garantindo segurança (não expondo a porta de dados publicamente na internet), limitação de recursos na VPS, compatibilidade com o SQLAlchemy 2.0 e migrações rastreáveis com Alembic?

## Decisão

Implementar o PostgreSQL v16 Alpine via Docker Compose mapeado localmente e configurar o SQLAlchemy + Alembic para carregar as configurações de ambiente dinamicamente.

---

## Explicação Detalhada

### Docker Compose

- **`image: postgres:16-alpine`**: usa a imagem oficial do PostgreSQL, versão 16, baseada em Alpine Linux (leve e segura).
- **`restart: unless-stopped`**: reinicia automaticamente o container em caso de falhas ou reinicialização da VPS, a menos que seja parado manualmente.
- **`environment`**: lê as credenciais (usuário, senha, nome do banco) a partir do arquivo `.env` (não versionado por motivos de segurança).
- **`ports: "127.0.0.1:5432:5432"`**: expõe a porta apenas para o host local (localhost) da VPS, impossibilitando acessos diretos vindos da internet pública.
- **`volumes: pgdata:/var/lib/postgresql/data`**: garante a persistência dos dados do banco usando um volume nomeado do Docker.
- **`networks: cinelake-network`**: rede bridge dedicada para comunicação interna segura entre o banco e outros serviços no futuro.
- **`healthcheck`**: utiliza a ferramenta nativa `pg_isready` para garantir que o PostgreSQL esteja totalmente pronto para conexões antes de outros componentes tentarem acessá-lo.
- **`deploy.resources.limits`**: define limites estritos de uso (1 vCPU e 1GB de RAM) para evitar que o banco de dados consuma todos os recursos da VPS.

### Configuração

O arquivo `config.py` foi estruturado para carregar as variáveis de ambiente a partir do `.env` e montar dinamicamente a string `DATABASE_URL`. Usamos uma `dataclass` congelada (`frozen=True`) para garantir a imutabilidade das configurações durante a execução da aplicação.

### SQLAlchemy

A função `get_engine()` foi configurada com `pool_pre_ping=True` para testar a validade das conexões da pool antes de passá-las à aplicação, garantindo resiliência contra quedas rápidas. O teste de integridade `check_database_connection()` executa de maneira segura a query `"SELECT 1"` encapsulada em `text()` para validar que a conexão está operando corretamente.

### Alembic

- O arquivo `alembic.ini` define as configurações padrão e a localização da pasta de migrações (`script_location = alembic`).
- O arquivo `env.py` foi customizado para substituir a URL estática pelo valor dinâmico carregado do `settings.database_url`.
- A migração `0001` cria a tabela inicial `service_heartbeat` para registrar o status dos microsserviços.

### Testes de Integração

Foram implementados testes de integração em `tests/integration/test_postgres_connection.py` que validam a conectividade real do SQLAlchemy com o banco e a presença física da tabela `service_heartbeat` pós-migrações.

---

## Execução

### 1. Instalar as novas dependências Python (PC e VPS)

No terminal (com o ambiente virtual ativo):
```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 2. Copiar e configurar o arquivo `.env`

```bash
cp .env.example .env
```
*(Edite o `.env` gerado preenchendo as senhas do banco de dados).*

### 3. Iniciar o container do PostgreSQL na VPS

```bash
docker compose up -d postgres
```

### 4. Executar as migrações com Alembic

```bash
alembic upgrade head
```

### 5. Rodar os testes de integração

```bash
pytest -v
```
