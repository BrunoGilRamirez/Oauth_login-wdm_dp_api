from models.schemas import *
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Request
from models.crud import *
from emailsender.sender import Sender
from session_management import get_session
from fastapi.security import OAuth2PasswordBearer
from starlette.datastructures import MutableHeaders
import secrets
import traceback
import os

#------------------------------------- cryptography -------------------------------------
session_root = get_session('.env.local')
secret_key_ps = os.getenv('secret_key_ps')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
cookie_path= os.getenv('path_cookie')
scheme = os.getenv('cryp_scheme')
httpsdir = os.getenv('httpsdir')
pwd_context = CryptContext(schemes=[scheme], deprecated="auto") # bcrypt is the hashing algorithm used to hash the password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="key")
messenger = Sender(os.getenv('email'), os.getenv('password'))

#------------------------------------- session -------------------------------------

#------------------------------------- database -------------------------------------
def get_db():
    db = session_root()
    try:
        yield db #yield is used to create a generator function
    finally:
        db.close()

#------------------------------------- security ------------------------------------------
def create_session_secret(secret:str, metadata:str, client:str)->list[str,str,datetime]:
    #generate a random number  of 20 digits
    code = str(secrets.randbelow(10**20))
    time_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {'secret':secret, 'metadata':metadata, 'client':client, 'session_code':code, 'time_created':time_created}
    return pwd_context.hash(str(data)), code, time_created

def generate_user_secret(name:str, role:str, email:str, employer:str, security:str):
    #generate a hash of the user data dictionary
    data = {'name':name, 'role':role, 'email':email, 'employer':employer, 'security':security}
    return pwd_context.hash(str(data))
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)
def check_if_still_on_valid_time(valid_until: str)->bool:
    if datetime.now() < valid_until:
        return True
    else:
        return False
def lockdown_user(db: Session, code: str, current_password: str, new_password: str, secret:str)->str|bool:
    code = get_code_by_value_operation_owner(db, code, 1, secret)
    print(f"Code: {code}")
    still_valid=check_if_still_on_valid_time(code.valid_until) if isinstance(code, Codes) else False
    if isinstance(code, Codes) and still_valid:
        secret = code.owner
        keys = get_keys_by_owner(db, secret)
        sessions = get_sessions_by_owner(db, secret)
        print(f"Keys: {keys}")
        print(f"Sessions: {sessions}")
        if verify_password(current_password, get_password_by_owner(db, secret).value):
            #update the valid field of all the keys and sessions to False
            if isinstance(keys, list) and isinstance(sessions, list):
                if update_valid_list_of_sessions(db, sessions) and update_valid_list_of_keys(db, keys) and delete_code(db, code):
                    if update_password(db, secret,get_password_hash(new_password)):
                        return True
    return False
def generate_security_code(db: Session, user: str, operation:int, return_time: bool=False)->bool|int|tuple[int,datetime]:
    '''Generates a random code and stores it in the database with the user as the owner. The code is valid for 5 minutes.
    Returns the code if successful, otherwise returns False.
    - db: the database session
    - user: the user's secret
    - operation: the operation to be performed with the code. 1 for password reset, 2 for user verification.
    - return_time: if True, returns the code and the time it is valid until. Otherwise, returns only the code.'''
    code = str(secrets.randbelow(10**8)) #generate a random 8-digit code
    time=datetime.now() + timedelta(minutes=5, seconds=1) 
    time_set=time.strftime('%Y-%m-%d %H:%M:%S')
    if create_code(db, CodeCreate(owner=user, value=code,valid_until=time_set, operation=operation)):
        if return_time: return code, time
        return code
    else:
        return False

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
    user = UserCreate(name=username, role=role, email=email, employer=employer_id, secret=secret, valid=False)
    sec_word=SecurityWordCreate(owner=secret, word=security_word)
    encoded_secret = encode_secret(secret)
    if not user_exists(session, user):
        if messenger.send_template_email(recipient=email,
                                         subject="Welcome to Weidmüller Data Product API",
                                         template="welcome.html",
                                         context={"username": username, 
                                                  "creation_date": datetime.now().strftime("%d/%m/%Y"),
                                                  "verification_link": f"{request.base_url}UI/verify/{encoded_secret}"
                                                 }
                                        ):
            if create_user(session, user) and create_password(session, PasswordCreate(value=password, owner=user.secret)) and create_security_word(session, sec_word):
                return secret
            else:
                return False
    else:
        return "User already exists"
def authenticate_user(session: Session, username: str, password: str)-> bool|Users:
    user = get_user_by_email(session, username)
    if not user:
        return False
    if not verify_password(password, get_password_by_owner(session, user.secret).value):
        return False
    return user
