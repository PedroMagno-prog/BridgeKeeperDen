"""Serviço assíncrono para descompactação e importação de cofres Obsidian (.zip)."""
from __future__ import annotations

import io
import re
import uuid
import zipfile
import frontmatter
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.article import Article
from app.db.models.article_section import ArticleSection
from app.db.models.article_tag import ArticleTag
from app.db.models.enums import VisibilityType


async def processar_zip_obsidian(
    db: AsyncSession,
    world_id: uuid.UUID,
    user_id: uuid.UUID,
    zip_bytes: bytes,
    use_folders_as_tags: bool = False,
) -> dict:
    """
    Processa todos os arquivos .md de um ZIP do Obsidian e os persiste em lote.
    Aplica Obscurecimento Total (Visão Nula) por padrão.
    """
    imported_count = 0
    skipped_count = 0

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for file_info in z.infolist():
            # Ignora pastas, arquivos oculstos do macOS/Obsidian e extensões que não sejam .md
            filename = file_info.filename
            if (
                file_info.is_dir()
                or filename.startswith("__MACOSX")
                or "/." in filename
                or filename.startswith(".")
                or not filename.endswith(".md")
            ):
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

            # Nome do arquivo como Título do Artigo
            path_parts = [p for p in filename.split("/") if p]
            file_name = path_parts[-1]
            article_title = file_name[:-3].strip()  # Remove extensão .md

            if not article_title:
                skipped_count += 1
                continue

            # 1. Definir Valores Padrão (Defaults)
            visibility = VisibilityType.NULA  # Obscurecimento Total por padrão
            in_game_date_raw = metadata.get("in_game_date", None)
            in_game_date = str(in_game_date_raw).strip() if in_game_date_raw else None

            # 2. Processar Tags (Default = Nenhuma)
            tags_set: set[str] = set()
            if "tags" in metadata and metadata["tags"]:
                front_tags = metadata["tags"]
                if isinstance(front_tags, list):
                    tags_set.update(str(t).strip() for t in front_tags)
                elif isinstance(front_tags, str):
                    tags_set.update(t.strip() for t in front_tags.split(","))

            # Opção de usar nome de subpastas como tags
            if use_folders_as_tags and len(path_parts) > 1:
                for folder in path_parts[:-1]:
                    if not folder.startswith("."):
                        tags_set.add(folder.strip())

            # 3. Dividir conteúdo em Seções por Headers (#, ##)
            sections_data = parse_markdown_sections(raw_text)

            # 4. Criar Entidade do Artigo
            article = Article(
                world_id=world_id,
                title=article_title,
                visibility=visibility,
                in_game_date=in_game_date,
                created_by=user_id,
            )
            db.add(article)
            await db.flush()

            # Adicionar Seções
            for sec in sections_data:
                db.add(
                    ArticleSection(
                        article_id=article.id,
                        title=sec["title"],
                        content=sec["content"],
                        order_index=sec["order_index"],
                    )
                )

            # Adicionar Tags
            for tag_name in tags_set:
                clean_tag = tag_name.strip()
                if clean_tag:
                    formatted_tag = clean_tag if clean_tag.startswith(".") else f".{clean_tag}"
                    db.add(
                        ArticleTag(
                            article_id=article.id,
                            name=formatted_tag,
                        )
                    )

            imported_count += 1

    await db.flush()
    return {
        "imported_count": imported_count,
        "skipped_count": skipped_count,
    }


def parse_markdown_sections(text: str) -> list[dict]:
    """Divide o corpo do Markdown em seções baseadas em títulos # / ##."""
    text_clean = text.strip()
    if not text_clean:
        return [{"title": "Visão Geral", "content": "", "order_index": 0}]

    header_regex = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    matches = list(header_regex.finditer(text_clean))

    if not matches:
        return [{"title": "Visão Geral", "content": text_clean, "order_index": 0}]

    sections: list[dict] = []
    if matches[0].start() > 0:
        pre_content = text_clean[: matches[0].start()].strip()
        if pre_content:
            sections.append({"title": "Visão Geral", "content": pre_content, "order_index": 0})

    for idx, match in enumerate(matches):
        sec_title = match.group(2).strip()
        start_pos = match.end()
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(text_clean)
        sec_content = text_clean[start_pos:end_pos].strip()

        sections.append({
            "title": sec_title if sec_title else "Seção Sem Título",
            "content": sec_content,
            "order_index": len(sections),
        })

    return sections
