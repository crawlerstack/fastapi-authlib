"""test auth"""
import pytest
from pydantic import BaseModel, constr

from fastapi_authlib.schemas.user import UserSchema
from fastapi_authlib.services import AuthService
from fastapi_authlib.utils.exceptions import (AuthenticationError,
                                              ObjectDoesNotExist)


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
    'groups, user, expect_group_value, expect_map_value',
    [
        [['user-groups/python-team'], UserSchema(id=1), 2, 1],
        [['user-groups/python-team2'], UserSchema(id=1), 3, 1],
        [['user-groups/python-team2', 'user-groups/python-team3'], UserSchema(id=1), 4, 2]
    ]
)
async def test_save_group_and_group_user_map(
    init_group_user_map, service, session, groups, user, expect_group_value, expect_map_value
):
    """Test save group and group user map"""
    await service.save_group_and_group_user_map(groups, user)
    result = await service.group_repository.count()
    assert result == expect_group_value

    group_map = await service.group_user_map_repository.get_by_user_id(user.id)
    assert len(group_map) == expect_map_value


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
                ]}
                                 )
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
                ]}
                                 )
        }, 1]
    ]
)
async def test_auth(init_session, session, service, mocker, token, expect_value):
    """Test auth"""
    mocker.patch.object(service, 'save_group_and_group_user_map')
    authorize_access_token = mocker.patch.object(
        service.oauth_client.oauth,
        'authorize_access_token',
        return_value=token
    )
    before_count = await service.repository.count()
    await service.auth(mocker.MagicMock())
    authorize_access_token.assert_called_once()
    after_count = await service.repository.count()
    assert after_count - before_count == expect_value


@pytest.mark.parametrize(
    'user_id, user_exist, user_active, userinfo_value, userinfo_exist, access_token_exist, access_token',
    [
        (
            1,
            True,
            True,
            UserInfo(name="user1", nickname="user2", picture='picture.jpg', groups=['user-groups/python-team']),
            False,
            True,
            {'access_token': 'access_token', 'refresh_token': 'refresh_token', 'expires_at': 1690424691}
        ),
        (
            1,
            True,
            True,
            UserInfo(name="user1", nickname="user2", picture='picture.jpg', groups=['user-groups/python-team']),
            False,
            False,
            None
        ),
        (
            1,
            True,
            True,
            UserInfo(name="user1", nickname="user1", picture='picture.jpg', groups=['user-groups/python-team']),
            True,
            None,
            None
        ),
        (
            1,
            True,
            True,
            UserInfo(name="user1", nickname="user2", picture='picture.jpg', groups=['user-groups/python-team']),
            True,
            None,
            None
        ),
        (2, True, False, None, None, None, None),
        (3, False, None, None, None, None, None)
    ]
)
async def test_verify_user(
    init_session, session, service, mocker, user_id, user_exist, user_active, userinfo_value, userinfo_exist,
    access_token_exist, access_token
):
    """Test verify_user"""
    if user_exist:
        if user_active:
            if userinfo_exist:
                userinfo = mocker.patch.object(
                    service.oauth_client.oauth,
                    'userinfo',
                    return_value=userinfo_value
                )
            else:
                mocker.patch.object(
                    service.oauth_client.oauth,
                    'userinfo',
                    side_effect=Exception
                )
                if access_token_exist:
                    mocker.patch.object(
                        service.oauth_client.oauth,
                        'fetch_access_token',
                        return_value=access_token
                    )
                    userinfo = mocker.patch.object(
                        service.oauth_client.oauth,
                        'userinfo',
                        return_value=userinfo_value
                    )
                else:
                    mocker.patch.object(
                        service.oauth_client.oauth,
                        'fetch_access_token',
                        side_effect=Exception
                    )
                    mocker.patch.object(
                        service.oauth_client.oauth,
                        'userinfo',
                        side_effect=Exception
                    )
                    with pytest.raises(AuthenticationError):
                        await service.verify_user(user_id)
                    return

            await service.verify_user(user_id)
            userinfo.assert_called()

        else:
            with pytest.raises(AuthenticationError):
                await service.verify_user(user_id)
    else:
        with pytest.raises(ObjectDoesNotExist):
            await service.verify_user(user_id)


@pytest.mark.parametrize(
    'user_id, expect_type',
    [
        (1, True),
        (2, 'AuthenticationError'),
        (3, 'ObjectDoesNotExist')
    ]
)
async def test_get_user_by_id(init_session, session, service, user_id, expect_type):
    """Test get_user_by_id"""
    if isinstance(expect_type, bool):
        user = await service.get_user_by_id(user_id)
        assert user.id == user_id
    elif expect_type == 'AuthenticationError':
        with pytest.raises(AuthenticationError):
            await service.get_user_by_id(user_id)
    else:
        with pytest.raises(ObjectDoesNotExist):
            await service.get_user_by_id(user_id)


async def test_format_payload(service):
    """Test format_payload"""
    user_obj_in = UserSchema(
        id=1,
        name="user1",
        email="user1@example.com"
    )
    user = service.format_payload(user_obj_in)
    assert user_obj_in.id == user.get('user_id')
    assert 'iat' in user.keys()


@pytest.mark.parametrize(
    'user_id, expect_value',
    [
        (1, True),
        (3, False)
    ]
)
async def test_clear_token_info(init_session, service, session, mocker, user_id, expect_value):
    """Test clear_token_info"""
    clear_session_with_user_id = mocker.patch.object(service, 'clear_session_with_user_id')
    if expect_value:
        before = await service.get_by_id(user_id)
        await service.clear_token_info(user_id)
        after = await service.get_by_id(user_id)
        assert before.active != after.active
    else:
        with pytest.raises(ObjectDoesNotExist):
            await service.clear_token_info(user_id)
    clear_session_with_user_id.assert_called_once()


@pytest.mark.parametrize(
    'user_id, expect_value',
    [
        (1, True),
        (3, False)
    ]
)
async def test_clear_session_with_user_id(init_session, service, session, user_id, expect_value, caplog):
    """Test clear_session_with_user_id"""
    if expect_value:
        before = await service.session_repository.count()
        await service.clear_session_with_user_id(user_id)
        after = await service.session_repository.count()
        assert before - 1 == after
    else:
        await service.clear_session_with_user_id(user_id)
        assert 'Session does not exist' in caplog.text  # noqa
