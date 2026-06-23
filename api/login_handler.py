from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.models import Token
from db.dals import UserDAL
from db.session import get_db
from hashing import Hasher

login_router = APIRouter()

async def _get_user_by_email_for_auth(email: str, db: AsyncSession):
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            return await user_dal.get_user_by_email(
                email=email
            )

async def authenticate_user(email: str, password: str, db: AsyncSession):
    user = await _get_user_by_email_for_auth(email=email, db=db)
    if user is None:
        return False
    if not Hasher.verify_password(password, user.hashed_password):
        return False
    return user

@login_router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password"
                            )
    access_token_expires = timedelta(minutes=60)  # ← замените на settings.ACCESS_TOKEN_EXPIRE_MINUTES
    access_token = create_access_token(
        data={"sub": user.email, "other_custom_data": [1, 2, 3, 4]},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}
