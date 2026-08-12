# ETAPA 4: Sistema de Convites de Jogadores, Links de Acesso (`/join/:code`) e Gestão de Membros do Mundo

> **Instrução para o Agente de IA da IDE:**
> Você deve implementar estritamente os requisitos e alterações descritos nesta etapa. Mantenha os padrões do projeto (FastAPI + SQLAlchemy Assíncrono no backend; Vue 3 + TypeScript + Pinia + CSS Variables no frontend). Siga rigorosamente a arquitetura de permissões existente e as convenções do projeto.

---

## 1. Visão Geral e Objetivos da Etapa 4

No estado atual do sistema, qualquer usuário cadastrado pode criar um *Mundo* e torna-se automaticamente seu proprietário com papel de **MESTRE** (`UserRole.MESTRE`). No entanto, não há um fluxo estruturado para convidar e integrar outros usuários cadastrados na plataforma como **JOGADORES** (`UserRole.JOGADOR`).

O objetivo desta etapa é implementar um **Mecanismo Completo de Convites e Gestão de Membros**, permitindo que Mestres compartilhem seus mundos com seus grupos de RPG com facilidade e segurança.

### Funcionalidades Entregues nesta Etapa:
1. **Código Único de Convite por Mundo (`invite_code`):** Cada Mundo possui uma chave alfanumérica única gerada automaticamente.
2. **Link de Convite Rápido (`/join/:invite_code`):** O Mestre pode copiar e compartilhar um link direto de acesso com seus jogadores.
3. **Página de Aceite de Convite (`JoinWorldView.vue`):** Interface amigável para o jogador visualizar informações do Mundo e confirmar sua entrada como `JOGADOR`.
4. **Convite Direto por E-mail / Username:** Autocomplete de busca de usuários cadastrados no sistema para adição direta pelo Mestre.
5. **Painel de Gestão de Membros do Mundo (`MembersModal.vue`):**
   - Listagem de membros com papéis (`MESTRE` / `JOGADOR`).
   - Alteração dinâmica de papéis pelo Mestre.
   - Expulsão / remoção de membros do Mundo.
   - Rotacionamento / revogação do código de convite (para invalidar links antigos).
6. **Ação de "Sair do Mundo":** Jogadores podem decidir voluntariamente sair de uma campanha.
7. **Opção "Entrar com Código" no Dashboard:** Permitir aos jogadores colarem diretamente um código de convite no Dashboard principal.

---

## 2. Detalhamento das Alterações - Backend (FastAPI / SQLAlchemy)

### 2.1. Alteração na Tabela `worlds` (`backend/app/db/models/world.py`)

Adicionar o campo `invite_code` único à entidade `World`:

```python
import secrets

def generate_invite_code() -> str:
    """Gera um código de convite único de 10 caracteres (ex: 'k9X2mQ8pL1')."""
    return secrets.token_urlsafe(8)[:10]

class World(Base):
    __tablename__ = "worlds"

    # ... campos existentes ...
    invite_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        default=generate_invite_code,
        index=True,
        comment="Código único para link de convite de jogadores",
    )
```

### 2.2. Migração Alembic (`backend/app/db/migrations/versions/c3d4e5f6a7b8_add_world_invite_code.py`)

Criar uma migração para incluir a coluna `invite_code` na tabela `worlds`.
*Para mundos pré-existentes sem o código, a migração deve popular com valores gerados únicos antes de aplicar a restrição `NOT NULL` e `UNIQUE`.*

### 2.3. Schemas de Pydantic (`backend/app/schemas/world.py` e `world_member.py`)

```python
class WorldInviteInfoOut(BaseModel):
    """Informações públicas do mundo exibidas na tela de convite /join/:code."""
    invite_code: str
    world_id: uuid.UUID
    world_name: str
    world_description: str | None
    owner_username: str
    members_count: int

class MemberUpdateRoleInput(BaseModel):
    role: UserRole

class DirectMemberAddInput(BaseModel):
    user_id_or_email: str
    role: UserRole = UserRole.JOGADOR

class MemberDetailOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    email: str
    role: UserRole
    joined_at: datetime
```

### 2.4. Atualização do Serviço de Mundo (`backend/app/services/world_service.py`)

Implementar as funções de negócio para membros e convites:

