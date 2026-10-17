# SalesApp API (`sales_api`)

API RESTful assíncrona e servidor WebSocket para o **SalesApp** — sistema completo de gestão de vendas, controle de estoque, despesas e métricas financeiras multi-empresa (*multi-tenant*). Desenvolvida com **FastAPI**, **SQLModel / SQLAlchemy 2.0 (Async)**, **PostgreSQL 16**, **Redis 7** e **Alembic**.

---

## ✨ Principais Funcionalidades

- **🔐 Autenticação, Segurança e Conta (`/users`)**
  - Cadastro de usuários com confirmação de e-mail via link seguro (integração com **Resend**).
  - Autenticação com **JWT (`access_token` e `refresh_token`)** e *blacklist* de tokens no **Redis** no logout.
  - Fluxo de recuperação de senha (*Esqueci minha senha* / *Reset de senha*) e troca de e-mail com token temporário no Redis.
  - Proteção por **Rate Limiting** via Redis em rotas sensíveis (login, cadastro, redefinição de senha, troca de e-mail, etc.).
  - Upload seguro de avatar de usuário e logo de empresa com validação de *magic bytes* (PNG, JPEG, WebP) e limite de tamanho.

- **🏢 Arquitetura Multi-Empresa / Multi-Tenant (`/companies`)**
  - Isolamento completo de dados por empresa (`company_id`).
  - Criação de empresas, alternância de empresa ativa e gerenciamento de perfil corporativo e endereço.
  - Sistema de convites para membros (aceitar/recusar) com notificações em **tempo real via WebSocket (`/ws`)**.
  - Controle de permissões por membro (`ADMIN`, `EDITOR`, `VIEWER`) e definição de cargo (`job_title`) por empresa.

- **🛒 Vendas (`/sales`) e Entradas de Estoque (`/stock_entries`)**
  - Criação transacional com múltiplos produtos, validação e atualização automática de saldo em estoque (`stock_amount`).
  - Suporte a **descontos** no total da venda e da entrada de estoque.
  - Cancelamento com estorno automático de quantidades no estoque e exclusão individual ou em lote (*bulk delete*) de registros cancelados.

- **📦 Produtos (`/products`), Categorias (`/categories`) e Outras Despesas (`/other_expenses`)**
  - CRUD completo com paginação, ordenação dinâmica, filtros de busca e rastreamento do autor (`created_by`).
  - Categorias tipadas (*Produtos* e *Outras Despesas*) com cálculo de faturamento/gastos líquidos por categoria (`/categories/amounts`), considerando descontos proporcionais.
  - Proteção contra exclusão de produtos ou categorias que possuam vínculos ativos.

- **📊 Dashboard (`/dashboard`) e Auditoria (`/history`)**
  - Indicadores financeiros consolidados (*Saldo Atual*, *Lucro Líquido*, *Receitas* e *Despesas*).
  - Séries temporais para gráficos (*Diário*, *Semanal*, *Mensal* e *Anual*) respeitando o fuso horário do cliente.
  - Ranking de *Produtos Mais Vendidos* (`/dashboard/top-products`) ordenado pelo faturamento líquido.
  - Log automático de auditoria (`History`) para criações, edições, cancelamentos e exclusões em todas as entidades.

---

## 🛠️ Tecnologias Utilizadas

