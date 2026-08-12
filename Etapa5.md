Aqui está o documento da **ETAPA 5** formatado rigorosamente como um prompt de instrução técnica para o Agente de IA da sua IDE.

---

# ETAPA 5: Importação em Lote de Cofre Obsidian (.zip) e Mapeamento de Lore

> **Instrução para o Agente de IA da IDE:**
> Você deve implementar estritamente os requisitos e alterações descritos nesta etapa. Mantenha os padrões do projeto (FastAPI + SQLAlchemy Assíncrono no backend; Vue 3 + TypeScript + Pinia + CSS Variables no frontend). Garanta que a importação de notas seja executada em uma única transação assíncrona de banco de dados para evitar inserções parciais. Reutilize o parser de Wikilinks `[[Artigo]]` e a estrutura de visibilidade de Névoa de Guerra existentes.

---

## 1. Visão Geral e Objetivos da Etapa 5

O objetivo desta etapa é permitir que o Mestre (**GM**) importe um cofre do Obsidian (*Obsidian Vault*) comprimido em formato `.zip` diretamente para o Codex de um Mundo existente no **BridgeKeeperPortal**.

O sistema descompactará o arquivo em memória, processará as notas em Markdown (`.md`), converterá cada arquivo em um `Article` do Codex, dividirá seções por cabeçalhos (`#`, `##`, `###`) e preservará a sintaxe de `[[Wikilinks]]` para integração imediata com o **Graph View** e o sistema de **Backlinks**.

### Funcionalidades Entregues nesta Etapa:

1. **Upload e Descompactação em Memória (`.zip`):** Endpoint para leitura de buffers de cofres do Obsidian sem necessidade de persistência temporária no disco do servidor.
2. **Parser de Markdown e Frontmatter (YAML):** Extração de títulos, cabeçalhos de seção e leitura de metadados em bloco YAML (caso existam na nota).
3. **Definição Estrita de Valores Padrão (Defaults):** Aplicação de regras de RPG e Névoa de Guerra para notas brutas importadas.
4. **Mapeamento Opcional de Pastas em Tags:** Opção no frontend para converter subpastas do cofre em tags do artigo.
5. **Modal de Importação (`ObsidianImportModal.vue`):** Interface de upload drag-and-drop com explicação clara dos valores padrão aplicados.

---

## 2. Mapeamento de Entidades e Valores Padrão (Defaults)

Notas brutas do Obsidian não possuem conceitos de RPG configurados. O parser deve aplicar estritamente a seguinte tabela de mapeamento e padrões:

| Conceito no Obsidian | Entidade no BridgeKeeper | Valor Padrão (Default) | Regra / Comportamento |
| --- | --- | --- | --- |
| **Arquivo `.md**` | `Article.title` | Nome do arquivo sem `.md` | Define o título do artigo no Codex. |
| **Conteúdo / Headers** | `ArticleSection` | Seção única *"Visão Geral"* | Cabeçalhos `#` e `##` dividem a nota em seções independentes ordenadas por `order_index`. |
| **Névoa de Guerra** | `Article.visibility` | **`NULA` (Obscurecimento Total)** | Todo o cofre importado pelo Mestre fica invisível aos Jogadores até ser liberado manualmente. |
| **Data *In-Game*** | `Article.in_game_date` | **`None` / `null**` | Fica vazio por padrão (salvo se presente no YAML Frontmatter como `in_game_date`). |
| **Tags de Categorização** | `ArticleTag` | **Nenhuma (`[]`)** | Sem tags por padrão (salvo se ativada a opção de conversão de pastas ou presente no YAML Frontmatter como `tags`). |
| **Links `[[Artigo]]**` | `Wikilinks` | Preservados ilesos | A sintaxe é mantida no texto para integração com o Graph View e o painel de Backlinks. |

---

## 3. Detalhamento das Alterações - Backend (FastAPI / SQLAlchemy)

### 3.1. Dependências do Projeto (`backend/requirements.txt`)

Adicionar a biblioteca de parse de frontmatter YAML:

```text
python-frontmatter==1.1.0

```

### 3.2. Serviço de Importação (`backend/app/services/obsidian_import_service.py`)

Criar o serviço responsável por descompactar o ZIP, realizar o parse de Markdown/YAML e persistir em lote:

