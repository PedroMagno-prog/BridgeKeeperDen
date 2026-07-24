from app.db.session import Base  # noqa: F401 – imported for Alembic target_metadata

# Todos os models devem ser importados aqui para o Alembic detectar as tabelas:
from app.db.models.enums import UserRole, VisibilityType  # noqa: F401
from app.db.models.user import User  # noqa: F401
from app.db.models.world import World  # noqa: F401
from app.db.models.world_member import WorldMember  # noqa: F401
from app.db.models.article import Article  # noqa: F401
from app.db.models.article_section import ArticleSection  # noqa: F401
from app.db.models.article_tag import ArticleTag  # noqa: F401
from app.db.models.character_inventory import CharacterInventory  # noqa: F401
from app.db.models.map import Map  # noqa: F401
from app.db.models.map_layer import MapLayer  # noqa: F401
from app.db.models.map_pin import MapPin  # noqa: F401
from app.db.models.manuscript import Manuscript  # noqa: F401
from app.db.models.manuscript_chapter import ManuscriptChapter  # noqa: F401
from app.db.models.timeline_era import TimelineEra  # noqa: F401
