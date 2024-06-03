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
    """
    Returns a database connection.

    This function creates a database connection using the `session_root` function and returns it as a generator.
    The connection is automatically closed when the generator is exhausted.

    Yields:
        - session: A database connection object.

    """
    db = session_root()
    try:
        yield db
    finally:
        db.close()
def get_db():
    db = session_root()
    try:
        yield db #yield is used to create a generator function
    finally:
        db.close()

#------------------------------------- security ------------------------------------------
def create_session_secret(secret:str, metadata:str, client:str)->list[str,str,datetime]:
    """
    Generates a session secret code and returns a hashed version of the data along with the code and creation time.

    Args:
        - secret (str): The secret value.
        - metadata (str): The metadata value.
        - client (str): The client value.

    Returns:
        - tuple: A tuple containing the hashed data, session code, and time created.
    """
    #generate a random number  of 20 digits
    code = str(secrets.randbelow(10**20))
    time_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = {'secret':secret, 'metadata':metadata, 'client':client, 'session_code':code, 'time_created':time_created}
    return pwd_context.hash(str(data)), code, time_created

def generate_user_secret(name:str, role:str, email:str, employer:str, security:str):
    """
    Generate a hash of the user data dictionary.

    Args:
        - name (str): The name of the user.
        - role (str): The role of the user.
        - email (str): The email of the user.
        - employer (str): The employer of the user.
        - security (str): The security information of the user.

    Returns:
        - str: The hashed representation of the user data dictionary.
    """
    data = {'name':name, 'role':role, 'email':email, 'employer':employer, 'security':security}
    return pwd_context.hash(str(data))
