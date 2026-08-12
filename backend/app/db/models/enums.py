"""
ENUMs compartilhados do sistema.

Mapeiam diretamente para os tipos PostgreSQL `user_role` e `visibility_type`
definidos no Documento 02.
"""
import enum


class UserRole(str, enum.Enum):
    """Papel do usuário dentro de um mundo."""
    MESTRE = "MESTRE"
    JOGADOR = "JOGADOR"


class VisibilityType(str, enum.Enum):
    """Nível de Névoa de Guerra (Fog of War) de um recurso."""
    TOTAL = "TOTAL"
    PARCIAL = "PARCIAL"
    CONTROLADO = "CONTROLADO"
    NULA = "NULA"
