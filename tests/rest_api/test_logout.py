"""Test logout"""

from fastapi_authlib.services import AuthService
from tests.rest_api.conftest import assert_status_code


def test_logout(client, mocker, token):
    """Test logout"""
    logout = mocker.patch.object(AuthService, 'logout')
    response = client.get('/logout', headers={'authorization': f'Bearer {token}'})
    assert_status_code(response)
    logout.assert_called_once()
