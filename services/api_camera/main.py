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
import logging
import aiofiles
from database import database


path = "/home/web/"
os.environ['TZ'] = 'Asia/Almaty'


DB = database.Database()
bot = telebot.TeleBot("2064531529:AAFjdN8IHOR1r906yg9ol2QkBTKUwp5ZaoQ")
group_id = "-1001649348891"
app = FastAPI(title="Backend documentation", description="This is documentation for developers", version="2.1.0")
app.mount("/static", StaticFiles(directory=path + "/static"), name="static")


@app.post("/video/")
async def upload_video(robotID: str = Form(...), cameraNUM: int = Form(...), createdtime: datetime = Form(...), uploaded_file: UploadFile = File(...)):
    try:
        file_location = f"static/video/{str(uploaded_file.filename)}"
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
            url_docker = "http://ai:4999/uploadfile/"
            r = requests.post(url_docker, files={"file": content})
            confidence = float(r.content[0]['confidence'])
            if confidence > 0.2:
                text = "WARNING!\n" + \
                    "Confidence: " + str(confidence) + \
                        "From robot: " + str(robotID) + \
                            "Camera number: " + str(cameraNUM) + \
                                "Created time: " + str(createdtime) + \
                                    "Link: http://185.121.81.245:7777/" + file_location
                bot.send_message(group_id, text)

        output = {
            "confidence": confidence,
            "location": "http://185.121.81.245:7777/" + file_location
        }
        return output
    except Exception as e:
        logging.error(e)
        return e


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True, workers=4)
