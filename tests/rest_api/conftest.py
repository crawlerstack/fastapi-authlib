"""rest api"""
import pytest
from fastapi import Response

from fastapi_authlib.config import settings
from fastapi_authlib.schemas.user import UserSchema
from fastapi_authlib.services import AuthService
from fastapi_authlib.utils import encode_token


@pytest.fixture
def user():
    """User schema"""
    return UserSchema(
        id=1,
        name="user1",
        email="user1@example.com"
    )


def assert_status_code(response: Response, code=200) -> None:
    """Check state code is ok."""
    assert response.status_code == code


@pytest.fixture
def token(user):
    """Encode token"""
    token = encode_token(
        AuthService().format_payload(user),
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return token
