from typing import List
from pydantic import BaseModel
from models import Companies

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
    secret: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    keys: List['Key'] = []
    company: Company

    class Config:
        from_attributes = True

class KeyBase(BaseModel):
    value: str
    valid_until: str
    owner: str
    registry: str

class KeyCreate(KeyBase):
    pass

class Key(KeyBase):
    id: int
    user: User

    class Config:
        from_attributes = True

class PasswordBase(BaseModel):
    value: str
    owner: str

class PasswordCreate(PasswordBase):
    pass

class Password(PasswordBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str