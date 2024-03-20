from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBasic, HTTPBasicCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import *
from schemas import *
from crud import *
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from session_management import get_session
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os
from starlette.datastructures import MutableHeaders
#import status from fastapi
from fastapi import status


session_root = get_session('.env')
#dependency
def get_db():
    db = session_root()
    try:
        yield db #yield is used to create a generator function
    finally:
        db.close()

#----------------- init app ---------------------
app = FastAPI()
temp = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
#----------------- cryptography -----------------
secret_key_ps = os.getenv('secret_key_ps')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # bcrypt is the hashing algorithm used to hash the password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="key")

# ------------------ security ---------------------
def generate_user_secret(name:str, role:str, email:str, employer:str):
    #generate a hash of the user data dictionary
    data = {'name':name, 'role':role, 'email':email, 'employer':employer}
    return pwd_context.hash(str(data))
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)
def authenticate_user(session: Session, username: str, password: str):
    user = get_user_by_email(session, username)
    if not user:
        return False
    if not verify_password(password, get_password_by_owner(session, user.secret).value):
        return False
    return user
def create_access_token(session: Session,data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key_ps, algorithm=ALGORITHM)
    Key_ = KeyCreate(owner=to_encode['sub'], value=encoded_jwt, registry=datetime.now().strftime('%Y-%m-%d'), valid_until=expire.strftime('%Y-%m-%d'))
    if create_key(session, Key_):
        return encoded_jwt
    else:
        return False
async def get_current_user(token: Request, session: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = await oauth2_scheme(token)
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
async def register_user(request: Request, session: Session = Depends(get_db)) -> bool|str:
    form_data = await request.form()
    username = form_data['name']
    role = form_data['role']
    email = form_data['email']
    employer = form_data['employer']
    password = get_password_hash(form_data['password'])
    employer_id = get_companies_by_name(session, employer)
    if not employer_id:
        create_company(session, CompanyCreate(name=employer, phone_number=0, registry=datetime.now().strftime('%Y-%m-%d'), email='not given'))
        employer_id = get_companies_by_name(session, employer)
    secret=generate_user_secret(username, role, email, employer)
    user = UserCreate(name=username, role=role, email=email, employer=employer_id, secret=secret)
    if not user_exists(session, user):
        if create_user(session, user) and create_password(session, PasswordCreate(value=password, owner=user.secret)):
            return True
        else:
            return False
    else:
        return "User already exists"
# ------------------- endpoints -------------------

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    file_name = "favicon.ico"
    file_path = os.path.join(app.root_path, "static", file_name)
    return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    return temp.TemplateResponse("index.html", {"request": request})
@app.get("/UI/register", response_class=HTMLResponse)
async def register(request: Request):
    return temp.TemplateResponse("register.html", {"request": request})
@app.post("/UI/register")
async def register(request: Request, db: Session = Depends(get_db)):
    feedback = await register_user(request, db)
    if feedback == True:
        print("User created")
        #redirect to login with method GET
        return RedirectResponse(url="/UI/login", status_code=303)
    elif feedback == False:
        return temp.TemplateResponse("register.html", {"request": request, "error": feedback})
    elif feedback == "User already exists":
        return temp.TemplateResponse("register.html", {"request": request, "error": feedback})
    
@app.get("/UI/login", response_class=HTMLResponse)
async def login(request: Request):
    return temp.TemplateResponse("login.html", {"request": request, "origin": "UI"})
@app.post("/UI/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    
    user = authenticate_user(db,form_data['username'], form_data['password'])
    if not user:
        return {"error": "Invalid credentials"}
    access_token_expires = timedelta(days=5)
    access_token = create_access_token(db,data={"sub": user.secret}, expires_delta=access_token_expires)
    redirect = RedirectResponse(url="/UI/home")
    redirect.set_cookie("access_token", access_token, httponly=True)

    return redirect

@app.get("/UI/home", response_class=HTMLResponse)
@app.post("/UI/home", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    token=request.cookies.get("access_token")
    if token:
        new_headers = MutableHeaders(request._headers)
        new_headers["Authorization"] = f"Bearer {token}"
        request._headers = new_headers
        request.scope.update(headers=request.headers.raw)
        user = await get_current_user(request, db)
        return temp.TemplateResponse("home.html", {"request": request, "user": user})
    else:
        return temp.TemplateResponse("index.html", {"request": request})

@app.post("/key")
async def login_for_access_key(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_db))-> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(days=float(5))
    access_token = create_access_token(session,data={"sub": user.secret}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me/")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_user)):
    return [{"item_id": "Foo", "owner": current_user.name}]