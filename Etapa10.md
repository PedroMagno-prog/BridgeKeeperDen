# 📝 Prompt de Implementação - Etapa 10: Frontend - Gestão de Árvore de Pastas e Navegação do Codex

## 🎯 Objetivo
Desenvolver na interface Vue 3 / TypeScript do **BridgeKeeperDen** a estrutura de navegação hierárquica em árvore de pastas no estilo Obsidian, permitindo:
1. Visualizar, criar, renomear, mover e excluir pastas e subpastas de artigos.
2. Navegar recursivamente entre pastas e artigos na barra lateral do Codex.
3. Preservar o estado de pastas abertas/fechadas durante a navegação.

---

## 🗂️ Arquivos Envolvidos
- `frontend/src/stores/articles.ts` *(Modificado)*
- `frontend/src/api/client.ts` ou `frontend/src/api/folders.ts` *(Novo/Modificado)*
- `frontend/src/components/codex/FolderTree.vue` *(Novo)*
- `frontend/src/components/codex/FolderItem.vue` *(Novo)*
- `frontend/src/components/codex/FolderModal.vue` *(Novo - Modal de criação/edição)*
- `frontend/src/views/CodexView.vue` *(Modificado)*

---

## 📋 Tarefas Detalhadas por Arquivo

### 1. Atualizar a API de Clientes Frontend (`frontend/src/api/folders.ts`)
Criar funções de chamada HTTP via Axios/fetch para os novos endpoints de pastas:
* `getFolderTree(worldId: number)`
* `createFolder(worldId: number, data: { name: string, parent_id?: number | null })`
* `updateFolder(worldId: number, folderId: number, data: { name?: string, parent_id?: number | null })`
* `deleteFolder(worldId: number, folderId: number)`

### 2. Atualizar a Store Pinia (`frontend/src/stores/articles.ts`)
Aprimorar o estado e as ações da store de artigos:
* **Estado (`State`)**:
  * `folderTree: FolderTreeResponse[]` (Árvore de pastas e artigos).
  * `selectedArticleId: number | null`.
  * `expandedFolderIds: Set<number>` (IDs das pastas atualmente expandidas).
* **Ações (`Actions`)**:
  * `fetchFolderTree(worldId: number)`: Carrega a estrutura de árvore do backend.
  * `toggleFolderExpand(folderId: number)`: Alterna o estado de expandido/recolhido da pasta no `expandedFolderIds`.
  * `createNewFolder(name: string, parentId?: number | null)`: Chama a API e recarrega a árvore.
  * `renameFolder(folderId: number, newName: string)`: Atualiza o nome da pasta.
  * `removeFolder(folderId: number)`: Exclui a pasta e atualiza a árvore.
  * `moveArticleToFolder(articleId: number, targetFolderId: number | null)`: Move um artigo para outra pasta.

### 3. Criar Componente Recursivo de Pasta (`frontend/src/components/codex/FolderItem.vue`)
Criar o componente individual de pasta com suporte a renderização aninhada:
* **Props**:
  * `folder: FolderTreeResponse` (Dados da pasta, subpastas `children` e artigos `articles`).
  * `level: number` (Nível de profundidade para controle de indentação `padding-left`).
* **Interface & Comportamento**:
  * Cabeçalho da pasta com ícone de pasta (fechada/aberta) e chevron.
  * Clique no cabeçalho dispara `toggleFolderExpand(folder.id)`.
  * Exibição condicional de `folder.children` (recursivamente invocando `<FolderItem />` com `level + 1`) e `folder.articles` quando a pasta estiver no estado expandido.
  * Botões de ação rápida ao passar o mouse (ou menu suspenso): "Nova Subpasta", "Novo Artigo nesta Pasta", "Renomear", "Excluir".

### 4. Criar Container da Árvore de Navegação (`frontend/src/components/codex/FolderTree.vue`)
Criar o componente contêiner da barra lateral do Codex:
* **Comportamento**:
  * Exibe barra de busca rápida/filtro por nome de artigo ou pasta.
  * Botão no topo para "Nova Pasta Raiz" e "Novo Artigo Raiz".
  * Renderiza a lista de pastas raízes usando `<FolderItem />` (com `level = 0`).
  * Renderiza a lista de artigos que estão na raiz do mundo (`folder_id === null`).
  * Garante realce visual (`active`) no artigo cujo `id === selectedArticleId`.

### 5. Criar Modal de Gestão de Pastas (`frontend/src/components/codex/FolderModal.vue`)
* Modal simples para inserção ou edição do nome de uma pasta.
* Suporta criação de pastas na raiz ou como subpasta de uma pasta pai pré-selecionada.

### 6. Refatorar a View Principal do Codex (`frontend/src/views/CodexView.vue`)
* Atualizar o layout flex/grid da view:
  * **Painel Lateral Esquerdo (Sidebar)**: Incluir o `<FolderTree />` com largura fixa/redimensionável.
  * **Painel Principal (Direito)**: Exibe a visualização/edição do artigo selecionado.
* Ao clicar em qualquer artigo da árvore, carregar os dados desse artigo na área principal e atualizar o `selectedArticleId` na URL (ex: via query params ou rota `/codex/:articleId`).

---

## 🧪 Requisitos de Teste e Validação
1. **Navegação Hierárquica**: Criar Pastas A, B e a subpasta A.1. Verificar se clicar no chevron expande/recolhe a pasta mantendo os filhos visíveis apenas quando aberta.
2. **Nivelamento de Indentação**: Garantir que subpastas de nível 2 e 3 tenham recuo visual alinhado e agradável.
3. **Persistência do Estado**: Alternar entre artigos do Codex e validar se as pastas anteriormente abertas continuam expandidas.
4. **Criação e Exclusão**: Testar a criação de uma subpasta, mover um artigo para ela e excluir uma pasta vazia. Verificar se a árvore é atualizada sem necessidade de recarregar a página inteira.

---
Instruções finais para a IA: Use Vue 3 Composition API com `<script setup lang="ts">`, componentes limpos e estilização via Tailwind CSS seguindo a paleta de cores escura e estética RPG do restante do projeto.