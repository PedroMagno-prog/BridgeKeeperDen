# 📝 Prompt de Implementação - Etapa 7: Modelagem de Dados e Unificação do Artigo (Database & Models)

## 🎯 Objetivo
Refatorar a camada de banco de dados do projeto **BridgeKeeperDen** para:
1. Suportar a criação e organização hierárquica de pastas de artigos (`ArticleFolder`).
2. Unificar a estrutura de texto dos artigos (`Article`) em um único arquivo de conteúdo Markdown contínuo (`content`), eliminando completamente o conceito de seções fragmentadas (`ArticleSection`).

---

## 🗂️ Arquivos Envolvidos
- `backend/app/db/models/article_folder.py` *(Novo)*
- `backend/app/db/models/article.py` *(Modificado)*
- `backend/app/db/models/article_section.py` *(Removido)*
- `backend/app/db/models/__init__.py` *(Modificado)*
- `backend/app/db/migrations/versions/xxxx_etapa7_folders_and_article_content.py` *(Novo - Migration)*

---

## 📋 Tarefas Detalhadas por Arquivo

### 1. Criar o modelo de pastas (`backend/app/db/models/article_folder.py`)
Crie a classe `ArticleFolder` herdando de `Base` (SQLAlchemy).
* **Campos da Tabela `article_folders`**:
  * `id`: `Integer`, Primary Key, autoincrement.
  * `world_id`: `Integer`, ForeignKey para `worlds.id` (ondelete="CASCADE"), `nullable=False`, `index=True`.
  * `parent_id`: `Integer`, ForeignKey para `article_folders.id` (ondelete="CASCADE"), `nullable=True`, `index=True`.
  * `name`: `String(255)`, `nullable=False`.
  * `created_at`: `DateTime(timezone=True)`, `server_default=func.now()`.
  * `updated_at`: `DateTime(timezone=True)`, `onupdate=func.now()`.
* **Relacionamentos**:
  * `world`: relacionamento com `World`.
  * `parent`: relacionamento self-referencial com `ArticleFolder` (`remote_side=[id]`, `back_populates="children"`).
  * `children`: relacionamento self-referencial com `ArticleFolder` (`back_populates="parent"`, `cascade="all, delete-orphan"`).
  * `articles`: relacionamento com `Article` (`back_populates="folder"`).

### 2. Modificar o modelo de artigo (`backend/app/db/models/article.py`)
Atualize o modelo `Article`:
* **Novas Colunas**:
  * `folder_id`: `Integer`, ForeignKey para `article_folders.id` (ondelete="SET NULL"), `nullable=True`, `index=True`.
  * `content`: `Text`, `nullable=False`, `default=""`.
* **Novos Relacionamentos**:
  * `folder`: relacionamento com `ArticleFolder` (`back_populates="articles"`).
* **Remoção de Relacionamento**:
  * Remover o relacionamento `sections` que apontava para `ArticleSection`.

### 3. Remover o modelo de seções (`backend/app/db/models/article_section.py`)
* Delete ou descontinue o arquivo `article_section.py`.

### 4. Atualizar exportações (`backend/app/db/models/__init__.py`)
* Importe `ArticleFolder`.
* Remova a importação e exportação de `ArticleSection`.

### 5. Migration do Alembic (`backend/app/db/migrations/versions/`)
Gere ou crie uma nova migration do Alembic para aplicar as mudanças:

* **Função `upgrade()`**:
  1. Criar a tabela `article_folders`.
  2. Adicionar as colunas `folder_id` e `content` na tabela `articles`.
  3. **Migração de Dados das Seções para `content`**:
     * Consultar todas as seções existentes na tabela `article_sections` agrupadas por `article_id` e ordenadas por ordem de criação/posicionamento.
     * Para cada artigo, concatenar suas seções no seguinte formato Markdown:
       ```markdown
       # [Título da Seção]
       
       [Conteúdo da Seção]
       ```
     * Caso o título da seção seja nulo ou vazio, incluir apenas o conteúdo da seção.
     * Executar o `UPDATE articles SET content = :concatenated_content WHERE id = :article_id`.
  4. Remover a FK e a tabela `article_sections`.

* **Função `downgrade()`**:
  1. Recriar a tabela `article_sections`.
  2. Remover as colunas `folder_id` e `content` da tabela `articles`.
  3. Remover a tabela `article_folders`.

---

## 🧪 Requisitos de Teste e Validação
1. Executar `alembic upgrade head` no ambiente de desenvolvimento/testes e verificar se todas as migrações ocorrem sem erros.
2. Confirmar se a tabela `article_folders` foi criada corretamente com suporte a subpastas (`parent_id`).
3. Verificar se o campo `content` de `articles` foi preenchido com a concatenação em formato Markdown das antigas seções.
4. Executar os testes existentes do Pytest (`pytest backend/tests/`) para garantir que nenhuma regressão de sintaxe ocorra nos modelos importados.

---
Instruções finais para a IA: Siga estritamente as convenções de código do projeto (FastAPI, SQLAlchemy v2, Alembic). Gere o código limpo, tipado e devidamente comentado.