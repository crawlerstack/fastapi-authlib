"""logout"""

from fastapi import APIRouter, Depends
from starlette.requests import Request

from fastapi_authlib.messages.base import BaseMessage
from fastapi_authlib.services import AuthService

router = APIRouter()


@router.get('/logout', response_model=BaseMessage)
async def logout(
    request: Request,
    service: AuthService = Depends()
):
    """
    Logout
    """
    user_info = request.state.user
    await service.logout(user_info.get('user_id'))
    request.session.clear()
    return {'message': 'Logout successful'}
