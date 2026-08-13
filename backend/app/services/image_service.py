"""Serviço de otimização e compressão de imagens de seções do Codex via Pillow."""
from __future__ import annotations

import io
from PIL import Image

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def otimizar_imagem_secao(image_bytes: bytes, filename: str) -> tuple[bytes, str]:
    """
    Verifica o tamanho da imagem. Se exceder 5MB, redimensiona (máx 1920px)
    e converte para formato WebP comprimido (qualidade 80).
    """
    if len(image_bytes) <= MAX_FILE_SIZE:
        return image_bytes, filename

    image = Image.open(io.BytesIO(image_bytes))

    # Converter modos RGBA/P para RGB se salvando em formato que não suporta alfa ou para otimizar
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        # Converter com fundo branco
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode in ("RGBA", "LA"):
            background.paste(image, mask=image.split()[-1])
        else:
            background.paste(image)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Redimensiona mantendo a proporção de aspecto (largura/altura máxima de 1920px)
    max_size = (1920, 1920)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    output = io.BytesIO()
    image.save(output, format="WEBP", quality=80, optimize=True)

    clean_base = filename.rsplit(".", 1)[0] if "." in filename else filename
    new_filename = f"{clean_base}_optimized.webp"

    return output.getvalue(), new_filename
