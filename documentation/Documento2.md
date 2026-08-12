# DOCUMENTO 02: Modelagem de Dados e Banco de Dados (ERD & SQL Schema)

Este documento define a arquitetura de persistência de dados para o sistema de *worldbuilding*. A modelagem foi projetada utilizando um banco de dados relacional (**PostgreSQL**), priorizando integridade referencial, consultas de alta performance e filtragem rígida de **Fog of War** no nível de banco de dados.

---

## 1. Raciocínio de Modelagem (Chain of Thought)

Para traduzir as regras de negócio do SRS (Documento 01) em uma estrutura de banco de dados eficiente, o raciocínio de modelagem foi dividida nos seguintes passos:

1. **Isolamento por Mundo (`worlds`):**
* Toda a informação pertence a um *Mundo*. Isso garante multitenancy simples (um usuário pode participar de múltiplos mundos) e simplifica as cláusulas `WHERE world_id = X` em todas as queries.


2. **Abstração Modular de Artigos (`articles`, `article_sections`, `article_tags`):**
* Em vez de criar tabelas engessadas para "NPC", "Cidade" ou "Item", centralizamos a entidade em `articles`.
* O conteúdo textual é normalizado em `article_sections` (chave-valor de Título/Conteúdo ordenados por `order_index`).
* As características do artigo são flexibilizadas via `article_tags` (ex: `.Facção`, `.Hostil`, `.Personagem`).


3. **Suporte a Inventário/Mochila (`character_inventories`):**
* Para atender à necessidade de inventário nos artigos de personagens sem engessar a estrutura geral, criamos uma tabela filha opcional ligada diretamente ao `article_id`.


4. **Estrutura de Cartografia Interativa (`maps`, `map_layers`, `map_pins`):**
* Posições dos marcadores utilizam porcentagem relativa (`x_position`, `y_position` de $0.00$ a $100.00$) para garantir responsividade independente da resolução da tela.
* `map_pins` suporta links polimórficos opcionais (`target_article_id` para abrir um artigo ou `target_map_id` para abrir um sub-mapa).


5. **Geração Dinâmica de Timeline (`articles` + `timeline_eras`):**
* A linha do tempo **não possui tabela própria de eventos**. Ela reflete diretamente os registros da tabela `articles` que possuem o campo `in_game_date` preenchido.
* A tabela `timeline_eras` apenas delimita faixas temporais com rótulos visuais.


6. **Implementação do Fog of War (`visibility_type`):**
* Criamos um tipo enumerado `visibility_type` (`TOTAL`, `PARCIAL`, `NULA`) aplicado nas tabelas que contêm conteúdo restrito (`articles`, `map_pins`, `manuscript_chapters`).
* Índices compostos cobrindo `(world_id, visibility)` foram adicionados para otimizar a filtragem das requisições feitas por jogadores.



---

## 2. Diagrama de Relacionamento (Representação Textual / ERD)

```text
[users] 1 --- * [worlds] (owner)
[users] * --- * [worlds] via [world_members] (role: MESTRE | JOGADOR)

[worlds] 1 --- * [articles]
  ├── 1 --- * [article_sections]
  ├── 1 --- * [article_tags]
  └── 1 --- * [character_inventories]

[worlds] 1 --- * [maps]
  ├── 1 --- * [map_layers]
  └── 1 --- * [map_pins] ──> (opcional: links para [articles] ou [maps])

[worlds] 1 --- * [manuscripts]
  └── 1 --- * [manuscript_chapters]

[worlds] 1 --- * [timeline_eras]

```

---

## 3. Dicionário de Dados

### 3.1. Tipos Customizados (ENUMs)

* `user_role`: `'MESTRE'`, `'JOGADOR'`
* `visibility_type`: `'TOTAL'`, `'PARCIAL'`, `'NULA'`

---

### 3.2. Tabelas Principais

#### Tabela: `users`

Armazena as contas de acesso à plataforma.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador único do usuário |
| `username` | `VARCHAR(50)` | `UNIQUE, NOT NULL` | Nome de exibição |
| `email` | `VARCHAR(255)` | `UNIQUE, NOT NULL` | Email para autenticação |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | Hash seguro da senha (bcrypt/argon2) |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Data de criação do cadastro |

---

#### Tabela: `worlds`

Contêiner isolado de um cenário/campanha.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador único do mundo |
| `name` | `VARCHAR(100)` | `NOT NULL` | Nome do mundo/cenário |
| `description` | `TEXT` | `NULL` | Resumo/Visão geral do mundo |
| `owner_id` | `UUID` | `FK (users.id)` | Mestre criador/proprietário do mundo |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Data de criação |

---

#### Tabela: `world_members`

Associação entre usuários e mundos, definindo papéis de acesso (*Mestre* ou *Jogador*).

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador do vínculo |
| `world_id` | `UUID` | `FK (worlds.id) ON DELETE CASCADE` | Mundo associado |
| `user_id` | `UUID` | `FK (users.id) ON DELETE CASCADE` | Usuário participante |
| `role` | `user_role` | `NOT NULL DEFAULT 'JOGADOR'` | Papel no mundo (`MESTRE` ou `JOGADOR`) |

