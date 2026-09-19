from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from DATABASE.database import Base

class User(Base):
    __tablename__ = 'users'

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False)

