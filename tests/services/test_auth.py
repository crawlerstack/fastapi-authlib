"""test auth"""

import pytest
from authlib.integrations.base_client import TokenExpiredError
from pydantic import BaseModel, constr

from fastapi_authlib.schemas.user import UserSchema
from fastapi_authlib.services import AuthService
from fastapi_authlib.utils.exceptions import AuthenticationError


class UserInfo(BaseModel):
    """User base schema."""
    iss: constr(max_length=100) = None
    sub: constr(max_length=100) = None
    aud: constr(max_length=100) = None
    exp: int = None
    iat: int = None
    nonce: constr(max_length=100) = None
    auth_time: int = None
    sub_legacy: constr(max_length=100) = None
    name: constr(max_length=100) = None
    nickname: constr(max_length=100) = None
    preferred_username: constr(max_length=100) = None
    email: constr(max_length=100) = None
    email_verified: bool = False
    profile: constr(max_length=100) = None
    picture: constr(max_length=100) = None
    groups_direct: list[constr(max_length=100)] = []
    groups: list[constr(max_length=100)] = []

    def get(self, key):
        """get"""
        return self.__getattribute__(key)  # pylint: disable=unnecessary-dunder-call


@pytest.fixture()
def service():
    """service fixtures"""
    return AuthService()


@pytest.mark.parametrize(
    'user_id',
    [
        1,
    ]
)
async def test_logout(init_session, session, service, user_id):
    """Test logout"""
    before = await service.get_by_id(user_id)
    await service.logout(user_id)
    after = await service.get_by_id(user_id)
    assert before.active != after.active


@pytest.mark.parametrize(
    'groups, user, expect_value',
    [
        [['user-groups/python-team'], UserSchema(id=1), 2],
        [['user-groups/python-team2'], UserSchema(id=1), 3],
    ]
)
async def test_save_group_and_group_user_map(init_group_user_map, service, session, groups, user, expect_value):
    """Test save group and group user map"""
    await service.save_group_and_group_user_map(groups, user)
    result = await service.group_repository.count()
    assert result == expect_value


@pytest.mark.parametrize(
    'token, expect_value',
    [
        [{
            'access_token': 'access_token',
            'token_type': 'Bearer',
            'expires_in': 7200,
            'refresh_token': 'refresh_token',
            'scope': 'openid email profile',
            'created_at': 1681978523,
            'id_token': 'id_token',
            'expires_at': 1681985725,
            'userinfo': UserInfo(**{
                'iss': 'iss',
                'sub': '2',
                'aud': 'aud',
                'exp': 1681978643,
                'iat': 1681978523,
                'nonce': 'B4JDgASRNADfrDf5qj7z',
                'auth_time': 1681451014,
                'sub_legacy': 'sub_legacy',
                'name': '张三',
                'nickname': 'zhangsan',
                'preferred_username': 'zhangsan',
                'email': 'user1@example.com',
                'email_verified': True,
                'profile': 'zhangsan',
                'picture': 'picture',
                'groups_direct': [
                    'user-groups/python-team'
                ]})
        }, 0],
        [{
            'access_token': 'access_token',
            'token_type': 'Bearer',
            'expires_in': 7200,
            'refresh_token': 'refresh_token',
            'scope': 'openid email profile',
            'created_at': 1681978523,
            'id_token': 'id_token',
            'expires_at': 1681985725,
            'userinfo': UserInfo(**{
                'iss': 'iss',
                'sub': '2',
                'aud': 'aud',
                'exp': 1681978643,
                'iat': 1681978523,
                'nonce': 'B4JDgASRNADfrDf5qj7z',
                'auth_time': 1681451014,
                'sub_legacy': 'sub_legacy',
                'name': '李四',
                'nickname': 'lisi',
                'preferred_username': 'lisi',
                'email': 'user3@example.com',
                'email_verified': True,
                'profile': 'lisi',
                'picture': 'picture',
                'groups_direct': [
                    'user-groups/python-team'
                ]})
        }, 1]
    ]
)
async def test_auth(init_session, session, service, mocker, token, expect_value):
    """Test auth"""
    mocker.patch.object(service, 'save_group_and_group_user_map')
    authorize_access_token = mocker.patch.object(service.oauth_client.oauth, 'authorize_access_token',
                                                 return_value=token)
    before_count = await service.repository.count()
    await service.auth(mocker.MagicMock())
    authorize_access_token.assert_called_once()
    after_count = await service.repository.count()
    assert after_count - before_count == expect_value


@pytest.mark.parametrize(
    'user_id, token, mocker_result, exist, expect_value',
    [
        [3, {"token": "token"}, False, False, 0],
        [1, {'access_token': 'access_token',
             'token_type': 'Bearer',
             'expires_in': 7200,
             'refresh_token': 'refresh_token',
             'scope': 'openid email profile',
             'created_at': 1681978523,
             'id_token': 'id_token',
             'expires_at': 1681985725, }, True, True, 2],
        [1, {'access_token': 'access_token',
             'token_type': 'Bearer',
             'expires_in': 7200,
             'refresh_token': 'refresh_token',
             'scope': 'openid email profile',
             'created_at': 1681978523,
             'id_token': 'id_token',
             'expires_at': 1681985725, }, False, True, 1]
    ]
)
async def test_update_token(init_session, session, service, mocker, user_id, token, mocker_result, exist, expect_value):
    """Test update token"""
    if not isinstance(user_id, int):
        raise TypeError
    if exist:
        if mocker_result:
            fetch_access_token = mocker.patch.object(service.oauth_client.oauth, 'fetch_access_token',
                                                     return_value=token)
        else:
            fetch_access_token = mocker.patch.object(service.oauth_client.oauth, 'fetch_access_token',
                                                     side_effect=TokenExpiredError)
        await service.update_token(user_id)
        result = await service.session_repository.count()
        assert result == expect_value
        fetch_access_token.assert_called_once()
    else:
        result = await service.update_token(user_id)
        assert result is False


@pytest.mark.parametrize(
    'user_id, mocker_result, exist, expect_value',
    [
        [2, False, False, 0],
        [1, True, True, 2],
        [1, False, True, 1]
    ]
)
async def test_user(init_session, session, service, mocker, user_id, mocker_result, exist, expect_value):
    """Test user"""
    mocker.patch.object(service, 'save_group_and_group_user_map')
    if exist:
        if mocker_result:
            mocker_value = UserInfo(**{
                'name': '李四',
                'nickname': 'lisi',
                'email': 'user3@example.com',
                'email_verified': True,
                'picture': 'picture.jpg',
                'groups': [
                    'user-groups/python-team'
                ]})
            userinfo = mocker.patch.object(service.oauth_client.oauth, 'userinfo', return_value=mocker_value)
            await service.user(user_id)
        else:
            userinfo = mocker.patch.object(service.oauth_client.oauth, 'userinfo', side_effect=Exception)
            with pytest.raises(AuthenticationError):
                await service.user(user_id)
        result = await service.session_repository.count()
        assert result == expect_value
        userinfo.assert_called_once()
    else:
        with pytest.raises(AuthenticationError):
            await service.user(user_id)
