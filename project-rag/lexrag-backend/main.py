from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
from db import users_collection
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()
# Get values from .env
FRONTEND_URL = os.getenv("FRONTEND_URL")

origins = [
    "http://localhost:3000",  # React frontend
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # allow only your frontend origin
    allow_credentials=True,
    allow_methods=["*"],        # allow POST, GET, PUT, DELETE etc.
    allow_headers=["*"],        # allow all headers
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str

# @app.post("/signup")
@app.post("/signup")
def signup(user: User):
    try:
        if user.password != user.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        if users_collection.find_one({"email": user.email}):
            raise HTTPException(status_code=400, detail="Email already registered")

        # Truncate password to 72 chars for bcrypt
        hashed_password = pwd_context.hash(user.password[:72])

        users_collection.insert_one({
            "username": user.username,
            "email": user.email,
            "password": hashed_password
        })
        return {"message": "User created successfully"}

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=str(e))


class LoginUser(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(user: LoginUser):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    
    # Verify password
    if not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    return {"message": "Login successful"}
