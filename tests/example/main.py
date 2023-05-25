"""main"""
import uvicorn
from fastapi import Depends, FastAPI
from fastapi_sa.database import db
from fastapi_sa.middleware import DBSessionMiddleware

from fastapi_authlib.oidc import OIDCClient
from fastapi_authlib.utils.check_user_depend import check_auth_session
from tests.example import index

config = {
    'database': 'sqlite+aiosqlite:////tmp/oidc_demo.db',
    'oauth_client_id': 'client_id',
    'oauth_client_secret': 'client_secret',
    'oauth_conf_url': 'conf_url',
    'session_secret': 'secret_key',
    'router_prefix': '/api/v1',
}


class OIDCDemo:
    """OIDCDemo"""

    def __init__(self, settings: dict):
        self.settings = settings
        self.router_prefix = self.settings.get('router_prefix')

    def run(self):
        """Run"""
        # 前期的环境初始化
        app = FastAPI(title='FastAPIOIDCSupportDemo', version='0.1.0')
        db.init(self.settings.get('database'))

        # oidc 环境初始化
        client = OIDCClient(
            app=app,
            oauth_client_id=self.settings.get('oauth_client_id'),
            oauth_client_secret=self.settings.get('oauth_client_secret'),
            oauth_conf_url=self.settings.get('oauth_conf_url'),
            database=self.settings.get('database'),
            session_secret=self.settings.get('session_secret'),
            router_prefix=self.router_prefix
        )
        client.init_oidc()

        # 自定义环境初始化
        app.include_router(index.router, tags=['index'], prefix=self.router_prefix,
                           dependencies=[Depends(check_auth_session)])
        app.add_middleware(DBSessionMiddleware)
        return app


if __name__ == '__main__':
    client_app = OIDCDemo(config).run()
    uvicorn.run(client_app, host="192.168.6.15", port=8001)
