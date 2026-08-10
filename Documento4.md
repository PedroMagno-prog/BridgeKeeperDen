# DOCUMENTO 04: Design de Interface (UX/UI) e Protótipo de Telas

Este documento define a experiência do usuário (UX) e o design visual (UI) para a plataforma. O conceito estético adota uma linha **minimalista, moderna e limpa (*clean dark mode*)**, priorizando o contraste de leitura, a facilidade de navegação e o uso de **ícones monocromáticos em vetor/silhueta** para manter uma atmosfera sóbria e profissional.

---

## 1. Diretrizes de Design & Guia de Estilo (Style Guide)

### 1.1. Paleta de Cores (Dark Theme com Destaque Dourado)

* **Fundo Principal (Canvas/Background):** `#0F172A` (Slate/Grafite Escuro Profundo)
* **Superfícies e Cartões (Panels/Cards):** `#1E293B` (Grafite Médio para contraste suave)
* **Bordas e Divisores:** `#334155` (Linhas finas e discretas)
* **Texto Principal:** `#F8FAFC` (Branco Puro / Alta legibilidade)
* **Texto Secundário / Rótulos:** `#94A3B8` (Cinza claro suave)
* **Cor de Destaque Primária (Accent/Gold):** `#D4AF37` / `#F59E0B` (Dourado Nobre para botões primários, links, foco de seleção e bordas ativas)
* **Cores de Visibilidade (*Fog of War*):**
* **Visão Total:** `#10B981` (Verde Esmeralda - Indicador discreto para o Mestre)
* **Visão Parcial:** `#F59E0B` (Dourado/Âmbar - Indicador com ícone de interrogação `?`)
* **Visão Nula:** `#EF4444` (Vermelho/Translúcido - Indicador de oculto para o Mestre)



### 1.2. Tipografia e Iconografia

* **Tipografia:** Fonte sem serifa de alta legibilidade (ex: *Inter* ou *Roboto*) com excelente renderização em telas de alta e baixa densidade.
* **Iconografia (Sem Emojis):** Uso exclusivo de **ícones em vetor/silhueta monocromática** (SVG estilo *Lucide Icons* ou *Heroicons*).
* Ícones claros (White/Silver) sobre fundos escuros.
* Ícones dourados para ações ativas/selecionadas.
* NENHUM emoji é utilizado na interface do sistema.



### 1.3. Estrutura Padrão de Layout (Shell da Aplicação)

A aplicação adota um layout responsivo de 3 blocos:

1. **Barra Superior (Header):**
* Seletor de Mundo Ativo (Dropdown).
* Badge de Perfil (`MESTRE` ou `JOGADOR`).
* Atalho para o Rolador de Dados Flutuante.
* Campo de Busca Global (Ctrl+K) com pesquisa rápida por artigos e marcadores.


2. **Barra Lateral Retrátil (Sidebar Esquerda):**
* Menu principal de módulos navegáveis por ícones de silhueta:
* *Codex / Artigos*
* *Mapas Interativos*
* *Linha do Tempo*
* *Manuscritos / Diário*




3. **Área Central de Conteúdo (Main Workspace):**
* Espaço dedicado onde as telas dos módulos são renderizadas com margens amplas e tipografia limpa.



---

## 2. Mapeamento e Detalhamento das Telas

Below está a especificação individual de cada tela do sistema, definindo seu intuito, componentes de interface e particularidades de navegação.

---

### TELA 1: Dashboard e Seleção de Mundo

* **Intuito:** Ponto de entrada do usuário no sistema. Permite escolher em qual mundo/campanha deseja navegar, criar um novo mundo (caso Mestre) e visualizar o resumo de atividades recentes.
* **Componentes Principais:**
* **Grade de Cards de Mundos:** Exibe os mundos disponíveis. Cada card possui o título do mundo, o papel do usuário naquele mundo (`MESTRE` com detalhe dourado ou `JOGADOR`) e a data da última atualização.
* **Botão "Criar Novo Mundo" (Apenas Mestre):** Modal simples solicitando Nome e Descrição rápida.
* **Atividades Recentes:** Lista simples com os últimos artigos editados ou capítulos publicados no mundo selecionado.



---

### TELA 2: Módulo Codex / Navegação de Artigos (Wiki)

* **Intuito:** Centralizar a listagem, categorização e busca rápida de todo o acervo de *lore* e dados do mundo.
* **Componentes Principais:**
* **Barra de Ferramentas e Filtros:**
* Campo de busca textual por título do artigo.
* Lista de pílulas de Tags de filtro (ex: `.Facção`, `.NPC`, `.Local`, `.Hostil`).
* Botão de ação "+ Novo Artigo" (destacado em Dourado).


* **Lista / Grade de Artigos:**
* Exibe os artigos organizados em linhas minimalistas.
* Cada item mostra: Título do Artigo, Tags associadas, Data *In-Game* (se houver).
* **Comportamento Mestre vs. Jogador:**
* *Mestre:* Vê todos os artigos. Ao lado do título, exibe um badge discreto do status de visão (`TOTAL`, `PARCIAL` ou `NULA`).
* *Jogador:* Não visualiza artigos com `Visão Nula`. Artigos com `Visão Parcial` aparecem com o título, um ícone de interrogação `?` ao lado e uma indicação de bloqueio (não clicável).







---

### TELA 3: Leitura e Edição de Artigo

