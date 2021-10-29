#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=no-name-in-module

__author__ = "Bauyrzhan Ospan"
__copyright__ = "Copyright 2021"
__version__ = "1.0.1"


from pydantic import ValidationError
from typing import List
import requests
from telebot import types
from typing import Optional
from fastapi import FastAPI, Form, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from random import randint, choice, randrange
from datetime import datetime, timedelta
import copy
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
import gunicorn
import uvloop
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pymongo import MongoClient
import logging


from module_locator import module_path



def path_locator():
   pass 

cwd = module_path(path_locator)
cwd = cwd.replace("/main.py", "")
os.chdir(cwd)

path = os.getcwd()
os.environ['TZ'] = 'Asia/Almaty'
logging.error("Programm started")









# region: Database


class Database:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')

        self.db = self.client["OceanMind"]
        self.users = self.db['users']
        self.statdata = self.db['statdata']
        self.incidents = self.db['incidents']
        self.videos = self.db['videos']
        self.photos = self.db['photos']
        self.alerts = self.db['alerts']
        if self.users.count_documents({}) == 0:
            self.initial_populate()

    def insert(self, table, data):
        if type(data) == list:
            result = table.insert_many(data)
            for d in data:
                d["_id"] = None
        else:
            result = table.insert_one(data)
            data["_id"] = None
        return result

    def get(self, table, key, data):
        try:
            result = table.find({key: data}, {'_id': False})
            result = list(result)
            return result
        except:
            return None

    def get_one(self, table, key, data):
        try:
            result = table.find_one({key: data}, {'_id': False})
            return dict(result)
        except:
            return None

    def delete(self, table, key, data):
        result = table.delete_many({key: data})
        return result

    def initial_populate(self):
        now = datetime.now().timestamp()
        user = {
        	"name": "John",
        	"surname": "Doe",
        	"username": "johndoe",
        	"position": "main",
        	"passwprd": "12345678",
            "hashed_password": "$2b$12$0wS0vT8Ne9YciDYIp86auO4DhAbDvup.EGdH8CIkmbaGsq3TxQtBm",
        	"phone_number": "123123456",
        	"city": "Nur-Sultan"
        }
        self.insert(self.users, user)

       



DB = Database()

# endregion









# region: Security vals
SECRET_KEY = "da9ddaaf9e55f5790789f17503113b8d9548c43b60b10599909811caf8e021ea"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# endregion


def random_date(end):
    start = datetime.strptime('1/1/2019 1:30 PM', '%m/%d/%Y %I:%M %p')
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)

# region: Create app and CORS
tags_metadata = [
    {
        "name": "getvalvesbycity",
        "description": "Получаешь список клапанов в выбранном городе",
    },
    {
        "name": "token",
        "description": "Получаешь токен",
    },
    {
        "name": "addvalve",
        "description": "Добавляет клапан",
    }, 
    {
        "name": "getmasterbycity",
        "description": "Добавляет мастер",
    },
    {
        "name": "getmasterhubbycity",
        "description": "Добавляет мастерхаб",
    },
]

app = FastAPI(
    title="OceanMind project documentation",
    description="This is documentation for developers",
    version="2.1.0",
    openapi_tags=tags_metadata
)
app.mount("/static/", StaticFiles(directory=path + "/static"), name="static")
templates = Jinja2Templates(directory=path + "/templates")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# endregion




# region: Security and management

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(DB, username: str):
	username_in_db = DB.get(DB.users, "username", username)
	if username_in_db[0]:
		user_dict = username_in_db[0]
		return UserInDB(**user_dict)