def verify_password(plain_password, hashed_password):
    """
    Verify if a plain password matches a hashed password.

    Args:
        - plain_password (str): The plain password to verify.
        - hashed_password (str): The hashed password to compare against.

    Returns:
        - bool: True if the plain password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    """
    Returns the hash of the given password.

    Args:
        - password (str): The password to be hashed.

    Returns:
        - str: The hashed password.
    """
    return pwd_context.hash(password)
def check_if_still_on_valid_time(valid_until: str) -> bool:
    """
    Check if the current time is still within the valid time range.

    Args:
        - valid_until (str): The valid until time in string format.

    Returns:
        - bool: True if the current time is still within the valid time range, False otherwise.
    """
    if datetime.now() < valid_until:
        return True
    else:
        return False

def generate_security_code(db: Session, user: str, operation:int, return_time: bool=False)->bool|int|tuple[int,datetime]:
    '''
    Generates a random code and stores it in the database with the user as the owner. The code is valid for 5 minutes.

    Args:
        - db (Session): The database session.
        - user (str): The user's secret.
        - operation (int): The operation to be performed with the code. 1 for password reset, 2 for user verification.
        - return_time (bool, optional): If True, returns the code and the time it is valid until. Otherwise, returns only the code. Defaults to False.

    Returns:
        - Union[bool, int, Tuple[int, datetime]]: The generated code if successful, otherwise returns False. If return_time is True, returns a tuple containing the code and the time it is valid until.
    '''
    code = str(secrets.randbelow(10**8)) #generate a random 8-digit code
    time=datetime.now() + timedelta(minutes=5, seconds=1) 
    time_set=time.strftime('%Y-%m-%d %H:%M:%S')
    if create_code(db, CodeCreate(owner=user, value=code,valid_until=time_set, operation=operation)):
        if return_time: return code, time
        return code
    else:
        return False

def auth_password_reset(db: Session, secret:str, code: str, new_password: str, current_password:str)->bool:
    """
    Resets the password for a user if the provided secret, code, and current password are valid.

    Args:
        - session (Session): The session object for the database connection.
        - secret (str): The secret associated with the user.
        - code (str): The code used for verification.
        - new_password (str): The new password to set.
        - current_password (str): The current password for verification.

    Returns:
        - bool: True if the password is successfully reset, False otherwise.
    """
    user = get_all_user_info(db, secret=secret)
    code = get_code_by_value(db, code)
    still_valid=check_if_still_on_valid_time(code.valid_until) if isinstance(code, Codes) else False
    verification = verify_password(current_password, get_password_by_owner(db, user.secret).value)
    print(f"User: {user}, Code: {code}, Still valid: {still_valid}, Verification: {verification}")
    if isinstance(user, User) and isinstance(code, Codes) and still_valid and verification:
        print (f"if statement: {user.secret} == {code.owner}: {user.secret == code.owner} type user secret: {type(user.secret)} type code owner: {type(code.owner)}")
        if user.secret == code.owner:
            print("User and code owner match")
            flag_update = update_password(db, user.secret, get_password_hash(new_password))
            flag_delete = delete_code(db, code)
            print(f"Update: {flag_update}, Delete: {flag_delete}")
            if flag_update and flag_delete:
                return True
    return False

#------------------------------------- User utilities -------------------------------------
async def register_user(request: Request, db: Session) -> bool|str:
    """
    Register a new user.

    Args:
        - request (Request): The incoming request object.
        - session (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        - Union[bool, str]: Returns the secret key if the user is successfully registered, False if there was an error during registration, or a string indicating that the user already exists.
    """
    form_data = await request.form()
    username = form_data['name']
    role = form_data['role']
    email = form_data['email']
    employer = form_data['employer']
    security_word = form_data['security']
    password = get_password_hash(form_data['password'])
    employer_id = get_companies_by_name(db, employer)
    if not employer_id:
        create_company(db, CompanyCreate(name=employer, phone_number=0, registry=datetime.now().strftime('%Y-%m-%d'), email='not given'))
        employer_id = get_companies_by_name(db, employer)
    secret=generate_user_secret(username, role, email, employer, security_word)
    user = UserCreate(name=username, role=role, email=email, employer=employer_id, secret=secret, valid=False)
    sec_word=SecurityWordCreate(owner=secret, word=security_word)
    encoded_secret = encode_secret(secret)
    if not user_exists(db, user):
        if messenger.send_template_email(recipient=email,
                                         subject="Welcome to Weidmüller Data Product API",
                                         template="welcome.html",
                                         context={"username": username, 
                                                  "creation_date": datetime.now().strftime("%d/%m/%Y"),
                                                  "verification_link": f"{request.base_url}UI/verify/{encoded_secret}"
                                                 }
                                        ):
            if create_user(db, user) and create_password(db, PasswordCreate(value=password, owner=user.secret)) and create_security_word(db, sec_word):
                return secret
            else:
                return False
    else:
        return "User already exists"
    
def authenticate_user(db: Session, username: str, password: str) -> bool|Users:
    """
    Authenticates a user by checking if the provided username and password match the stored credentials.

    Args:
        - session (Session): The database session object.
        - username (str): The username or email of the user.
        - password (str): The password of the user.

    Returns:
        - bool|Users: Returns the user object if authentication is successful, otherwise returns False.
    """
    user = get_user_by_email(db, username)
    if not user:
        return False
    if not verify_password(password, get_password_by_owner(db, user.secret).value):
        return False
    return user

def lockdown_user(db: Session, code: str, current_password: str, new_password: str, secret:str)->str|bool:
    """
    Locks down a user by updating their password and invalidating their sessions and keys.

    Args:
        - db (Session): The database session.
        - code (str): The code value used for verification.
        - current_password (str): The current password of the user.
        - new_password (str): The new password to be set for the user.
        - secret (str): The secret value associated with the user.

    Returns:
        - bool: True if the user was successfully locked down, False otherwise.
    """
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


async def get_user_secret_Oa2(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db))->str:
    """
    - Retrieves the user secret for OAuth2 authentication.

    Args:
        - token (str): The OAuth2 token.
        - session (Session): The database session.

    Returns:
        - str: The user secret.

    Raises:
        - HTTPException: If the token does not exist or is no longer valid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token does not exist or is no longer valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        sess = get_session_by_value(db, token)
        if isinstance(sess,Sessions):
            if check_if_still_on_valid_time(sess.valid_until):
                user = decode_and_verify(sess.owner, db)
                print(type(user))
                if isinstance(user, User):
                    return user
    except:
        traceback.print_exc()    
    raise credentials_exception

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Retrieves the current user based on the provided request and session.

    Args:
        - request (Request): The incoming request object.
        - session (Session, optional): The session object. Defaults to Depends(get_db).

    Returns:
        - Union[bool, Any]: The decoded and verified user if valid, otherwise False.
    """
    Error_raise = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials",
                                headers={"WWW-Authenticate": "Bearer"},
                                )   
    try:
        token = await oauth2_scheme(request)
        session = get_session_by_value(db, token)
        if session and session.valid and check_if_still_on_valid_time(session.valid_until):
            return decode_and_verify(session.owner, db)
    except:
        raise Error_raise
    
def decode_and_verify(secret: str, db: Session):
    """
    Decodes and verifies the given secret and retrieves user information from the database.

    Args:
        - secret (str): The secret to decode and verify.
        - db (Session): The database session.

    Returns:
        - user: The user information if the secret is valid, False otherwise.
    """
    try:
        user = get_all_user_info(db, secret=secret)
        return user
    except Exception as e:
        traceback.print_exc()
        return False

def encrypt_data(data: dict, expires_delta: timedelta):
    """
    Encrypts the given data and returns the encrypted data along with the expiration time.

    Args:
        - data (dict): The data to be encrypted.
        - expires_delta (timedelta): The time duration until the encrypted data expires.

    Returns:
        - tuple: A tuple containing the encrypted data and the expiration time.
    """
    expire = datetime.now(timezone.utc) + expires_delta
    data.update({"exp": expire})
    encoded = jwt.encode(data, secret_key_ps, algorithm=ALGORITHM)
    encrypted = pwd_context.hash(encoded)
    return encrypted, expire

def verify_user(secret: str, db: Session):
    """
    Verifies the user with the given secret and updates their validity status in the database.

    Args:
        - secret (str): The secret associated with the user.
        - db (Session): The database session.

    Returns:
        - bool: True if the user is successfully updated, False otherwise.
    """
    user = get_all_user_info(db, secret=secret)
    if isinstance(user, User):
        user.valid = True
        print(user.valid)
        confirm = update_user(db, user.id, user)
        if isinstance(confirm, Users):
            return True
        else:
            return False
#------------------------------------- token utilities -------------------------------------
async def create_access_token(db: Session, data: dict, expires_delta: timedelta, request: Request=None) -> str:
    """
    Creates an access token for the given data.

    Args:
        - db (Session): The session object.
        - data (dict): The data to be encoded in the access token.
        - expires_delta (timedelta): The expiration time for the access token.
        - request (Request, optional): The request object. Defaults to None.

    Returns:
        - str: The encoded access token.
    """
    if request:
        meta = request.headers.items()
        meta.append(("client", str(request.client._asdict())))
    else:
        meta = None
    to_encode = data.copy()
    owner = to_encode.get("sub")
    encoded_jwt, expire = encrypt_data(to_encode, expires_delta)
    Key_ = KeyCreate(value=encoded_jwt, 
                     valid_until=expire.strftime('%Y-%m-%d %H:%M:%S'),
                     owner=owner, 
                     registry=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     valid=True, 
                     metadata_=str(meta)
                    )
    if create_key(db, Key_):
        await send_email(db, data.get("sub"), "New Token", "new_token.html", { "creation_date": datetime.now().strftime("%d/%m/%Y"), "new_token": encoded_jwt})
        return encoded_jwt
    else:
        return False

def validate_token(token: str|None, db: Session) -> bool:
    """
    Validates the given token and returns the user information if the token is valid.

    Args:
        - token (str|None): The token to be validated.
        - session (Session): The session object for database operations.

    Returns:
        - bool: Returns the user information if the token is valid, otherwise returns False.
    """
    if isinstance(token, str):
        key = get_keys_by_value(db, token)
        if key:
            payload = jwt.decode(token, secret_key_ps, algorithms=[ALGORITHM])
            secret: str = payload.get("sub")
            user = get_all_user_info(db, secret=secret)
            return user
        else:
            return False
    else:
        return False
    
def request_add_token(request: Request, token: str):
    """
    Adds the provided token to the Authorization header of the request.

    Args:
        - request (Request): The request object to modify.
        - token (str): The token to add to the Authorization header.

    Returns:
        - Request: The modified request object with the token added to the Authorization header.
    """
    new_headers = MutableHeaders(request._headers)
    new_headers["Authorization"] = f"Bearer {token}"
    request._headers = new_headers
    request.scope.update(headers=request.headers.raw)
    return request

def request_remove_token(request: Request):
    """
    Removes the 'Authorization' header from the given request object.

    Args:
        - request (Request): The request object from which to remove the 'Authorization' header.

    Returns:
        - Request: The modified request object with the 'Authorization' header removed.
    """
    new_headers = MutableHeaders(request._headers)
    new_headers.pop("Authorization")
    request._headers = new_headers
    request.scope.update(headers=request.headers.raw)
    return request

#------------------------------------- session utilities -------------------------------------
def validate_user_session(request: Request, db: Session) -> bool:
    """
    Validates the user session by checking if the access token exists in the request session.

    Args:
        - request (Request): The request object containing the session.
        - db (Session): The database session.

    Returns:
        - bool: True if the access token exists in the session and is valid, False otherwise.
    """
    token = request.session.get("access_token")
    if token:
        return get_session_by_value(db, token)
    else:
        return False
    
def delete_user_session(request: Request, db: Session) -> bool:
    """
    Deletes the user session based on the access token stored in the request session.

    Args:
        - request (Request): The request object containing the session.
        - db (Session): The database session.

    Returns:
        - bool: True if the session was successfully deleted, False otherwise.
    """
    token = request.session.get("access_token")
    if token:
        return delete_session(db, token)
    else:
        return False
    
#------------------------------------- validate token or session -------------------------------------
def validate_token_or_session(token: str, db: Session) -> bool|Keys:
    """
    Validates the given token or session.

    Args:
        - token (str): The token to validate.
        - session (Session): The session to validate.

    Returns:
        - bool|Keys: Returns True if the token or session is valid, otherwise returns False or the Keys object.

    """
    try:
        key = get_keys_by_value(db, token)
    except:
        pass
    try:
        key = get_session_by_value(db, token)
    except:
        pass
    if key and key.valid and check_if_still_on_valid_time(key.valid_until):
        return decode_and_verify(key.owner, db)
    
#------------------------------------- async mail sender -------------------------------------
async def send_email(db:Session, owner: str|User|Users, subject: str, template: str, context: dict[str, str]=None)->bool:
    """
    Sends an email to the specified owner.

    Args:
        - db (Session): The database session.
        - owner (str|User|Users): The owner of the email. Can be a string representing a secret, or an instance of User or Users.
        - subject (str): The subject of the email.
        - template (str): The template to use for the email.
        - context (dict[str, str], optional): Additional context for the email template.

    Returns:
        - bool: True if the email was sent successfully, False otherwise.
    """
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
    """
    Decode the given encoded string using JWT and return the secret key.

    Args:
        - encoded (str): The encoded string to be decoded.

    Returns:
        - str|bool: The secret key if decoding is successful, False otherwise.
    """
    try:
        payload = jwt.decode(encoded, secret_key_ps, algorithms=[ALGORITHM])
        secret: str = payload.get("sub")
        return secret
    except:
        return False
    
def encode_secret(secret: str) -> str:
    """
    Encodes a secret using JWT.

    Args:
        - secret (str): The secret to be encoded.

    Returns:
        - str: The encoded secret.

    """
    return jwt.encode({"sub": secret}, secret_key_ps, algorithm=ALGORITHM)


def clean_form(request: Request):
    """"
    Clean the request form.
    Args:
        - request (Request): The incoming request object.
        - form (dict, optional): The form data. Defaults to None.
    Returns:
        - request (Request): The updated request object.
    """
    try:
        request._form = None
        return request
    except Exception as e:
        traceback.print_exc()
        return False