def auth_password_reset(session: Session, secret:str, code: str, new_password: str, current_password:str)->bool:
    user = get_all_user_info(session, secret=secret)
    code = get_code_by_value(session, code)
    still_valid=check_if_still_on_valid_time(code.valid_until) if isinstance(code, Codes) else False
    verification = verify_password(current_password, get_password_by_owner(session, user.secret).value)
    print(f"User: {user}, Code: {code}, Still valid: {still_valid}, Verification: {verification}")
    if isinstance(user, User) and isinstance(code, Codes) and still_valid and verification:
        print (f"if statement: {user.secret} == {code.owner}: {user.secret == code.owner} type user secret: {type(user.secret)} type code owner: {type(code.owner)}")
        if user.secret == code.owner:
            print("User and code owner match")
            flag_update = update_password(session, user.secret, get_password_hash(new_password))
            flag_delete = delete_code(session, code)
            print(f"Update: {flag_update}, Delete: {flag_delete}")
            if flag_update and flag_delete:
                return True

    return False
async def get_current_user_API(token: str = Depends(oauth2_scheme), session: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token does not exist or is no longer valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        key = get_keys_by_value(session, token)
        if isinstance(key,Keys) and key.valid:
            if check_if_still_on_valid_time(key.valid_until) is False:
                raise credentials_exception
            else:
                user = decode_and_verify(key.owner, session)
                print(type(user))
                if isinstance(user, User):
                    return True #the user is authenticated
    except:
        traceback.print_exc()
        raise credentials_exception

async def get_user_secret_Oa2(token: str = Depends(oauth2_scheme), session: Session = Depends(get_db))->str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token does not exist or is no longer valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        sess = get_session_by_value(session, token)
        if isinstance(sess,Sessions):
            if check_if_still_on_valid_time(sess.valid_until):
                user = decode_and_verify(sess.owner, session)
                print(type(user))
                if isinstance(user, User):
                    return user
    except:
        traceback.print_exc()    
    raise credentials_exception

async def get_current_user(request: Request, session: Session = Depends(get_db)):
    
    try:
        token = await oauth2_scheme(request)
    except:
        raise False
    try:
        key = get_keys_by_value(session, token)
    except:
        pass
    try:
        key = get_session_by_value(session, token)
    except:
        pass
    if key and key.valid and check_if_still_on_valid_time(key.valid_until):
        return decode_and_verify(key.owner, session)
    else:
        return False
    
def decode_and_verify(secret: str, db: Session):
    try:
        user= get_all_user_info(db, secret=secret)
        return user
    except Exception as e:
        traceback.print_exc()
        return False
def encrypt_data(data: dict, expires_delta: timedelta):
    expire = datetime.now(timezone.utc) + expires_delta
    data.update({"exp": expire})
    encoded = jwt.encode(data, secret_key_ps, algorithm=ALGORITHM)
    encrypted = pwd_context.hash(encoded)
    return encrypted, expire
def verify_user(secret: str, db: Session):
    user= get_all_user_info(db, secret=secret)
    if isinstance(user, User):
        user.valid=True
        print(user.valid)
        confirm= update_user(db, user.id, user)
        if isinstance(confirm, Users):
            return True
        else:
            return False
#------------------------------------- token utilities -------------------------------------
async def create_access_token(session: Session,data: dict, expires_delta: timedelta, request: Request=None) -> str:
    if request:
        meta=request.headers.items()
        meta.append(("client", str(request.client._asdict())))
    else:
        meta=None
    to_encode = data.copy()
    owner=to_encode.get("sub")
    encoded_jwt, expire = encrypt_data(to_encode, expires_delta)
    Key_ = KeyCreate(value=encoded_jwt, 
                     valid_until=expire.strftime('%Y-%m-%d %H:%M:%S'),
                     owner=owner, 
                     registry=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     valid=True, 
                     metadata_=str(meta)
                    )
    if create_key(session, Key_):
        await send_email(session,data.get("sub"), "New Token", "new_token.html", { "creation_date": datetime.now().strftime("%d/%m/%Y"), "new_token": encoded_jwt})
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
#------------------------------------- validate token or session -------------------------------------
def validate_token_or_session(token: str, session: Session) -> bool|Keys:
    try:
        key = get_keys_by_value(session, token)
    except:
        pass
    try:
        key = get_session_by_value(session, token)
    except:
        pass
    if key and key.valid and check_if_still_on_valid_time(key.valid_until):
        return decode_and_verify(key.owner, session)
#------------------------------------- async mail sender -------------------------------------
async def send_email(db:Session, owner: str|User|Users, subject: str, template: str, context: dict[str, str]=None)->bool:
    email = None
    name = None
    if isinstance(owner, str):
        user = get_all_user_info(db=db, secret=owner)
        email= user.email
        name = user.name
    else:
        email= owner.email
        name = owner.name
    context['username']=name
    if email is not None and name is not None:
        print(f"Sending email to {email}")
        messenger.send_template_email(recipient=email,
                                        subject=subject,
                                        template=template,
                                        context=context
                                        )
        return True
    else:
        return False
def decode_varification(encoded:str) -> str|bool:
    try:
        payload = jwt.decode(encoded, secret_key_ps, algorithms=[ALGORITHM])
        secret: str = payload.get("sub")
        return secret
    except:
        return False
def encode_secret(secret: str) -> str:
    return jwt.encode({"sub": secret}, secret_key_ps, algorithm=ALGORITHM)