import enum


class UserRole(str, enum.Enum):
    """Papéis de usuário no contexto de um Mundo."""
    MESTRE = "MESTRE"
    JOGADOR = "JOGADOR"


class VisibilityType(str, enum.Enum):
    """Níveis de visibilidade do Fog of War."""
    TOTAL = "TOTAL"
    PARCIAL = "PARCIAL"
    NULA = "NULA"
