# 📝 Prompt de Implementação - Etapa 9: Reformulação da Importação do Cofre do Obsidian

## 🎯 Objetivo
Refatorar o serviço de importação de cofres do Obsidian (`obsidian_import_service.py`) para:
1. Mapear e recriar a estrutura exata de pastas e subpastas do arquivo ZIP no banco de dados como `ArticleFolder`.
2. Associar cada artigo `.md` importado à sua respectiva `ArticleFolder` (`folder_id`).
3. Eliminar o comportamento antigo de transformar nomes de pastas em tags.
4. Manter a estrutura interna do arquivo Markdown contínua (`# `, `## `, `### `, `[[Wikilinks]]`) dentro do campo `content` do artigo.

---

## 🗂️ Arquivos Envolvidos
- `backend/app/services/obsidian_import_service.py` *(Modificado)*
- `backend/app/api/routes/articles.py` *(Modificado - endpoint de importação)*
- `backend/tests/test_obsidian_import.py` *(Modificado)*

---

## 📋 Tarefas Detalhadas por Arquivo

### 1. Refatorar o Serviço de Importação (`backend/app/services/obsidian_import_service.py`)

Atualize a classe/funções de importação do Obsidian:

* **Passo 1: Varredura de Diretórios e Criação de Pastas**
  * Ao receber o arquivo `.zip` (via `zipfile.ZipFile`):
    * Filtrar todos os caminhos de pastas (diretórios) e arquivos `.md` contidos no pacote.
    * Ignorar pastas ocultas da configuração do Obsidian (ex: `.obsidian/`, `.trash/`, `.git/`).
    * Mapear os caminhos relativos de diretórios e criar as entidades `ArticleFolder` correspondentes no banco de dados para o `world_id` informado.
    * Utilizar um dicionário `folder_path_map: Dict[str, int]` para armazenar a correspondência entre o caminho relativo da pasta no ZIP (ex: `"Geografia/Cidades"`) e o `id` da `ArticleFolder` criada no banco.
    * Garantir que pastas aninhadas respeitem a hierarquia configurando o `parent_id` correto.

* **Passo 2: Processamento e Importação dos Arquivos `.md`**
  * Para cada arquivo `.md` válido no ZIP:
    * Determinar a pasta pai extraindo o diretório do caminho do arquivo (`os.path.dirname(file_path)`).
    * Buscar o `folder_id` no `folder_path_map`. Se o arquivo estiver no diretório raiz do ZIP, `folder_id = None`.
    * Extrair o nome do arquivo (sem a extensão `.md`) para ser usado como o `title` do `Article`.
    * Ler todo o conteúdo textual do arquivo `.md` como uma única string.
    * Definir esse texto lido diretamente na coluna `content` do novo `Article`.
    * **Remover completamente** a lógica que transformava os segmentos do caminho da pasta em `ArticleTag`.

* **Passo 3: Extração Opcional de Tags Inline (`#tag`)**
  * Se o sistema possuir parser de tags, buscar apenas hashtags inseridas no corpo do texto Markdown (ex: `#lore`, `#npc`), ignorando cabeçalhos de título (`# Título`, `## Subtítulo`).
  * Vincular essas tags encontradas ao artigo via tabela de associação de tags.

* **Passo 4: Retorno e Métricas da Importação**
  * Retornar um sumário da importação contendo:
    * `folders_created`: Quantidade de pastas criadas.
    * `articles_created`: Quantidade de artigos importados.
    * `errors`: Lista de erros/avisos ocorridos durante o processo, se houver.

### 2. Ajustar Endpoint de Importação (`backend/app/api/routes/articles.py` ou `folders.py`)
* Garantir que a rota responsável pelo upload do ZIP (`POST /worlds/{world_id}/import-obsidian` ou similar) chame o serviço atualizado dentro de uma transação do banco de dados (`db.commit()`).
* Tratar exceções de arquivos ZIP corrompidos ou com codificação inválida (garantir leitura em `utf-8` com fallback seguro).

### 3. Atualizar e Expandir Testes Unitários (`backend/tests/test_obsidian_import.py`)
* Criar um fixture que gere um arquivo ZIP de teste contendo:
  * `Pasta1/SubpastaA/Artigo1.md`
  * `Pasta1/Artigo2.md`
  * `ArtigoRaiz.md`
* Executar a função de importação do serviço no banco de testes.
* Asserções necessárias:
  * Verificar se as entidades `ArticleFolder` foram criadas com a relação `parent_id` correta.
  * Verificar se `Artigo1.md` possui o `folder_id` correspondente à `SubpastaA`.
  * Verificar se `ArtigoRaiz.md` possui `folder_id == None`.
  * Confirmar que o campo `content` de cada artigo contém a string exata do Markdown original.
  * Confirmar que nenhuma tag foi gerada a partir dos nomes das pastas.

---

## 🧪 Requisitos de Teste e Validação
1. **Execução da Suíte de Testes**: Rodar `pytest backend/tests/test_obsidian_import.py` e garantir 100% de aprovação.
2. **Validação de Estrutura ZIP Completa**: Garantir que diretórios vazios ou arquivos sem extensão `.md` não causem falhas na importação.
3. **Preservação do Markdown**: Garantir que linhas iniciadas por `#`, `##`, `###` e referências `[[Wikilink]]` permaneçam inalteradas na coluna `content`.

---
Instruções finais para a IA: Siga as boas práticas de manipulação de I/O em memória (`io.BytesIO` e `zipfile.ZipFile`) sem salvar arquivos temporários desnecessários no disco do servidor.