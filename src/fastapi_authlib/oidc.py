"""OIDC"""
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI
from starlette.middleware.sessions import SessionMiddleware

from fastapi_authlib.config import settings
from fastapi_authlib.rest_api.handler import init_exception_handler
from fastapi_authlib.rest_api.routers import login, logout, user
from fastapi_authlib.utils.check_user_depend import check_auth_session


class OIDCClient:
    """OIDC"""

    def __init__(self, app: FastAPI, oauth_client_id: str, oauth_client_secret: str, oauth_conf_url: str,
                 database: str, session_secret: str, router_prefix: str = '', **kwargs):
        """
        Init OIDC basic configuration
        :param app:
        :param oauth_client_id:
        :param oauth_client_secret:
        :param oauth_conf_url:
        :param database:
        :param session_secret:
        :param router_prefix:
        :param kwargs:
        """
        if database:
            settings.set('DATABASE', database)
        else:
            raise TypeError('Database parameter is required parameter')

        if all([oauth_client_id, oauth_client_secret, oauth_conf_url]):
            settings.set('OAUTH_CLIENT_ID', oauth_client_id)
            settings.set('OAUTH_CLIENT_SECRET', oauth_client_secret)
            settings.set('OAUTH_CONF_URL', oauth_conf_url)
        else:
            raise TypeError('Missed Oauth parameters, it is required parameters')

        if app:
            self.app = app
        else:
            raise TypeError('App parameter is required parameter')

        if session_secret:
            self.session_secret = session_secret
        else:
            raise TypeError('Session secret is required parameter')

        self.route_prefix = router_prefix

    @staticmethod
    def migrate_db():
        """
        Migrates the database
        :return:
        """
        alembic_cfg = Config(Path(Path(__file__).parent, 'alembic/alembic.ini'))
        alembic_cfg.set_main_option("script_location", "fastapi_authlib:alembic")
        command.upgrade(alembic_cfg, 'head')

    def init_app(self):
        """
        Init app
        :return:
        """
        # init middleware
        self.app.add_middleware(SessionMiddleware,
                                secret_key=self.session_secret,
                                session_cookie='session_id',
                                max_age=60 * 60 * 4,
                                )

        # init handle
        init_exception_handler(self.app)

        # init route
        self.app.include_router(login.router, tags=['login'], prefix=self.route_prefix)
        self.app.include_router(logout.router,
                                tags=['logout'],
                                prefix=self.route_prefix,
                                dependencies=[Depends(check_auth_session)]
                                )
        self.app.include_router(user.router, tags=['user'], prefix=self.route_prefix,
                                dependencies=[Depends(check_auth_session)])

    def init_oidc(self):
        """Init oidc"""
        self.migrate_db()
        self.init_app()
