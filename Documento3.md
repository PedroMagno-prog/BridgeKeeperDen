# DOCUMENTO 03: Arquitetura do Sistema e Endpoints de API

Este documento detalha a arquitetura de software, a pilha tecnológica recomendada para manter o sistema em **baixo custo/gratuito**, os mecanismos internos de segurança para o *Fog of War* e o contrato de endpoints da API RESTful.

---

## 1. Raciocínio de Arquitetura (Chain of Thought / Passo a Passo)

Para definir a arquitetura técnica da aplicação, aplico o raciocínio passo a passo baseado nos requisitos do projeto:

### Passo 1: Seleção da Pilha Tecnológica (Stack) de Baixo Custo

* **Premissa:** O sistema deve ser de uso pessoal e compartilhado com amigos, sem custos fixos mensais de servidor.
* **Frontend:** **React + Vite (TypeScript)** ou **Next.js (App Router)**.
* *Escolha:* **React (Vite) + TailwindCSS**. É leve, permite compilação estática hospedável gratuitamente em plataformas como Vercel, Netlify ou Cloudflare Pages. Para a renderização interativa do mapa com zoom/pan, bibliotecas como **Leaflet.js** (com coordenadas customizadas em pixels/porcentagem) ou **react-zoom-pan-pinch** são ideais.


* **Backend:** **Node.js (Fastify / Express com TypeScript)** ou **Python (FastAPI)**.
* *Escolha:* **FastAPI (Python)** ou **Node.js (Fastify)**. Ambos oferecem alta performance, tipagem rigorosa e documentação automática de API (OpenAPI/Swagger). Podem ser hospedados em instâncias gratuitas/hobby (ex: Render, Fly.io ou Supabase Edge Functions).


* **Banco de Dados & Storage:**
* *Banco:* **PostgreSQL** (hospedado no plano gratuito do Supabase, Neon.tech ou Render).
* *Storage de Imagens de Mapas:* **Cloudinary** (plano gratuito com otimização automática para WebP) ou **Supabase Storage**.



---

### Passo 2: Arquitetura da Névoa de Guerra (Fog of War) no Backend

* **Problema:** Se o backend retornar o JSON completo de um artigo `VISAO_NULA` ou `VISAO_PARCIAL`, um jogador curioso poderia abrir as ferramentas de desenvolvedor do navegador (F12 / Inspect Network) e ler segredos do Mestre.
* **Solução Técnica (Defense in Depth):**
1. **Nível de Banco de Dados / Query:** A query SQL inclui filtros baseados no `user_role`.
2. **Nível de Servidor (DTO Transformer / Serializer):** Antes de enviar a resposta HTTP, um middleware/interceptor limpa os campos de acordo com a regra:
* Se `Role == JOGADOR` e `Visibility == VISÃO_NULA`: O recurso é removido da lista ou retorna `404 Not Found`.
* Se `Role == JOGADOR` e `Visibility == VISÃO_PARCIAL`: O backend sanitiza a resposta, preenchendo o título real ou fictício, zerando o campo `content` e retornando uma flag `is_locked: true`.
* Se `Role == MESTRE`: Retorna o objeto original completo.





---

### Passo 3: Mecanismo de Parsing de `@Mentions`

* **Formato de Armazenamento no Banco:** Em vez de salvar HTML estático com links fixos (que quebram se o artigo mudar de nome), o texto armazena tags padronizadas:
* Exemplo: `O rei viajou para @[article:uuid-1234] para consultar @[pin:uuid-5678].`


* **Formato de Renderização no Frontend:**
1. O backend (ou frontend) intercepta a string no formato `@[...]`.
2. O componente de texto do frontend substitui a tag por um componente interativo (`<MentionLink id="..." type="article"/>`).
3. Ao passar o mouse sobre a menção, exibe um *tooltip* simples; ao clicar, navega para o artigo ou centraliza o pino no mapa.



---

## 2. Visão Geral da Arquitetura do Sistema

```text
  [ Frontend Web (React + Vite + Tailwind) ]
                     │
                     │ HTTP / REST (JSON)
                     ▼
  [ Backend API Gateway / Middleware de Autenticação (JWT) ]
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
  [ Service Layer ]      [ Fog of War Sanitizer ]
  (Regras de Negócio)    (Filtra dados segundo o Role)
          │                     │
          └──────────┬──────────┘
                     ▼
    [ PostgreSQL Database (Supabase/Neon) ]
                     ▲
                     │ (Upload/Compression WebP)
    [ Cloudinary / Object Storage (Mapas) ]

```

---

## 3. Especificação dos Endpoints da API REST

Convenção da API: Todos os endpoints são prefixados com `/api/v1`. Todas as requisições privadas exigem o cabeçalho `Authorization: Bearer <JWT_TOKEN>`.

### 3.1. Autenticação & Gestão do Mundo

#### `POST /api/v1/auth/register`

* **Descrição:** Cria uma nova conta de usuário.

#### `POST /api/v1/auth/login`

* **Descrição:** Autentica o usuário e retorna o token JWT.

#### `GET /api/v1/worlds`

* **Descrição:** Lista os mundos onde o usuário é Mestre ou Jogador.

#### `POST /api/v1/worlds`

* **Descrição:** Cria um novo mundo. O usuário logado torna-se automaticamente `MESTRE`.

---

### 3.2. Módulo A: Artigos (Codex & Wiki)

