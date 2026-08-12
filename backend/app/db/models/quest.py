"""Modelos de Quest e QuestObjective (tabelas `quests` e `quest_objectives`)."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import String, Text, ForeignKey, Enum, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base
from app.db.models.enums import VisibilityType


class QuestStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ON_HOLD = "ON_HOLD"


class QuestCategory(str, enum.Enum):
    MAIN_QUEST = "MAIN_QUEST"
    SIDE_QUEST = "SIDE_QUEST"
    MONSTER_HUNT = "MONSTER_HUNT"
    ARTIFACT_SEARCH = "ARTIFACT_SEARCH"
    OUTPOST = "OUTPOST"
    FACTION = "FACTION"


class Quest(Base):
    """Missão / Quest do Quest Journal de um mundo."""

    __tablename__ = "quests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    article_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    category: Mapped[QuestCategory] = mapped_column(
        Enum(QuestCategory, native_enum=True, name="quest_category"),
        nullable=False,
        default=QuestCategory.SIDE_QUEST,
    )
    status: Mapped[QuestStatus] = mapped_column(
        Enum(QuestStatus, native_enum=True, name="quest_status"),
        nullable=False,
        default=QuestStatus.NOT_STARTED,
    )
    visibility: Mapped[VisibilityType] = mapped_column(
        Enum(VisibilityType, native_enum=True, name="visibility_type", create_type=False),
        nullable=False,
        default=VisibilityType.NULA,
    )
    rewards: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    created_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    # ── Relacionamentos ───────────────────────────────────────────────────────
    world: Mapped["World"] = relationship("World")
    article: Mapped["Article | None"] = relationship("Article", lazy="selectin")
    objectives: Mapped[list["QuestObjective"]] = relationship(
        "QuestObjective",
        back_populates="quest",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="QuestObjective.order_index",
    )

    def __repr__(self) -> str:
        return f"<Quest id={self.id} title={self.title!r} status={self.status.value}>"


class QuestObjective(Base):
    """Objetivo / Etapa individual de uma Quest."""

    __tablename__ = "quest_objectives"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Relacionamentos ───────────────────────────────────────────────────────
    quest: Mapped["Quest"] = relationship("Quest", back_populates="objectives")

    def __repr__(self) -> str:
        return f"<QuestObjective id={self.id} desc={self.description!r} completed={self.is_completed}>"
