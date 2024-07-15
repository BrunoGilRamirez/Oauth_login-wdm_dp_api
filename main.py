"""
This file contains the main code for an OAuth login web application using FastAPI.
It includes various endpoints for user registration, login, home page, user settings, access keys, and logout.
"""

import os
# Rest of the code...
import os
from turtle import st
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
from cryptical_op.codes import create_session_secret



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
    """
    Returns a FileResponse object for the favicon.ico file.

    :return: FileResponse object for the favicon.ico file.
    """
    file_name = "favicon.ico"
    file_path = os.path.join(app.root_path, "static", file_name)
    return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})

#--------------------------- root --------------------------------
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request, db: Session = Depends(get_db)):
    """
    Handle the request for the home page.

    Args:
        - request (Request): The incoming request object.
        - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        - RedirectResponse: A redirect response to the appropriate page.
    """
    token = request.session.get("access_token")
    if token:
        add_token_to_request(request, token)
        user = await get_current_user(request, db)
        if user:
            return RedirectResponse(url="/UI/home")
        else:
            request.session.pop("access_token")
    return RedirectResponse(url="/UI/login", status_code=303)  # 303 is the code for "See Other" (since HTTP/1.1)

#--------------------------- UI --------------------------------
@app.get("/UI/register", response_class=HTMLResponse)
@app.post("/UI/register", response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db)):
    """
    Handle the registration process for a user.

    Args:
        - request (Request): The incoming request object.
        - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        - Union[TemplateResponse, RedirectResponse]: The response object based on the request method and registration outcome.
    """
    empleadores = get_empleadores(db) #TODO: end in extras a domain check
    if request.method == "GET":
        return temp.TemplateResponse("auth/register.html", {"request": request, "employers": empleadores})
    elif request.method == "POST":
        confirm,feedback = await register_user(request, db)
        if confirm and isinstance(feedback,str):
            return RedirectResponse(url="/UI/login", status_code=303)
        elif confirm and feedback is None:
            feedback= "Your email was not sent. Please, try to log in, after this will be sent again in a few minutes."
        return temp.TemplateResponse("auth/register.html", {"request": request, "error": feedback, "employers": empleadores})
    