def authenticate_user(DB, username: str, password: str):
    user = get_user(DB, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    logging.error("returned in authenticate_user")
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    logging.error('look b')
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(DB, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token, tags=['token'])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(DB, form_data.username, form_data.password)
    if user == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    username = current_user.username
    this_user = DB.get_one(DB.users, "username", username)
    all_users = []
    for doc in DB.users.find():
        doc.pop("_id")
        user = doc        
        all_users.append(user)
    if this_user['position'] == "main":
        return this_user, all_users
    else:
        return this_user


@app.post("/users/delete/")
async def users_delete(to_be_deleted_username: str = Form(...), current_user: User = Depends(get_current_active_user)):
    username = current_user.username
    this_user = DB.get_one(DB.users, "username", username)
    if this_user['position'] == "main":
        DB.delete(DB.users, "username", to_be_deleted_username)
        return f"Пользователь {to_be_deleted_username} удален"



@app.post("/users/new")
async def new_user(username_to_be_created: str = Form(...), password: str = Form(...),
                   name: str = Form(...), surname: str = Form(...), phone_number: str = Form(...),
                   position_doljnost: str = Form(...), city: str = Form(...), current_user: User = Depends(get_current_active_user)):
    if len(DB.get(DB.users, "username", username_to_be_created)) == 0: 
        user = {
            "name": name,
            "surname": surname,
            "username": username_to_be_created,
            "position": position_doljnost,
            "password": password,
            "hashed_password": pwd_context.hash(password),
            "phone_number": phone_number,
            "city": city
        }
        username = current_user.username
        this_user = DB.get_one(DB.users, "username", username)

        if this_user["position"] == "main":
            DB.insert(DB.users, user)
            return f"Пользователь {username_to_be_created} создан"
        else:
            return "Вы не являетесь главным админом, у вас нет доступа к данной функции"
    else:
        return "Этот логин уже занят"


@app.post("/users/change")
async def change_user(username_of_user_to_be_changed: str = Form(...), password: str = Form(...),
                   name: str = Form(...), surname: str = Form(...), phone_number: str = Form(...),
                   position_doljnost: str = Form(...), city: str = Form(...), current_user: User = Depends(get_current_active_user)):
    username = current_user.username
    this_user = DB.get_one(DB.users, "username", username)
    if this_user["position"] == "main":
        DB.users.update_one({"username": username_of_user_to_be_changed}, {"$set": {"name": name}})
        DB.users.update_one({"username": username_of_user_to_be_changed}, {"$set": {"surname": surname}})
        DB.users.update_one({"username": username_of_user_to_be_changed}, {"$set": {"position": position_doljnost}})
        DB.users.update_one({"username": username_of_user_to_be_changed}, {"$set": {"password": pwd_context.hash(password)}})
        DB.users.update_one({"username": username_of_user_to_be_changed}, {"$set": {"phone_number": phone_number}})
        DB.users.update_one({"username": username_of_user_to_be_changed}, {"$set": {"city": city}})
        return f"Информация пользователя {username_of_user_to_be_changed} была изменена"
    else:
        return "Вы не являетесь главным администратором, у вас нет доступа к данной функции"
# endregion









# region: Telegram bot


def send_tg_code():
    current_datetime = str(datetime.now())
    current_date = current_datetime.split()[0]
    current_time = current_datetime.split()[1][0:5]
    current_hour = int(current_time.split(":")[0])
    current_mins = int(current_time.split(":")[1])

    code = str(randint(100000, 999999))
    DB.check_codes.update_one({"name": "the_last_code"}, {"$set": {"code": code}})
    DB.check_codes.update_one({"name": "the_last_code"}, {"$set": {"current_date": current_date}})
    DB.check_codes.update_one({"name": "the_last_code"}, {"$set": {"current_hour": current_hour}})
    DB.check_codes.update_one({"name": "the_last_code"}, {"$set": {"current_mins": current_mins}})
    url = "https://api.telegram.org/bot2005360209:AAFupr-tnEjp3RQ69HcSSJk6PaMWq3gh-Wc/sendMessage?chat_id=-538471557&text=" + code
    response = requests.get(url)



# endregion















# region: Main methods

@app.get("/getsecretcode/")
async def getsecretcode():
    send_tg_code()
    return "secret code created"






@app.get("/getincidents/{city}")
async def getincidents(city: str):
    incidents = DB.get(DB.incidents, "city", city)
    return incidents


@app.get("/getcameras/{city}")
async def getcameras(city: str):
    cameras = DB.get(DB.cameras, "city", city)
    return cameras










# endregion

# region:FronEnd


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
	return templates.TemplateResponse("index.html", {"request": request})

# endregion

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True, workers=4)

