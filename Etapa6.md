# ETAPA 6: Refinamentos de Cartografia, Controle Granular de Acesso por Jogador e Anexos de Imagem nas Seções

> **Instrução para o Agente de IA da IDE:**
> Você deve implementar estritamente os requisitos, alterações e refatorações descritos nesta etapa. Mantenha a consistência com a arquitetura existente (FastAPI + SQLAlchemy Assíncrono + Alembic no backend; Vue 3 + TypeScript + Pinia + TailwindCSS/CSS Variables no frontend). Garanta que nenhuma funcionalidade anterior seja quebrada e que todas as migrações de banco de dados sejam tratadas adequadamente.

---

## 1. Visão Geral e Objetivos da Etapa 6

Esta etapa foca no refinamento de usabilidade e na expansão do sistema de permissões e mídias do **BridgeKeeperPortal**:

1. **Aprimoramento da Cartografia 2D (`MapsView.vue` / `MapCanvas.vue`)**:
* Ampliar a faixa de zoom do canvas (permitindo zoom out até `10%` / `0.1x` e zoom in até `500%` / `5.0x`).
* Adicionar um controle deslizante (*slider*) de opacidade para a imagem de fundo do mapa, facilitando o contraste e a localização visual de marcadores (*pins*) em mapas muito coloridos.


2. **Reformulação do Controle de Visibilidade e Acesso Granular por Jogador (Codex e Inventários)**:
* Atualizar a Enum de Visibilidade para conter 4 níveis: `NULA`, `PARCIAL`, `CONTROLADO` (novo) e `TOTAL`.
* Permitir a atribuição de permissões individuais por jogador para cada recurso (**Artigo**, **Inventário** e **Grupo de Inventário**).
* O Mestre mantém acesso total e irrestrito a todo o sistema.
* Recursos criados por Jogadores virão por padrão com visibilidade `TOTAL` para seu criador.


3. **Anexo de Imagens em Seções de Artigo (`ArticleSection`)**:
* Permitir o upload/anexo de uma imagem complementar em cada seção de um artigo.
* Implementar otimização/compressão automática no backend usando **Pillow**: imagens que excederem **5MB** serão redimensionadas e convertidas para formato otimizado WebP.



---

## 2. Detalhamento das Alterações - Backend (FastAPI / SQLAlchemy)

### 2.1. Atualização do Enum de Visibilidade (`backend/app/db/models/enums.py`)

Atualizar o enum `VisibilityType`:

```python
class VisibilityType(str, enum.Enum):
    NULA = "NULA"           # Invisível para o jogador
    PARCIAL = "PARCIAL"       # Jogador só vê o título/nome (bloqueado)
    CONTROLADO = "CONTROLADO" # Jogador pode LER o conteúdo completo, mas NÃO PODE editar/excluir (Somente Leitura)
    TOTAL = "TOTAL"         # Jogador tem acesso completo ao CRUD (Ler, Editar, Excluir)

```

> **Migração Alembic (`backend/app/db/migrations/versions/d4e5f6a7b8c9_update_visibility_type.py`)**:
> Adicionar a instrução SQL para atualizar a enum no PostgreSQL:
> `ALTER TYPE visibility_type ADD VALUE IF NOT EXISTS 'CONTROLADO';`

---

### 2.2. Modelagem da Matriz de Permissões Granulares por Usuário

Para permitir que cada jogador tenha uma permissão individual em um artigo, inventário ou grupo, criar tabelas de permissões específicas:

#### A. Permissões de Artigos (`backend/app/db/models/article_user_permission.py`)

```python
class ArticleUserPermission(Base):
    __tablename__ = "article_user_permissions"
    __table_args__ = (
        UniqueConstraint("article_id", "user_id", name="uq_article_user_perm"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    visibility: Mapped[VisibilityType] = mapped_column(Enum(VisibilityType, native_enum=True), nullable=False)

```

#### B. Permissões de Inventários (`backend/app/db/models/inventory_user_permission.py`)

```python
class InventoryUserPermission(Base):
    __tablename__ = "inventory_user_permissions"
    __table_args__ = (
        UniqueConstraint("inventory_id", "user_id", name="uq_inventory_user_perm"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventories.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    visibility: Mapped[VisibilityType] = mapped_column(Enum(VisibilityType, native_enum=True), nullable=False)

```

#### C. Permissões de Grupos de Inventário (`backend/app/db/models/inventory_group_user_permission.py`)

```python
class InventoryGroupUserPermission(Base):
    __tablename__ = "inventory_group_user_permissions"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user_perm"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inventory_groups.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    visibility: Mapped[VisibilityType] = mapped_column(Enum(VisibilityType, native_enum=True), nullable=False)

```

