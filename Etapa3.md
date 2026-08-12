# ETAPA 3: Módulo Quest Journal (Missões), Categorização, Objetivos e Visualizador em Grafo de Conexões (Graph View)

> **Instrução para o Agente de IA da IDE:**
> Você deve implementar estritamente os requisitos e alterações descritos nesta etapa. Mantenha os padrões do projeto (FastAPI + SQLAlchemy Assíncrono no backend; Vue 3 + TypeScript + Pinia + CSS Variables no frontend). Integre e reutilize os componentes desenvolvidos nas Etapas 1 e 2 (Wikilinks `[[Artigo]]`, Autocomplete, Fog of War e Links para Mapas/Locais).

---

## 1. Visão Geral e Objetivos da Etapa 3

O objetivo desta etapa é entregar o **Quest Journal (Diário de Missões)** e a **Visualização em Grafo de Conexões (Graph View)**, consolidando o BridgeKeeperDen em uma plataforma viva de gestão de campanhas e worldbuilding.

### Funcionalidades Entregues nesta Etapa:
1. **Quest Journal Completo:** Registro, acompanhamento e gerenciamento de missões com ciclo de vida (Status: *Não Iniciada*, *Em Progresso*, *Concluída*, *Falhada*, *Suspensa*).
2. **Categorização & Tags:** Classificação de missões em categorias de RPG (ex: *Main Quest*, *Posto Avançado*, *Caçada de Monstro*, *Busca por Artefato*, *Missão Secundária*, *Facção*).
3. **Checklist Dinâmico de Objetivos:** Cada missão possui etapas/objetivos ordenáveis com checkbox de conclusão reativa.
4. **Vínculo Direto com o Codex & Mapas:** Quests contêm suporte completo a Wikilinks `[[Artigo]]` no seu corpo de texto, recompensas e objetivos, podendo estar vinculadas a um Artigo Principal de Lore do Codex ou Marcador de Mapa.
5. **Fog of War Granular em Missões:** Suporte aos três níveis de visão (*TOTAL*, *PARCIAL*, *NULA*), permitindo ao Mestre manter missões secretas ou parciais até o momento certo da campanha.
6. **Visualizador em Grafo (Interactive Graph View):** Teia de conexões estilo Obsidian/WorldAnvil renderizada em Canvas/SVG interativo, mapeando as conexões entre Artigos, Quests, Locais de Mapa e Personagens em tempo real.

---

## 2. Detalhamento das Alterações - Backend (FastAPI / SQLAlchemy)

### 2.1. Modelagem de Dados de Quests (`backend/app/db/models/quest.py` e `quest_objective.py`)

Criar os modelos relacionais para o Quest Journal:

```python
# Enums
class QuestStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ON_HOLD = "ON_HOLD"

class QuestCategory(str, enum.Enum):
    MAIN_QUEST = "MAIN_QUEST"
    SIDE_QUEST = "SIDE_QUEST"
    MONSTER_HUNT = "MONSTER_HUNT"
    ARTIFACT_SEARCH = "ARTIFACT_SEARCH"
    OUTPOST = "OUTPOST"
    FACTION = "FACTION"

# Tabela `quests`
class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    article_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    category: Mapped[QuestCategory] = mapped_column(Enum(QuestCategory, native_enum=True), nullable=False, default=QuestCategory.SIDE_QUEST)
    status: Mapped[QuestStatus] = mapped_column(Enum(QuestStatus, native_enum=True), nullable=False, default=QuestStatus.NOT_STARTED)
    visibility: Mapped[VisibilityType] = mapped_column(Enum(VisibilityType, native_enum=True), nullable=False, default=VisibilityType.NULA)
    rewards: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    objectives: Mapped[list["QuestObjective"]] = relationship("QuestObjective", back_populates="quest", cascade="all, delete-orphan", lazy="selectin", order_by="QuestObjective.order_index")
    article: Mapped["Article | None"] = relationship("Article", lazy="selectin")

# Tabela `quest_objectives`
class QuestObjective(Base):
    __tablename__ = "quest_objectives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quests.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quest: Mapped["Quest"] = relationship("Quest", back_populates="objectives")
```

### 2.2. Schemas de Pydantic (`backend/app/schemas/quest.py` e `graph.py`)

