"""User"""

from fastapi_authlib.models import User
from fastapi_authlib.repository.base import BaseRepository
from fastapi_authlib.schemas.user import UserCreate, UserSchema, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate, UserSchema]):
    """
    User repository
    """
    model = User
    model_schema = UserSchema
