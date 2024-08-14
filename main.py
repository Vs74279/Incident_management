from fastapi import FastAPI, Depends, HTTPException, Query, status, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, relationship
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import random
 
# Initialize the FastAPI app
app = FastAPI()
 
# Serve static files (CSS, JS, Images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")
 
# JWT setup
SECRET_KEY = "your_secret_key"  # Replace with your actual secret key
ALGORITHM = "HS256"
 
# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
# Database setup for PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Vikash8435@localhost:5432/testdb"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
 
# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
# Example data for pin codes
pin_data = {
    "110001": {"city": "New Delhi", "country": "India"},
    "10001": {"city": "New York", "country": "USA"},
    "560001": {"city": "Bangalore", "country": "India"},
    "94101": {"city": "San Francisco", "country": "USA"},
    "400001": {"city": "Mumbai", "country": "India"},
    "20001": {"city": "Washington D.C.", "country": "USA"},
    "841245": {"city": "Siwan", "country": "India"},
}
 
# Pydantic models for data validation
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    address: str
    pin_code: str
    city: str
    country: str
    password: str
 
class LoginRequest(BaseModel):
    username: str
    password: str
 
class IncidentCreate(BaseModel):
    title: str
    description: str
    priority: str
    reporter_id: int  # Add reporter_id to the model
 
class PasswordResetRequest(BaseModel):
    email: EmailStr
 
class PasswordReset(BaseModel):
    token: str
    new_password: str
 
# SQLAlchemy models
class User(Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    address = Column(String)
    pin_code = Column(String)
    city = Column(String)
    country = Column(String)
    hashed_password = Column(String)
 
    incidents = relationship("Incident", back_populates="owner")
 
class Incident(Base):
    __tablename__ = "incidents"
 
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(String)
    status = Column(String)
    reported_at = Column(DateTime)
    reporter_id = Column(Integer, ForeignKey("users.id"))
 
    owner = relationship("User", back_populates="incidents")
 
# Create the database tables
Base.metadata.create_all(bind=engine)
 
# Helper function to generate unique incident IDs
def generate_incident_id():
    return f"RMG{random.randint(10000, 99999)}{datetime.now().year}"
 
# Helper functions for password management
def get_password_hash(password):
    return pwd_context.hash(password)
 
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
 
def create_reset_token(email: str):
    expiration = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    return jwt.encode({"sub": email, "exp": expiration}, SECRET_KEY, algorithm=ALGORITHM)
 
def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
 
def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
 
@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        address=user.address,
        pin_code=user.pin_code,
        city=user.city,
        country=user.country,
        hashed_password=hashed_password  # Store hashed password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"username": db_user.username, "email": db_user.email}
 
@app.post("/login/")
def login_user(login: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == login.username).first()
    if not db_user or not verify_password(login.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username or password")
    token = jwt.encode({"sub": db_user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"message": "Login successful", "token": token}
 
@app.post("/create-incident/")
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    # Validate reporter_id
    reporter = db.query(User).filter(User.id == incident.reporter_id).first()
    if not reporter:
        raise HTTPException(status_code=400, detail="Invalid reporter_id")
 
    # Create new incident
    db_incident = Incident(
        incident_id=generate_incident_id(),
        title=incident.title,
        description=incident.description,
        priority=incident.priority,
        status="Open",
        reported_at=datetime.now(),
        reporter_id=incident.reporter_id
    )
 
    # Add incident to the database
    try:
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        return {"incident_id": db_incident.incident_id, "status": db_incident.status}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create incident: {e}")
 
@app.post("/password-reset-request/")
def password_reset_request(request: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
 
    token = create_reset_token(user.email)
 
    # For testing, return the token directly instead of sending an email
    return {"token": token}
 
@app.post("/reset-password/")
def reset_password(reset: PasswordReset, db: Session = Depends(get_db)):
    email = verify_reset_token(reset.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
 
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
 
    user.hashed_password = get_password_hash(reset.new_password)  # Store hashed password
    db.add(user)
    db.commit()
    return {"message": "Password reset successful"}
 
@app.get("/all-incidents/")
def get_all_incidents(db: Session = Depends(get_db)):
    incidents = db.query(Incident).all()
    return [
        {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "description": incident.description,
            "priority": incident.priority,
            "status": incident.status
        }
        for incident in incidents
    ]
 
@app.get("/location/")
def get_location_by_pin(pin_code: str = Query(...)):
    if pin_code in pin_data:
        return pin_data[pin_code]
    else:
        raise HTTPException(status_code=404, detail="Location not found for the given pin code")
 
# Endpoint to get the logged-in user's ID
@app.get("/get-user-id/")
def get_user_id(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = authorization.split(" ")[1]  # Assuming 'Bearer <token>' format
    user = get_user_from_token(token, db)
    return {"user_id": user.id}
 
# Serve the frontend HTML files
@app.get("/")
def serve_frontend():
    return FileResponse('static/index.html')
 
@app.get("/incidents/")
def serve_incidents_page():
    return FileResponse('static/incidents.html')
 