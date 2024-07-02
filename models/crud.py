from sqlalchemy.orm import Session
from sqlalchemy import desc, DateTime
from models.models import *
from models.schemas import *
from datetime import datetime
import traceback
#------------------- Companies -------------------
def create_company(db: Session, company: CompanyCreate) -> Companies|bool:
    try:
        new_company = Companies(**company.model_dump())
        db.add(new_company)
        db.commit()
        return new_company
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def get_company(db: Session, company_id: int):
    return db.query(Companies).filter(Companies.id == company_id).first()
def get_companies(db: Session):
    return db.query(Companies).all()
def get_companies_by_name(db: Session, name: str):
    companies = db.query(Companies).filter(Companies.name == name).first()
    if companies:
        return companies.id
    else:
        return False
def update_company(db: Session, company_id: int, company: CompanyCreate) -> Companies|bool:
    try:
        db.query(Companies).filter(Companies.id == company_id).update(company.model_dump())
        db.commit()
        return get_company(db, company_id)
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def delete_company(db: Session, company_id: int) -> bool:
    try:
        company = get_company(db, company_id)
        db.delete(company)
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def user_exists(db: Session, user: UserCreate) -> bool:
    user = db.query(Users).filter(Users.name == user.name, Users.email == user.email, Users.employer == user.employer).first()
    if user:
        return True
    else:
        return False
#------------------- Users -------------------
def user_exists(db: Session, secret:str) -> bool:
    user = db.query(Users).filter(Users.secret == secret).first()
    if user:
        return True
    else:
        return False
def create_user(db: Session, user: UserCreate) -> bool:
    new_user = Users(**user.model_dump())
    try:
        db.add(new_user)
        db.commit()
        #db.refresh(new_user)
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def get_user_by_user(db: Session, user: UserCreate) -> Users|bool:
    user = db.query(Users).filter(Users.name == user.name, Users.email == user.email, Users.employer == user.employer).first()
    if user:
        return user
    else:
        return False         
def get_user_by_secret(db: Session, secret: str) -> Users|bool:
    user = db.query(Users).filter(Users.secret == secret).first()
    if user:
        return user
    else:
        return False
def get_user_by_email(db: Session, email: str) -> Users|bool:
    user = db.query(Users).filter(Users.email == email).first()
    if user:
        return user
    else:
        return False
def get_all_user_info(db: Session, user: UserCreate|None=None, secret: str|None=None) -> User|bool:
    if user is not None:
        user_ = db.query(Users).filter(Users.name == user.name, Users.email == user.email, Users.employer == user.employer).first()
    if secret is not None:
        user_ = db.query(Users).filter(Users.secret == secret).first()
    if isinstance(user_, Users):
        employer = db.query(Companies).filter(Companies.id == user_.employer).first()
        if isinstance(employer, Companies):
            employer_schema = Company(id=employer.id,name=employer.name, phone_number=employer.phone_number, registry=str(employer.registry), email=employer.email)
            return User( id=user_.id, name=user_.name,role=user_.role, email=user_.email, employer=user_.employer, secret=user_.secret, companies=employer_schema, valid=user_.valid)
    
    return False

def update_user(db: Session, user_id: int, user: User) ->bool:
    try:
        db.query(Users).filter(Users.id == user_id).update({
            Users.id: user.id,
            Users.name: user.name,
            Users.role: user.role,
            Users.email: user.email,
            Users.employer: user.employer,
            Users.secret: user.secret,
            Users.valid: user.valid
        })
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def delete_user(db: Session, user_id: int):
    try:
        user = (db, user_id)
        db.delete(user)
        db.commit()
        return user
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False

#------------------- Codes -------------------
def create_code(db: Session, code: CodeCreate) -> bool:
    new_code = Codes(**code.model_dump())
    try:
        db.add(new_code)
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False    
def get_code_by_owner(db: Session, owner: str) -> Codes|bool:
    code = db.query(Codes).filter(Codes.owner == owner).first()
    if code:
        return code
    else:
        return False
def get_code_by_owner_operation(db: Session, owner: str, operation: int) -> Codes|bool:
    code = db.query(Codes).filter(Codes.owner == owner, Codes.operation == operation).first()
    if code:
        return code
    else:
        return False
def get_code_by_value(db: Session, value: str) -> Codes|bool:
    code = db.query(Codes).filter(Codes.value == value).first()
    if code:
        return code
    else:
        return False
def  get_code_by_value_operation_owner(db: Session, value: str, operation: int, owner: str) -> Codes|bool:
    code = db.query(Codes).filter(Codes.value == value, Codes.operation == operation, Codes.owner == owner).first()
    if code:
        return code
    else:
        return False
    
def delete_code(db: Session, code:Codes) -> bool:
    try:
        db.delete(code)
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
#------------------- Keys -------------------
def create_key(db: Session, key: KeyCreate) -> bool:
    new_key = Keys(**key.model_dump())
    db.add(new_key)
    try:
        db.commit()
        #db.refresh(new_key)
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def get_keys_by_owner(db: Session, owner: str) -> list[Keys]|bool:
    return db.query(Keys).filter(Keys.owner == owner).all()
