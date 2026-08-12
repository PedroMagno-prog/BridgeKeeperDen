# ETAPA 2: Módulo de Mapas Interativos 2D, Marcadores (Pins), Sub-Mapas e Integracao com Codex

> **Instrução para o Agente de IA da IDE:**
> Você deve implementar estritamente os requisitos e alterações descritos nesta etapa. Mantenha os padrões do projeto (FastAPI + SQLAlchemy Assíncrono no backend; Vue 3 + TypeScript + Pinia + CSS Variables no frontend). Reutilize os componentes criados na Etapa 1 (ex: `WikilinkRenderer.vue` para preview de artigos nos popups de marcadores).

---

## 1. Visão Geral e Objetivos da Etapa 2

O objetivo desta etapa é transformar o módulo de cartografia do **BridgeKeeperDen** em um sistema completo de mapas interativos navegáveis, permitindo ao Mestre e aos Jogadores explorarem a geografia do mundo e conectarem locais diretamente à *lore* do Codex.

### Funcionalidades Entregues nesta Etapa:
1. **Gestão Completa de N Mapas por Mundo:** Suporte a criação, edição, deleção e upload de imagens de fundo de alta resolução para mapas.
2. **Canvas Interativo (Zoom, Pan e Drag-and-Drop de Pins):** Navegação fluida com zoom in/out (roda do mouse/botões), pan (arraste de câmera) e re-posicionamento interativo de marcadores via drag-and-drop para o Mestre.
3. **Marcadores Polimórficos e Popups de Preview:** Marcadores (`MapPin`) associados a **Artigos do Codex** ou **Sub-Mapas**. Ao clicar no pino, exibe um Popover flutuante com preview do artigo (com renderização de Wikilinks) e ação de navegação direta.
4. **Navegação Hierárquica em Sub-Mapas (Breadcrumbs):** Suporte a navegação aninhada (ex: *Continente -> Reino -> Cidade -> Masmorra*) com trilha de navegação (Breadcrumbs) para fácil retorno.
5. **Névoa de Guerra (Fog of War) nos Marcadores e Camadas:**
   - **Visão Total:** Marcador visível, interativo e com preview completo.
   - **Visão Parcial:** Marcador exibe o ícone de interrogação `?`, nome do local e mensagem "Conteúdo não descoberto" (bloqueado para clique/leitura).
   - **Visão Nula:** Oculto para Jogadores. Visível para o Mestre com opacidade reduzida e indicador de oculto.

---

## 2. Detalhamento das Alterações - Backend (FastAPI / SQLAlchemy)

### 2.1. Expansão dos Schemas e Endpoints de Mapas (`backend/app/schemas/map.py`)

Garantir que os schemas contemplem os dados do artigo/sub-mapa vinculado para exibição rápida no popup:

```python
class MapPinArticleSummary(BaseModel):
    id: uuid.UUID
    title: str
    visibility: VisibilityType
    tags: list[str] = []
    first_section_preview: str | None = None

class MapPinOut(BaseModel):
    id: uuid.UUID
    title: str
    x_position: float
    y_position: float
    icon: str
    color: str
    visibility: VisibilityType
    layer_id: uuid.UUID | None = None
    target_article_id: uuid.UUID | None = None
    target_map_id: uuid.UUID | None = None
    target_article: MapPinArticleSummary | None = None
    target_map_title: str | None = None
    is_locked: bool = False
```

### 2.2. Endpoints de Edição e Deleção de Mapa (`backend/app/api/routes/maps.py`)

Adicionar endpoints para gerenciar o ciclo de vida dos mapas:
* **`PUT /worlds/{world_id}/maps/{map_id}`**: Atualiza título e URL da imagem do mapa (Apenas Mestre).
* **`DELETE /worlds/{world_id}/maps/{map_id}`**: Remove o mapa e seus pins/camadas em cascata (Apenas Mestre).
* **`DELETE /worlds/{world_id}/maps/{map_id}/pins/{pin_id}`**: Deleta um pino do mapa (Apenas Mestre).
* **`DELETE /worlds/{world_id}/maps/{map_id}/layers/{layer_id}`**: Deleta uma camada do mapa (Apenas Mestre).

### 2.3. Lógica de Atualização de Posição de Marcadores (`backend/app/services/map_service.py`)

Implementar método em `map_service.py` para atualização rápida das coordenadas relativas `(x_position, y_position)` no evento de drag-and-drop do pino no frontend:

