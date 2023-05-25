"""Group"""
from sqlalchemy import select

from fastapi_authlib.models import GroupUserMap
from fastapi_authlib.repository.base import BaseRepository
from fastapi_authlib.schemas.group_user_map import (GroupUserMapCreate,
                                                    GroupUserMapSchema,
                                                    GroupUserMapUpdate)
from fastapi_authlib.utils.exceptions import ObjectDoesNotExist


class GroupUserMapRepository(BaseRepository[GroupUserMap, GroupUserMapCreate, GroupUserMapUpdate, GroupUserMapSchema]):
    """
    GroupUserMap repository
    """
    model = GroupUserMap
    model_schema = GroupUserMapSchema

    async def get_by_group_and_user_id(self, group_id: int, user_id: int) -> GroupUserMapSchema:
        """Get GroupUserMap by group_id and user_id"""
        stmt = select(GroupUserMap).filter(GroupUserMap.group_id == group_id).filter(GroupUserMap.user_id == user_id)
        group_user: GroupUserMap = await self.session.scalar(stmt)
        if not group_user:
            # Task does not exist
            raise ObjectDoesNotExist()
        return self.model_schema.from_orm(group_user)
