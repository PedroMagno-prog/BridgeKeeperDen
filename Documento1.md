1. **Documento 01: Especificação de Requisitos e Regras de Negócio (SRS)** *(Este documento)*
2. **Documento 02: Modelagem de Dados e Banco de Dados (ERD / SQL Schema)**
3. **Documento 03: Arquitetura do Sistema e Endpoints de API (Backend & Frontend)**
4. **Documento 04: Design de Interface (UX/UI) e Protótipo de Telas**

---

# DOCUMENTO 01: Especificação de Requisitos e Regras de Negócio (SRS)

## 1. Visão Geral e Objetivos do Sistema

O sistema (**Worldbuilder Personal/Group**) é uma aplicação web de baixo custo e alta performance para criação de mundo, consulta de *lore* e gestão de sessões de RPG de mesa.

* **Foco Central:** Simplicidade de edição, links dinâmicos entre documentos, mapa interativo e controle severo de visibilidade (*Fog of War*) entre Mestre e Jogadores.
* **Modelo de Hospedagem:** Web (Acessível via navegador desktop/mobile).

---

## 2. Perfis de Acesso e Controle de Visibilidade (*Fog of War*)

### 2.1. Papéis no Sistema (Roles)

* **MESTRE (GM):** Possui acesso irrestrito a todos os dados do sistema, ignorando qualquer restrição de visibilidade.
* **JOGADOR (Player):** Possui acesso limitado aos dados do sistema, estritamente determinado pelas *Tags de Visão* de cada recurso.

### 2.2. Níveis de Visibilidade (Visão/Access Level)

Cada recurso (Artigo, Marcador de Mapa, Capítulo) possui uma propriedade obrigatória de visibilidade:

| Nível de Visão | Comportamento para o JOGADOR | Comportamento para o MESTRE |
| --- | --- | --- |
| **Visão Total** | Acesso completo para leitura de título, seções, metadados e marcadores. | Acesso total. |
| **Visão Parcial** | O título e localização são visíveis. Exibe um ícone de interrogação (`?`). **Impossível clicar, abrir ou ler o conteúdo interno.** | Acesso total (vê o conteúdo e a indicação de que está "Parcial" para os jogadores). |
| **Visão Nula** | O elemento é **completamente invisível** (não renderizado no DOM nem retornado nas APIs do jogador). | Acesso total. |

### 2.3. Regras de Negócio de Criação (Defaults)

* **RN-01 (Default do Mestre):** Todo conteúdo criado por um usuário com papel *MESTRE* é salvo por padrão com a tag **Visão Nula** (Invisível para os jogadores até que o mestre altere manualmente).
* **RN-02 (Default do Jogador):** Todo conteúdo criado por um usuário com papel *JOGADOR* (ex: anotações, histórico do personagem) é salvo por padrão com a tag **Visão Total**.

---

## 3. Especificação dos Módulos do Sistema

### Módulo A: Núcleo de Artigos e Lore

* **Estrutura do Artigo:** O artigo não possui formulários engessados. Ele é composto por:
* **Título** (obrigatório).
* **Tags** (ex: `.Facção`, `.Hostil`, `.NPC`, `.Local`).
* **Nível de Visão** (Total, Parcial, Nula).
* **Data In-Game / Registro Cronológico** (opcional - utilizado para alimentar a Timeline).
* **Grupo de Seções:** Coleção dinâmica de blocos contendo `Título da Seção` e `Descrição/Texto` (suporta Rich Text / Markdown).


* **Seção Especial de Personagem (Mochila/Inventário):** Se o artigo for de um personagem, permite adicionar um grupo de seções específico para listagem de itens/equipamentos.
* **Sistema de Menções (`@Mentions`):** Ao digitar `@` em qualquer campo de texto de uma seção, o sistema exibe uma busca rápida de Artigos ou Pins de Mapa. Ao selecionar, cria um link dinâmico interno.

### Módulo B: Mapas Interativos

* **Mapa Base:** Upload de imagem estática (PNG/JPG) com zoom e pan (arrastar).
* **Marcadores (Pins):**
* Posição (coordenadas X, Y relativas à imagem).
* Ícone, cor e rótulo do marcador.
* Nível de Visão independente (Total, Parcial, Nula).
* **Comportamento em Hover/Clique:**
* *Visão Total:* Abre pop-up com resumo e botão para abrir o artigo vinculado.
* *Visão Parcial:* Exibe apenas o ícone `?` e o Título do Pin ao passar o cursor. Bloqueado para cliques.
* *Visão Nula:* O pin não aparece no mapa do jogador.




* **Camadas (Layers):** Permite ativar/desativar grupos de pins (ex: "Rotas Comerciais", "Fronteiras Políticas", "Locais Perigosos").
* **Sub-Mapas (Aninhamento):** Um marcador pode ter como destino a abertura de outro Mapa (ex: clicar no pin "Vila de Oakhaven" redireciona para o Mapa da Vila).

### Módulo C: Cronologia e Linha do Tempo Automática

* **Geração Automática:** A linha do tempo **não é criada manualmente**. Ela compila automaticamente todos os Artigos que possuem uma `Data In-Game` preenchida.
* **Estrutura de Exibição:** Ordenação cronológica crescente dos artigos baseada na data informada.
* **Eras e Agrupamentos:** As "Eras" são definidas como cabeçalhos/seções divisórias dentro da linha do tempo, agrupando eventos compreendidos entre determinado período de anos/datas.

### Módulo D: Manuscritos e Diários de Sessão

* **Propósito:** Registro contínuo de resumos das sessões de jogo e contos.
* **Divisão em Capítulos:** Cada documento pode ser dividido em Capítulos/Momentos Marcantes, utilizando formatação de *Header* em destaque visual para separação.
* **Suporte a Menções:** Suporte completo ao parser de `@Mentions` para vincular personagens, locais e pins citados no resumo da sessão.

### Módulo E: Ferramentas Utilitárias

* **Rolador de Dados Simplificado:**
* Widget acessível em qualquer tela (módulo flutuante ou barra lateral).
* Suporte a notação padrão de dados (`d4`, `d6`, `d8`, `d10`, `d12`, `d20`, `d100` + modificadores simples, ex: `1d20+5`).


* **Sistema de Tags de Relação:**
* Substitui grafos complexos de diplomacia.
* Permite adicionar tags em formato chave-valor ou atributos no artigo (ex: `.Facção`, `.Hostil`, `.Aliado`, `.Nobreza`).
* Permite filtrar artigos rapidamente através de buscas combinadas de tags.



---

## 4. Requisitos Não-Funcionais (RNFs)

* **RNF-01 (Custo e Armazenamento):** O sistema deve otimizar o uso de armazenamento. Imagens enviadas para mapas devem ser comprimidas automaticamente no upload (conversão para formato WebP ou JPEG otimizado).
* **RNF-02 (Performance de Renderização):** A renderização dos marcadores no mapa deve ser eficiente (utilizando Canvas 2D ou manipulação otimizada de SVG/DOM via bibliotecas como Leaflet.js).
* **RNF-03 (Segurança de Dados no Fog of War):** Os dados de artigos/pins com status **Visão Nula** **NÃO devem ser enviados** nas requisições JSON da API para usuários com papel *JOGADOR*. A filtragem deve ocorrer estritamente no *Backend* e nunca apenas ocultada via CSS no *Frontend*.