```python
# Quest Schemas
class ObjectiveCreate(BaseModel):
    description: str
    is_completed: bool = False
    order_index: int = 0

class QuestCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str = ""
    category: QuestCategory = QuestCategory.SIDE_QUEST
    status: QuestStatus = QuestStatus.NOT_STARTED
    visibility: VisibilityType | None = None
    rewards: str | None = None
    article_id: uuid.UUID | None = None
    objectives: list[ObjectiveCreate] = []

class QuestOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    title: str
    description: str
    category: QuestCategory
    status: QuestStatus
    visibility: VisibilityType
    rewards: str | None
    article_id: uuid.UUID | None
    article_title: str | None = None
    objectives: list[ObjectiveOut] = []
    created_at: datetime
    is_locked: bool = False

# Graph Schemas
class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "ARTICLE", "QUEST", "MAP", "PIN"
    category: str | None = None
    visibility: VisibilityType

class GraphEdge(BaseModel):
    source: str
    target: str
    label: str | None = None

class WorldGraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
```

### 2.3. Endpoints da API REST (`backend/app/api/routes/quests.py` e `graph.py`)

- **`GET /worlds/{world_id}/quests`**: Lista missões com filtros por `status`, `category` e busca por texto, respeitando o Fog of War.
- **`POST /worlds/{world_id}/quests`**: Cria uma nova missão com objetivos em cascata (Apenas Mestre ou Jogador respeitando RN-01/RN-02).
- **`GET /worlds/{world_id}/quests/{quest_id}`**: Detalhes da missão.
- **`PUT /worlds/{world_id}/quests/{quest_id}`**: Atualiza título, descrição, status, categoria, visibilidade e objetivos.
- **`DELETE /worlds/{world_id}/quests/{quest_id}`**: Remove a missão.
- **`PATCH /worlds/{world_id}/quests/{quest_id}/objectives/{obj_id}/toggle`**: Alterna o status `is_completed` de um objetivo.
- **`GET /worlds/{world_id}/graph`**:
  - Compila em tempo real todos os nós e arestas acessíveis ao usuário no mundo.
  - Varre Wikilinks `[[...]]` em seções de artigos, manuscritos, marcadores de mapa e missões.
  - Conecta arestas direcionadas entre origem e destino.
  - Sanitiza e remove nós/arestas com visibilidade `NULA` para Jogadores.

---

## 3. Detalhamento das Alterações - Frontend (Vue 3 / TypeScript / Pinia)

### 3.1. Pinia Store de Quests (`frontend/src/stores/quests.ts`)

```typescript
export interface QuestObjective {
  id: string
  description: string
  is_completed: boolean
  order_index: number
}

export interface Quest {
  id: string
  title: string
  description: string
  category: 'MAIN_QUEST' | 'SIDE_QUEST' | 'MONSTER_HUNT' | 'ARTIFACT_SEARCH' | 'OUTPOST' | 'FACTION'
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'ON_HOLD'
  visibility: 'TOTAL' | 'PARCIAL' | 'NULA'
  rewards?: string
  article_id?: string
  article_title?: string
  objectives: QuestObjective[]
  is_locked?: boolean
}

// Actions: fetchQuests, createQuest, updateQuest, deleteQuest, toggleObjective, fetchWorldGraph
```

### 3.2. View do Quest Journal (`frontend/src/views/QuestJournalView.vue`)

Layout moderno e dinâmico permitindo alternar entre duas visões de organização:

1. **Visão Kanban (por Status):** Colunas (*Não Iniciada*, *Em Progresso*, *Concluída*, *Falhada*) com drag/click para alteração rápida de status.
2. **Visão por Categorias:** Agrupamento por *Main Quest*, *Caçadas*, *Artefatos*, etc.
3. **Filtros e Busca:** Pílulas de categorias e busca por texto em tempo real.

### 3.3. Componente `QuestCard.vue` (`frontend/src/components/quests/QuestCard.vue`)

- **Exibição do Card:**
  - Ícone vetorial da categoria (ex: Coroa para *Main Quest*, Caveira para *Monster Hunt*, Bússola para *Outpost*).
  - Título + Badge de Visibilidade + Badge de Status.
  - Barra de progresso dos objetivos `(ex: 3/5 etapas concluídas - 60%)`.
  - Preview de Wikilinks `[[...]]` no corpo da missão.

