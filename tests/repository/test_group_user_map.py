"""Test group user map repository"""
import pytest

from fastapi_authlib.repository.group_user_map import GroupUserMapRepository


@pytest.fixture()
async def repo():
    """Repo fixture"""
    return GroupUserMapRepository()


@pytest.mark.parametrize(
    'user_id, expect_value',
    [
        (1, 1),
        (3, 0)
    ]
)
async def test_get_by_user_id(init_group_user_map, repo, session, user_id, expect_value):
    """Test get by group id and user id"""

    resp = await repo.get_by_user_id(user_id)
    assert len(resp) == expect_value
