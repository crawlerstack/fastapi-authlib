"""login"""

from fastapi import APIRouter, Depends
from starlette.requests import Request
from starlette.responses import Response

from fastapi_authlib.messages.base import BaseMessage
from fastapi_authlib.services import AuthService
from fastapi_authlib.utils.auth_dependency import set_header_authenticate

router = APIRouter()


@router.get('/login')
async def login(
    callback: str,
    request: Request,
    service: AuthService = Depends()
):
    """
    Login
    """
    return await service.login(request, callback)


@router.get('/auth', response_model=BaseMessage)
async def auth(
    request: Request,
    response: Response,
    service: AuthService = Depends(),
):
    """
    Auth
    """
    user = await service.auth(request)
    # clear session, three-party authentication uses cookies
    request.session.clear()
    await set_header_authenticate(response, user)
    return {'message': 'authentication successful.'}
