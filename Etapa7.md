# ETAPA 7: Edição Inline/Live-Preview de Artigos com Auto-Save (Debounce & Unmount) e Parsing de Wikilinks em Tempo Real

> **Instrução para o Agente de IA da IDE:**
> Você deve implementar estritamente os requisitos, alterações e refatorações descritos nesta etapa. Substitua a edição via modal estanque do Codex por uma experiência de edição inline e live-preview direta na página do artigo. Mantenha os padrões do projeto (FastAPI + SQLAlchemy Assíncrono no backend; Vue 3 + TypeScript + Pinia + Vue Router no frontend) e respeite a matriz de permissões desenvolvida na Etapa 6.

---

## 1. Visão Geral e Objetivos da Etapa 7

Esta etapa elimina a barreira entre "modo leitura" e "modo edição" na visualização de Artigos do Codex. Se o usuário tiver permissão de edição (Mestre, Criador ou jogador com permissão `TOTAL`), a página do artigo permitirá a edição direta e fluida de suas seções com salvamento automático reativo.

### Funcionalidades Entregues nesta Etapa:

1. **Edição Inline & Live Preview Unificados:** A leitura e a edição de títulos e seções ocorrem na mesma tela, com suporte a preview em tempo real de mídias e Wikilinks (`[[Artigo]]`).
2. **Auto-Save com Debounce de 3 Segundos:** Alterações em títulos, seções e tags são acumuladas e enviadas ao backend automaticamente após 3 segundos de inatividade de digitação.
3. **Salvamento Garantido na Navegação (*Route Leave / Unmount*):** Se o usuário clicar em um link interno, mudar de aba no menu lateral ou navegar para outra rota, qualquer alteração pendente é salva imediatamente antes da transição.
4. **Indicador de Status de Sincronização:** Feedback visual discreto no cabeçalho do artigo exibindo o estado do documento (*"Salvo"*, *"Salvando..."*, *"Alterações não salvas"*, *"Erro ao salvar"*).
5. **Reconhecimento de Wikilinks em Tempo Real:** O autocomplete e a resolução de links internos `[[...]]` funcionam de maneira contínua durante a digitação no próprio bloco da seção.

---

## 2. Detalhamento das Alterações - Backend (FastAPI / SQLAlchemy)

### 2.1. Otimização dos Endpoints de Artigo (`backend/app/api/routes/articles.py`)

Ajustar os endpoints de atualização para permitir requisições parciais de salvamento automático sem reescrever a estrutura inteira de forma destrutiva quando apenas uma seção for alterada.

* **`PUT /api/v1/worlds/{world_id}/articles/{article_id}`**:
* Garantir tratamento idempotente e performático ao receber o payload do auto-save.
* Atualizar a coluna `updated_at` a cada salvamento bem-sucedido.


* **`PATCH /api/v1/worlds/{world_id}/articles/{article_id}/sections/{section_id}` (Opcional/Otimização)**:
* Endpoint dedicado para atualização cirúrgica de uma única seção (título, conteúdo ou `image_url`) caso o payload completo do artigo seja desnecessário.



---

## 3. Detalhamento das Alterações - Frontend (Vue 3 / TypeScript / Pinia)

### 3.1. Composable de Auto-Save (`frontend/src/composables/useAutoSave.ts`)

Criar um composable para encapsular a lógica de debounce e salvamento pendente:

```typescript
import { ref, watch, onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

export function useAutoSave<T>(
  source: () => T,
  saveFn: (data: T) => Promise<void>,
  delayMs = 3000
) {
  const status = ref<'SAVED' | 'SAVING' | 'PENDING' | 'ERROR'>('SAVED')
  let timer: number | null = null
  let pendingData: T | null = null

  const triggerSave = async () => {
    if (!pendingData) return
    status.value = 'SAVING'
    try {
      await saveFn(pendingData)
      pendingData = null
      status.value = 'SAVED'
    } catch (err) {
      status.value = 'ERROR'
      console.error('Erro no Auto-Save:', err)
    }
  }

  // Monitora alterações nos dados
  watch(
    source,
    (newData) => {
      pendingData = JSON.parse(JSON.stringify(newData))
      status.value = 'PENDING'
      if (timer) clearTimeout(timer)
      timer = window.setTimeout(triggerSave, delayMs)
    },
    { deep: true }
  )

  // Salva imediatamente se o usuário tentar mudar de rota
  onBeforeRouteLeave(async () => {
    if (timer) clearTimeout(timer)
    if (pendingData) {
      await triggerSave()
    }
  })

  // Salva se o componente for desmontado
  onUnmounted(async () => {
    if (timer) clearTimeout(timer)
    if (pendingData) {
      await triggerSave()
    }
  })

  return { status, triggerSave }
}

```