@app.get("/UI/login", response_class=HTMLResponse)
@app.post("/UI/login", response_class=RedirectResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    """
    Handle the login functionality for the UI.

    Args:
        - request (Request): The incoming request object.
        - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        - RedirectResponse: The redirect response to the home page if login is successful.
    """
    if request.method == "GET":
        return temp.TemplateResponse("auth/login.html", {"request": request, "origin": "UI"})
    
    if request.method == "POST":
        form_data = await request.form()
        user = authenticate_user(db,form_data['email'], form_data['password'])
        if user is not None:
            if user.valid is not False:
                client_=str(request.client._asdict())
                session_secret,code_,time_created_ = create_session_secret(context=pwd_context ,secret=user.secret, metadata=str(request.headers.items()), client=client_)
                data={"sub": session_secret}
                access_token, expires = encrypt_data(data, timedelta(days=14))
                meta=request.headers.items()
                meta=str(meta)
                if create_session(db, SessionCreate(owner=user.secret, 
                                            registry=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                                            valid_until=expires.strftime('%Y-%m-%d %H:%M:%S'), 
                                            valid=True, 
                                            metadata_=meta, 
                                            client=client_,
                                            value=access_token,
                                            code=code_,
                                            time_created=time_created_
                                            )
                                        ):
                    if await send_email(db,owner=user.secret, 
                            subject="Nuevo inicio de sesión", 
                            template="new_session.html", 
                            context={"username": user.name, 
                                        "creation_date": datetime.now().strftime("%d/%m/%Y"), 
                                        "metadata": client_, 
                                        "link":f"{request.base_url}lockdown/{encode_secret(access_token)}"
                                        }):
                        pass # TODO: introduce a module to handle all the non-sent mails
                    request.session['access_token'] = access_token 
                    return RedirectResponse(url="/UI/home", status_code=status.HTTP_303_SEE_OTHER)
            else:
                errorMessage = "You need to verify your account with the URL sent to your registered email."
        else:
            errorMessage = "This user does not exist or the password is incorrect"

        return temp.TemplateResponse("auth/login.html", {"request": request, "error": errorMessage})
        

@app.get("/UI/home", response_class=HTMLResponse)
@app.post("/UI/home", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """
    Handle the '/UI/home' endpoint for both GET and POST requests.

    Parameters:
    - request (Request): The incoming request object.
    - db (Session, optional): The database session. Defaults to the result of the 'get_db' dependency.

    Returns:
    - TemplateResponse: The response containing the rendered HTML template.

    """
    token=request.session.get("access_token")
    status_code_ = 307
    if request.method== "GET":
        pass
    elif request.method == "POST":
        status_code_ = 303
    if token:
        user = False
        add_token_to_request(request, token)
        user = await get_current_user(request, db)
        if user:
            return temp.TemplateResponse("user/home.html", {"request": request})
        else:
            request.session.pop("access_token")
    return RedirectResponse(url="/UI/login", status_code=status_code_)
    
@app.get("/UI/logout", response_class=RedirectResponse)
async def logout(request: Request, db: Session = Depends(get_db)):
    """
    Logout endpoint that clears the user session and redirects to the home page.

    Args:
        - request (Request): The incoming request object.
        - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        - RedirectResponse: A redirect response to the home page.
    """
    delete_user_session(request, db=db)
    request.session.clear()
    response = RedirectResponse(url="/")
    return response

@app.get("/UI/user_settings", response_class=HTMLResponse)
@app.post("/UI/user_settings", response_class=HTMLResponse)
async def user_settings(request: Request, db: Session = Depends(get_db)):
    """
    Handle the '/UI/user_settings' endpoint for both GET and POST requests.
    Args:
        - request (Request): The incoming request object.
        - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        - Union[TemplateResponse, RedirectResponse]: The response object based on the request method.
    If the request method is GET, the response is the rendered HTML template.
    If the request method is POST, the response is a redirect to the home page.
    """
    token=request.session.get("access_token")
    status_code_ = 307
    if token:
        add_token_to_request(request, token)
        user = await get_current_user(request, db)
        if user:
            chunk=int(len(user.email)*0.35)
            email=user.email[:chunk]+"..."+user.email[user.email.find("@"):]
            message=""
            if request.method== "GET":
                pass
            elif request.method == "POST":
                status_code_ = 303
                form = await request.form()
                current_pass = form.get('currentPassword')
                new_pass = form.get('newPassword')
                verif_code = form.get('verificationCode')
                clean_form(request)
                if current_pass and new_pass and verif_code:
                    if auth_password_reset(db=db, secret=user.secret, code=verif_code, new_password=new_pass, current_password=current_pass):
                                message="Password changed successfully"
                    else:
                        message="Password change failed, check your current password and the verification code"
            return temp.TemplateResponse("user/usr_settings.html", {"request": request, "user": user, 'token': token, 'email': email, 'message': message})
        else:
            request.session.clear()
            clean_form(request) 
    return RedirectResponse(url="/UI/login", status_code=status_code_)

    
@app.get("/UI/access_keys", response_class=HTMLResponse)
@app.post("/UI/access_keys", response_class=HTMLResponse)
async def access_keys(request: Request, db: Session = Depends(get_db)):
    """
    Handle the '/UI/access_keys' endpoint for both GET and POST requests.
    Args:
        - request (Request): The incoming request object.
        - db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        - Union[TemplateResponse, RedirectResponse]: The response object based on the request method.
    If the request method is GET, the response is the rendered HTML template.
    If the request method is POST, the response is a redirect to the home page.
    """
    status_code_ = 307
    token=request.session.get("access_token")
    if token:
        add_token_to_request(request, token)
        user = await get_current_user(request, db)
        if isinstance(user, User):
            keys = get_keys_by_owner(db, user.secret)
            if request.method== "GET" and user:
                pass
            elif request.method == "POST" and user:
                status_code_ = 303
                if request.headers.get('Create')=="True":
                    token= await create_access_token(db, data={"sub": user.secret}, expires_delta=timedelta(days=5))
                if request.headers.get('Delete'):
                    id=int(request.headers.get('Delete'))
                    if not delete_key(db, id):
                        return temp.TemplateResponse("user/access_keys.html", {"request": request, "keys": keys,"error": "Key deletion failed", 'token': token})
            return temp.TemplateResponse("user/access_keys.html", {"request": request, "keys": keys, 'token': token})
        else:
            request.session.clear()
    return RedirectResponse(url="/UI/login", status_code=status_code_)

@app.get("/UI/verify/{encoded}", include_in_schema=False)
async def verify(encoded:str, db: Session = Depends(get_db)):
    """
    Handle the '/UI/verify/{encoded}' endpoint.
    GET: Verifies the user.
    Args:
        - encoded (str): The encoded user secret.
        - db (Session, optional): The database session. Defaults to Depends(get_db).
    Returns:
        - dict: A dictionary containing the message, if the user is verified or not.
    """
    user_secret=decode_verification(encoded)
    if user_secret:
        if verify_user(user_secret,db):
            return {"message": "User verified."}
        else:
            return {"message": "The user does not exists."}

@app.get("/UI/code-pass")
async def code_pass(user: User = Depends(get_user_secret_Oa2), db: Session = Depends(get_db)):
    """
    Handle the '/UI/code-pass' endpoint.
    GET: Sends the Code to change the password.
    Args:
        - user (User, optional): The user object. Defaults to Depends(get_user_secret_Oa2).
        - db (Session, optional): The database session. Defaults to Depends(get_db).
        
    Returns:
        - dict: A dictionary containing the time left.
    """
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
    If the request is a POST, it will reset the user's password and disable all the user's sessions and tokens if the security code is correct.
    Args:
        - request (Request): The incoming request object.
        - db (Session, optional): The database session. Defaults to Depends(get_db).
        - encoded (str): The encoded session secret.
    Returns:
        - Union[TemplateResponse, RedirectResponse]: The response object based on the request method.
    If the request method is GET, the response is the rendered HTML template.
    If the request method is POST, the response is a redirect to the home page.
    '''
    session_secret=decode_verification(encoded)
    user = None
    status_code_ = 307
    if session_secret:
        session_ = get_session_by_value(db, session_secret)
        if isinstance(session_, Sessions):
            user = get_user_by_secret(db, session_.owner)
        if user:
            timeleft = None
            if request.method == "GET":
                message = "Code sent to your email."
                code = get_code_by_owner_operation(db,user.secret,1)
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
                status_code_ = 303
                form = await request.form()
                current_pass = form.get('currentPassword')
                new_pass = form.get('newPassword')
                verif_code = form.get('verificationCode')
                clean_form(request)
                if current_pass and new_pass and verif_code:
                    if lockdown_user(db=db, code=verif_code, current_password=current_pass, new_password=new_pass, secret=user.secret) :
                        message = "Password changed successfully, all sessions and tokens disabled"
                    else:
                        message= "Password change failed, check your current password and the verification code"
            return temp.TemplateResponse("auth/change_pass.html", {"request": request, "path":f"/lockdown/{encoded}","message": message, "encoded": encoded,'xpr_tm':timeleft})
    return RedirectResponse(url="/UI/login", status_code=status_code_ )

@app.get('/UI/forgotten_password')
@app.post('/UI/forgotten_password')
async def forgotten_password(request: Request, db: Session = Depends(get_db)):
    """
    Handle the '/UI/forgotten_password' endpoint.
    GET: Sends the Code to change the password.
    POST: Changes the password.
    Args:
        - request (Request): The incoming request object.
        - db (Session, optional): The database session. Defaults to Depends(get_db).
    Returns:
        - Union[TemplateResponse, RedirectResponse]: The response object based on the request method.
    If the request method is GET, the response is the rendered HTML template.
    If the request method is POST, the response is a redirect to the home page.
    """
    if request.method == "GET":
        return temp.TemplateResponse("auth/forgotten.html", {"request": request})
    elif request.method == "POST":
        form = await request.form()
        email = form.get('email')
        if email:
            user = get_user_by_email(db, email)
            if user:
                client_=str(request.client._asdict())
                session_r, value_r = generate_recovery_session(db, user, client= client_)
                message = "El correo ya fue previamente enviado, verifique su bandeja de entrada o spam. Solo puede generar una sesión por dia."
                if session_r:
                    flag = await send_email(
                        db=db,
                        owner= user,
                        subject= "Forgotten Password? Here's your recovery session access Weidmüller Data Product API",
                        template= "forgotten_password.html",
                        context= {
                            "access_link": f"{request.base_url}UI/forgotten_password/recovery/?sess={session_r}",
                            "access_link_disable_link": f"{request.base_url}UI/forgotten_password/recovery/?sess={session_r}&disable=True"
                        })
                    if flag:
                        message = "Correo enviado a su correo electrónico, siga el enlace para restablecer su contraseña."
                    elif delete_recovery_session(db=db, value=value_r):
                        message="Algo esta fallando con nuestro servicio de correo, contacte con soporte, le ayudaran con el problema. Lamentamos los inconvenientes"
                return temp.TemplateResponse("auth/forgotten.html", {"request": request, "message": message})
            return temp.TemplateResponse("auth/forgotten.html", {"request": request, "message": "El usuario no existe"})    
                
@app.get('/UI/forgotten_password/recovery')
async def forgotten_password_recovery(request: Request, sess: str=None, disable: bool = False,db: Session = Depends(get_db)):
    if sess is None:
        sess = request.session.get('sess')
    user, stat, session= verify_recovery_session(db, sess)
    message = "Session not found"
    context = { "request": request}
    if isinstance(user, Users) and stat == "valid":
        request.session['recovery_session'] = sess
        message = "Code sent to your email."
        code = get_code_by_owner_operation(db,user.secret,3)
        if isinstance(code, Codes):
            if  check_if_still_on_valid_time(code.valid_until) is False:
                if delete_code(db, code):
                    code,time = generate_security_code(db=db, user=user.secret, operation=3,return_time=True)
                    if await send_email(db,owner=user,subject="Security Code",template="pass_change.html",context={"username": user.name, "code": code}):
                        timeleft = time - datetime.now()
            elif code.value is not None:
                #transform valid_until string to datetime to calculate the time left
                timeleft = code.valid_until - datetime.now()
                message = "Code already sent to your email."
        elif code is False:
            code,time = generate_security_code(db=db, user=user.secret, operation=3,return_time=True)
            if await send_email(db,owner=user,subject="Security Code",template="pass_change.html",context={"username": user.name, "code": code}):
                timeleft = time - datetime.now()
        context["xpr_tm"] = timeleft.total_seconds()
        context["sess_exp"] = (session.expires - datetime.now()).total_seconds()
        return temp.TemplateResponse("auth/forgotten_recovery.html", context)
    elif stat != "unknown":
        message = f"Session {stat}"
        request.session.pop('recovery_session',None)
    return {"message": message}


@app.post('/UI/forgotten_password/recovery')
async def forgotten_password_recovery_post(request: Request, db: Session = Depends(get_db)):
    sess = request.session.get("recovery_session", '')
    user, stat, session= verify_recovery_session(db, sess)
    message = "Session not found"
    context = { "request": request}
    if isinstance(user, Users) and stat == "valid":
        form = await request.form()
        new_pass = form.get('password')
        verif_code = form.get('verificationCode')
        print( f"Verification code: {verif_code} and password: {new_pass}")
        if  new_pass and verif_code:
            if lockdown_user(db=db, code=verif_code, current_password='', new_password=new_pass, secret=user.secret, only_change=True, type_op=3) and update_recovery_session(db, session, True):
                message = "Password changed successfully, all sessions and tokens disabled"
                await send_email(db=db,
                        owner=user, 
                        subject="Password changed successfully, all sessions and tokens disabled", 
                        template="confirm_password.html"
                        )
                request.session.pop('recovery_session')
            else:
                message= "Password change failed, check your current password and the verification code"
            context["message"]= message
        context["sess_exp"] = (session.expires - datetime.now()).total_seconds()
        return temp.TemplateResponse("auth/forgotten_recovery.html", context)
    return RedirectResponse(url="/UI/login", status_code=303)