---

### 2.3. Lógica de Resolução de Permissões no Fog of War (`backend/app/services/fog_of_war.py`)

Refatorar as funções de sanitização de visibilidade para considerar a seguinte ordem de precedência:

1. **Se o usuário for `MESTRE**`: Permissão implícita é `TOTAL` (pode ler, editar, excluir tudo).
2. **Se o recurso foi criado pelo próprio Jogador**:
* `created_by == user_id`: Permissão padrão é `TOTAL` (por RN-02).


3. **Se existir um registro em `_user_permissions` para o `user_id` no recurso**:
* Usa a visibilidade atribuída especificamente para aquele usuário (`NULA`, `PARCIAL`, `CONTROLADO` ou `TOTAL`).


4. **Caso contrário**:
* Usa a visibilidade padrão (`visibility`) configurada no recurso pai.



#### Regras de Ação no Frontend / Backend segundo a Visibilidade Resolvida:

* `NULA`: Recurso omitido nas consultas da API do jogador.
* `PARCIAL`: Retorna apenas ID e Título (`is_locked: True`). Leitura do conteúdo e edição bloqueadas.
* `CONTROLADO`: Retorna o recurso com conteúdo completo (`can_edit: False`, `can_delete: False`). Edição/exclusão bloqueadas no backend (retorna HTTP 403 se tentar `PUT` ou `DELETE`).
* `TOTAL`: Retorna o recurso completo (`can_edit: True`, `can_delete: True`).

---

### 2.4. Anexo e Compressão de Imagens em Seções (`ArticleSection`)

1. **Alteração na Tabela `article_sections` (`backend/app/db/models/article_section.py`)**:
* Adicionar coluna `image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)`


2. **Instalação do Pillow (`backend/requirements.txt`)**:
```text
Pillow==10.4.0

```


3. **Serviço de Processamento de Imagens (`backend/app/services/image_service.py`)**:
```python
import io
from PIL import Image

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def otimizar_imagem_secao(image_bytes: bytes, filename: str) -> tuple[bytes, str]:
    """
    Verifica o tamanho da imagem. Se for maior que 5MB, redimensiona
    e converte para WebP comprimida antes do armazenamento.
    """
    if len(image_bytes) <= MAX_FILE_SIZE:
        return image_bytes, filename

    image = Image.open(io.BytesIO(image_bytes))

    # Redimensiona mantendo a proporção (largura máxima de 1920px)
    max_size = (1920, 1920)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    output = io.BytesIO()
    image.save(output, format="WEBP", quality=80, optimize=True)

    new_filename = f"{filename.rsplit('.', 1)[0]}_optimized.webp"
    return output.getvalue(), new_filename

```


4. **Endpoint de Upload de Imagem de Seção (`backend/app/api/routes/articles.py`)**:
* `POST /api/v1/worlds/{world_id}/articles/{article_id}/sections/{section_id}/image`
* Recebe `UploadFile`, executa `otimizar_imagem_secao`, armazena na pasta de mídia ou storage estático e atualiza o `image_url` da seção.



---

## 3. Detalhamento das Alterações - Frontend (Vue 3 / TypeScript / Pinia)

### 3.1. Ajustes no Módulo de Mapas (`frontend/src/components/maps/MapCanvas.vue` e `MapsView.vue`)

1. **Ampliação do Zoom**:
* Alterar limites de zoom no `MapCanvas.vue`:
```typescript
const minZoom = 0.1  // 10%
const maxZoom = 5.0  // 500%

```


* Atualizar botões de controle e o manipulador de roda do mouse (`handleWheel`).


2. **Controle de Opacidade do Mapa de Fundo**:
* Adicionar estado reativo `bgOpacity` (faixa de `0.1` a `1.0`, padrão `1.0`).
* Adicionar slider de controle de opacidade na barra de ferramentas superior do `MapsView.vue`.
* Aplicar binding de estilo no elemento da imagem do mapa:
```html
<img :src="mapDetail.image_url" :style="{ opacity: bgOpacity }" class="map-image" />

```





---

### 3.2. Gerenciamento Granular de Permissões por Jogador (UI)

1. **Exibição dos Novos Badges de Visibilidade (`VisibilityBadge.vue`)**:
* Adicionar suporte ao status `CONTROLADO`:
* Ícone: `👁️` ou `🛡️`
* Cor: Destaque Azul/Ciano (`#3B82F6`)
* Label: *"Controlado (Somente Leitura)"*