---

#### Tabela: `articles`

A entidade central da enciclopédia/codex.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador único do artigo |
| `world_id` | `UUID` | `FK (worlds.id) ON DELETE CASCADE` | Mundo ao qual pertence |
| `title` | `VARCHAR(150)` | `NOT NULL` | Título do artigo |
| `visibility` | `visibility_type` | `NOT NULL` | Nível de Névoa de Guerra (`TOTAL`, `PARCIAL`, `NULA`) |
| `in_game_date` | `VARCHAR(50)` | `NULL` | Data fictícia do mundo (usada para ordens na Timeline) |
| `in_game_sort_order` | `BIGINT` | `NULL` | Timestamp/inteiro normalizado para ordenação exata na Timeline |
| `created_by` | `UUID` | `FK (users.id)` | Criador do artigo |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Data de criação real |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Última modificação real |

---

#### Tabela: `article_sections`

Blocos organizacionais dentro de um artigo.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador da seção |
| `article_id` | `UUID` | `FK (articles.id) ON DELETE CASCADE` | Artigo pai |
| `title` | `VARCHAR(150)` | `NOT NULL` | Título do bloco/seção |
| `content` | `TEXT` | `NOT NULL DEFAULT ''` | Conteúdo da seção (suporta Markdown e `@Mentions`) |
| `order_index` | `INT` | `NOT NULL DEFAULT 0` | Ordem de exibição dentro do artigo |

---

#### Tabela: `article_tags`

Etiquetas para categorização, identificação e buscas avançadas.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador único da tag |
| `article_id` | `UUID` | `FK (articles.id) ON DELETE CASCADE` | Artigo associado |
| `name` | `VARCHAR(50)` | `NOT NULL` | Nome da tag (ex: `.Hostil`, `.NPC`, `.Facção`) |

---

#### Tabela: `character_inventories`

Mochila/Inventário vinculada a artigos de personagens.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador do item no inventário |
| `article_id` | `UUID` | `FK (articles.id) ON DELETE CASCADE` | Artigo do personagem dono do item |
| `item_name` | `VARCHAR(100)` | `NOT NULL` | Nome do item/equipamento |
| `quantity` | `INT` | `NOT NULL DEFAULT 1` | Quantidade do item |
| `description` | `TEXT` | `NULL` | Detalhes ou notas sobre o item |

---

#### Tabela: `maps`

Gerenciamento de imagens de mapa.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador do mapa |
| `world_id` | `UUID` | `FK (worlds.id) ON DELETE CASCADE` | Mundo associado |
| `title` | `VARCHAR(100)` | `NOT NULL` | Nome do mapa (ex: "Mapa Global de Valoria") |
| `image_url` | `VARCHAR(500)` | `NOT NULL` | Caminho do arquivo de imagem otimizado (WebP/JPG) |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Data de criação |

---

#### Tabela: `map_layers`

Camadas organizacionais de marcadores em um mapa.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador da camada |
| `map_id` | `UUID` | `FK (maps.id) ON DELETE CASCADE` | Mapa pai |
| `name` | `VARCHAR(50)` | `NOT NULL` | Nome da camada (ex: "Cidades", "Rotas de Comércio") |
| `is_default_active` | `BOOLEAN` | `DEFAULT TRUE` | Se a camada vem visível por padrão |

---

#### Tabela: `map_pins`

Marcadores posicionados interativamente sobre a imagem do mapa.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador do marcador |
| `map_id` | `UUID` | `FK (maps.id) ON DELETE CASCADE` | Mapa onde o marcador está localizado |
| `layer_id` | `UUID` | `FK (map_layers.id) ON DELETE SET NULL` | Camada associada (opcional) |
| `target_article_id` | `UUID` | `FK (articles.id) ON DELETE SET NULL` | Link para artigo da wiki (opcional) |
| `target_map_id` | `UUID` | `FK (maps.id) ON DELETE SET NULL` | Link para sub-mapa aninhado (opcional) |
| `title` | `VARCHAR(100)` | `NOT NULL` | Nome do pino |
| `x_position` | `NUMERIC(5,2)` | `NOT NULL` | Coordenada X relativa em % (0 a 100) |
| `y_position` | `NUMERIC(5,2)` | `NOT NULL` | Coordenada Y relativa em % (0 a 100) |
| `icon` | `VARCHAR(50)` | `DEFAULT 'default-pin'` | Identificador do ícone gráfico |
| `color` | `VARCHAR(7)` | `DEFAULT '#FF0000'` | Código hexadecimal de cor |
| `visibility` | `visibility_type` | `NOT NULL` | Visão/Acesso do pino (`TOTAL`, `PARCIAL`, `NULA`) |

---

#### Tabela: `manuscripts`