def get_keys_by_value(db: Session, value: str) -> Keys|bool:
    return db.query(Keys).filter(Keys.value == value).first()
def get_key(db: Session, key_id: int):
    return db.query(Keys).filter(Keys.id == key_id).first()
def get_keys(db: Session)-> list[Keys]:
    return db.query(Keys).all()
def update_key(db: Session, key_id: int, key: Key):
    try:
        db.query(Keys).filter(Keys.id == key_id).update({
            Keys.valid: key.valid,
        })
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
    
def update_valid_list_of_keys(db: Session, keys: list[Key]) -> bool:
    try:
        for key in keys:
            db.query(Keys).filter(Keys.value == key.value).update({
                Keys.valid: False
            })
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False

def delete_key(db: Session, key_id: int):
    key = get_key(db, key_id)
    try:
        db.delete(key)
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False

#------------------- Passwords -------------------
def create_password(db: Session, password: PasswordCreate) -> bool:
    new_password = Passwords(**password.model_dump())
    try:
        db.add(new_password)
        db.commit()
        return True if get_password_by_owner(db, password.owner) else False
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def update_password(db: Session, owner: str, new:str ) -> bool:
    try:
        db.query(Passwords).filter(Passwords.owner == owner).update({Passwords.value: new})
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def get_password_by_owner(db: Session, owner: str) -> Passwords|bool:
    password = db.query(Passwords).filter(Passwords.owner == owner).first()
    if password:
        return password
    else:
        return False
def get_password_by_id(db: Session, password_id: int):
    return db.query(Passwords).filter(Passwords.id == password_id).first()

#------------------- SecurityWords -------------------
def create_security_word(db: Session, security_word: SecurityWordCreate) -> bool:
    new_security_word = SecurityWords(**security_word.model_dump())
    try:
        db.add(new_security_word)
        db.commit()
        return True
    except Exception as e:
        print(f"\n\n\n{e}\n\n\n")
        db.rollback()
        return False
def get_security_word_by_owner(db: Session, owner: str) -> SecurityWords|bool:
    security_word = db.query(SecurityWords).filter(SecurityWords.owner == owner).first()
    if security_word:
        return security_word
    else:
        return False

def update_security_word(db: Session, owner: str, security_word: SecurityWordCreate) -> SecurityWords|bool:
    try:
        db.query(SecurityWords).filter(SecurityWords.owner == owner).update(security_word.model_dump())
        db.commit()
        return get_security_word_by_owner(db, owner)
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
#------------------- Sessions -------------------
def create_session(db: Session, session: SessionCreate) -> bool:
    new_session = Sessions(**session.model_dump())
    try:
        db.add(new_session)
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def get_sessions_by_owner(db: Session, owner: str) -> list[Sessions]|bool:
    try:
        return db.query(Sessions).filter(Sessions.owner == owner).all()
    except Exception as e:
        traceback.print_exc()
        return False
def get_session_by_value(db: Session, value: str) -> Sessions|bool:
    session = db.query(Sessions).filter(Sessions.value == value).first()
    if session:
        return session
    else:
        return False
def delete_session(db: Session, value: str):
    try:
        session = get_session_by_value(db, value)
        db.delete(session)
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def update_session(db: Session, value: str, session: Session) -> Sessions|bool:
    try:
        db.query(Sessions).filter(Sessions.value == value).update({
            Sessions.valid: session.valid,
        })
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def update_valid_list_of_sessions(db: Session, sessions: list[Session]) -> bool:
    try:
        for session in sessions:
            db.query(Sessions).filter(Sessions.value == session.value).update({
                Sessions.valid: False
            })
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
    

# --------------------------- recovery sessions ---------------------------

def create_recovery_session(db: Session, recovery_session: RecoverySessionCreate) -> bool:
    new_recovery_session = RecoverySessions(**recovery_session.model_dump())
    try:
        db.add(new_recovery_session)
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False
def get_recovery_sessions_by_owner(db: Session, owner: str) -> list[RecoverySessions]|bool:
    try:
        return db.query(RecoverySessions)\
            .filter(RecoverySessions.owner == owner)\
            .order_by(desc(RecoverySessions.expires)) \
            .all()
    except Exception as e:
        traceback.print_exc()
        return False

def get_recovery_sessions_by_owner_and_expires(db: Session, owner: str, expires: str) -> RecoverySessions|list[RecoverySessions]:
    expires_dt = datetime.strptime(expires, "%Y-%m-%d %H:%M:%S")
    try:
        return db.query(RecoverySessions)\
            .filter(RecoverySessions.owner == owner, RecoverySessions.expires == expires_dt)\
            .order_by(desc(RecoverySessions.expires)) \
            .all()
    except Exception as e:
        traceback.print_exc()
        return None
    
def delete_recovery_session(db: Session, value: str):
    try:
        recovery_session = db.query(RecoverySessions).filter(RecoverySessions.value == value).first()
        db.delete(recovery_session)
        db.commit()
        return True
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        return False