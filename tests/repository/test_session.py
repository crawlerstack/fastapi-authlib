"""Test session repository"""
import pytest

from fastapi_authlib.repository.session import SessionRepository


@pytest.fixture()
async def repo():
    """Repo fixture"""
    return SessionRepository()


async def test_get_session_from_user_id(init_session, repo, session):
    """Test get by name"""
    user_id = 1
    resp = await repo.get_session_from_user_id(user_id)
    assert resp.user_id == user_id
