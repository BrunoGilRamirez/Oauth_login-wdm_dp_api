from typing import List
from pydantic import BaseModel

class CompanyBase(BaseModel):
    name: str
    phone_number: int
    registry: str
    email: str

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: int
    users: List['User'] = []

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    name: str
    role: str
    email: str
    employer: int

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    keys: List['Key'] = []
    company: Company

    class Config:
        from_attributes = True

class KeyBase(BaseModel):
    owner: int
    value: str
    registry: str
    valid_until: str

class KeyCreate(KeyBase):
    pass

class Key(KeyBase):
    id: int
    user: User

    class Config:
        from_attributes = True

class PasswordBase(BaseModel):
    value: str

class PasswordCreate(PasswordBase):
    pass

class Password(PasswordBase):
    id: int
    user: User

    class Config:
        from_attributes = True