2. **Modal/Painel de Permissões por Jogador (`ResourcePermissionsModal.vue`)**:
* Criar componente genérico para o Mestre configurar a matriz de acessos de um recurso (Artigo, Inventário ou Grupo).
* Lista todos os Jogadores do Mundo atalhando seletores individuais:
* `Jogador 1`: `[ TOTAL ▾ ]`
* `Jogador 2`: `[ CONTROLADO ▾ ]`
* `Jogador 3`: `[ PARCIAL ▾ ]`
* `Jogador 4`: `[ NULA ▾ ]`




3. **Validação de Ações no Codex e Inventário**:
* Ocultar botões de edição (`✏️`) e exclusão (`🗑️`) para Jogadores com permissão `CONTROLADO`.
* Se um jogador com nível `CONTROLADO` tentar acessar a rota de edição, bloquear a ação no frontend e exibir aviso: *"Sua permissão neste recurso é de Somente Leitura"*.



---

### 3.3. Anexo e Exibição de Imagens em Seções do Codex (`CodexView.vue`)

1. **Exibição da Imagem da Seção**:
* No modo de leitura da seção, renderizar `<img v-if="section.image_url" :src="section.image_url" class="section-img" />` abaixo ou ao lado do título da seção.


2. **Upload Inline no Modo de Edição**:
* No modal/formulário de edição de seções, adicionar campo de upload de imagem `<input type="file" accept="image/*" @change="handleSectionImageUpload" />`.
* Exibir indicador de envio e preview da imagem anexada.



---

## 4. Plano de Ação Passo a Passo para a IDE (Execution Checklist)

Siga rigorosamente a ordem de execução abaixo:

1. **[Backend]** Atualizar o Enum `VisibilityType` em `backend/app/db/models/enums.py`.
2. **[Backend]** Criar os modelos SQLAlchemy `ArticleUserPermission`, `InventoryUserPermission` e `InventoryGroupUserPermission`.
3. **[Backend]** Atualizar `ArticleSection` adicionando a coluna `image_url`.
4. **[Backend]** Gerar e executar migração Alembic para inclusão do novo valor de Enum e das novas tabelas/colunas.
5. **[Backend]** Adicionar `Pillow==10.4.0` ao `requirements.txt` e criar o serviço `image_service.py` com a lógica de otimização/compressão de imagem para <5MB.
6. **[Backend]** Refatorar `fog_of_war.py` para resolver permissões com base no usuário logado e nas tabelas de permissão individual.
7. **[Backend]** Criar/atualizar endpoints REST para atribuição de permissões por recurso e upload de imagem de seção.
8. **[Frontend]** Atualizar limites de zoom (0.1x a 5.0x) e adicionar slider de opacidade no `MapCanvas.vue` e `MapsView.vue`.
9. **[Frontend]** Atualizar `VisibilityBadge.vue` para suportar o estado `CONTROLADO`.
10. **[Frontend]** Criar o componente `ResourcePermissionsModal.vue` para configuração de permissões por jogador.
11. **[Frontend]** Atualizar `CodexView.vue` e `InventarioView.vue` aplicando bloqueios de edição para o nível `CONTROLADO` e suporte a anexo de imagens nas seções do Codex.

---

## 5. Critérios de Aceite e Testes de Verificação

### Testes de Backend:

* [ ] O enum `VisibilityType` aceita o valor `'CONTROLADO'`.
* [ ] Um Jogador com permissão `'CONTROLADO'` em um Artigo consegue realizar `GET /articles/{id}` e ler o conteúdo completo, mas recebe HTTP `403 Forbidden` ao tentar `PUT` ou `DELETE`.
* [ ] Se o Jogador A tem permissão `'CONTROLADO'` e o Jogador B tem permissão `'NULA'` no mesmo artigo, o Jogador B recebe HTTP `404 Not Found` ao consultar o artigo.
* [ ] Upload de imagem maior que 5MB para uma seção de artigo é redimensionado/convertido automaticamente para WebP otimizado pelo Pillow.

### Testes de Frontend:

* [ ] O canvas de mapa permite navegar desde zoom out em `10%` até zoom in em `500%`.
* [ ] Ajustar o slider de opacidade reduz suavemente a visibilidade da imagem de fundo do mapa, destacando os marcadores.
* [ ] O Mestre consegue abrir o modal de permissões de um artigo e definir acessos diferentes para cada jogador do mundo.
* [ ] Jogadores visualizando um artigo com permissão `CONTROLADO` conseguem ler o texto e ver as imagens da seção, mas não têm acesso aos botões de editar ou excluir.