```python
async def atualizar_posicao_pin(
    db: AsyncSession,
    pin_id: uuid.UUID,
    map_id: uuid.UUID,
    x_position: Decimal,
    y_position: Decimal,
) -> MapPin | None:
    pin = await buscar_pin(db, pin_id, map_id)
    if not pin:
        return None
    pin.x_position = x_position
    pin.y_position = y_position
    await db.flush()
    return pin
```

### 2.4. Atualização da Sanitização de Fog of War (`backend/app/services/fog_of_war.py`)

No método `sanitize_pin`:
* Quando o pino for `TOTAL` e possuir `target_article_id`, carregar com segurança o resumo da primeira seção do artigo sem expor segredos.
* Quando o pino for `PARCIAL` para Jogador, zerar `target_article_id` e `target_map_id`, forçando `is_locked = True` e ícone `question-icon`.

---

## 3. Detalhamento das Alterações - Frontend (Vue 3 / TypeScript / Pinia)

### 3.1. Expansão do Pinia Store (`frontend/src/stores/maps.ts`)

Adicionar gerenciamento de pilha de navegação (Breadcrumbs) e novas ações:

```typescript
export interface MapBreadcrumb {
  id: string
  title: string
}

// Dentro do useMapsStore:
const breadcrumbs = ref<MapBreadcrumb[]>([])

function pushBreadcrumb(mapItem: MapBreadcrumb) {
  const index = breadcrumbs.value.findIndex(b => b.id === mapItem.id)
  if (index !== -1) {
    breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
  } else {
    breadcrumbs.value.push(mapItem)
  }
}

function clearBreadcrumbs() {
  breadcrumbs.value = []
}

async function updatePinPosition(mapId: string, pinId: string, x: number, y: number) {
  // Chamada PATCH/PUT rápida para atualizar coordenadas
}

async function deleteMap(mapId: string) { ... }
async function deletePin(mapId: string, pinId: string) { ... }
```

### 3.2. Componente `MapCanvas.vue` (`frontend/src/components/maps/MapCanvas.vue`)
Isolar a renderização e física de interatividade do mapa:

* **Props:** `mapDetail: MapDetail`, `isMestre: boolean`
* **Funcionalidades Internas:**
  - **Zoom suave:** Roda do mouse (wheel) centralizado na coordenada do cursor + botões `+` / `-`.
  - **Pan (Arraste de Câmera):** Clique com o botão esquerdo em área vazia e arraste.
  - **Drag-and-Drop de Marcadores (Modo Mestre):**
    - Quando o Mestre segura Shift ou ativa "Modo Mover Pinos", permite arrastar qualquer pino no canvas.
    - Ao soltar o pino, calcula a nova porcentagem relativa `x%` e `y%` baseada nas dimensões da imagem e dispara `updatePinPosition`.
  - **Click em Marcadores:** Seleciona o pino ativo e abre o Popover flutuante.

### 3.3. Componente `PinPopover.vue` (`frontend/src/components/maps/PinPopover.vue`)
Card flutuante posicionado adjacente ao marcador selecionado no canvas:

* **Exibição:**
  - **Título do Pino** + Badge de Visibilidade.
  - **Se vinculado a um Artigo:** Exibe preview da 1ª seção do artigo (processado por `<WikilinkRenderer :text="previewText" />`).
  - **Se vinculado a um Sub-Mapa:** Exibe badge "Sub-Mapa" e botão destacado **"Explorar Sub-Mapa →"**.
  - **Se Visão Parcial:** Exibe mensagem *"Local conhecido, mas detalhes não descobertos"*.
* **Ações:**
  - Botão **"Abrir Artigo no Codex"**: Navega para `/codex?id=...`.
  - Botão **"Ir para Sub-Mapa"**: Dispara alteração do mapa atual para o `target_map_id` e adiciona o mapa anterior ao Breadcrumb.
  - Botões de Mestre: **"Editar Pino"** e **"Excluir Pino"**.

### 3.4. Componente `PinModal.vue` (`frontend/src/components/maps/PinModal.vue`)
Formulário modal para o Mestre criar ou editar um Marcador:

* **Campos:**
  - **Título do Local** (obrigatório).
  - **Ícone**: Seletor visual de ícones em vetor (Cidade, Castelo, Masmorra, Ruína, Caverna, Monstro, Ponto de Interesse, Taverna).
  - **Cor de Destaque**: Seletor de cores hexadecimal.
  - **Visibilidade**: Dropdown (`TOTAL`, `PARCIAL`, `NULA`).
  - **Camada (Layer)**: Seleção opcional da camada a qual o pino pertence.
  - **Vínculo Polimórfico**:
    - Seleção entre *"Vincular a Artigo"* ou *"Vincular a Sub-Mapa"*.
    - Autocomplete com os artigos existentes no mundo ou dropdown de mapas disponíveis.

### 3.5. Componente `MapModal.vue` (`frontend/src/components/maps/MapModal.vue`)
Formulário modal para o Mestre criar ou editar um Mapa do Mundo:

* **Campos:**
  - **Título do Mapa** (ex: *Continente de Valoria*, *Planalto Central*, *Masmorra de Thanatos*).
  - **URL da Imagem / Upload**: Link direto para a imagem do mapa ou arquivo enviado.

### 3.6. Atualização do `MapsView.vue` (`frontend/src/views/MapsView.vue`)

Integrar a barra de ferramentas superior com Breadcrumbs, ações e o novo Canvas:

* **Barra de Navegação Superior (Breadcrumb Bar):**
  - Exibe a trilha de mapas explorados: `Mundus > Continente do Sul > Cidade de Thanatos`.
  - Permite clicar em qualquer nível anterior para voltar instantaneamente.
* **Barra de Ferramentas de Camadas (Layers Drawer):**
  - Painel retrátil na direita para alternar visibilidade de camadas (ex: *"Cidades"*, *"Fronteiras"*, *"Locais Perigosos"*).
* **Modo Mestre:**
  - Botões para "+ Novo Mapa", "Editar Mapa", "Deletar Mapa", e toggle para "Modo Arraste de Pinos".

---

## 4. Plano de Ação Passo a Passo para a IDE (Execution Checklist)

Siga rigorosamente a ordem de implementação abaixo:

1. **[Backend]** Atualizar os Schemas `MapPinOut` e `MapPinArticleSummary` em `backend/app/schemas/map.py`.
2. **[Backend]** Implementar a função `atualizar_posicao_pin` e métodos de exclusão em `backend/app/services/map_service.py`.
3. **[Backend]** Atualizar as rotas `PUT`, `DELETE` de mapas e pins em `backend/app/api/routes/maps.py`.
4. **[Backend]** Garantir que `sanitize_pin` em `backend/app/services/fog_of_war.py` inclua o resumo do artigo vinculado para marcadores `TOTAL`.
5. **[Frontend]** Atualizar a store Pinia `frontend/src/stores/maps.ts` adicionando breadcrumbs e métodos de atualização de posição/deleção.
6. **[Frontend]** Criar o componente `frontend/src/components/maps/PinPopover.vue`.
7. **[Frontend]** Criar o componente `frontend/src/components/maps/PinModal.vue`.
8. **[Frontend]** Criar o componente `frontend/src/components/maps/MapModal.vue`.
9. **[Frontend]** Refatorar/Criar `frontend/src/components/maps/MapCanvas.vue` com suporte a zoom, pan, drag-and-drop de pins e popover.
10. **[Frontend]** Atualizar `frontend/src/views/MapsView.vue` unificando a barra de Breadcrumbs, o canvas e o gerenciamento de mapas e sub-mapas.

---

## 5. Critérios de Aceite e Testes de Verificação

### Testes de Backend:
- [ ] Requisição `GET /worlds/{world_id}/maps/{map_id}` retorna lista de pins com o resumo do artigo vinculado (`target_article`).
- [ ] Mudar as coordenadas de um pino via `PUT /worlds/{world_id}/maps/{map_id}/pins/{pin_id}` persiste a posição no banco.
- [ ] Jogador tentando acessar um pino `PARCIAL` recebe `is_locked = True` e `target_article_id = null`.

### Testes de Frontend:
- [ ] É possível criar múltiplos mapas por mundo e alternar entre eles.
- [ ] Clicar num pino vinculado a um artigo abre o popover exibindo o resumo e o link direcionando para o Codex.
- [ ] Clicar num pino vinculado a um sub-mapa carrega o novo mapa e adiciona o mapa anterior ao Breadcrumb de navegação.
- [ ] Mestre pode arrastar um pino no canvas para ajustar sua posição x/y.
- [ ] Alternar as camadas no painel lateral esconde/exibe instantaneamente os marcadores pertencentes àquelas camadas.