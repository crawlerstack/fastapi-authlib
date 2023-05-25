"""User check"""
import time
from datetime import datetime, timedelta

from fastapi import Cookie
from starlette.exceptions import HTTPException
from starlette.requests import Request

from fastapi_authlib.services import AuthService


async def check_auth_session(request: Request, session_id: str = Cookie(None)):
    """
    Get current user
    """
    if session_id:
        session = request.session
        if 'user' in session:
            user = session.get('user')
            if user.get('exp') < time.time():
                status = await AuthService().update_token(user_id=user.get('user_id'))
                if not status:
                    request.session.pop('user')
                    raise HTTPException(status_code=401, detail='The authentication expires')
                exp = (datetime.now() + timedelta(hours=3)).timestamp()
                user['exp'] = int(exp)
                request.session['user'] = user
            request.state.user = user
            return
    raise HTTPException(status_code=401, detail='No Authentication')