```python
import io
import re
import zipfile
import uuid
import frontmatter
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.article import Article
from app.db.models.article_section import ArticleSection
from app.db.models.article_tag import ArticleTag
from app.db.models.enums import VisibilityType

async def processar_zip_obsidian(
    db: AsyncSession,
    world_id: uuid.UUID,
    user_id: uuid.UUID,
    zip_bytes: bytes,
    use_folders_as_tags: bool = False,
) -> dict:
    """
    Processa todos os arquivos .md de um ZIP do Obsidian e os persiste em lote.
    """
    imported_count = 0
    skipped_count = 0

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for file_info in z.infolist():
            # Ignora pastas do sistema, arquivos ocultos do macOS/Obsidian e extensões que não sejam .md
            if file_info.is_dir() or file_info.filename.startswith("__MACOSX") or not file_info.filename.endswith(".md"):
                continue

            content_bytes = z.read(file_info.filename)
            try:
                content_str = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content_str = content_bytes.decode("latin-1", errors="ignore")

            # Parse de Frontmatter (YAML)
            post = frontmatter.loads(content_str)
            raw_text = post.content
            metadata = post.metadata

            # Nome do arquivo como Título do Artigo
            path_parts = [p for p in file_info.filename.split("/") if p]
            file_name = path_parts[-1]
            article_title = file_name[:-3]  # Remove extensão .md

            # 1. Definir Valores Padrão (Defaults)
            visibility = VisibilityType.NULA  # Obscurecimento Total por padrão
            in_game_date = metadata.get("in_game_date", None)

            # 2. Processar Tags (Default = Nenhuma)
            tags_set = set()
            if "tags" in metadata:
                front_tags = metadata["tags"]
                if isinstance(front_tags, list):
                    tags_set.update(str(t).strip() for t in front_tags)
                elif isinstance(front_tags, str):
                    tags_set.update(t.strip() for t in front_tags.split(","))

            # Opção de usar nome de subpastas como tags
            if use_folders_as_tags and len(path_parts) > 1:
                for folder in path_parts[:-1]:
                    if not folder.startswith("."):
                        tags_set.add(folder.strip())

            # 3. Dividir conteúdo em Seções por Headers (#, ##)
            sections_data = parse_markdown_sections(raw_text)

            # 4. Criar Entidade do Artigo
            article = Article(
                world_id=world_id,
                title=article_title,
                visibility=visibility,
                in_game_date=in_game_date,
                created_by=user_id,
            )
            db.add(article)
            await db.flush()

            # Adicionar Seções
            for sec in sections_data:
                db.add(ArticleSection(
                    article_id=article.id,
                    title=sec["title"],
                    content=sec["content"],
                    order_index=sec["order_index"],
                ))

            # Adicionar Tags
            for tag_name in tags_set:
                if tag_name:
                    db.add(ArticleTag(
                        article_id=article.id,
                        name=tag_name if tag_name.startswith(".") else f".{tag_name}"
                    ))

            imported_count += 1

    await db.flush()
    return {
        "imported_count": imported_count,
        "skipped_count": skipped_count,
    }


def parse_markdown_sections(text: str) -> list[dict]:
    """Divide o corpo do Markdown em seções baseadas em títulos # / ##."""
    header_regex = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    matches = list(header_regex.finditer(text))

    if not matches:
        return [{"title": "Visão Geral", "content": text.strip(), "order_index": 0}]

    sections = []
    if matches[0].start() > 0:
        pre_content = text[:matches[0].start()].strip()
        if pre_content:
            sections.append({"title": "Visão Geral", "content": pre_content, "order_index": 0})

    for idx, match in enumerate(matches):
        sec_title = match.group(2).strip()
        start_pos = match.end()
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sec_content = text[start_pos:end_pos].strip()

        sections.append({
            "title": sec_title,
            "content": sec_content,
            "order_index": len(sections),
        })

    return sections

```

### 3.3. Schemas de Pydantic (`backend/app/schemas/article.py`)

```python
class ObsidianImportResultOut(BaseModel):
    imported_count: int
    skipped_count: int
    message: str

```

### 3.4. Rota da API REST (`backend/app/api/routes/articles.py`)

```python
@router.post(
    "/import/obsidian",
    response_model=ObsidianImportResultOut,
    status_code=status.HTTP_201_CREATED,
    summary="Importa um cofre Obsidian em formato .zip",
)
async def importar_cofre_obsidian(
    file: UploadFile = File(...),
    use_folders_as_tags: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    ctx: WorldContext = Depends(get_world_ctx),
):
    """
    Importa um ZIP de um cofre do Obsidian.
    Apenas Mestre pode executar.
    Aplica Obscurecimento Total (Visão Nula) por padrão para proteger dados não revelados.
    """
    if not ctx.is_mestre:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o Mestre do mundo pode importar cofres de notas."
        )

    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo enviado deve ser do tipo .zip."
        )

    zip_bytes = await file.read()
    res = await obsidian_import_service.processar_zip_obsidian(
        db,
        ctx.world_id,
        ctx.user.id,
        zip_bytes,
        use_folders_as_tags=use_folders_as_tags,
    )
    await db.commit()

    return ObsidianImportResultOut(
        imported_count=res["imported_count"],
        skipped_count=res["skipped_count"],
        message=f"{res['imported_count']} notas importadas com sucesso com Obscurecimento Total (Visão Nula).",
    )

```

