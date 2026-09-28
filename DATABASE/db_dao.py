from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from DATABASE.database import async_session_maker
from DATABASE.models import User, Coef, Robot, Dataset, Case


class BaseDAO:
    model = None

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_all(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def add(cls, **values):
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return new_instance

class UsersDAO(BaseDAO):
    model = User

class CoefDAO(BaseDAO):
    model = Coef

class RobotDAO(BaseDAO):
    model = Robot

class DatasetDAO(BaseDAO):
    model = Dataset
    @classmethod
    async def get_by_case(cls, case_id: int) -> Dataset | None:
        async with async_session_maker() as session:
            query = select(cls.model).where(Dataset.case_id == case_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()


    @classmethod
    async def upsert_for_case(cls, case_id: int, object_type: str,
        data: dict, source_file: str | None = None ) -> Dataset:
        """Создаёт или перезаписывает датасет кейса."""
        async with async_session_maker() as session:
            async with session.begin():
                ds = await session.scalar(
                    select(Dataset).where(Dataset.case_id == case_id)
                )

                if ds is None:
                    ds = Dataset(
                        case_id=case_id,
                        object_type=object_type,
                        source_file=source_file,
                        data=data,
                    )
                    session.add(ds)
                else:
                    ds.object_type = object_type
                    ds.source_file = source_file
                    ds.data = data
            await session.refresh(ds)
            return ds


class CaseDAO(BaseDAO):
    model = Case
    ALLOWED_FIELDS = {"name", "description", "robot_count", "shortened", "tariff"}
    @classmethod
    async def update_case(cls, id: int,
                          name: Optional[str] = None,
                          description: Optional[str] = None,
                          robot_count: Optional[str] = None,
                          shortened: Optional[str] = None,
                          tariff: Optional[str] = None,
                          ) -> Dataset:
        """Создаёт или перезаписывает датасет кейса и обновляет object_type в Case."""
        async with async_session_maker() as session:
            async with session.begin():
                case = await session.get(Case, id)
                if case is None:
                    raise ValueError(f"Кейс {id} не найден")

                # собираем только непустые значения
                updates = {
                    "name": name,
                    "description": description,
                    "robot_count": robot_count,
                    "shortened": shortened,
                    "tariff": tariff
                }

                changed = False
                for field, value in updates.items():
                    if value is None or field not in cls.ALLOWED_FIELDS:
                        continue
                    if field in {"robot_count", "shortened", "tariff"}:
                        value = int(value)
                    if getattr(case, field) != value:
                        setattr(case, field, value)
                        changed = True

                if not changed:
                    pass

            await session.refresh(case)
            return case