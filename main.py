from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import *
from schemas import *
from crud import *
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from session_management import get_session
from flask import Flask, request, render_template
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.templating import Jinja2Templates


session_root = get_session('.env')
#dependency
def get_db():
    db = session_root()
    try:
        yield db #yield is used to create a generator function
    finally:
        db.close()



#----------------- init app ---------------------
flapp = Flask(__name__)
app = FastAPI()
app.mount('/this', WSGIMiddleware(flapp))
#mount the templates folder to the app
temp = Jinja2Templates(directory="templates")
# mount the static folder to the app
app.mount("/static", StaticFiles(directory="static"), name="static")
#----------------- cryptography -----------------
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS512"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # bcrypt is the hashing algorithm used to hash the password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="key")

#------------------ flask -----------------------
@flapp.route('/') 
def index():
    return render_template('index.html')
@flapp.route('/register', methods=['POST', 'GET'])
def register_user( ):
    session = session_root()

    if request.method == 'POST':
        username = request.form['name']
        password = request.form['role']
        email = request.form['email']
        employer = request.form['employer']
        employer_id = get_companies_by_name(session, employer)
        if not employer_id:
            create_company(session, CompanyCreate(name=employer, phone_number=0, registry=datetime.now().strftime('%Y-%m-%d'), email='not given'))
            employer_id = get_companies_by_name(session, employer)
        user = UserCreate(name=username, role=password, email=email, employer=employer_id)
        if create_user(session, user):
            return render_template('register.html', success='Usuario creado con exito')
        else:
            #retorna un mensaje de error en la pagina
            return render_template('register.html', error='Error al crear el usuario')
        session.close()
    return render_template('register.html')
@flapp.route('/login', methods=['POST', 'GET'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    return render_template('login.html')


# ------------------ security ---------------------

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)
def authenticate_user(session: Session, username: str, password: str):
    user = get_user(session, username)
    if not user:
        return False
    if not verify_password(password, get_password(session, user.id)):
        return False
    return user
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
async def get_current_user(token: str = Depends(oauth2_scheme)):
    print(oauth2_scheme)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user = get_user_by_key_value(session, token)
    except JWTError:
        raise credentials_exception
    if user is None:
        raise credentials_exception
    return user
async def get_current_active_user(current_user: Users = Depends(get_current_user)):
    if current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# ------------------- endpoints -------------------
favicon_path = 'favicon.ico'

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)
@app.post("/key")
async def login_for_access_key(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_db))-> Key:
     user = authenticate_user(session, form_data.username, form_data.password)


@app.get("/users/me/")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.name}]