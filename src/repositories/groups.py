import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import models
import repositories.users
import serializers

logger = logging.getLogger(__name__)


async def create_group(
    session: AsyncSession, group_in: serializers.GroupIn
) -> models.Group:
    group = models.Group(name=group_in.name)
    if group_in.members:
        group.members = await repositories.users.get_by_ids(session, group_in.members)
    session.add(group)
    return group


async def get_by_id(session: AsyncSession, group_id: int) -> models.Group | None:
    return await session.get(models.Group, group_id)
