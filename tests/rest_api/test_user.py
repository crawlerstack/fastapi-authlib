"""Test user"""
from datetime import datetime, timedelta

from fastapi_authlib.services import AuthService
from tests.rest_api.conftest import assert_status_code


def test_user(client, mocker):
    """Test user"""
    # 借助auth接口实现session_id的生成
    mocker.patch.object(AuthService,
                        'auth',
                        return_value={'user_id': 1, 'exp': (datetime.now() + timedelta(hours=3)).timestamp()})
    auth_response = client.get('/auth', params={'callback_url': 'http://example.com'}, follow_redirects=False)
    session_id = auth_response.cookies['session_id']

    user_mock_value = {
        "id": 1,
        "update_time": "2023-05-24T16:00:46.321352",
        "create_time": "2023-05-23T14:05:17.684109",
        "name": "张三",
        "nickname": "zhangsan",
        "email": "san.zhang@example.com",
        "email_verified": True,
        "picture": "https://www.gravatar.com/avatar/2fb82010acfbad47662844b7007012d4?s=80&d=identicon",
        "active": True
    }

    user = mocker.patch.object(AuthService, 'user', return_value=user_mock_value)
    response = client.get('/users', cookies={'session_id': session_id})
    assert_status_code(response)
    user.assert_called_once()
    assert response.json() == {'message': 'ok', 'data': user_mock_value}
