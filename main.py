from fastapi import FastAPI
import uvicorn
from fastapi.routing import APIRouter
from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import  declarative_base
import settings
from sqlalchemy.dialects.postgresql import UUID
import uuid
import re
from fastapi import HTTPException
from pydantic import BaseModel, field_validator
from pydantic import EmailStr


########################################
# BLOCK FOR COMMON INTERACTION WITH DB #
########################################

# create async engine for interaction with db
engine = create_async_engine(settings.REAL_DATABASE_URL, future=True, echo=True)

# create session maker for interaction with db
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

##############################
# BLOCK WITH DATABASE MODELS #
##############################

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)


###########################################################
# BLOCK FOR INTERACTION WITH DATABASE IN BUSINESS CONTEXT #
###########################################################


class UserDAL:
    """Data access layer for user."""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(
            self,
            name: str,
            surname: str,
            email: str) -> User:
        new_user = User(
                name=name,
                surname=surname,
                email=email
        )
        self.db_session.add(new_user)
        await self.db_session.flush()
        return new_user

#########################
# BLOCK WITH API MODELS #
#########################


LETTER_MATCH_PATTERN = re.compile(r'^[a-яА-Яa-zA-Z\-]+$')

class TunedModel(BaseModel):
    class Config:

        orm_mode = True


class ShowUser(TunedModel):
    user_id: uuid.UUID
    name: str
    surname: str
    email: EmailStr
    is_active: bool


class UserCreate(BaseModel):
    name: str
    surname: str
    email: EmailStr

    @classmethod
    @field_validator("name")
    def validate_name(cls, name):
        if not LETTER_MATCH_PATTERN.match(name):
            raise HTTPException(status_code=422, detail="Name should contains only letters")
        return name

    @classmethod
    @field_validator("surname")
    def validate_surname(cls, surname):
        if not LETTER_MATCH_PATTERN.match(surname):
            raise HTTPException(status_code=422, detail="Surname should contains only letters")
        return surname



##########################
# BLOCK WITH API ROUTERS #
##########################

# create instance of the app
app = FastAPI(title='Larning platform')

# create router for user
user_router = APIRouter()


async def _create_new_user(body: UserCreate) -> ShowUser:
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.create_user(
                    name=body.name,
                    surname=body.surname,
                    email=body.email
            )

            return ShowUser(
                    user_id=user.user_id,
                    name=user.name,
                    surname=user.surname,
                    email=user.email,
                    is_active=user.is_active
            )


@user_router.post('/', response_model=ShowUser)
async def create_user(body: UserCreate) -> ShowUser:
    return await _create_new_user(body)


# create the instance for the routers
main_api_router = APIRouter()


# set routers to the app instance
main_api_router.include_router(user_router, prefix='/user', tags=['user'])
app.include_router(main_api_router)


if __name__ == '__main__':
    # run app on the host and port
    uvicorn.run(app, host='0.0.0.0', port=8000)