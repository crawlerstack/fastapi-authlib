# fastapi-authlib

fastapi-authlib provides easy integration between FastAPI and openid connection in your application.
Provides the initialization and dependencies of oidc, aiming to unify authentication management and
reduce the difficulty of use.

## Installing

install and update using pip:

```shell
pip install fastapi-authlib
```

## Examples

### Create settings for examples, `settings.py`

```python
config = {
    'database': 'sqlite+aiosqlite:////tmp/oidc_demo.db',
    'oauth_client_id': 'client_id',
    'oauth_client_secret': 'client_secret',
    'oauth_conf_url': 'conf_url',
    'secret_key': 'secret_key',
    'router_prefix': '',
}
```

settings.py is a simple configuration file of the use case, which mainly provides the database link,
the necessary parameters used by oidc, the session authentication key and the routing prefix.

Please use your authentication server configuration to populate the parameter value prefixed with oauth.
Other parameters can be modified according to the actual situation.

### Create api route, `api_router.py`

```python
from fastapi import APIRouter
from starlette.requests import Request

router = APIRouter()


@router.get('/index')
async def index(
        *,
        request: Request,
):
    """
    User
    """
    user_info = request.state.user
    return {'name': user_info.get('user_name')}
```

For authenticated api, you can use `request.state.user` to get the current user.

### Create oidc demo entry, `main.py`

```python
"""main"""
import uvicorn
from fastapi import Depends, FastAPI
from fastapi_sa.database import db
from fastapi_sa.middleware import DBSessionMiddleware

from fastapi_authlib.oidc import OIDCClient
from fastapi_authlib.utils.auth_dependency import check_auth_depends
from api_router import index
from .settings import config


class OIDCDemo:
    """OIDCDemo"""

    def __init__(self, settings: dict):
        self.settings = settings
        self.router_prefix = self.settings.get('router_prefix')

    def run(self):
        """Run"""
        # Early environment initialization
        app = FastAPI(title='FastAPIOIDCSupportDemo', version='0.1.0')
        db.init(self.settings.get('database'))

        # Oidc environment initialization
        client = OIDCClient(
            app=app,
            **config
        )
        # If you only init app, you should use init_app() instead
        client.init_oidc()

        # Customize the environment initialization
        # add dependencies to the interface that needs to be authenticated
        app.include_router(
            index.router,
            tags=['index'],
            prefix=config.get('router_prefix'),
            dependencies=[Depends(check_auth_depends)]
        )
        app.add_middleware(DBSessionMiddleware)
        return app


if __name__ == '__main__':
    client_app = OIDCDemo(config).run()
    uvicorn.run(client_app, host="0.0.0.0", port=8001)

```

### Use Step

- Create app and init db
- Init the environment of oidc, If you don't want to do data migration, you should use init_app method.
  Usually database migration and oidc initialization are performed together
- Register routing and other middleware, the DBSessionMiddleware is required
- Start a fastapi server with uvicorn or other

### Other

Provide the following apis
- /login
- /auth
- /logout
- /users

## Based on

- [FastAPI](https://github.com/tiangolo/fastapi)
- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy)
- [Fastapi-sa](https://github.com/whg517/fastapi-sa)
- [Authlib](https://github.com/lepture/authlib)

## Develop

You may need to read the [develop document](./docs/development.md) to use SRC Layout in your IDE.
