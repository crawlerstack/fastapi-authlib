"""User check"""
import logging
from datetime import datetime

from fastapi import Header
from jwt import DecodeError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_401_UNAUTHORIZED

from fastapi_authlib.config import settings
from fastapi_authlib.services import AuthService
from fastapi_authlib.utils import (decode_token, encode_token,
                                   get_authorization_scheme_param)
from fastapi_authlib.utils.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


async def check_auth_depends(
    request: Request,
    response: Response,
    www_authenticate: str = Header(None),
):
    """
    Get current user
    """
    scheme, token = get_authorization_scheme_param(www_authenticate)
    if not www_authenticate or scheme.lower() != "bearer":
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='No Authentication',
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify token validity
    user = await _verify_token(response, token)
    # Cache user basic information
    request.state.user = user


async def _verify_token(response: Response, token: str) -> dict:
    """"""
    try:
        payload = decode_token(token, settings.SECRET_KEY, settings.ALGORITHM)
        nst = payload.get('nst')
        if not nst:
            raise AuthenticationError('Malformed, missing exp parameter')

        if nst > int(datetime.utcnow().timestamp()):
            return payload

        user = await AuthService().verify_user(payload.get('user_id'))
        # Assigned only when token changes
        await _set_header_authenticate(response, user)
        return user

    except DecodeError as ex:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
            headers={"WWW-Authenticate": "Bearer"}
        ) from ex
    except (AuthenticationError, Exception) as ex:
        logger.debug('Verify token error, exception info: %s', ex)
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='Authentication failed',
            headers={"WWW-Authenticate": "Bearer"}
        ) from ex


async def _set_header_authenticate(response: Response, user: dict) -> None:
    """"""
    token = encode_token(user, settings.SECRET_KEY, settings.ALGORITHM)
    response.headers['WWW-Authenticate'] = f'Bearer {token}'