---

## 4. Detalhamento das Alterações - Frontend (Vue 3 / TypeScript / Pinia)

### 4.1. Atualização do Store Pinia (`frontend/src/stores/articles.ts`)

Adicionar a ação de upload multipart para importação de cofres:

```typescript
async function importObsidianVault(file: File, useFoldersAsTags: boolean) {
  const worldId = wid()
  if (!worldId) throw new Error('Nenhum mundo selecionado.')

  const formData = new FormData()
  formData.append('file', file)
  formData.append('use_folders_as_tags', String(useFoldersAsTags))

  const { data } = await api.post(`/worlds/${worldId}/articles/import/obsidian`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  await fetchArticles()
  return data
}

```

### 4.2. Componente `ObsidianImportModal.vue` (`frontend/src/components/codex/ObsidianImportModal.vue`)

Modal com zona de soltura de arquivo (.zip) e avisos sobre valores padrão:

* **Zone de Drop/Upload:** Suporte a seleção ou drag-and-drop de arquivo `.zip`.
* **Painel de Configurações Padrão:**
* 🛡️ **Névoa da Guerra:** `Obscurecimento Total (Visão Nula)`
* 📅 **Data In-Game:** `Nenhuma`
* 🏷️ **Tags:** `Nenhuma`


* **Checkbox Opcional:** `[ ] Mapear pastas e subpastas do cofre em Tags dos artigos.`
* **Feedback Visual:** Spinner durante o processamento de envio e descompactação.

### 4.3. Integração na View do Codex (`frontend/src/views/CodexView.vue`)

* Adicionar o botão **"📥 Importar Cofre Obsidian"** ao lado do botão *"Novo Artigo"* (visível apenas quando o usuário for `MESTRE`).
* Abrir o modal `ObsidianImportModal.vue` ao clicar.

---

## 5. Plano de Ação Passo a Passo para a IDE (Execution Checklist)

Siga rigorosamente a ordem de execução abaixo:

1. **[Backend]** Adicionar `python-frontmatter==1.1.0` no arquivo `backend/requirements.txt`.
2. **[Backend]** Criar o schema `ObsidianImportResultOut` em `backend/app/schemas/article.py`.
3. **[Backend]** Criar o serviço `backend/app/services/obsidian_import_service.py` com o parse de ZIP em memória, diviçoes por headers e regras de defaults.
4. **[Backend]** Criar a rota `POST /worlds/{world_id}/articles/import/obsidian` em `backend/app/api/routes/articles.py`.
5. **[Frontend]** Adicionar a ação `importObsidianVault` na store Pinia `frontend/src/stores/articles.ts`.
6. **[Frontend]** Criar o componente modal `frontend/src/components/codex/ObsidianImportModal.vue`.
7. **[Frontend]** Atualizar `frontend/src/views/CodexView.vue` incluindo o botão de acionamento do modal para o Mestre.

---

## 6. Critérios de Aceite e Testes de Verificação

### Testes de Backend:

* [ ] Enviar um arquivo `.zip` contendo notas Markdown para `POST /worlds/{world_id}/articles/import/obsidian` gera as entradas correspondentes nas tabelas `articles` e `article_sections`.
* [ ] Todas as notas importadas possuem `visibility = 'NULA'`, `in_game_date = None` e `tags = []` por padrão.
* [ ] Notas com cabeçalhos `#` e `##` são divididas corretamente em múltiplas `article_sections`.
* [ ] O processo ignora subpastas ocultas (ex: `.obsidian`, `__MACOSX`) e foca apenas em arquivos `.md`.

### Testes de Frontend:

* [ ] O botão "Importar Cofre Obsidian" está visível no Codex apenas para o Mestre do Mundo.
* [ ] Fazer o envio de um arquivo `.zip` válido fecha o modal, exibe o toast/mensagem de sucesso e atualiza a listagem de artigos.
* [ ] As notas importadas renderizam corretamente os `[[Wikilinks]]` internos no Codex e aparecem na teia de conexões do **Graph View**.