from sqlalchemy.orm import Session
from models import Companies, Users, Keys, Passwords
from schemas import CompanyCreate, UserCreate, KeyCreate, PasswordCreate, User, Company

# Create a new company
def create_company(db: Session, company: CompanyCreate) -> Companies|bool:
    try:
        new_company = Companies(**company.model_dump())
        db.add(new_company)
        db.commit()
        #db.refresh(new_company)
        return new_company
    except Exception as e:
        db.rollback()
        return False

# Get a company by ID
def get_company(db: Session, company_id: int):
    return db.query(Companies).filter(Companies.id == company_id).first()

# Get all companies
def get_companies(db: Session):
    return db.query(Companies).all()
def get_companies_by_name(db: Session, name: str):
    companies = db.query(Companies).filter(Companies.name == name).first()
    if companies:
        return companies.id
    else:
        return False
# Update a company
def update_company(db: Session, company_id: int, company: CompanyCreate) -> Companies|bool:
    try:
        db.query(Companies).filter(Companies.id == company_id).update(company.model_dump())
        db.commit()
        return get_company(db, company_id)
    except Exception as e:
        db.rollback()
        return False

# Delete a company
def delete_company(db: Session, company_id: int) -> bool:
    try:
        company = get_company(db, company_id)
        db.delete(company)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
def user_exists(db: Session, user: UserCreate) -> bool:
    user = db.query(Users).filter(Users.name == user.name, Users.email == user.email, Users.employer == user.employer).first()
    if user:
        return True
    else:
        return False
# Create a new user
def create_user(db: Session, user: UserCreate) -> bool:
    new_user = Users(**user.model_dump())
    try:
        db.add(new_user)
        db.commit()
        #db.refresh(new_user)
        return True
    except Exception as e:
        db.rollback()
        return False
def get_user_by_user(db: Session, user: UserCreate) -> Users|bool:
    user = db.query(Users).filter(Users.name == user.name, Users.email == user.email, Users.employer == user.employer).first()
    if user:
        return user
    else:
        return False
            
def get_all_user_info(db: Session, user: UserCreate|None=None, secret: str|None=None) -> User|bool:
    if user is not None:
        user = db.query(Users).filter(Users.name == user.name, Users.email == user.email, Users.employer == user.employer).first()
    else:
        user = db.query(Users).filter(Users.secret == secret).first()
    employer = db.query(Companies).filter(Companies.id == user.employer).first()
    if user and employer:
        employer_schema = Company(id=employer.id,name=employer.name, phone_number=employer.phone_number, registry=str(employer.registry), email=employer.email)
        return User(id=user.id, name=user.name, role=user.role, email=user.email, employer=employer.id, secret=user.secret, company=employer_schema)
    else:
        return False
def get_user_by_secret(db: Session, secret: str) -> Users|bool:
    user = db.query(Users).filter(Users.secret == secret).first()
    if user:
        return user
    else:
        return False

def get_user(db: Session, user_id: int):
    return db.query(Users).filter(Users.id == user_id).first()
def get_user_by_name(db: Session, name: str):
    user = db.query(Users).filter(Users.name == name).first()
    if user:
        return user.id
    else:
        return False
def get_user_by_email(db: Session, email: str) -> Users|bool:
    user = db.query(Users).filter(Users.email == email).first()
    if user:
        return user
    else:
        return False
# Get all users
def get_users(db: Session):
    return db.query(Users).all()

# Update a user
def update_user(db: Session, user_id: int, user: UserCreate)-> Users|bool:
    try:
        db.query(Users).filter(Users.id == user_id).update(user.model_dump())
        db.commit()
        return get_user(db, user_id)
    except Exception as e:
        db.rollback()
        return False

# Delete a user
def delete_user(db: Session, user_id: int):
    try:
        user = get_user(db, user_id)
        db.delete(user)
        db.commit()
        return user
    except Exception as e:
        db.rollback()
        return False

# Create a new key
def create_key(db: Session, key: KeyCreate) -> bool:
    new_key = Keys(**key.model_dump())
    db.add(new_key)
    try:
        db.commit()
        #db.refresh(new_key)
        return True
    except Exception as e:
        db.rollback()
        return False

def get_keys_by_user(db: Session, user_id: int) -> Keys|bool:
    return db.query(Keys).filter(Keys.user_id == user_id).all()
def get_keys_by_value(db: Session, value: str) -> Keys|bool:
    return db.query(Keys).filter(Keys.value == value).all()

# Get a key by ID
def get_key(db: Session, key_id: int):
    return db.query(Keys).filter(Keys.id == key_id).first()

# Get all keys
def get_keys(db: Session):
    return db.query(Keys).all()

# Update a key
# Update a key
def update_key(db: Session, key_id: int, key: KeyCreate):
    try:
        db.query(Keys).filter(Keys.id == key_id).update(key.model_dump())
        db.commit()
        return get_key(db, key_id)
    except Exception as e:
        db.rollback()
        return False

# Delete a key
def delete_key(db: Session, key_id: int):
    key = get_key(db, key_id)
    db.delete(key)
    db.commit()
    return key

# Create a new password
def create_password(db: Session, password: PasswordCreate) -> bool:
    new_password = Passwords(**password.model_dump())
    
    db.add(new_password)
    db.commit()
    return True if get_password_by_owner(db, password.owner) else False
    #except:
        #db.rollback()
        #return False

# Get a password by ID
def get_password(db: Session, password_id: int):
    return db.query(Passwords).filter(Passwords.id == password_id).first()

# Get all passwords
def get_passwords(db: Session):
    return db.query(Passwords).all()

# Update a password
def update_password(db: Session, password_id: int, password: PasswordCreate):
    try:
        db.query(Passwords).filter(Passwords.id == password_id).update(password.model_dump())
        db.commit()
        return get_password(db, password_id)
    except Exception as e:
        db.rollback()
        return False

# Delete a password
def delete_password(db: Session, password_id: int):
    try:
        password = get_password(db, password_id)
        db.delete(password)
        db.commit()
        return password
    except Exception as e:
        db.rollback()
        return False
def get_password_by_owner(db: Session, owner: str) -> Passwords|bool:
    password = db.query(Passwords).filter(Passwords.owner == owner).first()
    if password:
        return password
    else:
        return False