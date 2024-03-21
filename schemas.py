from typing import List
from pydantic import BaseModel
from models import Companies
from pydantic import BaseModel
from typing import List    

class CompaniesBase(BaseModel):
    name: str
    phone_number: int
    registry: str
    email: str
class CompaniesCreate(CompaniesBase):
    pass
class Company(CompaniesBase):
    id: int
    users: List['User'] = []

    class Config:
        from_attributes = True

class SecurityWordCompaniesBase(BaseModel):
    owner: int
    value: str
class SecurityWordCompaniesCreate(SecurityWordCompaniesBase):
    pass
class SecurityWordCompanie(SecurityWordCompaniesBase):
    class Config:
        from_attributes = True

class UsersBase(BaseModel):
    name: str
    role: str
    email: str
    employer: int
    secret: str
class UsersCreate(UsersBase):
    pass
class User(UsersBase):
    id: int
    companies: Company
    keys: List['Key'] = []

    class Config:
        from_attributes = True

class KeysBase(BaseModel):
    value: str
    valid_until: str
    owner: str
    registry: str
class KeysCreate(KeysBase):
    pass
class Key(KeysBase):
    users: User
    id: int
    class Config:
        from_attributes = True

class PasswordsBase(BaseModel):
    value: str
    owner: str
class PasswordsCreate(PasswordsBase):
    pass
class Password(PasswordsBase):
    id: int

    class Config:
        from_attributes = True

class SecurityWordBase(BaseModel):
    word: str
    owner: str
class SecurityWordsCreate(SecurityWordBase):
    pass
class SecurityWord(SecurityWordBase):
    class Config:
        from_attributes = True

class SessionsBase(BaseModel):
    owner: str
    registry: str
    valid_until: str
    valid: bool
    metadata_: str
    value: str
class SessionsCreate(SessionsBase):
    pass
class Session(SessionsBase):
    id: int
    users: User

    class Config:
        from_attributes = True
class Token(BaseModel):
    access_token: str
    token_type: str