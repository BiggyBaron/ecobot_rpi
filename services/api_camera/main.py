#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=no-name-in-module

__author__ = "Bauyrzhan Ospan"
__copyright__ = "Copyright 2021"
__version__ = "1.0.1"

import requests
import telebot
from telebot import types
from calendar import weekday
from types import new_class
import telebot
from telebot import types
from typing import Optional
from fastapi import FastAPI, Form, Depends, HTTPException, status, Request, File, UploadFile, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel, errors
from random import randint, choice, randrange
from datetime import date, datetime, timedelta
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
import pymongo
import logging
import aiofiles
from module_locator import module_path



def path_locator():
   pass 

cwd = module_path(path_locator)
cwd = cwd.replace("/main.py", "")
os.chdir(cwd)

path = os.getcwd()
os.environ['TZ'] = 'Asia/Almaty'
logging.error("API started again")

# region: Database
class Database:
    def __init__(self):
        self.client = MongoClient('mongodb://database:27017/')

        self.db = self.client["TrashDash"]
        self.users = self.db['users']
        self.statdata = self.db['statdata']
        self.videos = self.db['videos']
        self.photos = self.db['photos']
        self.alerts = self.db['alerts']
        self.robots = self.db['robots']
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

# region: Create app and CORS

app = FastAPI(
    title="OceanMind project documentation for MasterHubs",
    description="This is documentation for developers",
    version="2.1.0"
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# endregion


class StatData(BaseModel):
    temperature: int
    robotID: str
    humidity: int
    battery: int


try:
    app.mount("/static", StaticFiles(directory=path + "/static"), name="static")
except:
    os.mkdir(path + "/static")
    app.mount("/static", StaticFiles(directory=path + "/static"), name="static")



# region TG bot

# bot = telebot.TeleBot("2064531529:AAFjdN8IHOR1r906yg9ol2QkBTKUwp5ZaoQ")
# def send_tg_video(f):
#     bot.send_document("-691892965",f)
    # url = "https://api.telegram.org/bot2064531529:AAFjdN8IHOR1r906yg9ol2QkBTKUwp5ZaoQ/sendVideo?chat_id=-691892965&video=open('output.mp4', 'rb')" + info
    # response = requests.get(url)



# endregion




# region Google Vision API func



def check_for_car(file):
    url_docker = "http://ai:4999/uploadfile/" # For docker container
    url_ext = "http://0.0.0.0:4999/uploadfile/" # For external client

    if __name__ == "__main__":
        # files = open(PATHTOVIDEOFILE, 'rb')

        r = requests.post(url_docker, files={"file": file})

        if float(r.content[0]['confidence']) > 0.5:
            return True





# endregion




# region: Talking to real masterhub methods


@app.post("/stat")
@app.post("/stat/")
async def upload_stat_data(temperature: int = Form(...), robotID: str = Form(...), battery: int = Form(...)):
    data_dict = {
        "temperature": temperature,
        "robotID": robotID,
        "battery": battery
    }
    data_dict['datetime'] = datetime.now()
    DB.insert(DB.statdata, data_dict)
    return "statdata recorded"

# robotID: str = Form(...), cameraNUM: int = Form(...), createdtime: datetime = Form(...), 

bot = telebot.TeleBot("2064531529:AAFjdN8IHOR1r906yg9ol2QkBTKUwp5ZaoQ")



@app.post("/video/")
async def upload_video(robotID: str = Form(...), cameraNUM: int = Form(...), createdtime: datetime = Form(...), uploaded_file: UploadFile = File(...)):
    try:
        file_location = f"static/video/{str(uploaded_file.filename)}"
        # async with aiofiles.open(file_location, 'wb') as out_file:
        #     content = await uploaded_file.read()  # async read
        #     bot.send_video("-691892965",content, caption=f"VIDEOPOST: robot ID is {robotID}; cameraNUM is {cameraNUM}; created time is {createdtime}")

        #     await out_file.write(content)  # async write
        with open(file_location, 'wb+') as out_file:
            content = uploaded_file.file.read()
            out_file.write(content)

        new_entry = {
            "robotID": robotID,
            "cameraNUM": cameraNUM,
            "video": file_location,
            "createdtime": createdtime
        }
        DB.insert(DB.videos, new_entry)

        with open(file_location, 'rb+') as out_file:
            content = out_file.read()
            is_car = check_for_car(content)
            if is_car == True:
                bot.send_message("-1001649348891", f"WARNING WARNING WARNING - CAR DETECTED. video link is http://185.121.81.245:7777/{file_location}")
 

        return {"info": f"file {uploaded_file.filename} saved at {file_location}"}
    except Exception as e:
        logging.error(e)
        return e


    # return Response(content=contents, media_type="application/xml")





@app.get("/imageget/{robotID}")
@app.get("/imageget/{robotID}/")
async def imageget(robotID: str):
    this_robot = DB.get_one(DB.robots, "robotID", robotID)
    now  = datetime.now()                         
    duration = now - this_robot['last_update']                       
    duration_in_s = duration.total_seconds() 
    if this_robot['status_needed'] == True:
        return True
    elif duration_in_s > 3600:
        return True
    else:
        return False
    



@app.post("/imagepost")
@app.post("/imagepost/")
async def imagepost(robotID: str = Form(...), cameraNUM: int = Form(...), createdtime: datetime = Form(...), photodata: UploadFile = File(...)):
    try:
        file_location = f"static/photo/{str(photodata.filename)}"
        # async with aiofiles.open(file_location, 'wb+') as out_file:
        
        #     content = await photodata.file.read()  # async read
            
        #     await out_file.write(content)  # async write

        with open(file_location, 'wb+') as out_file:
            content = photodata.file.read()
            out_file.write(content)
        
        new_entry = {
            "robotID": robotID,
            "cameraNUM": cameraNUM,
            "photo": file_location,
            "createdtime": createdtime
        }
        now = datetime.now()
        DB.insert(DB.photos, new_entry)
        DB.robots.update_one({"robotID": robotID}, {"$set": {"last_update": now}})
        # async with aiofiles.open(file_location, 'rb+') as out_file:

        #     await out_file.read()
        #     bot.send_photo("-691892965", out_file, caption=f"IMAGEPOST: robot ID is {robotID}; cameraNUM is {cameraNUM}; created time is {createdtime}")
        with open(file_location, 'rb+') as out_file:
            content = out_file.read()
            bot.send_message("-1001649348891", "photo recorded, see by link - http://185.121.81.245:7777/{file_location}")
        return "photodata is recorded"
    except Exception as e:
        logging.error(e)
        return e



@app.post("/alert")
@app.post("/alert/")
async def alert(robotID: str = Form(...), cameraNUM: int = Form(...), createdtime: datetime = Form(...), photodata: UploadFile = File(...)):
    try:
        file_location = f"static/alerts/{str(photodata.filename)}"
        # async with aiofiles.open(file_location, 'wb') as out_file:
        #     content = await photodata.read()  # async read
        #     bot.send_photo("-691892965",content, caption=f"This is ALERT from robot with robot ID is {robotID}; cameraNUM is {cameraNUM}; created time is {createdtime}")
        #     await out_file.write(content)  # async write
        with open(file_location, 'wb+') as out_file:
            content = photodata.file.read()
            out_file.write(content)
        new_entry = {
            "robotID": robotID,
            "cameraNUM": cameraNUM,
            "photo": file_location,
            "createdtime": createdtime
        }
        DB.insert(DB.alerts, new_entry)
        with open(file_location, 'rb+') as out_file:
            content = out_file.read()
            bot.send_message("-1001649348891", "ALERT ALERT recorded, see by link - http://185.121.81.245:7777/{file_location}")
        return "alert is recorded"
    except Exception as e:
        logging.error(e)
        return e














# endregion

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True, workers=4)
