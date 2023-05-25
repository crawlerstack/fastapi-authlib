"""login"""

from urllib.parse import urlencode

from fastapi import APIRouter, Depends
from starlette.requests import Request
from starlette.responses import RedirectResponse

from fastapi_authlib.services import AuthService

router = APIRouter()


@router.get('/login')
async def login(
    request: Request,
    service: AuthService = Depends()
):
    """
    Login
    """
    redirect_uri = request.url_for('auth')
    url = f"{str(redirect_uri)}{'?' + urlencode(request.query_params) if request.query_params else ''}"
    return await service.login(request, url)


@router.get('/auth')
async def auth(
    callback_url: str,
    request: Request,
    service: AuthService = Depends(),
):
    """
    Auth
    """
    user = await service.auth(request)
    request.session.clear()
    request.session['user'] = user
    return RedirectResponse(url=callback_url)
