# 📝 Prompt de Implementação - Etapa 6: Suporte Global a Menções, Grafo de Conexões e Revisão de CSS

## 🎯 Objetivo
Finalizar a evolução do Codex e do sistema:
1. Atualizar o parser e extrator global de `[[Wikilinks]]` para que menções em todo o app (Manuscritos, Mapas, Quests, etc.) apontem corretamente para os novos artigos e pastas do Codex.
2. Refatorar o `GraphService` no backend e o `GraphView.vue` no frontend para gerar o mapa visual de conexões extraindo links do campo `content`.
3. **Auditar e Reforçar o CSS/Tailwind** de todos os novos componentes introduzidos nas etapas anteriores, assegurando consistência estética (Tema Dark/RPG), responsividade e ausência de bugs visuais.

---

## 🗂️ Arquivos Envolvidos
- `backend/app/services/graph_service.py` *(Modificado)*
- `frontend/src/utils/wikilinkParser.ts` *(Modificado)*
- `frontend/src/components/ui/WikilinkText.vue` *(Modificado)*
- `frontend/src/views/GraphView.vue` *(Modificado)*
- `frontend/src/assets/css/main.css` *(Modificado - refinamento de estilos globais)*
- Componentes criados nas etapas 4 e 5 (`FolderTree.vue`, `ArticleEditor.vue`, `WikilinkAutocomplete.vue`, `SaveStatusBadge.vue`) *(Revisão de CSS)*

---

## 📋 Tarefas Detalhadas por Arquivo

### 1. Refatorar Extração do Grafo no Backend (`backend/app/services/graph_service.py`)
* **Remoção de Código Legado**: Elimine qualquer consulta que busque dados em `article_sections`.
* **Nova Lógica de Parsing de Conexões**:
  * Buscar todos os artigos ativos pertencentes ao `world_id`.
  * Utilizar regex para rastrear todas as ocorrências de `[[Nome do Artigo]]` dentro de `article.content`.
  * Mapear os títulos citados para os IDs dos artigos de destino correspondentes.
  * Construir a estrutura de nós (`nodes`) e arestas (`edges`):
    * `nodes`: `[{ id: article.id, label: article.title, folder_id: article.folder_id }]`
    * `edges`: `[{ source: article_origem_id, target: article_destino_id }]`

### 2. Atualizar Parser de Wikilinks no Frontend (`frontend/src/utils/wikilinkParser.ts` e `WikilinkText.vue`)
* Garantir que o parser converta a sintaxe `[[Título do Artigo]]` em links interativos em qualquer lugar do aplicativo.
* Ao clicar em um Wikilink fora do Codex (ex: dentro do Jornal de Quests ou Pin do Mapa):
  * Redirecionar o usuário para o Codex.
  * Selecionar o artigo correspondente na store (`selectedArticleId`).
  * Expandir automaticamente as pastas ancestrais na árvore para manter o artigo visível e destacado no menu lateral.

### 3. Refatorar Visualização do Grafo (`frontend/src/views/GraphView.vue`)
* Atualizar a integração com a biblioteca de renderização do grafo.
* Permitir filtrar os nós do grafo por pasta (`folder_id`).
* Adicionar funcionalidade de duplo clique em um nó do grafo para navegar diretamente para o artigo no Codex.

---

## 🎨 Auditoria e Reforço de CSS / Estilização (Checklist Obrigatório)

Realize uma revisão visual minuciosa nos componentes criados e ajustados:

### A. Barra Lateral e Árvore de Pastas (`FolderTree.vue`, `FolderItem.vue`)
* **Scrolbar & Layout**: Configurar `overflow-y-auto` dedicado para o painel de pastas, impedindo que a barra lateral role junto com o conteúdo do editor.
* **Truncamento de Texto**: Adicionar as classes `truncate w-full block` no título de artigos e pastas para prevenir que nomes longos quebrem a estrutura do menu lateral.
* **Hierarquia Visual**:
  * Garantir destaque para o item selecionado (`bg-primary-900/40 text-amber-400 font-medium` ou equivalente do tema).
  * Hover suave (`hover:bg-slate-800/60 transition-colors`).
  * Alinhamento e espaçamento consistente dos ícones de pasta e chevrons.

### B. Editor e Barra de Ferramentas (`ArticleEditor.vue`, `SaveStatusBadge.vue`)
* **Tipografia e Cabeçalhos**:
  * `# ` (h1): Maior, negrito, cor de destaque (ex: `text-2xl font-bold text-amber-100 mb-3`).
  * `## ` (h2): Intermediário (ex: `text-xl font-semibold text-amber-200/90 mb-2`).
  * `### ` (h3): Subcabeçalho (ex: `text-lg font-medium text-slate-200 mb-2`).
* **Selo de Salvamento (`SaveStatusBadge.vue`)**:
  * Garantir animações suaves (`fade-in`, `fade-out`) sem causa do efeito "jank"/salto na interface.
* **Menu de Autocompletar (`WikilinkAutocomplete.vue`)**:
  * Estilizar como um popover flutuante escuro com elevação (`shadow-2xl border border-slate-700 bg-slate-900 rounded-lg z-50`).
  * Destacar a opção focada pelo teclado (`bg-amber-500/20 text-amber-300`).

### C. Responsividade e Adaptação
* Verificar o comportamento do layout split (Árvore + Editor) em resoluções menores, garantindo botão de colapso da barra lateral em dispositivos móveis/telas pequenas.

---

## 🧪 Requisitos de Teste e Validação
1. **Validação do Grafo**: Criar dois artigos ("Reino de Eldoria" e "Capital Valen"), incluir `[[Capital Valen]]` dentro do conteúdo de "Reino de Eldoria", acessar a tela de Grafo e verificar se a aresta conectando os dois nós é exibida.
2. **Navegação via Menção**: Em um card de Quest, incluir `[[Reino de Eldoria]]`. Clicar na menção e verificar se o sistema abre o Codex, expande a pasta correta e carrega o artigo.
3. **Inspeção Estética/CSS**:
   * Verificar se não há barras de rolagem duplas ou indesejadas na interface.
   * Testar nomes extensos de pastas/artigos e validar que o layout permanece intacto.
   * Confirmar se as cores e contrastes seguem a identidade escura/RPG do projeto.

---
Instruções finais para a IA: Garanta um acabamento visual polido e impecável. Todo o CSS deve ser limpo, performático e integrado ao ecossistema Tailwind CSS do projeto.