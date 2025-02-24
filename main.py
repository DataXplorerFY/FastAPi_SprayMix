from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from passlib.context import CryptContext
import os

load_dotenv()

app = FastAPI()

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv(
    "MONGO_URI", 
    "mongodb+srv://mindstale000:2sqxJILGoXod1ReG@cluster0.2u66e.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print("MongoDB connection failed:", e)

# Database and collection
db = client["spray_mix"]
users_collection = db["users_collection"]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Pydantic models
class RegisterRequest(BaseModel):
    number: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    number: str
    password: str

@app.get("/")
def home():
    return {"message": "API is working!"}

@app.post("/register")
def register(data: RegisterRequest):
    number = data.number
    password = data.password
    username = data.full_name

    if users_collection.find_one({"number": number}):
        raise HTTPException(status_code=409, detail="User already exists.")

    hashed_password = hash_password(password)
    new_user = {"number": number, "password": hashed_password, "username": username}
    users_collection.insert_one(new_user)

    return {"message": "User registered successfully."}

@app.post("/login")
def login(data: LoginRequest):
    number = data.number
    password = data.password

    user = users_collection.find_one({"number": number})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid number or password.")

    return {"message": "Login successful."}

@app.post("/delete_account")
def delete_account(data: LoginRequest):
    number = data.number
    password = data.password

    user = users_collection.find_one({"number": number})
    
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid number or password.")

    users_collection.delete_one({"number": number})
    return {"message": "Account deleted successfully."}

