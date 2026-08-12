# ETAPA 1: Sistema de Wikilinks, Menções Cross-Entity (`[[Artigo]]`) e Backlinks

## 🎯 Objetivo
Implementar a infraestrutura de interconexão de conteúdo no BridgeKeeperDen no estilo Obsidian/WorldAnvil. Qualquer campo de texto e descrição no sistema (seções de artigos, itens de inventário, marcadores de mapa, missões) deve reconhecer a sintaxe `[[Nome do Artigo]]` ou `[[Nome do Artigo|Texto de Exibição]]`, transformando-a em links interativos e alimentando o sistema de **Backlinks**.

---

## 🏗️ 1. Alterações no Backend (FastAPI + SQLAlchemy)

### 1.1. Schemas e Endpoints de Resolução (`backend/app/schemas/article.py` & `backend/app/api/routes/articles.py`)
- **Endpoint de Resolução Rápida**: Criar endpoint `GET /api/v1/worlds/{world_id}/articles/resolve`
  - **Query param**: `title: str`
  - **Retorno**: `{ "exists": bool, "article_id": Optional[UUID], "title": str, "slug": str, "type": str }`
- **Endpoint de Autocomplete de Menções**: Criar endpoint `GET /api/v1/worlds/{world_id}/articles/search-mentions?query=...`
  - Retorna uma lista de até 10 itens `{ id, title, type }` ordenada por relevância para popular o menu suspenso do editor frontend.

### 1.2. Mapeamento e Extração de Links (`backend/app/services/article_service.py`)
- Criar a função utilitária `extract_wikilinks(content: str) -> list[str]` utilizando Expressões Regulares para identificar todas as referências `[[...]]`.
- Ao criar ou atualizar um artigo, processar o conteúdo das seções para catalogar as menções realizadas.
- **Endpoint de Backlinks**: Criar endpoint `GET /api/v1/worlds/{world_id}/articles/{article_id}/backlinks`
  - Retorna a lista de artigos que mencionam o `article_id` atual no seu corpo de texto.

---

## 🎨 2. Alterações no Frontend (Vue 3 + TypeScript + Pinia)

### 2.1. Utilitário de Parsing (`frontend/src/utils/wikilinkParser.ts`)
- Criar a função `parseWikilinks(text: string, worldId: string): string`
- **Sintaxes suportadas**:
  - `[[Cidade de Thanatos]]` -> Substitui por uma tag de link estilizada `<span class="wikilink" data-target="Cidade de Thanatos">Cidade de Thanatos</span>`.
  - `[[Cidade de Thanatos|capital]]` -> Substitui mantendo o rótulo personalizado `<span class="wikilink" data-target="Cidade de Thanatos">capital</span>`.
- Caso o artigo mencionado não exista no mundo atual, atribuir a classe `.wikilink-broken` para feedback visual (link não encontrado).

### 2.2. Componente Leitor Reativo (`frontend/src/components/ui/WikilinkText.vue`)
- Componente para renderização de texto contendo Wikilinks.
- Implementar delegação de eventos de clique nos elementos `.wikilink`:
  - **Clique simples**: Exibe um modal/drawer de pré-visualização rápida do artigo de destino sem trocar de página.
  - **Double click / Ctrl + Click**: Redireciona a rota via `router.push` para a visualização completa do artigo no Codex.

### 2.3. Autocomplete no Editor (`frontend/src/components/ui/WikilinkInput.vue`)
- Adicionar escuta no evento de digitação em `textarea` / editores de texto para capturar a digitação de `[[`.
- Exibir popover de sugestão buscando os artigos em tempo real através da rota `search-mentions`.
- Selecionar uma opção insere automaticamente `[[Título do Artigo]]` e fecha o menu.

### 2.4. Integração na View do Codex (`frontend/src/views/CodexView.vue`)
- Substituir as áreas de renderização de texto cru das seções do artigo pelo componente `<WikilinkText />`.
- Adicionar uma aba lateral ou rodapé contendo o painel **"Conexões e Backlinks"**, consumindo o endpoint de backlinks do backend.

---

## 🧪 3. Critérios de Aceite e Verificação
1. **Parser de Texto**: Escrever `[[Thanatos]]` em qualquer seção de um artigo renderiza um link verde/destacado.
2. **Apelidos Personalizados**: Escrever `[[Thanatos|Capital Antiga]]` renderiza visualmente apenas o texto "Capital Antiga", direcionando para o artigo "Thanatos".
3. **Tratamento de Links Quebrados**: Digitar `[[Local Inexistente]]` exibe o link com visual pontilhado/avermelhado.
4. **Interação**: Clicar em um link interno dentro da página do Codex abre a caixa de preview ou navega para o artigo correto.
5. **Painel de Backlinks**: O artigo de destino lista corretamente os artigos que o mencionaram.