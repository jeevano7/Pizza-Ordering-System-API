from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from jose import JWTError, jwt
from werkzeug.security import generate_password_hash, check_password_hash
import uvicorn

#FastAPI app
app = FastAPI()

#Database setup
DATABASE_URL = "postgresql://user:password@localhost/pizza_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password_hash = Column(String)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    item = Column(String)
    quantity = Column(Integer)
    status = Column(String)

Base.metadata.create_all(bind=engine)

#Pydantic schemas
class UserCreate(BaseModel):
    username: str
    password: str

class OrderCreate(BaseModel):
    user_id: int
    item: str
    quantity: int

#JWT settings
SECRET_KEY = "*****************"
ALGORITHM = "HS256"

#Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Routes
@app.post("/signup")
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = generate_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    return {"message": "User created"}

@app.post("/login")
async def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not check_password_hash(db_user.password_hash, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode({"sub": user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}

@app.post("/order")
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = Order(user_id=order.user_id, item=order.item, quantity=order.quantity, status="pending")
    db.add(db_order)
    db.commit()
    return {"message": "Order created"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
