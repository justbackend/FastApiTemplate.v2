import uuid
from typing import Any

import bcrypt
from passlib.context import CryptContext
from pydantic import SecretStr
from sqlalchemy import String, LargeBinary, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, Mapped

from app.models.base import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, primary_key=True
    )
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    _password: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    @property
    def password(self):
        return self._password.decode("utf-8")

    @password.setter
    def password(self, password: SecretStr):
        _password_string = password.get_secret_value()
        self._password = bcrypt.hashpw(
            _password_string.encode("utf-8"), bcrypt.gensalt()
        )

    def check_password(self, password: SecretStr):
        return pwd_context.verify(password.get_secret_value(), self.password)

    @classmethod
    async def find(cls, database_session: AsyncSession, where_conditions: list[Any]):
        _stmt = select(cls).where(*where_conditions)
        _result = await database_session.execute(_stmt)
        return _result.scalars().first()
