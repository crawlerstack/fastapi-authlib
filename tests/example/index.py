"""User"""
from fastapi import APIRouter
from starlette.requests import Request

router = APIRouter()


@router.get('/index')
async def index(
    *,
    request: Request,
):
    """
    Index
    """
    user_info = request.state.user
    return {'name': user_info.get('user_name')}
