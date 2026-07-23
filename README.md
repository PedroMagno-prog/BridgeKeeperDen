# BridgeKeeper Portal

Monorepo com frontend Vue.js e backend Python (FastAPI + PostgreSQL).

---

## 📁 Estrutura do Projeto

```
BridgeKeeperPortal/
├── frontend/                    # Vue 3 + TypeScript + Pinia + Vue Router
│   ├── src/
│   │   ├── assets/
│   │   │   ├── css/             # Estilos globais e variáveis CSS
│   │   │   ├── images/          # Imagens e ícones estáticos
│   │   │   └── fonts/           # Fontes customizadas
│   │   ├── components/          # Componentes reutilizáveis
│   │   ├── views/               # Páginas/rotas
│   │   ├── stores/              # Pinia stores (estado global)
│   │   ├── router/              # Configuração do Vue Router
│   │   └── main.ts              # Entry point
│   ├── public/
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
│
└── backend/                     # FastAPI + SQLAlchemy + Alembic + PostgreSQL
    ├── app/
    │   ├── api/
    │   │   ├── deps/
    │   │   │   └── database.py  # Dependency injection de sessão DB
    │   │   ├── routes/          # Módulos de rotas (ex: users.py)
    │   │   └── router.py        # Router principal (agrega sub-routers)
    │   ├── core/
    │   │   └── config.py        # Settings via pydantic-settings + .env
    │   ├── db/
    │   │   ├── migrations/
    │   │   │   ├── versions/    # Arquivos de migração Alembic
    │   │   │   └── env.py       # Ambiente Alembic (async-compatible)
    │   │   ├── models/          # Modelos SQLAlchemy ORM
    │   │   └── session.py       # Engine async + SessionLocal + Base
    │   ├── schemas/             # Pydantic schemas (request/response)
    │   ├── services/            # Lógica de negócio (service layer)
    │   └── main.py              # FastAPI app factory + CORS + routers
    ├── tests/                   # Testes com pytest-asyncio
    ├── alembic.ini              # Configuração do Alembic
    ├── requirements.txt         # Dependências Python
    └── .env.example             # Template de variáveis de ambiente
```

---

## 🚀 Como rodar

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

### Backend

```bash
cd backend

# 1. Criar e ativar virtualenv
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
copy .env.example .env
# edite o .env com suas credenciais PostgreSQL

# 4. Rodar migrações
alembic upgrade head

# 5. Iniciar servidor
uvicorn app.main:app --reload   # http://localhost:8000
```

### Documentação da API

| URL | Descrição |
|-----|-----------|
| `http://localhost:8000/api/v1/docs` | Swagger UI |
| `http://localhost:8000/api/v1/redoc` | ReDoc |

---

## 🔑 Variáveis de Ambiente (backend/.env)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `SECRET_KEY` | Chave secreta JWT | — |
| `POSTGRES_HOST` | Host do PostgreSQL | `localhost` |
| `POSTGRES_PORT` | Porta | `5432` |
| `POSTGRES_USER` | Usuário | `postgres` |
| `POSTGRES_PASSWORD` | Senha | `postgres` |
| `POSTGRES_DB` | Nome do banco | `bridgekeeper_db` |
| `BACKEND_CORS_ORIGINS` | Origens permitidas (JSON array) | `["http://localhost:5173"]` |

---

## 🛠 Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Vue 3, TypeScript, Pinia, Vue Router, Vite |
| Backend | FastAPI, Python 3.11+ |
| ORM | SQLAlchemy 2 (async) |
| Migrações | Alembic |
| Banco de dados | PostgreSQL |
| Autenticação | python-jose + passlib/bcrypt |