### 3.4. Componente `QuestModal.vue` (`frontend/src/components/quests/QuestModal.vue`)

Modal para criação/edição de missões:
- Formulário de dados básicos (Título, Categoria, Status, Visibilidade, Artigo do Codex vinculado).
- **Editor de Descrição e Recompensas:** Integrado com `<WikilinkTextarea>` para autocomplete em `[[`.
- **Gerenciador de Objetivos:** Lista reordenável com adição de novos itens, checkbox de conclusão e exclusão.

### 3.5. View do Grafo Interativo (`frontend/src/views/GraphView.vue`)

Visualizador de rede em tempo real estilo *Obsidian Graph View*:

- **Renderizador em Canvas HTML5 / SVG / D3.js (Force-Directed Graph):**
  - **Nós (Nodes):** Representados por círculos coloridos segundo a entidade (Dourado = Quests, Azul = Artigos, Verde = Locais de Mapa).
  - **Tamanho dos Nós:** Proporcional ao número de conexões/backlinks que a entidade possui.
  - **Arestas (Edges):** Linhas de conexão animadas/suaves unindo entidades que se mencionam via `[[Wikilinks]]`.
  - **Física de Simulação:** Repulsão de nós e atração por arestas com suporte a drag de nós, zoom (wheel) e pan.
  - **Hover & Click em Nó:** Destaca a rede de conexões direta daquele nó e abre uma gaveta (Drawer) com o preview do artigo/missão e botão para navegação rápida.
  - **Filtros de Nós:** Painel de controle para exibir/ocultar apenas Quests, apenas Artigos ou apenas Mapas.

---

## 4. Plano de Ação Passo a Passo para a IDE (Execution Checklist)

Siga rigorosamente a ordem abaixo:

1. **[Backend]** Criar as tabelas e modelos SQLAlchemy `Quest` e `QuestObjective` em `backend/app/db/models/quest.py`.
2. **[Backend]** Atualizar `backend/app/db/models/__init__.py` e gerar/rodar migração Alembic para a tabela `quests` e `quest_objectives`.
3. **[Backend]** Criar Schemas Pydantic em `backend/app/schemas/quest.py` e `backend/app/schemas/graph.py`.
4. **[Backend]** Criar o serviço `backend/app/services/quest_service.py` e o gerador de grafo `backend/app/services/graph_service.py`.
5. **[Backend]** Criar as rotas de API em `backend/app/api/routes/quests.py` e `backend/app/api/routes/graph.py`, registrando-as no `api_router`.
6. **[Frontend]** Criar a store Pinia `frontend/src/stores/quests.ts`.
7. **[Frontend]** Criar os componentes `QuestCard.vue` e `QuestModal.vue` em `frontend/src/components/quests/`.
8. **[Frontend]** Criar a view `frontend/src/views/QuestJournalView.vue` adicionando a rota no Vue Router.
9. **[Frontend]** Criar a view `frontend/src/views/GraphView.vue` com o canvas interativo em Grafo direcionado por força.
10. **[Frontend]** Adicionar atalhos para a "Linha de Missões" e "Visão em Grafo" na sidebar do sistema (`AppSidebar.vue`).

---

## 5. Critérios de Aceite e Testes de Verificação

### Testes de Backend:
- [ ] Requisição `GET /worlds/{world_id}/quests` retorna lista de missões filtradas respeitando a regra de *Fog of War*.
- [ ] Alterar o objetivo de uma missão via `PATCH /quests/{id}/objectives/{obj_id}/toggle` atualiza o estado de conclusão no banco.
- [ ] Requisição `GET /worlds/{world_id}/graph` analisa os Wikilinks das seções de artigos e descrições de quests e retorna a lista consistente de nós e arestas.

### Testes de Frontend:
- [ ] É possível criar uma missão, atribuir uma categoria (*Main Quest*, *Caçada*, etc.) e adicionar objetivos com checkboxes.
- [ ] Digitar `[[` no campo de descrição ou recompensas da missão aciona o autocomplete do Codex.
- [ ] Mudar o status de uma missão no Kanban atualiza o card e a barra de progresso.
- [ ] A tela de **Graph View** renderiza visualmente a rede de artigos e quests conectadas.
- [ ] Clicar num nó do grafo exibe o painel de detalhes e permite navegar até o artigo/missão correspondente.