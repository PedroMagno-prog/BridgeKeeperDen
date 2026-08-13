# 📝 Prompt de Implementação - Etapa 8: Backend - Schemas, Serviços e Rotas da API

## 🎯 Objetivo
Atualizar a camada de APIs (FastAPI) e regras de negócio no backend para:
1. Oferecer CRUD completo e montagem de árvore hierárquica para Pastas (`ArticleFolder`).
2. Adequar os Schemas, Serviços e Rotas de Artigos para manipularem o campo `content` único (Markdown) e a referência `folder_id`.
3. Criar um endpoint otimizado de atualização parcial (`PATCH /articles/{id}/content`) com baixa latência para suportar o *autosave*.

---

## 🗂️ Arquivos Envolvidos
- `backend/app/schemas/folder.py` *(Novo)*
- `backend/app/schemas/article.py` *(Modificado)*
- `backend/app/services/folder_service.py` *(Novo)*
- `backend/app/services/article_service.py` *(Modificado)*
- `backend/app/api/routes/folders.py` *(Novo)*
- `backend/app/api/routes/articles.py` *(Modificado)*
- `backend/app/api/router.py` *(Modificado)*

---

## 📋 Tarefas Detalhadas por Arquivo

### 1. Criar Schemas de Pastas (`backend/app/schemas/folder.py`)
Crie os schemas Pydantic para `ArticleFolder`:
* `FolderCreate`: `name: str`, `parent_id: Optional[int] = None`.
* `FolderUpdate`: `name: Optional[str] = None`, `parent_id: Optional[int] = None`.
* `FolderResponse`: `id: int`, `world_id: int`, `name: str`, `parent_id: Optional[int]`, `created_at: datetime`. Configurado com `from_attributes = True`.
* `FolderTreeResponse`: Schema recursivo representando o nó da pasta na árvore:
  * `id: int`
  * `name: str`
  * `parent_id: Optional[int]`
  * `children: List['FolderTreeResponse'] = []`
  * `articles: List[ArticleSummarySchema] = []` *(Lista simplificada dos artigos na pasta)*

### 2. Refatorar Schemas de Artigo (`backend/app/schemas/article.py`)
* Remova todas as referências aos schemas de `ArticleSection` (`ArticleSectionCreate`, `ArticleSectionResponse`, etc.).
* Atualize `ArticleCreate`:
  * `title: str`
  * `content: Optional[str] = ""`
  * `folder_id: Optional[int] = None`
  * `tags: Optional[List[str]] = []`
* Atualize `ArticleUpdate`:
  * `title: Optional[str] = None`
  * `content: Optional[str] = None`
  * `folder_id: Optional[int] = None`
  * `tags: Optional[List[str]] = None`
* Criar `ArticleContentUpdate`:
  * `content: str` *(Usado especificamente para a rota de autosave)*
* Atualize `ArticleResponse`:
  * Incluir `content: str` e `folder_id: Optional[int]`.
  * Garantir que não tente carregar o atributo removido `sections`.

### 3. Criar Serviço de Pastas (`backend/app/services/folder_service.py`)
Implemente a classe `FolderService` (injetando a sessão `AsyncSession` ou `Session` do SQLAlchemy):
* `create_folder(world_id: int, data: FolderCreate) -> ArticleFolder`: Cria uma pasta garantindo que o `parent_id` (se fornecido) pertença ao mesmo `world_id`.
* `update_folder(folder_id: int, data: FolderUpdate) -> ArticleFolder`: Atualiza nome ou move a pasta para outro `parent_id` (evitando referência circular).
* `delete_folder(folder_id: int) -> None`: Deleta a pasta (e por exclusão em cascata ou tratamento, ajusta subpastas/artigos).
* `get_world_folder_tree(world_id: int) -> List[FolderTreeResponse]`:
  * Busca todas as pastas do mundo e todos os artigos do mundo.
  * Monta a árvore hierárquica em memória (pastas raiz com `parent_id = None` contendo suas filhas e artigos correspondentes).
  * Retorna também os artigos que estão na raiz (`folder_id = None`).

### 4. Atualizar Serviço de Artigos (`backend/app/services/article_service.py`)
* Atualizar métodos `create_article` e `update_article` para salvar e manipular `folder_id` e `content`.
* Criar método `update_article_content(article_id: int, content: str) -> Article`:
  * Atualiza unicamente o campo `content` e a data `updated_at`.
  * Retorna o artigo atualizado com execução otimizada de query.
* Remover todas as manipulações e queries relacionadas a `ArticleSection`.

### 5. Criar Rotas de Pastas (`backend/app/api/routes/folders.py`)
Implemente as rotas sob o prefixo `/worlds/{world_id}/folders`:
* `GET /`: Retorna a árvore hierárquica completa do mundo (`FolderTreeResponse`).
* `POST /`: Cria uma nova pasta.
* `PUT /{folder_id}`: Atualiza/move uma pasta.
* `DELETE /{folder_id}`: Exclui uma pasta.

### 6. Atualizar Rotas de Artigos (`backend/app/api/routes/articles.py`)
* Ajustar endpoints existentes (`POST`, `PUT`, `GET`) para usarem os novos schemas unificados sem `sections`.
* Adicionar rota de autosave acelerada:
  * `PATCH /articles/{article_id}/content`
  * **Payload**: `ArticleContentUpdate` (`{"content": "..."}`)
  * **Resposta**: Status `200 OK` confirmando o salvamento.

### 7. Registrar Rotas (`backend/app/api/router.py`)
* Incluir a nova router `folders.router` com a tag `"folders"`.

---

## 🧪 Requisitos de Teste e Validação
1. **Testar Árvore de Pastas**: Criar uma pasta raiz, uma subpasta e mover um artigo para a subpasta. Chamar `GET /worlds/{world_id}/folders` e verificar se a estrutura em árvore é retornada corretamente.
2. **Testar Rota de Content Patch (Autosave)**: Enviar uma requisição `PATCH /articles/{id}/content` com uma string Markdown e verificar no banco se o campo `content` foi alterado rapidamente.
3. **Testar Exclusão de Pasta**: Garantir que, ao excluir uma pasta, os artigos contidos nela tenham o `folder_id` definido como `NULL` (ou sejam removidos conforme a regra de cascata desejada), sem quebrar a integridade do banco.
4. **Rodar Pytest**: Executar a suíte de testes do backend (`pytest backend/tests/`) garantindo que todas as rotas de artigos passem sem erros de modelo ou de chave de seções ausente.

---
Instruções finais para a IA: Mantenha o padrão de dependências de autenticação (`deps/auth.py`) e permissão de mundo (`deps/world_access.py`) já utilizados no projeto.