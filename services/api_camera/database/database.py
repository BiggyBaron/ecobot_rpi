from pymongo import MongoClient
from datetime import date, datetime, timedelta


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

