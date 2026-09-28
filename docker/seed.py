import asyncio

from sqlalchemy import func, select

from DATABASE.database import async_session_maker, engine
from DATABASE.models import Case, Coef, Dataset, Robot, User
from LOGIN.auth import get_password_hash

SYSTEM_EMAIL = "system@robotect.local"


def cell(value):
    text = str(value)
    return {"unit": "", "base": text, "min": "", "max": "", "note": "", "scenario": text}


COEFFICIENTS = [
    ("k_FOT", 0.8, 1.0, 1.2),
    ("k_load", 0.8, 1.0, 1.2),
    ("k_res", 0.8, 1.0, 1.2),
    ("k_PO", 0.8, 1.0, 1.2),
    ("k_integ", 0.8, 1.0, 1.2),
    ("k_PNR", 0.8, 1.0, 1.2),
    ("k_learn", 0.8, 1.0, 1.2),
    ("k_service", 0.8, 1.0, 1.2),
    ("k_lic", 0.8, 1.0, 1.2),
    ("k_conn", 0.8, 1.0, 1.2),
    ("k_cons", 0.8, 1.0, 1.2),
    ("k_rep", 0.8, 1.0, 1.2),
    ("horizon", 3, 5, 7),
    ("inflation", 0.02, 0.05, 0.08),
]


async def wait_database():
    for _ in range(30):
        try:
            async with engine.connect() as connection:
                await connection.execute(select(1))
            return
        except Exception:
            await asyncio.sleep(1)
    raise RuntimeError("База не ответила")


async def main():
    await wait_database()
    from DATABASE.database import Base
    import DATABASE.models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        user = await session.scalar(select(User).where(User.email == SYSTEM_EMAIL))
        if user is None:
            user = User(
                name="System",
                email=SYSTEM_EMAIL,
                hashed_password=get_password_hash("not-a-jury-login"),
            )
            session.add(user)
            await session.flush()

        if await session.scalar(select(func.count()).select_from(Coef)) == 0:
            session.add_all([
                Coef(name=name, min=low, base=base, max=high, from_dataset=False)
                for name, low, base, high in COEFFICIENTS
            ])

        if await session.get(Robot, 1) is None:
            session.add(Robot(
                id=1,
                model="AMR-200",
                capacity=200,
                cost=1000000,
                accum_life=5,
                mass=180,
                size_x=950,
                size_y=650,
                size_z=300,
                max_speed=1.5,
                navigation_type="Лидар",
                charge_time=0.33,
                work_time=8,
                efficiency=50,
                accuracy=10,
                from_dataset="каталог сайта",
            ))

        case = await session.get(Case, 1)
        if case is None:
            case = Case(
                id=1,
                user_id=user.id,
                name="Кейс 1",
                object_type="Склад",
                description="",
                robot_count=1,
                tariff=0,
                shortened=0,
            )
            session.add(case)
            await session.flush()

        dataset = await session.scalar(select(Dataset).where(Dataset.case_id == case.id))
        if dataset is None:
            session.add(Dataset(
                case_id=case.id,
                object_type="Склад",
                source_file="docker",
                data={
                    "Площадь рабочих зон": cell(15000),
                    "Режим работы": cell(16),
                    "Средняя масса грузовой единицы": cell(40),
                    "Входящие операции": cell(400),
                    "Внутрискладские операции": cell(900),
                    "Исходящие операции": cell(500),
                },
            ))

        await session.commit()
        print(f"seed ready, case_id={case.id}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