#### `GET /api/v1/worlds/{world_id}/articles`

* **Descrição:** Lista os artigos do mundo com suporte a filtros por tag e busca textual.
* **Query Params:** `?tag=.Facção&search=Guilhar`
* **Comportamento do Fog of War:**
* *Mestre:* Recebe todos os artigos.
* *Jogador:* Oculta artigos com `visibility = NULA`. Artigos `PARCIAL` retornam apenas `id`, `title`, `visibility` e `is_locked: true`.



#### `POST /api/v1/worlds/{world_id}/articles`

* **Descrição:** Cria um novo artigo.
* **Corpo da Requisição (JSON):**

```json
{
  "title": "Cultura dos Anões de Ferro",
  "in_game_date": "1442 D.C.",
  "in_game_sort_order": 14420000,
  "visibility": "NULA",
  "tags": [".Cultura", ".Anões"],
  "sections": [
    {
      "title": "Origens",
      "content": "Fundada por @[article:8a1b2c3d-0000-0000-0000-000000000000] nas montanhas.",
      "order_index": 0
    }
  ]
}

```

* **Regra de Default:** Se quem estiver criando for `MESTRE`, `visibility` padrão = `NULA`. Se for `JOGADOR`, `visibility` padrão = `TOTAL`.

#### `GET /api/v1/worlds/{world_id}/articles/{article_id}`

* **Descrição:** Obtém o detalhe de um artigo específico e suas seções.

#### `PUT /api/v1/worlds/{world_id}/articles/{article_id}`

* **Descrição:** Atualiza título, tags, visibilidade e seções de um artigo.

#### `DELETE /api/v1/worlds/{world_id}/articles/{article_id}`

* **Descrição:** Remove um artigo (Apenas Mestre ou Criador do artigo).

#### `POST /api/v1/worlds/{world_id}/articles/{article_id}/inventory`

* **Descrição:** Adiciona/atualiza os itens de mochila para artigos de personagens.

---

### 3.3. Módulo B: Mapas Interativos e Marcadores (Pins)

#### `GET /api/v1/worlds/{world_id}/maps`

* **Descrição:** Lista os mapas cadastrados no mundo.

#### `POST /api/v1/worlds/{world_id}/maps`

* **Descrição:** Faz upload da imagem do mapa (comprime para WebP) e salva o registro.

#### `GET /api/v1/worlds/{world_id}/maps/{map_id}`

* **Descrição:** Obtém dados do mapa, suas camadas (`layers`) e os marcadores (`pins`).
* **Resposta de Exemplo (Visão Sanitizada para Jogador):**

```json
{
  "id": "map-uuid-1111",
  "title": "Continente do Sul",
  "image_url": "https://storage.com/maps/continente_sul.webp",
  "layers": [
    { "id": "layer-1", "name": "Capitais", "is_default_active": true }
  ],
  "pins": [
    {
      "id": "pin-uuid-9999",
      "title": "Eldoria",
      "x_position": 45.50,
      "y_position": 32.10,
      "icon": "city-icon",
      "color": "#3B82F6",
      "visibility": "TOTAL",
      "target_article_id": "art-uuid-2222"
    },
    {
      "id": "pin-uuid-8888",
      "title": "Local Desconhecido",
      "x_position": 80.10,
      "y_position": 12.40,
      "icon": "question-icon",
      "color": "#9CA3AF",
      "visibility": "PARCIAL",
      "target_article_id": null
    }
  ]
}

```

#### `POST /api/v1/worlds/{world_id}/maps/{map_id}/pins`

* **Descrição:** Cria um novo marcador no mapa.

#### `PUT /api/v1/worlds/{world_id}/maps/{map_id}/pins/{pin_id}`

* **Descrição:** Atualiza a posição (X, Y), ícone, cor ou estado de visibilidade de um marcador.

---

### 3.4. Módulo C: Linha do Tempo (Timeline)

#### `GET /api/v1/worlds/{world_id}/timeline`

* **Descrição:** Retorna os eventos e eras organizados cronologicamente.
* **Processamento Interno:**
1. Busca todos os artigos que possuem `in_game_sort_order != NULL` respeitando a regra de *Fog of War*.
2. Busca as eras cadastradas em `timeline_eras`.
3. Agrupa e ordena os eventos entre as eras correspondentes.


* **Resposta de Exemplo:**

```json
{
  "eras": [
    {
      "title": "Era dos Reis",
      "start_sort_order": 10000000,
      "end_sort_order": 20000000
    }
  ],
  "timeline_events": [
    {
      "article_id": "art-uuid-2222",
      "title": "Fundação de Eldoria",
      "in_game_date": "Anos 1200 D.C.",
      "in_game_sort_order": 12000000,
      "visibility": "TOTAL"
    }
  ]
}

```

---

### 3.5. Módulo D: Manuscritos e Resumos de Sessão

#### `GET /api/v1/worlds/{world_id}/manuscripts`

* **Descrição:** Lista os manuscritos/diários de sessão.

#### `GET /api/v1/worlds/{world_id}/manuscripts/{manuscript_id}/chapters`

* **Descrição:** Lista os capítulos/momentos marcantes de um manuscrito com filtragem por visão.

#### `POST /api/v1/worlds/{world_id}/manuscripts/{manuscript_id}/chapters`

* **Descrição:** Cria um novo capítulo com formatação em destaque/Header e suporte a `@Mentions`.

---
