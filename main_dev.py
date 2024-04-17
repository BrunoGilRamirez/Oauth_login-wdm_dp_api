import os
#local imports
from models import *
from schemas import *
from crud import *
from extras import *
#fastapi imports
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse,HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
#starlette imports
from starlette.middleware.sessions import SessionMiddleware



#------------------------------------- init app -----------------------------------------
app = FastAPI()
temp = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=os.getenv('SECRET_KEY_sessions'), https_only=True)

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
    if validate_token(request.session.get("access_token"),db):
        return RedirectResponse(url="/UI/home")
    else:
        try:
            request.session.pop("access_token")
        except:
            pass
        return RedirectResponse(url="/UI/login")

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
            await send_email(db,owner=user.secret, 
                       subject="New session", 
                       template="new_session.html", 
                       context={"username": user.secret, 
                                "creation_date": datetime.now().strftime("%d/%m/%Y"), 
                                "metadata": meta, 
                                "link":f"{httpsdir}/lockdown/{user.secret}"
                                }
                        )
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
        request_add_token(request, token)
        user = await get_current_user(request, db)
        if not user:
            request.session.clear()
            try:
                request.form(None)
            except:
                pass
            return RedirectResponse(url="/UI/login")
        return temp.TemplateResponse("user/home.html", {"request": request, "user": user})
    else:
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
    if request.method== "GET":
        pass
    elif request.method == "POST":
        pass
    if token:
        request_add_token(request, token)
        user = await get_current_user(request, db)
        if not user:
            request.session.clear()
            try:
                request.form(None)
            except:
                pass
            return RedirectResponse(url="/UI/login")
        return temp.TemplateResponse("user/usr_settings.html", {"request": request, "user": user})
    else:
        return temp.TemplateResponse("auth/index.html", {"request": request})
@app.get("/UI/access_keys", response_class=HTMLResponse)
@app.post("/UI/access_keys", response_class=HTMLResponse)
async def access_keys(request: Request, db: Session = Depends(get_db)):
    token=request.session.get("access_token")
    if token:
        request_add_token(request, token)
        user = await get_current_user(request, db)
        if request.method== "GET" and user:
            pass
        elif request.method == "POST" and user:
            if request.headers.get('Create')=="True":
                token= await create_access_token(db, data={"sub": user.secret}, expires_delta=timedelta(days=5))
            if request.headers.get('Delete'):
                id=int(request.headers.get('Delete'))
                if not delete_key(db, id):
                    return temp.TemplateResponse("user/access_keys.html", {"request": request, "user": user, "error": "Key deletion failed"})
        elif not user:
            return RedirectResponse(url="/UI/login")
        keys = get_keys_by_owner(db, user.secret)
        return temp.TemplateResponse("user/access_keys.html", {"request": request, "user": user, "keys": keys})
    else:
        return temp.TemplateResponse("auth/index.html", {"request": request})
@app.get("/UI/verify/{encoded}")
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

@app.get("/token_is_valid")
async def token_is_valid(flag: bool = Depends(get_current_user_API)):
    if flag:
        return {"valid": True}
    else:
        return {"valid": False}
