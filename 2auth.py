from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import database
import re

app = FastAPI()

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Secret Key for JWT
SECRET_KEY = "493869e1fabb5f07a2bcba608030c78b2eccd81cfaa5ebe8c97c81c5db584618"
ALGORITHM = "HS256"

#  Pydantic Model for User Registration
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8)

# Pydantic Model for User Login
class UserLogin(BaseModel):
    username: str
    password: str

#  Register New User with Validation
@app.post("/register/")
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    # Ensure username only contains letters, numbers, and underscores
    if not re.match("^[a-zA-Z0-9_]+$", user.username):
        raise HTTPException(status_code=400, detail="Username can only contain letters, numbers, and underscores.")

    # Check if username already exists
    existing_user = db.query(database.User).filter(database.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists.")

    # Check if email is already registered
    existing_email = db.query(database.User).filter(database.User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Hash the password before storing
    hashed_password = pwd_context.hash(user.password)
    new_user = database.User(username=user.username, email=user.email, password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully!"}

# Login API (Returns JWT Token)
@app.post("/login/")
def login(user: UserLogin, db: Session = Depends(database.get_db)):
    existing_user = db.query(database.User).filter(database.User.username == user.username).first()

    # Check if user exists
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")

    # Verify Password
    if not pwd_context.verify(user.password, existing_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")

    # Generate JWT Token
    token = jwt.encode({"sub": existing_user.username}, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": token, "token_type": "bearer"}