```python
async def buscar_mundo_por_codigo_convite(
    db: AsyncSession, invite_code: str
) -> World | None:
    stmt = select(World).where(World.invite_code == invite_code)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def rotacionar_codigo_convite(
    db: AsyncSession, world_id: uuid.UUID
) -> str:
    world = await buscar_mundo(db, world_id)
    if not world:
        raise ValueError("Mundo não encontrado")
    world.invite_code = generate_invite_code()
    await db.flush()
    return world.invite_code

async def entrar_no_mundo_por_codigo(
    db: AsyncSession, user_id: uuid.UUID, invite_code: str
) -> tuple[World, WorldMember]:
    world = await buscar_mundo_por_codigo_convite(db, invite_code)
    if not world:
        raise HTTPException(status_code=404, detail="Código de convite inválido ou expirado.")

    # Verificar se já é membro
    membro_existente = await obter_role_no_mundo(db, world.id, user_id)
    if membro_existente:
        raise HTTPException(status_code=400, detail="Você já é membro deste mundo.")

    novo_membro = WorldMember(
        world_id=world.id,
        user_id=user_id,
        role=UserRole.JOGADOR
    )
    db.add(novo_membro)
    await db.flush()
    return world, novo_membro

async def listar_membros_do_mundo(
    db: AsyncSession, world_id: uuid.UUID
) -> list[dict]:
    stmt = (
        select(WorldMember, User)
        .join(User, User.id == WorldMember.user_id)
        .where(WorldMember.world_id == world_id)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": member.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": member.role,
            "joined_at": member.created_at if hasattr(member, 'created_at') else None
        }
        for member, user in rows
    ]

async def remover_membro_do_mundo(
    db: AsyncSession, world_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    world = await buscar_mundo(db, world_id)
    if world and world.owner_id == user_id:
        raise HTTPException(status_code=400, detail="O criador do mundo não pode ser removido.")

    stmt = delete(WorldMember).where(
        WorldMember.world_id == world_id,
        WorldMember.user_id == user_id
    )
    await db.execute(stmt)
```

### 2.5. Rotas de API REST (`backend/app/api/routes/worlds.py` e `users.py`)

- **`GET /api/v1/worlds/invite-info/{invite_code}`**: Retorna detalhes básicos do mundo para pré-visualização na tela de convite pública/autenticada.
- **`POST /api/v1/worlds/join/{invite_code}`**: Adiciona o usuário logado como `JOGADOR` no mundo.
- **`GET /api/v1/worlds/{world_id}/members`**: Lista todos os membros do mundo (Apenas membros do mundo).
- **`POST /api/v1/worlds/{world_id}/members`**: Adiciona um usuário diretamente buscando por e-mail ou username (Apenas Mestre).
- **`PUT /api/v1/worlds/{world_id}/members/{target_user_id}/role`**: Altera a role do membro para `MESTRE` ou `JOGADOR` (Apenas Mestre).
- **`DELETE /api/v1/worlds/{world_id}/members/{target_user_id}`**: Remove um jogador do mundo (Mestre remove jogador, ou Jogador remove a si mesmo).
- **`POST /api/v1/worlds/{world_id}/rotate-invite`**: Gera um novo `invite_code` invalidando o link antigo (Apenas Mestre).
- **`GET /api/v1/users/search?q={query}`**: Busca rápida por username ou e-mail de usuários cadastrados para o autocomplete de convites diretos.

---

## 3. Detalhamento das Alterações - Frontend (Vue 3 / TypeScript / Pinia)

### 3.1. Expansão do Pinia Store (`frontend/src/stores/worlds.ts`)

Adicionar gerenciamento do código de convite, lista de membros e ações:

```typescript
export interface WorldMemberDetail {
  id: string
  user_id: string
  username: string
  email: string
  role: 'MESTRE' | 'JOGADOR'
  joined_at?: string
}

export interface WorldInviteInfo {
  invite_code: string
  world_id: string
  world_name: string
  world_description: string | null
  owner_username: string
  members_count: number
}

// Métodos a adicionar na store:
// - fetchMembers(worldId: string)
// - fetchInviteInfo(code: string)
// - joinWorld(code: string)
// - rotateInviteCode(worldId: string)
// - addMemberDirect(worldId: string, emailOrUsername: string)
// - updateMemberRole(worldId: string, userId: string, role: 'MESTRE' | 'JOGADOR')
// - removeMember(worldId: string, userId: string)
```

### 3.2. Nova Tela: Página de Convite (`frontend/src/views/JoinWorldView.vue`)

Rota dedicada `/join/:code` acessível por link compartilhado:

- **Se não estiver logado:** Redireciona para `/login` salvando o redirecionamento de volta para `/join/:code` pós-login.
- **Se logado:**
  - Carrega as informações públicas do mundo via `fetchInviteInfo(code)`.
  - Exibe um card estilizado em tema dark com acento dourado:
    - Ícone de brasão/brasão do mundo.
    - Título do Mundo e Descrição.
    - Nome do Mestre Criador e quantidade atual de membros.
  - Botão principal destacado: **"Aceitar Convite & Entrar no Mundo"**.
  - Após aceitar, redireciona automaticamente para `/dashboard` com o mundo selecionado como ativo.

