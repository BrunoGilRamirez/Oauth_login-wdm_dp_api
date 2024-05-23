import os
#local imports
from models.models import *
from models.schemas import *
from models.crud import *
from extras import *
#fastapi imports
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse,HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
#starlette imports
import traceback
from starlette.middleware.sessions import SessionMiddleware



#------------------------------------- init app -----------------------------------------
app = FastAPI(docs_url=None, redoc_url=None)
temp = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=os.getenv('SECRET_KEY_sessions'), https_only=True, same_site="strict")

#---------------------------Middleware--------------------------------
@app.middleware("http")
async def passive_auth(request: Request, call_next):
    response=await call_next(request)
    ack=request.session.get("access_token")
    return response
#---------------------------------------- endpoints ---------------------------------------
#--------------------------- icons --------------------------------
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    file_name = "favicon.ico"
    file_path = os.path.join(app.root_path, "static", file_name)
    return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})

#--------------------------- root --------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request, db: Session = Depends(get_db)):
    token = request.session.get("access_token")
    if token:
        if validate_token(token,db):
            return RedirectResponse(url="/UI/home")
        else:
            request.session.pop("access_token")
    return RedirectResponse(url="/UI/login", status_code=303) #303 is the code for "See Other" (since HTTP/1.1

#--------------------------- UI --------------------------------
@app.get("/UI/register", response_class=HTMLResponse)
@app.post("/UI/register", response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db)):
    if request.method == "GET":
        return temp.TemplateResponse("auth/register.html", {"request": request})
    elif request.method == "POST":
        feedback = await register_user(request, db)
        if isinstance(feedback, str) and feedback != "User already exists":

            return RedirectResponse(url="/UI/login", status_code=303)
        elif feedback == False:
            return temp.TemplateResponse("auth/register.html", {"request": request, "error": feedback})
        elif feedback == "User already exists":
            return temp.TemplateResponse("auth/register.html", {"request": request, "error": feedback})
    