* **Intuito:** Exibir o conteúdo detalhado de um artigo específico e permitir sua criação/edição através de um formato limpo baseado em seções.
* **Componentes Principais:**
* **Cabeçalho do Artigo:**
* Título em destaque (*Font-size elevado*).
* Selector de Visibilidade (Dropdown de seleção rápida: `Visão Total`, `Visão Parcial`, `Visão Nula` - Visível/editável apenas pelo Mestre).
* Campo de Data *In-Game* (Alimenta a linha do tempo).
* Container de Tags (Adição/Remoção rápida de etiquetas estilo `.Hostil`).


* **Grupo de Seções de Conteúdo:**
* Blocos verticais ordenáveis contendo *Título da Seção* e *Corpo do Texto*.
* Suporte ao menu de `@Mentions`: Ao digitar `@`, surge um popover limpo para selecionar outro Artigo ou Pino do Mapa, inserindo o link interno.


* **Painel da Mochila / Inventário (Opcional):**
* Seção especial para artigos de personagens. Tabela simples e funcional de itens contendo: Nome do Item, Quantidade e Descrição curta.


* **Modo de Edição Inline / Autosave:** Alternância simples entre leitura limpa e edição dos blocos de texto.



---

### TELA 4: Módulo de Mapas Interativos (Visualizador e Cartografia)

* **Intuito:** Apresentar imagens de mapas em alta resolução com navegação fluida (zoom e arrasto), permitindo ao Mestre posicionar marcadores (*pins*) que conectam a geografia ao Codex de artigos.
* **Componentes Principais:**
* **Canvas do Mapa (Navegador):**
* Renderizador da imagem do mapa com controles de Zoom (+/-) no canto inferior e suporte a pan (arrastar com o mouse/touch).


* **Marcadores / Pins Interativos:**
* Ícones em vetor/silhueta (ex: castelo, cidade, ruína, caveira, montanha) posicionados dinamicamente sobre a imagem.


* **Painel Lateral de Camadas (Layers Drawer):**
* Lista de checkboxes para alternar a visibilidade de camadas (ex: "Rotas Marítimas", "Fronteiras", "Cidades Custeiras").


* **Pop-Up / Tooltip de Marcador:**
* *Ao passar o cursor/clicar no pino (Visão Total):* Abre um pequeno card flutuante contendo o Título do Pino, um breve resumo do artigo vinculado e o botão "Abrir Artigo".
* *Ao passar o cursor (Visão Parcial - Jogador):* O pino assume o ícone de silhueta de interrogação `?`. O card exibe apenas o Título do Local e a mensagem *"Conteúdo não descoberto"*.
* *Visão Nula:* O pino simplesmente não é renderizado no canvas do jogador. O Mestre enxerga o pino com opacidade reduzida e um ícone de olho riscado.


* **Modo de Edição de Marcador (Apenas Mestre):**
* Clique com o botão direito no mapa para "Adicionar Pino". Permite arrastar o pino para a posição desejada, escolher a cor (hex), o ícone de silhueta, vincular a um Artigo e definir a Visibilidade.





---

### TELA 5: Módulo Linha do Tempo (Timeline Automática)

* **Intuito:** Visualizar a cronologia do mundo de forma limpa e sequencial, gerada automaticamente a partir dos artigos que possuem datas associadas.
* **Componentes Principais:**
* **Trilho Cronológico Vertical:**
* Linha central contínua decorada com a cor dourada de destaque.
* Divisores de Eras Históricas (Header estilizado em caixa alta agrupando os eventos compreendidos naquele período).


* **Cards de Eventos da Timeline:**
* Conectados ao trilho cronológico.
* Exibem a **Data In-Game**, o **Título do Artigo** que gerou o evento e um pequeno trecho explicativo da primeira seção do artigo.
* Clique no card redireciona o usuário diretamente para o artigo completo no Codex.


* **Filtros da Timeline:** Busca rápida por eventos dentro de determinada Era ou com tags específicas.



---

### TELA 6: Módulo de Manuscritos & Diário de Sessão

* **Intuito:** Ambiente focado na escrita e leitura de crônicas, contos e resumos de sessões de jogo de forma contínua.
* **Componentes Principais:**
* **Sidebar Interna de Capítulos:**
* Lista vertical ordenada de Capítulos/Sessões (ex: "Sessão 01: O Resgate na Taverna", "Sessão 02: A Emboscada").
* Indicador de Visibilidade em cada capítulo.


* **Área do Manuscrito (Modo Foco):**
* Layout estilo documento com margens largas e tipografia espaçada para leitura confortável.
* Os títulos dos capítulos funcionam como divisores (*Headers* em destaque visual com acento dourado).
* Suporte completo às menções `@` no texto (passar o mouse sobre a menção exibe um card rápido do artigo citado).





---

### WIDGET GLOBAL: Rolador de Dados Simplificado

* **Intuito:** Utilitário rápido e acessível a partir de qualquer tela para rolagem de dados de RPG durante a sessão, sem poluir a interface principal.
* **Comportamento e Design:**
* **Formato:** Painel gaveta (Drawer) ou modal flutuante minimizável no canto inferior direito da tela.
* **Interface de Rolagem:**
* Botões rápidos com ícones vetoriais de silhueta dos dados clássicos: `d4`, `d6`, `d8`, `d10`, `d12`, `d20`, `d100`.
* Campo numérico para adição de **Modificador** (ex: `+3`, `-2`).
* Botão principal "Rolar" com destaque dourado.


* **Histórico de Rolagens:**
* Pequeno feed exibindo as últimas 5 rolagens feitas (ex: `1d20 + 4 = 18 [14]`).





---