Agrupador de resumos de sessões e contos.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador do manuscrito |
| `world_id` | `UUID` | `FK (worlds.id) ON DELETE CASCADE` | Mundo associado |
| `title` | `VARCHAR(150)` | `NOT NULL` | Título do livro/diário de sessão |
| `created_by` | `UUID` | `FK (users.id)` | Autor |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT NOW()` | Data de criação |

---

#### Tabela: `manuscript_chapters`

Capítulos/Momentos marcantes dentro de um manuscrito.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador do capítulo |
| `manuscript_id` | `UUID` | `FK (manuscripts.id) ON DELETE CASCADE` | Manuscrito pai |
| `title` | `VARCHAR(150)` | `NOT NULL` | Título do capítulo/sessão |
| `content` | `TEXT` | `NOT NULL DEFAULT ''` | Texto do resumo (suporta Markdown e `@Mentions`) |
| `order_index` | `INT` | `NOT NULL DEFAULT 0` | Ordem cronológica dentro do manuscrito |
| `visibility` | `visibility_type` | `NOT NULL` | Nível de visão do capítulo |

---

#### Tabela: `timeline_eras`

Divisores e eras históricas para agrupar visualmente os eventos da linha do tempo.

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | `UUID` | `PRIMARY KEY` | Identificador da era |
| `world_id` | `UUID` | `FK (worlds.id) ON DELETE CASCADE` | Mundo associado |
| `title` | `VARCHAR(100)` | `NOT NULL` | Nome da era (ex: "Segunda Era da Magia") |
| `start_sort_order` | `BIGINT` | `NOT NULL` | Valor de ordem inicial da era |
| `end_sort_order` | `BIGINT` | `NOT NULL` | Valor de ordem final da era |

---

## 4. DDL em SQL (PostgreSQL Schema)

```sql
-- Habilita extensão para geração de UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. TIPOS CUSTOMIZADOS (ENUMS)
CREATE TYPE user_role AS ENUM ('MESTRE', 'JOGADOR');
CREATE TYPE visibility_type AS ENUM ('TOTAL', 'PARCIAL', 'NULA');

-- 2. TABELA DE USUÁRIOS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. TABELA DE MUNDOS
CREATE TABLE worlds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. VÍNCULO DE MEMBROS DO MUNDO
CREATE TABLE world_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'JOGADOR',
    CONSTRAINT unique_world_user UNIQUE(world_id, user_id)
);

-- 5. TABELA DE ARTIGOS (CODEX)
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    visibility visibility_type NOT NULL DEFAULT 'NULA',
    in_game_date VARCHAR(50),
    in_game_sort_order BIGINT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. SEÇÕES DOS ARTIGOS
CREATE TABLE article_sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    order_index INT NOT NULL DEFAULT 0
);

-- 7. TAGS DOS ARTIGOS
CREATE TABLE article_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL
);

-- 8. INVENTÁRIO DO PERSONAGEM
CREATE TABLE character_inventories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    item_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    description TEXT
);

-- 9. TABELA DE MAPAS
CREATE TABLE maps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. CAMADAS DOS MAPAS
CREATE TABLE map_layers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    map_id UUID NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    is_default_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 11. MARCADORES/PINS DO MAPA
CREATE TABLE map_pins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    map_id UUID NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
    layer_id UUID REFERENCES map_layers(id) ON DELETE SET NULL,
    target_article_id UUID REFERENCES articles(id) ON DELETE SET NULL,
    target_map_id UUID REFERENCES maps(id) ON DELETE SET NULL,
    title VARCHAR(100) NOT NULL,
    x_position NUMERIC(5,2) NOT NULL CHECK (x_position BETWEEN 0 AND 100),
    y_position NUMERIC(5,2) NOT NULL CHECK (y_position BETWEEN 0 AND 100),
    icon VARCHAR(50) DEFAULT 'default-pin',
    color VARCHAR(7) DEFAULT '#FF0000',
    visibility visibility_type NOT NULL DEFAULT 'NULA'
);

-- 12. TABELA DE MANUSCRITOS
CREATE TABLE manuscripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 13. CAPÍTULOS DOS MANUSCRITOS
CREATE TABLE manuscript_chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manuscript_id UUID NOT NULL REFERENCES manuscripts(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    order_index INT NOT NULL DEFAULT 0,
    visibility visibility_type NOT NULL DEFAULT 'NULA'
);

-- 14. ERAS HISTÓRICAS DA TIMELINE
CREATE TABLE timeline_eras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    start_sort_order BIGINT NOT NULL,
    end_sort_order BIGINT NOT NULL
);

-- ============================================================================
-- ÍNDICES DE DESEMPENHO E SEGURANÇA (FOG OF WAR)
-- ============================================================================

-- Otimização de busca em Artigos por Mundo e Visibilidade (Regra RNF-03)
CREATE INDEX idx_articles_world_visibility ON articles(world_id, visibility);

-- Otimização da Linha do Tempo (Ordenação de artigos por data in-game)
CREATE INDEX idx_articles_timeline ON articles(world_id, in_game_sort_order) 
WHERE in_game_sort_order IS NOT NULL;

-- Otimização de Busca de Tags
CREATE INDEX idx_article_tags_name ON article_tags(name);
CREATE INDEX idx_article_tags_article ON article_tags(article_id);

-- Otimização dos Pins de Mapa por Visibilidade
CREATE INDEX idx_map_pins_map_visibility ON map_pins(map_id, visibility);

```