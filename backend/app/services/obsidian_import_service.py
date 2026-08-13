"""Serviço assíncrono para descompactação e importação de cofres Obsidian (.zip)."""
from __future__ import annotations

import io
import re
import uuid
import zipfile
import frontmatter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.article import Article
from app.db.models.article_folder import ArticleFolder
from app.db.models.article_tag import ArticleTag
from app.db.models.enums import VisibilityType

# Regex para capturar #tags inline (ex: #lore, #npc, #local/sublocal), ignorando cabeçalhos Markdown (# Título, ## Subtítulo)
INLINE_TAG_REGEX = re.compile(r"(?:^|\s)#([a-zA-Z0-9_\-\./]+)")


def is_ignored_path(path: str) -> bool:
    """Verifica se o caminho do arquivo ou diretório deve ser ignorado (arquivos ocultos ou de sistema)."""
    parts = [p for p in path.split("/") if p]
    for p in parts:
        if p.startswith(".") or p == "__MACOSX" or p.startswith("._") or p in (".obsidian", ".trash", ".git"):
            return True
    return False


async def ensure_folder_hierarchy(
    db: AsyncSession,
    world_id: uuid.UUID,
    dir_path: str,
    folder_cache: dict[str, int],
    created_counter: list[int],
) -> int | None:
    """
    Cria recursivamente as entidades ArticleFolder para o caminho de diretório informado.
    Armazena a correspondência no cache `folder_cache`.
    """
    if not dir_path or dir_path in (".", ""):
        return None

    if dir_path in folder_cache:
        return folder_cache[dir_path]

    parts = [p.strip() for p in dir_path.split("/") if p.strip()]
    current_path = ""
    parent_id: int | None = None

    for part in parts:
        current_path = f"{current_path}/{part}" if current_path else part
        if current_path in folder_cache:
            parent_id = folder_cache[current_path]
            continue

        # Verificar se a pasta já existe no banco
        stmt = select(ArticleFolder).where(
            ArticleFolder.world_id == world_id,
            ArticleFolder.parent_id == parent_id,
            ArticleFolder.name == part,
        )
        res = await db.execute(stmt)
        existing_folder = res.scalar_one_or_none()

        if existing_folder:
            folder_id = existing_folder.id
        else:
            new_folder = ArticleFolder(
                world_id=world_id,
                name=part,
                parent_id=parent_id,
            )
            db.add(new_folder)
            await db.flush()
            folder_id = new_folder.id
            created_counter[0] += 1

        folder_cache[current_path] = folder_id
        parent_id = folder_id

    return parent_id


async def processar_zip_obsidian(
    db: AsyncSession,
    world_id: uuid.UUID,
    user_id: uuid.UUID,
    zip_bytes: bytes,
    use_folders_as_tags: bool = False,  # Parâmetro mantido por compatibilidade de assinatura
) -> dict:
    """
    Processa um cofre .zip do Obsidian:
    1. Recria a estrutura hierárquica de pastas no banco como `ArticleFolder`.
    2. Importa cada arquivo `.md` vinculado à sua respectiva pasta (`folder_id`).
    3. Preserva o conteúdo Markdown e extrai tags de Frontmatter e hashtags inline (`#tag`).
    """
    imported_count = 0
    skipped_count = 0
    folders_created_counter = [0]
    folder_cache: dict[str, int] = {}

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        infolist = z.infolist()

        # 1. Primeiro passo: Varredura inicial e criação de pastas vazias no ZIP
        for file_info in infolist:
            filename = file_info.filename
            if is_ignored_path(filename):
                continue
            if file_info.is_dir():
                clean_dir = filename.rstrip("/")
                await ensure_folder_hierarchy(db, world_id, clean_dir, folder_cache, folders_created_counter)

        # 2. Segundo passo: Importação dos arquivos .md
        for file_info in infolist:
            filename = file_info.filename
            if file_info.is_dir() or is_ignored_path(filename):
                if not file_info.is_dir() and is_ignored_path(filename):
                    skipped_count += 1
                continue

            if not filename.endswith(".md"):
                skipped_count += 1
                continue

            # Extrair diretório do arquivo e garantir a pasta correspondente
            path_parts = [p.strip() for p in filename.split("/") if p.strip()]
            dir_parts = path_parts[:-1]
            dir_path = "/".join(dir_parts)
            folder_id = await ensure_folder_hierarchy(db, world_id, dir_path, folder_cache, folders_created_counter)

            file_name = path_parts[-1]
            article_title = file_name[:-3].strip()  # Remove .md

            if not article_title:
                skipped_count += 1
                continue

            content_bytes = z.read(filename)
            try:
                content_str = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content_str = content_bytes.decode("latin-1", errors="ignore")

            # Parse de Frontmatter (YAML)
            try:
                post = frontmatter.loads(content_str)
                raw_text = post.content
                metadata = post.metadata or {}
            except Exception:
                raw_text = content_str
                metadata = {}

            visibility = VisibilityType.NULA  # Obscurecimento Total por padrão (Mestre)
            in_game_date_raw = metadata.get("in_game_date", None)
            in_game_date = str(in_game_date_raw).strip() if in_game_date_raw else None

            # Processar Tags (Frontmatter + Inline Body Hashtags)
            tags_set: set[str] = set()

            # Frontmatter tags
            if "tags" in metadata and metadata["tags"]:
                front_tags = metadata["tags"]
                if isinstance(front_tags, list):
                    tags_set.update(str(t).strip() for t in front_tags)
                elif isinstance(front_tags, str):
                    tags_set.update(t.strip() for t in front_tags.split(","))

            # Inline body tags (#tag)
            inline_matches = INLINE_TAG_REGEX.findall(raw_text)
            for inline_tag in inline_matches:
                clean_it = inline_tag.strip()
                if clean_it and not clean_it.startswith("#"):
                    tags_set.add(clean_it)

            # Criar Entidade do Artigo vinculado ao folder_id da pasta recriada
            article = Article(
                world_id=world_id,
                folder_id=folder_id,
                title=article_title,
                content=raw_text.strip(),
                visibility=visibility,
                in_game_date=in_game_date,
                created_by=user_id,
            )
            db.add(article)
            await db.flush()

            # Adicionar Tags
            for tag_name in tags_set:
                clean_tag = tag_name.strip()
                if clean_tag:
                    formatted_tag = clean_tag if clean_tag.startswith(".") else f".{clean_tag}"
                    db.add(ArticleTag(article_id=article.id, name=formatted_tag))

            imported_count += 1

    await db.flush()
    return {
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "folders_created": folders_created_counter[0],
        "message": f"{imported_count} notas e {folders_created_counter[0]} pastas importadas com sucesso.",
    }