### 3.2. Refatoração da View do Codex (`frontend/src/views/CodexView.vue`)

Reformular a área de detalhe do artigo de modo que a visualização seja interativa:

1. **Cabeçalho do Artigo**:
* O título torna-se um campo editável em linha (`<input>` transparente ou `contenteditable`) para usuários com permissão de escrita (`can_edit === true`).
* Badge indicador do status de sincronização no topo da tela:
* 🟢 *"Salvo"*
* 🟡 *"Salvando..."*
* 🟠 *"Alterações pendentes"*
* 🔴 *"Erro ao salvar"*




2. **Blocos de Seções com Foco e Preview**:
* Cada seção do artigo exibe o texto processado via `<WikilinkText>` por padrão.
* Ao clicar sobre o bloco de texto de uma seção (ou ao focar), o elemento alterna suavemente para o `<WikilinkInput>`, permitindo a edição e o acionamento do autocomplete de `[[`.
* Ao desfoque (*blur*) ou inatividade de 3 segundos, o estado é enviado para o auto-save e o bloco volta a exibir a renderização do `<WikilinkText>`.


3. **Adição/Remoção de Seções e Tags em Linha**:
* Botões discretos `+ Adicionar Seção` no rodapé da página.
* Gerenciamento de tags inline (adicionar/remover etiquetas estilo `.NPC`, `.Local`).



---

## 4. Plano de Ação Passo a Passo para a IDE (Execution Checklist)

Siga rigorosamente a ordem de execução abaixo:

1. **[Frontend]** Criar o composable `frontend/src/composables/useAutoSave.ts`.
2. **[Backend]** Garantir que a rota `PUT /api/v1/worlds/{world_id}/articles/{article_id}` em `backend/app/api/routes/articles.py` processe atualizações parciais com velocidade e sem erros de concorrência.
3. **[Frontend]** Atualizar a store `frontend/src/stores/articles.ts` para suportar atualizações de seções e expor ações de auto-save.
4. **[Frontend]** Refatorar `frontend/src/views/CodexView.vue`:
* Remover os modais de edição de artigo antigos.
* Implementar o título editável inline e os blocos de seção com alternância automática entre foco (`WikilinkInput`) e leitura (`WikilinkText`).
* Conectar a reatividade das seções ao `useAutoSave` configurado com o tempo de 3000ms.


5. **[Frontend]** Adicionar o componente visual de status de salvamento no cabeçalho do artigo.
6. **[Frontend]** Adicionar os interceptores de mudança de rota (`onBeforeRouteLeave`) e encerramento do componente (`onUnmounted`) para acionar a persistência imediata dos dados pendentes.

---

## 5. Critérios de Aceite e Testes de Verificação

### Testes de Backend:

* [ ] Alterações enviadas pelo auto-save atualizam os registros na tabela `articles` e `article_sections` e modificam o campo `updated_at`.
* [ ] Requisições concorrentes de salvamento automático não geram inconsistências no banco de dados.

### Testes de Frontend:

* [ ] Abrir um artigo com permissão de escrita permite digitar diretamente no título e nas seções sem abrir modais.
* [ ] Após digitar qualquer texto e aguardar 3 segundos sem apertar teclas, o status muda para *"Salvando..."* e depois para *"Salvo"*.
* [ ] Digitar um Wikilink no formato `[[Nome do Artigo]]` ativa o popup de autocomplete em tempo real.
* [ ] Se o usuário digitar um texto e clicar imediatamente em um link de outro artigo ou em um item da sidebar, o sistema força o salvamento dos dados pendentes antes de concluir a navegação.