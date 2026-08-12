"""Schemas Pydantic para gestão de permissões individuais por usuário."""
from __future__ import annotations

import uuid
from pydantic import BaseModel
from app.db.models.enums import VisibilityType


class UserPermissionOut(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str
    visibility: VisibilityType


class UserPermissionUpdateInput(BaseModel):
    user_id: uuid.UUID
    visibility: VisibilityType


class ResourcePermissionsUpdateInput(BaseModel):
    permissions: list[UserPermissionUpdateInput]
