from pydantic import BaseModel, EmailStr, Field


class SUserRegister(BaseModel):
    email: EmailStr = Field(description="Электронная почта")
    password: str = Field(min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")
    name: str = Field(min_length=3, max_length=50, description="Имя, от 3 до 50 символов")


class SUserRegisterHashed(BaseModel):
    email: EmailStr = Field(description="Электронная почта")
    hashed_password: str = Field(description="Пароль, шифрованный")
    name: str = Field(min_length=3, max_length=50, description="Имя, от 3 до 50 символов")


class SUserAuth(BaseModel):
    email: EmailStr = Field(description="Электронная почта")
    password: str = Field(min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")

class SCoefCreate(BaseModel):
    name : str = Field(description="Электронная почта")
    min : float = Field(description="Минимальное значение")
    base : float= Field(description="Базовое значение")
    max : float = Field(description="Максимальное значение")
    from_dataset : bool = Field(description="Взято из датасета")