"""Test group user map repository"""
import pytest

from fastapi_authlib.repository.group_user_map import GroupUserMapRepository
from fastapi_authlib.utils.exceptions import ObjectDoesNotExist


@pytest.fixture()
async def repo():
    """Repo fixture"""
    return GroupUserMapRepository()


@pytest.mark.parametrize(
    'group_id, user_id, expect_value',
    [
        (1, 1, True),
        (1, 3, False)
    ]
)
async def test_get_by_group_and_user_id(init_group_user_map, repo, session, group_id, user_id, expect_value):
    """Test get by group id and user id"""
    if expect_value:
        resp = await repo.get_by_group_and_user_id(group_id, user_id)
        assert resp.user_id == user_id
        assert resp.group_id == group_id
    else:
        with pytest.raises(ObjectDoesNotExist):
            await repo.get_by_group_and_user_id(group_id, user_id)
