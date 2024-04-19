from flask import Flask, request, render_template, redirect, url_for, make_response, session
from flask_session import Session
from session_management import get_session
from models import *
from models.schemas import *
from crud import *
from passlib.context import CryptContext
session_root = get_session('.env')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
flapp = Flask(__name__)
def generate_user_secret(name:str, role:str, email:str, employer:str):
    #generate a hash of the user data dictionary
    data = {'name':name, 'role':role, 'email':email, 'employer':employer}
    return pwd_context.hash(str(data))
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)
@flapp.route('/') 
def index():
    return render_template('index.html')
@flapp.route('/register', methods=['POST', 'GET'])
def register_user( ):
    session = session_root()

    if request.method == 'POST':
        username = request.form['name']
        role = request.form['role']
        email = request.form['email']
        employer = request.form['employer']
        password = get_password_hash(request.form['password'])
        employer_id = get_companies_by_name(session, employer)
        if not employer_id:
            create_company(session, CompanyCreate(name=employer, phone_number=0, registry=datetime.now().strftime('%Y-%m-%d'), email='not given'))
            employer_id = get_companies_by_name(session, employer)
        secret=generate_user_secret(username, password, email, employer)
        user = UserCreate(name=username, role=role, email=email, employer=employer_id, secret=secret)
        if not user_exists(session, user):
            if create_user(session, user) and create_password(session, PasswordCreate(value=password, owner=user.secret)):
                return redirect(url_for('login', user_secret=user.secret))
            else:
                return render_template('register.html', error='Error creating password')
        else:
            return render_template('register.html', error='User already exists')
    session.close()
    return render_template('register.html')
@flapp.route('/home/<user_secret>', methods=['POST', 'GET'])
def home(user_secret:str):
    session=session_root()
    user= get_all_user_info(session, secret=
                            user_secret)
    session.close()
    return render_template('home.html', user=user)
@flapp.route('/login', methods=['POST', 'GET'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    return render_template('login.html',origin='this')