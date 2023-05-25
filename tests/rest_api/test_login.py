"""Test login"""
from starlette.responses import Response

from fastapi_authlib.services import AuthService
from tests.rest_api.conftest import assert_status_code


def test_login(client, mocker):
    """Test login"""
    login = mocker.patch.object(AuthService, 'login',
                                return_value=Response(status_code=200))
    response = client.get('/login')
    assert_status_code(response)
    login.assert_called_once()


def test_auth(client, mocker):
    """Test auth"""
    auth = mocker.patch.object(AuthService, 'auth', return_value={'user_name': 'test'})
    response = client.get('/auth', params={'callback_url': 'http://example.com'}, follow_redirects=False)
    assert response.status_code == 307
    assert response.cookies.get('session_id')
    auth.assert_called_once()
