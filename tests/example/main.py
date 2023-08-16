"""main"""
import uvicorn
from fastapi import Depends, FastAPI
from fastapi_sa.database import db
from fastapi_sa.middleware import DBSessionMiddleware

from fastapi_authlib.oidc import OIDCClient
from fastapi_authlib.utils.auth_dependency import check_auth_depends
from tests.example import index

config = {
    'database': 'sqlite+aiosqlite:////tmp/oidc_demo.db',
    'oauth_client_id': 'd4e0ba60d9b001fff05252f2cc9b9a2f0ba2a550bcca217bbf110d1d1d8eee59',
    'oauth_client_secret': 'efb715ee218f48483b9cda3ffee499eb1fd12d5025f88c535eff00eb1b9a0cff',
    'oauth_conf_url': 'http://gitlab.zncdata.net/.well-known/openid-configuration',
    'secret_key': 'secret_key',
    'router_prefix': '/api/v1',
    'platform': 'gitlab'
}


class OIDCDemo:
    """OIDCDemo"""

    def __init__(self, settings: dict):
        self.settings = settings
        self.router_prefix = self.settings.get('router_prefix')

    def run(self):
        """Run"""
        # 前期的环境初始化
        app = FastAPI(title='FastAPIAuthlibDemo', version='0.1.0')
        db.init(self.settings.get('database'))

        # oidc 环境初始化
        client = OIDCClient(
            app=app,
            oauth_client_id=self.settings.get('oauth_client_id'),
            oauth_client_secret=self.settings.get('oauth_client_secret'),
            oauth_conf_url=self.settings.get('oauth_conf_url'),
            database=self.settings.get('database'),
            secret_key=self.settings.get('secret_key'),
            router_prefix=self.router_prefix,
            platform=self.settings.get('platform'),
        )
        client.init_oidc()

        # 自定义环境初始化
        app.include_router(
            index.router,
            tags=['index'],
            prefix=self.router_prefix,
            dependencies=[Depends(check_auth_depends)]
        )

        app.add_middleware(DBSessionMiddleware)
        return app


if __name__ == '__main__':
    client_app = OIDCDemo(config).run()
    uvicorn.run(client_app, host="0.0.0.0", port=8001)
