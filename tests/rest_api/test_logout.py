"""Test logout"""
from datetime import datetime, timedelta

from fastapi_authlib.services import AuthService
from tests.rest_api.conftest import assert_status_code


def test_logout(client, mocker):
    """Test logout"""
    # 借助auth接口实现session_id的生成
    mocker.patch.object(AuthService,
                        'auth',
                        return_value={'user_id': 1, 'exp': (datetime.now() + timedelta(hours=3)).timestamp()})
    auth_response = client.get('/auth', params={'callback_url': 'http://example.com'}, follow_redirects=False)
    session_id = auth_response.cookies['session_id']

    logout = mocker.patch.object(AuthService, 'logout')
    response = client.get('/logout', cookies={'session_id': session_id})
    assert_status_code(response)
    logout.assert_called_once()