@app.get("/UI/login", response_class=HTMLResponse)
@app.post("/UI/login", response_class=RedirectResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    if request.method == "GET":
        return temp.TemplateResponse("auth/login.html", {"request": request, "origin": "UI"})
    elif request.method == "POST":
        form_data = await request.form()
        user = authenticate_user(db,form_data['username'], form_data['password'])
        if user is False:
            return temp.TemplateResponse("auth/login.html", {"request": request, "error": "This user does not exist or the password is incorrect"})
        elif user.valid is False:
            return temp.TemplateResponse("auth/login.html", {"request": request, "error": "You need to verify your account with the URL sent to your registered email."})
        data={"sub": user.secret}
        access_token, expires = encrypt_data(data, timedelta(days=14))
        meta=request.headers.items()
        meta.append(("client", str(request.client._asdict())))
        meta=str(meta)
        flag=create_session(db, 
                       SessionCreate(owner=user.secret, 
                                     registry=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                                     valid_until=expires.strftime('%Y-%m-%d %H:%M:%S'), 
                                     valid=True, 
                                     metadata_=meta, 
                                     value=access_token
                                     )
                                )
        if not flag:
            return temp.TemplateResponse("auth/login.html", {"request": request, "error": "Session creation failed"})
        else:
            email_sended=await send_email(db,owner=user.secret, 
                       subject="Nuevo inicio de sesión", 
                       template="new_session.html", 
                       context={"username": user.name, 
                                "creation_date": datetime.now().strftime("%d/%m/%Y"), 
                                "metadata": meta, 
                                "link":f"{request.base_url}lockdown/{encode_secret(user.secret)}"
                                }
                        )
            if not email_sended:
                print("Email not sent")
            request.session['access_token'] = access_token 
            redirect = RedirectResponse(url="/UI/home", status_code=status.HTTP_302_FOUND)
        
        return redirect

@app.get("/UI/home", response_class=HTMLResponse)
@app.post("/UI/home", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    token=request.session.get("access_token")
    if request.method== "GET":
        pass
    elif request.method == "POST":
        pass
    if token:
        user = False
        request_add_token(request, token)
        user = await get_current_user(request, db)
        if user:
            return temp.TemplateResponse("user/home.html", {"request": request})
        else:
            request.session.pop("access_token")
    
    return temp.TemplateResponse("auth/index.html", {"request": request})
    
@app.get("/UI/logout", response_class=RedirectResponse)
async def logout(request: Request, db: Session = Depends(get_db)):
    delete_user_session(request,db=db)
    request.session.clear()
    response = RedirectResponse(url="/")
    return response

@app.get("/UI/user_settings", response_class=HTMLResponse)
@app.post("/UI/user_settings", response_class=HTMLResponse)
async def user_settings(request: Request, db: Session = Depends(get_db)):
    token=request.session.get("access_token")
    if token:
        request_add_token(request, token)
        user = await get_current_user(request, db)
        if user:
            chunk=int(len(user.email)*0.35)
            email=user.email[:chunk]+"..."+user.email[user.email.find("@"):]
            message=""
            if request.method== "GET":
                pass
            elif request.method == "POST":
                form = await request.form()
                current_pass = form.get('currentPassword')
                new_pass = form.get('newPassword')
                verif_code = form.get('verificationCode')
                clean_form(request)
                if current_pass and new_pass and verif_code:
                    if auth_password_reset(session=db, secret=user.secret, code=verif_code, new_password=new_pass, current_password=current_pass):
                                message="Password changed successfully"
                    else:
                        message="Password change failed, check your current password and the verification code"
            return temp.TemplateResponse("user/usr_settings.html", {"request": request, "user": user, 'token': token, 'email': email, 'message': message})
        else:
            request.session.clear()
            clean_form(request) 
    return RedirectResponse(url="/UI/login")
def clean_form(request: Request):
    try:
        request._form = None
        return request
    except Exception as e:
        traceback.print_exc()
        return False
    
@app.get("/UI/access_keys", response_class=HTMLResponse)
@app.post("/UI/access_keys", response_class=HTMLResponse)
async def access_keys(request: Request, db: Session = Depends(get_db)):
    token=request.session.get("access_token")
    if token:
        request_add_token(request, token)
        user = await get_current_user(request, db)
        if isinstance(user, User):
            keys = get_keys_by_owner(db, user.secret)
            if request.method== "GET" and user:
                pass
            elif request.method == "POST" and user:
                if request.headers.get('Create')=="True":
                    token= await create_access_token(db, data={"sub": user.secret}, expires_delta=timedelta(days=5))
                if request.headers.get('Delete'):
                    id=int(request.headers.get('Delete'))
                    if not delete_key(db, id):
                        return temp.TemplateResponse("user/access_keys.html", {"request": request, "keys": keys,"error": "Key deletion failed", 'token': token})
            return temp.TemplateResponse("user/access_keys.html", {"request": request, "keys": keys, 'token': token})
        else:
            request.session.clear()
            return RedirectResponse(url="/UI/login")
    return RedirectResponse(url="/UI/login")

@app.get("/UI/verify/{encoded}", include_in_schema=False)
async def verify(encoded:str, db: Session = Depends(get_db)):
    print(encoded)
    user_secret=decode_varification(encoded)
    print(user_secret)
    if user_secret:
        if verify_user(user_secret,db):
            return {"message": "User verified"}
        else:
            return {"message": "User not verified"}
    else:
        return {"message": "User not found"}

@app.get("/UI/code-pass")
async def code_pass(user: User = Depends(get_user_secret_Oa2), db: Session = Depends(get_db)):
    if isinstance(user, User):
        code = get_code_by_owner_operation(db,user.secret,2)
        if isinstance(code, Codes):
            if  check_if_still_on_valid_time(code.valid_until) is False:
                if delete_code(db, code):
                    code,time = generate_security_code(db=db, user=user.secret, operation=2,return_time=True)
                    if await send_email(db,owner=user,subject="Security Code",template="pass_change.html",context={"username": user.name, "code": code}):
                    #if True:
                        timeleft = time - datetime.now()
                        return {"Expires": timeleft}
            elif code.value is not None:
                #transform valid_until string to datetime to calculate the time left
                timeleft = code.valid_until - datetime.now()
                return {"Expires": timeleft}
        elif code is False:
            code,time = generate_security_code(db=db, user=user.secret, operation=2,return_time=True)
            if await send_email(db,owner=user,subject="Security Code",template="pass_change.html",context={"username": user.name, "code": code}):
            #if True:
                timeleft = time - datetime.now()
                return {"Expires": timeleft}


@app.get("/lockdown/{encoded}", include_in_schema=False)
@app.post("/lockdown/{encoded}", include_in_schema=False)
async def lockdown(request: Request, encoded:str, db: Session = Depends(get_db)):
    '''When this endpoint is called, it sends a security code to the user's email.
    If the request is a POST, it will reset the user's password and disable all the user's sessions and tokens if the security code is correct.'''
    user_secret=decode_varification(encoded)
    if user_secret:
        user = get_user_by_secret(db, user_secret)
        if user:
            timeleft = None
            if request.method == "GET":
                message = "Code sent to your email."
                code = get_code_by_owner_operation(db,user.secret,2)
                if isinstance(code, Codes):
                    if  check_if_still_on_valid_time(code.valid_until) is False:
                        if delete_code(db, code):
                            code,time = generate_security_code(db=db, user=user.secret, operation=1,return_time=True)
                            if await send_email(db,owner=user,subject="Security Code",template="pass_change.html",context={"username": user.name, "code": code}):
                                timeleft = time - datetime.now()
                    elif code.value is not None:
                        #transform valid_until string to datetime to calculate the time left
                        timeleft = code.valid_until - datetime.now()
                        message = "Code already sent to your email."
                elif code is False:
                    code,time = generate_security_code(db=db, user=user.secret, operation=1,return_time=True)
                    if await send_email(db,owner=user,subject="Security Code",template="pass_change.html",context={"username": user.name, "code": code}):
                        timeleft = time - datetime.now()
            elif request.method == "POST":
                form = await request.form()
                current_pass = form.get('currentPassword')
                new_pass = form.get('newPassword')
                verif_code = form.get('verificationCode')
                clean_form(request)
                if current_pass and new_pass and verif_code:
                    print(f"current_pass: {current_pass}, new_pass: {new_pass}, verif_code: {verif_code}")
                    if lockdown_user(db=db, code=verif_code, current_password=current_pass, new_password=new_pass, secret=user.secret) :
                        message = "Password changed successfully, all sessions and tokens disabled"
                    else:
                        message= "Password change failed, check your current password and the verification code"
            return temp.TemplateResponse("auth/change_pass.html", {"request": request, "path":f"/lockdown/{encoded}","message": message, "encoded": encoded,'xpr_tm':timeleft})
    return RedirectResponse(url="/UI/login")
    
#--------------------------- API --------------------------------
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
    access_token = await create_access_token(session,data={"sub": user.secret}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

