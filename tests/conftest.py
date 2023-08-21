"""Test config"""
import logging
import os
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi_sa.database import db
from fastapi_sa.middleware import DBSessionMiddleware
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.testclient import TestClient
from uvicorn import Config, Server

from fastapi_authlib.models import (BaseModel, Group, GroupUserMap, Session,
                                    User)
from fastapi_authlib.oidc import OIDCClient

logger = logging.getLogger(__name__)


@pytest.fixture()
def settings():
    """settings fixture"""
    # 默认值设置
    oidc_settings = {
        'oauth_client_id': 'client_id',
        'oauth_client_secret': 'client_secret',
        'oauth_conf_url': 'conf_url',
        'secret_key': 'secret_key',
        'platform': 'platform',
    }
    return oidc_settings


@pytest.fixture()
def db_url():
    """db url"""
    return "sqlite+aiosqlite:////tmp/oidc_test.db"


@pytest.fixture()
def db_session_ctx():
    """db session context"""
    token = db.set_session_ctx()
    yield
    db.reset_session_ctx(token)


@pytest.fixture()
async def session(db_session_ctx):
    """session fixture"""
    async with db.session.begin():
        yield db.session


@pytest.fixture(autouse=True)
async def migrate(db_url):
    """migrate fixture"""
    os.makedirs(Path(db_url.split('///')[1]).parent, exist_ok=True)
    _engine = create_async_engine(db_url)
    async with _engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)
    await _engine.dispose()


async def server_start(app):
    """Server start"""

    _uvicorn_server = Server(Config(app))

    config = _uvicorn_server.config
    if not config.loaded:
        config.load()

    _uvicorn_server.lifespan = config.lifespan_class(config)
    await _uvicorn_server.startup()

    return _uvicorn_server


async def server_stop(uvicorn_server):
    """Server stop"""
    if hasattr(uvicorn_server, 'servers'):
        await uvicorn_server.shutdown()


@pytest.fixture()
def init_oidc_demo(migrate, settings, db_url):
    """init oidc demo"""
    logger.debug('Starting OIDCClient!!!')
    settings.setdefault('database', db_url)
    app = FastAPI()
    db.init(db_url)
    OIDCClient(app, **settings).init_app()
    app.add_middleware(DBSessionMiddleware)
    return app


@pytest.fixture(autouse=True)
async def oidc_demo_server(init_oidc_demo):
    """spider keeper server fixture"""
    uvicorn_server = await server_start(init_oidc_demo)
    yield uvicorn_server
    await server_stop(uvicorn_server)
    logger.debug('Stopping OIDCClient!!!')


@pytest.fixture()
async def client(oidc_demo_server):
    """client"""

    _client = TestClient(
        oidc_demo_server.config.app,
        raise_server_exceptions=False
    )
    yield _client


@pytest.fixture()
async def init_user():
    """Init user fixture."""
    async with db():
        users = [
            User(
                name="user1", nickname="user1", email="user1@example.com", email_verified=True, picture='picture.jpg',
                active=True
            ),
            User(
                name="user2", nickname="user2", email="user2@example.com", email_verified=True, picture='picture.jpg',
                active=False
            )
        ]
        db.session.add_all(users)
        await db.session.flush()


@pytest.fixture()
async def init_session(init_user):
    """Init session fixture."""
    async with db():
        oauth_tokens = [
            Session(
                platform_name='gitlab', token_type='Bearer', access_token='access_token1',
                refresh_token='refresh_token', expires_at=1681285750, user_id=1
            ),
            Session(
                platform_name='gitlab', token_type='Bearer', access_token='access_token1',
                refresh_token='refresh_token', expires_at=1681285750, user_id=2
            )
        ]
        db.session.add_all(oauth_tokens)
        await db.session.flush()


@pytest.fixture()
async def init_group():
    """Init group fixture."""
    async with db():
        users = [
            Group(name="user-groups/python-team"),
            Group(name="user-groups/java-team"),
        ]
        db.session.add_all(users)
        await db.session.flush()


@pytest.fixture()
async def init_group_user_map(init_user, init_group):
    """Init group user map fixture."""
    async with db():
        users = [
            GroupUserMap(group_id=1, user_id=1),
        ]
        db.session.add_all(users)
        await db.session.flush()