- **Framework Web:** [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **ORM e Banco de Dados:** [SQLModel](https://sqlmodel.tiangolo.com/) + [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/) + `asyncpg` ([PostgreSQL 16](https://www.postgresql.org/))
- **Migrações:** [Alembic](https://alembic.sqlalchemy.org/)
- **Cache, Rate Limit e Tokens:** [Redis 7](https://redis.io/) (`redis.asyncio`)
- **Validação e Configurações:** [Pydantic v2](https://docs.pydantic.dev/) + `pydantic-settings`
- **Segurança:** `python-jose` (JWT) + `passlib[bcrypt]`
- **E-mails Transacionais:** [Resend API](https://resend.com/) (com templates HTML responsivos)
- **Testes Automatizados:** [Pytest](https://docs.pytest.org/) + `pytest-asyncio` + `httpx`
- **Infraestrutura:** Docker & Docker Compose (App, PostgreSQL, PostgreSQL Test, Redis e pgAdmin 4)

---

## 📂 Estrutura do Projeto

```text
sales_api/
├── app/
│   ├── api/
│   │   ├── routes/          # Endpoints REST (users, companies, sales, stock_entries, products, categories, etc.)
│   │   ├── schemas/         # Contratos Pydantic de entrada e saída
│   │   ├── dependencies.py  # Injeção de dependências (usuário autenticado, permissões, rate limit)
│   │   ├── router.py        # Registro central de todas as rotas
│   │   ├── tokens.py        # Geração e validação de tokens JWT
│   │   └── websocket.py     # Gerenciador de conexões WebSocket em tempo real
│   ├── database/
│   │   ├── models/          # Modelos SQLModel das tabelas do PostgreSQL
│   │   ├── engine.py        # Configuração do AsyncEngine e sessão do banco
│   │   └── redis.py         # Cliente assíncrono do Redis (blacklist, rate limit e chaves temporárias)
│   ├── enums/               # Enumerações de domínio (SaleStatus, StockEntryStatus, CategoryType, CompanyPermission, etc.)
│   ├── services/            # Regras de negócio, BaseService genérico, envio de e-mails e histórico
│   ├── utils/               # Utilitários (validação e armazenamento de uploads de imagens)
│   ├── config.py            # Carregamento tipado das variáveis de ambiente (.env)
│   └── main.py              # Ponto de entrada da aplicação FastAPI, CORS, StaticFiles e WebSocket
├── migrations/              # Ambiente e versões de migração do banco de dados (Alembic)
├── tests/                   # Suíte de testes de integração assíncronos (Pytest)
├── docker-compose.yml       # Orquestração dos containers (app, database, database_test, redis, pgadmin)
├── Dockerfile               # Imagem Docker da API
└── requirements.txt         # Dependências Python
```

---

## ⚙️ Configuração e Execução

### 1. Variáveis de Ambiente (`.env`)

Crie um arquivo `.env` na raiz do projeto `sales_api`:

```env
# Banco de Dados Principal (PostgreSQL)
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=sales_api
DB_HOST=localhost
DB_PORT=5432

# Banco de Dados de Testes
DB_TEST_NAME=sales_api_test
DB_TEST_PORT=5433

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Autenticação JWT
JWT_SECRET=sua_chave_secreta_super_segura
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Aplicação e CORS
DEBUG=True
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
FRONTEND_URL=http://localhost:3000

# E-mails (Resend)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxx
EMAIL_FROM="SalesApp <onboarding@resend.dev>"
EMAIL_VERIFICATION_EXPIRE_HOURS=24
```

### 2. Executando com Docker Compose (Recomendado)

Suba os serviços de banco de dados, Redis e a API (as migrações do Alembic são aplicadas automaticamente ao iniciar o container `app`):

```bash
docker compose up -d
```

- **API:** [http://localhost:8000](http://localhost:8000)
- **Documentação Swagger (OpenAPI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **pgAdmin 4:** [http://localhost:5050](http://localhost:5050) (`pgadmin@gmail.com` / `secret`)

---

## 🗄️ Migrações de Banco de Dados (Alembic)

Com os containers rodando, você pode gerenciar as migrações diretamente pelo Docker:

```bash
# Aplicar todas as migrações pendentes
docker compose exec app alembic upgrade head

# Verificar a revisão atual do banco
docker compose exec app alembic current

# Verificar se há alterações nos models ainda sem migração
docker compose exec app alembic check

# Gerar uma nova migração automaticamente
docker compose exec app alembic revision --autogenerate -m "descricao_da_migracao"

# Reverter a última migração
docker compose exec app alembic downgrade -1
```

---

## 🧪 Executando os Testes

O `docker-compose.yml` inclui um container dedicado de banco de testes (`database_test`) para que a execução dos testes nunca afete o banco de desenvolvimento:

```bash
# Certifique-se de que o banco de testes está ativo
docker compose up -d database_test

# Executar toda a suíte de testes
docker compose exec app pytest

# Executar um arquivo de teste específico
docker compose exec app pytest tests/test_categories.py
```

---

## 📡 Principais Grupos de Rotas

| Prefixo | Descrição |
| :--- | :--- |
| `/users` | Cadastro, verificação de e-mail, login, refresh, logout, perfil, avatar, troca de senha/e-mail e reset de senha |
| `/companies` | Criação e edição de empresas, upload de logo, convites, membros e permissões |
| `/dashboard` | Resumo financeiro (`/budgets`), gráfico Receitas vs Despesas (`/chart`) e Top Produtos (`/top-products`) |
| `/sales` | Listagem, detalhes, criação com desconto, cancelamento e exclusão de vendas |
| `/stock_entries` | Listagem, detalhes, criação com desconto, cancelamento e exclusão de entradas de estoque |
| `/products` | CRUD de produtos e controle de estoque |
| `/categories` | CRUD de categorias e totais líquidos por categoria (`/categories/amounts`) |
| `/other_expenses` | CRUD de outras despesas |
| `/history` | Histórico paginado de ações e auditoria da empresa |
| `/ws` | Conexão WebSocket autenticada para notificações em tempo real |

---

## 📄 Licença

Este projeto está sob a licença MIT.
