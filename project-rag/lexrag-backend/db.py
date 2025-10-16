from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
# Connect to local MongoDB Compass
MONGO_URL = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URL)

db = client["lexrag"]          # database
users_collection = db["users"] # collection
