from typing import List
from pydantic import BaseModel
from pydantic import BaseModel
from typing import List    

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

class SecurityWordCompaniesBase(BaseModel):
    owner: int
    value: str
class SecurityWordCompaniesCreate(SecurityWordCompaniesBase):
    pass
class SecurityWordCompanie(SecurityWordCompaniesBase):
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    name: str
    role: str
    email: str
    employer: int
    secret: str
    valid: bool
class UserCreate(UserBase):
    pass
class User(UserBase):
    id: int
    companies: Company
    keys: List['Key'] = []
    security_words: List['SecurityWord'] = []
    sessions: List['Session'] = []    

    class Config:
        from_attributes = True

class CodeBase(BaseModel):
    owner: str
    value: str
    valid_until: str
    operation: int
class CodeCreate(CodeBase):
    pass
class Code(CodeBase):
    id: int
    class Config:
        from_attributes = True

class KeyBase(BaseModel):
    value: str
    valid_until: str
    owner: str
    registry: str
    valid: bool
    metadata: str=None
class KeyCreate(KeyBase):
    pass
class Key(KeyBase):
    users: User
    id: int
    class Config:
        from_attributes = True

class LoginAttemptBase(BaseModel):
    user: str
    registry: str
    host: str
class LoginAttemptCreate(LoginAttemptBase):
    pass
class LoginAttempt(LoginAttemptBase):
    id: int
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

class RecoverySessionBase(BaseModel):
    owner: str
    value: str
    registry: str
    expires: str
    used: bool
    client: str
class RecoverySessionCreate(RecoverySessionBase):
    pass
class RecoverySession(RecoverySessionBase):
    class Config:
        from_attributes = True


class SecurityWordBase(BaseModel):
    word: str
    owner: str
class SecurityWordCreate(SecurityWordBase):
    pass
class SecurityWord(SecurityWordBase):
    id: int
    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    owner: str
    registry: str
    valid_until: str
    valid: bool
    metadata_: str
    client: str
    value: str
    code: str
    time_created:str
class SessionCreate(SessionBase):
    pass
class Session(SessionBase):
    id: int
    users: User

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str