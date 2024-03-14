from sqlalchemy.orm import Session
from models import Companies, Users, Keys, Passwords
from schemas import CompanyCreate, UserCreate, KeyCreate, PasswordCreate

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

# Create a new user
def create_user(db: Session, user: UserCreate) -> Users|bool:
    new_user = Users(**user.model_dump())
    try:
        db.add(new_user)
        db.commit()
        #db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        return False

# Get a user by ID
def get_user(db: Session, user_id: int):
    return db.query(Users).filter(Users.id == user_id).first()

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
def create_key(db: Session, key: KeyCreate):
    try:
        new_key = Keys(**key.model_dump())
        db.add(new_key)
        db.commit()
        #db.refresh(new_key)
        return new_key
    except Exception as e:
        db.rollback()
        return False

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
def create_password(db: Session, password: PasswordCreate) -> Passwords|bool:
    new_password = Passwords(**password.model_dump())
    try:
        db.add(new_password)
        db.commit()
        return new_password
    except:
        db.rollback()
        return False

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