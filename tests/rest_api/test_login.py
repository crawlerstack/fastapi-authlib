"""Test login"""
from starlette.responses import Response

from fastapi_authlib.schemas.user import UserSchema
from fastapi_authlib.services import AuthService
from tests.rest_api.conftest import assert_status_code


def test_login(client, mocker):
    """Test login"""
    login = mocker.patch.object(AuthService, 'login', return_value=Response(status_code=200))
    response = client.get('/login')
    assert_status_code(response)
    login.assert_called_once()


def test_auth(client, mocker):
    """Test auth"""
    user = UserSchema(
        id=1,
        name="user1",
        email="user1@example.com"
    )
    token = AuthService().format_payload(user)

    auth = mocker.patch.object(AuthService, 'auth', return_value=token)
    response = client.get('/auth', params={'callback_url': 'https://foo.com'}, follow_redirects=False)
    assert response.status_code == 307
    assert response.headers.get('authorization')
    auth.assert_called_once()
