from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Index, BigInteger, Integer, ForeignKey, DateTime, func, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from DATABASE.database import Base

class User(Base):
    __tablename__ = 'users'

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True))

    # связи
    cases: Mapped[List["Case"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
        order_by="Case.updated_at.desc()")


class Coef(Base):
    __tablename__ = 'coefficients'

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    min: Mapped[float] = mapped_column()
    base: Mapped[float] = mapped_column(nullable=False)
    max: Mapped[float] = mapped_column()
    from_dataset: Mapped[bool] = mapped_column(nullable=False)

class Robot(Base):
    __tablename__ = 'robots'

    model: Mapped[str] = mapped_column()
    capacity:  Mapped[int] = mapped_column(nullable=False)
    cost: Mapped[int] =  mapped_column(nullable=False)
    accum_life: Mapped[int] = mapped_column(nullable=False)
    mass: Mapped[int] = mapped_column(nullable=False)
    length: Mapped[int] = mapped_column(nullable=False)
    width: Mapped[int] = mapped_column(nullable=False)
    height: Mapped[int] = mapped_column(nullable=False)
    max_speed: Mapped[float] = mapped_column(nullable=False)
    navigation_type: Mapped[str] = mapped_column(nullable=False)
    charge_time: Mapped[float] = mapped_column(nullable=False)
    work_time: Mapped[float] = mapped_column(nullable=False)
    efficiency: Mapped[float] = mapped_column(nullable=False)
    accuracy: Mapped[float] = mapped_column(nullable=False)
    operationg_conditions: Mapped[str] = mapped_column(nullable=False)

class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_case_user_name"),
        Index("idx_cases_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,
                                    autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    robot_count: Mapped[int] = mapped_column()
    tariff: Mapped[int] = mapped_column()
    shortened: Mapped[int] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now())

    # связи
    user: Mapped[User] = relationship(back_populates="cases")
    dataset: Mapped[Optional["Dataset"]] = relationship(
        back_populates="case",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )


class Dataset(Base):
    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint("case_id", name="uq_dataset_case"),     # ← 1:1
        Index("idx_datasets_data", "data", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,
                                    autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False, unique=True,                             # ← тоже можно
    )
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_file: Mapped[Optional[str]] = mapped_column(String(512))
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now())                                     # ← при апдейте

    case: Mapped["Case"] = relationship(back_populates="dataset")