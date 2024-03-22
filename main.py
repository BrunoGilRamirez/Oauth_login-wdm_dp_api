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
    print (f"session {ack}")
    return response
# --------------------------------------- endpoints ---------------------------------------
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
        return temp.TemplateResponse("index.html", {"request": request})
#--------------------------- UI --------------------------------

@app.get("/UI/register", response_class=HTMLResponse)
@app.post("/UI/register", response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db)):
    if request.method == "GET":
        return temp.TemplateResponse("register.html", {"request": request})
    elif request.method == "POST":
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
@app.post("/UI/login", response_class=RedirectResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    if request.method == "GET":
        return temp.TemplateResponse("login.html", {"request": request, "origin": "UI"})
    elif request.method == "POST":
        form_data = await request.form()
        user = authenticate_user(db,form_data['username'], form_data['password'])
        if not user:
            return {"error": "Invalid credentials"}
        access_token_expires = timedelta(days=5)
        access_token = create_access_token(db,data={"sub": user.secret}, expires_delta=access_token_expires)
        redirect = RedirectResponse(url="/UI/home")
        request.session['access_token'] = access_token
        redirect.set_cookie(key="access_token", value=access_token, httponly=True)


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
        sess=request.session.get("access_token")
        print(f"\nPeticion: {sess}\nAutorizacion: {request.headers.get('Authorization')}")
        user = await get_current_user(request, db)
        return temp.TemplateResponse("home.html", {"request": request, "user": user})
    else:
        return temp.TemplateResponse("index.html", {"request": request})
    
@app.get("/UI/logout", response_class=RedirectResponse)
async def logout(request: Request):
    request.session.clear()
    response = RedirectResponse(url="/")
    return response

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
    access_token = create_access_token(session,data={"sub": user.secret}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me/")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_user)):
    return [{"item_id": "Foo", "owner": current_user.name}]