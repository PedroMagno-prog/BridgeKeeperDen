# 📝 Prompt de Implementação - Etapa 11: Frontend - Editor Markdown Live Preview, Autosave e Inline Links

## 🎯 Objetivo
Substituir o modelo antigo de edição por seções fragmentadas por um **Editor Markdown Unificado** no estilo Obsidian, contendo:
1. Suporte a *Live Preview* em tempo real com renderização visual de cabeçalhos (`# `, `## `, `### `).
2. Autocompletar inteligente para *inline links* ao digitar `[[Wikilinks]]`.
3. Salvamento automático (*autosave*) transparente com *debounce* e indicador de status visual.

---

## 🗂️ Arquivos Envolvidos
- `frontend/src/composables/useAutoSave.ts` *(Modificado/Expandido)*
- `frontend/src/components/codex/ArticleEditor.vue` *(Novo)*
- `frontend/src/components/codex/WikilinkAutocomplete.vue` *(Novo)*
- `frontend/src/components/ui/SaveStatusBadge.vue` *(Novo)*
- `frontend/src/views/CodexView.vue` *(Modificado)*

---

## 📋 Tarefas Detalhadas por Arquivo

### 1. Refatorar o Composable de Autosave (`frontend/src/composables/useAutoSave.ts`)
Implemente/Aprimore o composable de salvamento reativo:
* **Entradas**:
  * `saveFn`: Função assíncrona que executa a chamada HTTP (ex: `articlesStore.patchContent`).
  * `delay`: Tempo de *debounce* em milissegundos (padrão: `800ms`).
* **Estados Exportados**:
  * `status`: Enum ou União de strings (`'idle' | 'modified' | 'saving' | 'saved' | 'error'`).
  * `lastSavedAt`: `Date | null`.
* **Comportamento**:
  * Ao chamar `triggerChange(newContent: string)`, define `status = 'modified'` e reinicia o timer do `debounce`.
  * Quando o timer expira, altera `status = 'saving'` e executa `saveFn(newContent)`.
  * Em caso de sucesso: define `status = 'saved'`, atualiza `lastSavedAt` e volta para `'idle'` após alguns segundos.
  * Em caso de erro: define `status = 'error'`.

### 2. Criar Indicador Visual de Status (`frontend/src/components/ui/SaveStatusBadge.vue`)
Criar um selo discreto para exibir o estado atual do salvamento no cabeçalho da página do artigo:
* **Estados Visuais**:
  * `'modified'`: Ícone de ponto amarelo/laranja e texto *"Modificado..."*.
  * `'saving'`: Spinner discreto e texto *"Salvando..."*.
  * `'saved'`: Ícone de check verde e texto *"Salvo"* (fade out suave).
  * `'error'`: Ícone de aviso vermelho e botão *"Tentar novamente"*.

### 3. Criar Componente de Autocompletar (`frontend/src/components/codex/WikilinkAutocomplete.vue`)
Componente popover flutuante para busca de artigos ao digitar `[[`:
* **Props**:
  * `searchQuery: string`: O texto digitado pelo usuário após as chaves `[[`.
  * `position: { top: number, left: number }`: Coordenadas do cursor no editor para posicionar o popover.
* **Comportamento**:
  * Filtra os artigos cadastrados na store `articlesStore` pelo `searchQuery`.
  * Suporta navegação por setas do teclado (`ArrowUp`, `ArrowDown`) e seleção via `Enter` ou `Tab`.
  * Emite o evento `@select(articleTitle: string)` ao escolher um artigo.

### 4. Criar o Editor Markdown Unificado (`frontend/src/components/codex/ArticleEditor.vue`)
Construir o componente principal do editor:
* **Props & Emits**:
  * `modelValue: string` (Conteúdo Markdown do artigo).
  * `articleId: number`.
* **Recursos do Editor**:
  * Suporte a edição em tempo real com estilos dinâmicos para `# `, `## `, `### ` mantendo a sintaxe Markdown pura no texto subjacente.
  * **Intercepção do Gatilho `[[`**:
    * Ao detectar a digitação de `[[`, captura a posição do cursor e ativa o `<WikilinkAutocomplete />`.
    * Ao selecionar um artigo no autocompletar, substitui a busca pelo formato `[[Título do Artigo]]` e fecha o popover.
  * Integre o composable `useAutoSave` apontando para o endpoint `PATCH /articles/{articleId}/content`.

### 5. Integrar o Novo Editor na View do Codex (`frontend/src/views/CodexView.vue`)
* Substitua os componentes legados baseados em seções pelo novo `<ArticleEditor />`.
* Adicione o `<SaveStatusBadge />` no topo do painel do artigo ao lado do título.
* Garanta que, ao alternar entre artigos na árvore de pastas, o editor carregue o novo `content` instantaneamente e reinicie o estado do `useAutoSave`.

---

## 🧪 Requisitos de Teste e Validação
1. **Validação de Live Preview**: Digitar `# Título 1`, `## Título 2` e `### Título 3` no editor e confirmar que a formatação visual e a hierarquia são aplicadas imediatamente.
2. **Validação de Wikilinks**: Digitar `[[` no meio do texto, verificar se o popover abre próximo ao cursor, navegar com as setas e selecionar um artigo. O resultado no texto deve ser `[[Nome do Artigo Selecionado]]`.
3. **Validação do Autosave**: Digitar um parágrafo e parar de digitar. Verificar se o badge altera de *"Modificado..."* para *"Salvando..."* e depois para *"Salvo"*, confirmando no Inspect Network a requisição `PATCH /articles/{id}/content`.
4. **Resiliência a Troca Rápida de Artigos**: Alternar rapidamente entre dois artigos na árvore e garantir que alterações pendentes do artigo anterior sejam salvas antes de carregar o novo.

---
Instruções finais para a IA: Mantenha o design responsivo e fluído. Priorize a atalhos de teclado produtivos (UX focada em escrita rápida sem distrações).