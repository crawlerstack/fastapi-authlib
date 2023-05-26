"""auth"""
import logging
from datetime import datetime, timedelta

from authlib.integrations.base_client.errors import (OAuthError,
                                                     TokenExpiredError)
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request

from fastapi_authlib.config import settings
from fastapi_authlib.models import User
from fastapi_authlib.repository.group import GroupRepository
from fastapi_authlib.repository.group_user_map import GroupUserMapRepository
from fastapi_authlib.repository.session import SessionRepository
from fastapi_authlib.repository.user import UserRepository
from fastapi_authlib.schemas.group import GroupCreate
from fastapi_authlib.schemas.group_user_map import GroupUserMapCreate
from fastapi_authlib.schemas.session import SessionCreate, SessionUpdate
from fastapi_authlib.schemas.user import UserCreate, UserSchema, UserUpdate
from fastapi_authlib.services.base import EntityService
from fastapi_authlib.utils.exceptions import (AuthenticationError,
                                              ObjectDoesNotExist, OIDCError)

logger = logging.getLogger(__name__)
oauth_client = OAuth(settings)


class AuthService(EntityService[User, UserCreate, UserUpdate, UserSchema]):
    """
    Auth service.
    """
    REPOSITORY_CLASS = UserRepository

    @property
    def session_repository(self):
        """Session repository"""
        return SessionRepository()

    @property
    def group_repository(self):
        """Group repository"""
        return GroupRepository()

    @property
    def group_user_map_repository(self):
        """Group user map repository"""
        return GroupUserMapRepository()

    def __init__(self):
        self.oauth_client = oauth_client
        self.register_oauth()

    def register_oauth(self):
        """Register OAuth"""
        self.oauth_client.register(
            name='oauth',
            server_metadata_url=settings.OAUTH_CONF_URL,
            client_kwargs={
                'scope': 'openid email profile',
                'verify': False
            })

    async def login(self, request: Request, redirect_uri: str, **_):
        """
        Login
        :param request:
        :param redirect_uri:
        :param _:
        :return:
        """
        return await self.oauth_client.oauth.authorize_redirect(request, redirect_uri)

    async def logout(self, user_id: int, **_):
        """
        Logout
        :param user_id:
        :param _:
        :return:
        """
        # 清除数据库中的对应数据
        try:
            await self.clear_token_info(pk=user_id)
        except ObjectDoesNotExist:
            logger.warning('User does not exist')

    async def auth(self, request: Request, **_) -> dict:
        """
        Auth
        :param request:
        :param _:
        :return:
        """
        # 进行认证处理, 认证的同时已经获取到了userinfo
        try:
            token = await self.oauth_client.oauth.authorize_access_token(request)
        except OAuthError as ex:
            logger.error('OAuth Error, exception info: %s', ex)
            raise OIDCError('OAuth Error') from ex
        userinfo = token.get('userinfo')

        # 使用email作为后端唯一性判断指标
        try:
            users = await self.repository.get(search_fields={'email': userinfo.email})
            user_id = users[0].id
            active = users[0].active
            user_obj_in = UserUpdate(name=userinfo.name,
                                     nickname=userinfo.nickname,
                                     picture=userinfo.picture,
                                     active=True)
            user = await self.repository.update_by_id(pk=user_id, obj_in=user_obj_in)
            # session表中无user_id对应数据，如有，直接删除
            if active:
                # 删除
                session = await self.session_repository.get_session_from_user_id(user_id)
                await self.session_repository.delete_by_id(session.id)

        except ObjectDoesNotExist:
            # 使用email作为后端唯一性判断指标
            user_obj_in = UserCreate(name=userinfo.name,
                                     nickname=userinfo.nickname,
                                     email=userinfo.email,
                                     email_verified=userinfo.email_verified,
                                     picture=userinfo.picture,
                                     active=True,
                                     )
            user = await self.repository.create(obj_in=user_obj_in)
        session_obj_in = SessionCreate(user_id=user.id, platform_name='gitlab', **token)
        await self.session_repository.create(obj_in=session_obj_in)
        groups = userinfo.get('groups_direct')
        await self.save_group_and_group_user_map(groups, user)
        exp = (datetime.now() + timedelta(hours=3)).timestamp()
        return {'user_id': user.id, 'user_name': user.name, 'email': user.email, 'exp': int(exp)}

    async def update_token(self, user_id: int) -> bool:
        """Check token"""

        # 进行user的获取
        # 通过user_id获取对应的id, 进而获取 oauth_token的信息进行刷新操作
        try:
            session = await self.session_repository.get_session_from_user_id(user_id=user_id)
        except ObjectDoesNotExist:
            return False
        try:
            token = await self.oauth_client.oauth.fetch_access_token(refresh_token=session.refresh_token,
                                                                     grant_type='refresh_token')
            # 刷新成功后保存token信息
            await self.session_repository.update_by_id(pk=session.id,
                                                       obj_in=SessionUpdate(**token))
        except TokenExpiredError as ex:
            logger.warning('Failed to refresh token, exception info: %s', ex)
            # 清除token相关信息
            await self.clear_token_info(pk=user_id)
            return False
        return True

    async def user(self, user_id: int, **_) -> UserSchema:
        """User"""
        # 单独获取userinfo数据
        # access_token的默认过期时间为3小时
        # 根据user交换获取 access_token
        user = await self.repository.get_by_id(user_id)
        if not user.active:
            raise AuthenticationError()
        try:
            session = await self.session_repository.get_session_from_user_id(user_id)
            userinfo = await self.oauth_client.oauth.userinfo(token={'access_token': session.access_token})
            user_obj_in = UserUpdate(name=userinfo.name,
                                     nickname=userinfo.nickname,
                                     picture=userinfo.picture)
            await self.repository.update_by_id(pk=user_id, obj_in=user_obj_in)
            await self.save_group_and_group_user_map(groups=userinfo.get('groups'), user=user)
            return user
        except Exception as ex:
            logger.warning('Get userinfo error, exception info: %s', ex)
            await self.clear_token_info(pk=user_id)
            raise AuthenticationError() from ex

    async def clear_token_info(self, pk: int, **_):
        """
        Clear token info
        :param pk:
        :param _:
        :return:
        """

        # 1. 清除 Session表中关于pk对应的user_id数据
        await self.clear_session_with_user_id(user_id=pk)
        # 2. 清除 User表中active字段进行False
        await self.repository.update_by_id(pk=pk, obj_in=UserUpdate(active=False))

    async def clear_session_with_user_id(self, user_id: int):
        """
        Clear session with user id
        :param user_id:
        :return:
        """
        try:
            session = await self.session_repository.get_session_from_user_id(user_id=user_id)
            return await self.session_repository.delete_by_id(session.id)
        except ObjectDoesNotExist:
            logger.warning('Session does not exist')

    async def save_group_and_group_user_map(self, groups: list, user: UserSchema):
        """Save group and group user map"""
        # 判断group是否已经保存
        for name in groups:
            try:
                group = await self.group_repository.get_by_name(name=name)
            except ObjectDoesNotExist:
                # 插入
                group = await self.group_repository.create(obj_in=GroupCreate(name=name))

            # group user map表逻辑处理
            try:
                await self.group_user_map_repository.get_by_group_and_user_id(group_id=group.id,
                                                                              user_id=user.id)
            except ObjectDoesNotExist:
                await self.group_user_map_repository.create(
                    obj_in=GroupUserMapCreate(group_id=group.id, user_id=user.id))
