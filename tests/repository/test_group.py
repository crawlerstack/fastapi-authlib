"""Test group repository"""
import pytest

from fastapi_authlib.repository.group import GroupRepository


@pytest.fixture()
async def repo():
    """Repo fixture"""
    return GroupRepository()


async def test_get_by_name(init_group, repo, session):
    """Test get by name"""
    name = 'user-groups/python-team'
    resp = await repo.get_by_name(name)
    assert resp.name == name
