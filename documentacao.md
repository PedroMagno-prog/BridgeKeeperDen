# Documentação de Deploy — BridgeKeeper Den

## 1. Banco de Dados: CockroachDB Cloud
- **Painel**: [https://cockroachlabs.cloud/](https://cockroachlabs.cloud/)
- **Host**: `bridgekeeper-31640.j77.aws-us-east-2.cockroachlabs.cloud:26257`
- **Dialeto**: SQLAlchemy `cockroachdb+asyncpg` (gerenciado automaticamente pelo backend)

---

## 2. Backend no Render.com

### Configurações de Serviço:
- **Environment**: `Python 3`
- **Root Directory**: `backend` (ou deixe vazio se executar a partir da raiz com `-c backend/alembic.ini`)
- **Build Command**:
  ```bash
  pip install -r requirements.txt && alembic upgrade head
  ```
- **Start Command**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

### Variáveis de Ambiente no Render:

| Key | Value | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql://velhodaponte:zuZJCKTM7nDYzhGhPkYmVQ@bridgekeeper-31640.j77.aws-us-east-2.cockroachlabs.cloud:26257/defaultdb?ssl=require` | URL do banco CockroachDB |
| `BACKEND_CORS_ORIGINS` | `["https://bridgekeeperden1.vercel.app","https://bridgekeeper-phi.vercel.app"]` | Origens autorizadas para o frontend |
| `SECRET_KEY` | `0a6750834d87bf5cff6b4bbd5997d128` | Chave secreta para JWT |
| `DEBUG` | `False` | Desativa modo debug em produção |
| `PYTHON_VERSION` | `3.11.9` | Versão do Python utilizada |

---

## 3. Frontend no Vercel

- **Painel**: [https://vercel.com/](https://vercel.com/)
- **Framework Preset**: `Vite`
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### Variáveis de Ambiente no Vercel:

| Key | Value | Descrição |
|---|---|---|
| `VITE_API_URL` | `https://bridgekeeperden.onrender.com/api/v1` | URL base da API FastAPI no Render |

### Domínios do Frontend:
- `https://bridgekeeperden1.vercel.app`
- `https://bridgekeeper-phi.vercel.app`
