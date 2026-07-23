from app.db.session import Base  # noqa: F401 – imported for Alembic target_metadata

# Todos os models devem ser importados aqui para o Alembic detectar as tabelas:
from app.db.models.usuario import Usuario      # noqa: F401
from app.db.models.personagem import Personagem  # noqa: F401
