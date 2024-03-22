from schemas import *
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Request
from crud import *
from session_management import get_session
from fastapi.security import OAuth2PasswordBearer
from starlette.datastructures import MutableHeaders
from starlette.middleware.sessions import SessionMiddleware
import os

#------------------------------------- cryptography -------------------------------------
secret_key_ps = os.getenv('secret_key_ps')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
cookie_path= os.getenv('path_cookie')
scheme = os.getenv('cryp_scheme')
pwd_context = CryptContext(schemes=[scheme], deprecated="auto") # bcrypt is the hashing algorithm used to hash the password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="key")

#------------------------------------- session -------------------------------------
session_root = get_session('.env')

#------------------------------------- database -------------------------------------
def get_db():
    db = session_root()
    try:
        yield db #yield is used to create a generator function
    finally:
        db.close()

#------------------------------------- security ------------------------------------------
def generate_user_secret(name:str, role:str, email:str, employer:str, security:str):
    #generate a hash of the user data dictionary
    data = {'name':name, 'role':role, 'email':email, 'employer':employer, 'security':security}
    return pwd_context.hash(str(data))
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)

#------------------------------------- User utilities -------------------------------------
async def register_user(request: Request, session: Session = Depends(get_db)) -> bool|str:
    form_data = await request.form()
    username = form_data['name']
    role = form_data['role']
    email = form_data['email']
    employer = form_data['employer']
    security_word = form_data['security']
    password = get_password_hash(form_data['password'])
    employer_id = get_companies_by_name(session, employer)
    if not employer_id:
        create_company(session, CompanyCreate(name=employer, phone_number=0, registry=datetime.now().strftime('%Y-%m-%d'), email='not given'))
        employer_id = get_companies_by_name(session, employer)
    secret=generate_user_secret(username, role, email, employer, security_word)
    user = UserCreate(name=username, role=role, email=email, employer=employer_id, secret=secret)
    sec_word=SecurityWordCreate(owner=secret, value=security_word)
    
    if not user_exists(session, user):
        if create_user(session, user) and create_password(session, PasswordCreate(value=password, owner=user.secret)) and create_security_word(session, sec_word):
            return True
        else:
            return False
    else:
        return "User already exists"
def authenticate_user(session: Session, username: str, password: str):
    user = get_user_by_email(session, username)
    if not user:
        return False
    if not verify_password(password, get_password_by_owner(session, user.secret).value):
        return False
    return user
async def get_current_user(request: Request, session: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = await oauth2_scheme(request)
    except:
        raise credentials_exception

    try:
        key = get_keys_by_value(session, token)
        if key:
            payload = jwt.decode(token, secret_key_ps, algorithms=[ALGORITHM])
            secret: str = payload.get("sub")
            user= get_all_user_info(session, secret=secret)
            if user:
                return user
            else:
                raise credentials_exception
        else:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

#------------------------------------- token utilities -------------------------------------
def create_access_token(session: Session,data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key_ps, algorithm=ALGORITHM)
    Key_ = KeyCreate(owner=to_encode['sub'], 
                        value=encoded_jwt, 
                        registry=datetime.now().strftime('%Y-%m-%d'), 
                        valid_until=expire.strftime('%Y-%m-%d')
                    )
    if create_key(session, Key_):
        return encoded_jwt
    else:
        return False
def validate_token(token: str|None, session: Session) -> bool:
    if isinstance(token, str):
        key = get_keys_by_value(session, token)
        if key:
            payload = jwt.decode(token, secret_key_ps, algorithms=[ALGORITHM])
            secret: str = payload.get("sub")
            user= get_all_user_info(session, secret=secret)
            return user
        else:
            return False
    else:
        return False
def request_add_token(request: Request, token: str):
    new_headers = MutableHeaders(request._headers)
    new_headers["Authorization"] = f"Bearer {token}"
    request._headers = new_headers
    request.scope.update(headers=request.headers.raw)
    return request
def request_remove_token(request: Request):
    new_headers = MutableHeaders(request._headers)
    new_headers.pop("Authorization")
    request._headers = new_headers
    request.scope.update(headers=request.headers.raw)
    return request
#------------------------------------- session utilities -------------------------------------
def validate_user_session(request: Request, db: Session) -> bool:
    token = request.session.get("access_token")
    if token:
        return get_session_by_value(db, token)
    else:
        return False
def delete_user_session(request: Request, db: Session) -> bool:
    token = request.session.get("access_token")
    if token:
        return delete_session(db, token)
    else:
        return False
def create_user_session(db: Session, token: str, user: UserCreate):
    session = SessionCreate(owner=user.secret, value=token, registry=datetime.now().strftime('%Y-%m-%d'))
    if create_session(db, session):
        return True
    else:
        return False