### 3.3. Componente `MembersModal.vue` (`frontend/src/components/worlds/MembersModal.vue`)

Modal gerenciador de equipe acessível pelo Header ou Dashboard (quando o usuário é Mestre):

* **Aba 1 — Link de Convite Rápido:**
  - Exibe o link completo `https://.../join/k9X2mQ8pL1` em um campo somente-leitura.
  - Botão **"Copiar Link"** com feedback visual (`"Copiado!"`).
  - Botão **"Gerar Novo Link (Rotacionar)"** com alerta de confirmação.
* **Aba 2 — Membros Atuais:**
  - Tabela/Lista de todos os participantes do mundo.
  - Exibe avatar de iniciais, username, e-mail e badge da role (`MESTRE` em dourado, `JOGADOR` em prata).
  - Select para alterar a role do participante entre `MESTRE` e `JOGADOR`.
  - Botão de exclusão `🗑️ Expulsar` (com confirmação).
* **Aba 3 — Convite Direto por E-mail / Username:**
  - Campo de busca com autocomplete trazendo usuários cadastrados no sistema.
  - Botão **"Adicionar como Jogador"**.

### 3.4. Atualização das Views Existentes

1. **`DashboardView.vue`**:
   - Adicionar botão **"Entrar com Código de Convite"** ao lado do botão "Criar Novo Mundo".
   - Abrir um modal simples para o usuário colar a chave de convite e se juntar instantaneamente.
   - Adicionar botão `"Gerenciar Membros"` nos cards de mundos onde o usuário é Mestre.
2. **`AppHeader.vue`**:
   - Adicionar ícone de **"Membros & Convites"** (👥) na barra superior ao lado do seletor de mundo ativo.
3. **`router/index.ts`**:
   - Adicionar a rota `/join/:code` apontando para `JoinWorldView.vue`.

---

## 4. Plano de Ação Passo a Passo para a IDE (Execution Checklist)

Siga rigorosamente a ordem de execução abaixo:

1. **[Backend]** Atualizar `World` em `backend/app/db/models/world.py` adicionando a função `generate_invite_code` e o campo `invite_code`.
2. **[Backend]** Criar arquivo de migração Alembic para adicionar a coluna `invite_code` na tabela `worlds`.
3. **[Backend]** Atualizar schemas em `backend/app/schemas/world.py` com `WorldInviteInfoOut`, `MemberDetailOut` e `DirectMemberAddInput`.
4. **[Backend]** Implementar funções de gerenciamento de convites e membros em `backend/app/services/world_service.py`.
5. **[Backend]** Adicionar rota de busca de usuários `GET /users/search` em `backend/app/api/routes/users.py`.
6. **[Backend]** Adicionar rotas de convites, aceite e membros em `backend/app/api/routes/worlds.py`.
7. **[Frontend]** Atualizar a store Pinia `frontend/src/stores/worlds.ts` incluindo métodos de convite e membros.
8. **[Frontend]** Criar o componente `frontend/src/components/worlds/MembersModal.vue`.
9. **[Frontend]** Criar a view `frontend/src/views/JoinWorldView.vue` e registrar a rota `/join/:code` em `frontend/src/router/index.ts`.
10. **[Frontend]** Atualizar `frontend/src/views/DashboardView.vue` e `frontend/src/components/ui/AppHeader.vue` integrando a ação de convite por código e gestão de membros.

---

## 5. Critérios de Aceite e Testes de Verificação

### Testes de Backend:
- [ ] Ao criar um mundo, o campo `invite_code` é gerado automaticamente com 10 caracteres únicos.
- [ ] Chamada `POST /api/v1/worlds/join/{invite_code}` adiciona o usuário autenticado à tabela `world_members` como `JOGADOR`.
- [ ] Tentar entrar novamente em um mundo onde já é membro retorna HTTP 400.
- [ ] Apenas o `MESTRE` do mundo consegue alterar a role de membros ou rotacionar o `invite_code`.
- [ ] O criador do mundo (`owner_id`) não pode ser removido do mundo.

### Testes de Frontend:
- [ ] Acessar `/join/:code` exibe o card de confirmação com nome do mundo e botão de aceite.
- [ ] Clicar em "Copiar Link" no modal de membros copia a URL `/join/:invite_code` para a área de transferência.
- [ ] O Mestre consegue alterar o papel de um jogador para `MESTRE` ou remover um membro.
- [ ] No Dashboard, a opção "Entrar com Código" permite colar um código de convite e entrar no mundo com sucesso.