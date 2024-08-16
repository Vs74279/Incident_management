from fastapi import FastAPI, Depends, HTTPException, Query, status, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from database import SessionLocal, engine
from models import Base, User, Incident
from schemas import UserCreate, LoginRequest, IncidentCreate, PasswordResetRequest, PasswordReset
from utils import (
    get_password_hash, verify_password, create_reset_token,
    verify_reset_token, get_user_from_token, generate_incident_id,
)
import random

# Initialize the FastAPI app
app = FastAPI()

# Serve static files (CSS, JS, Images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create the database tables
Base.metadata.create_all(bind=engine)

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
        hashed_password=hashed_password
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
    token = jwt.encode({"sub": db_user.username}, "your_secret_key", algorithm="HS256")
    return {"message": "Login successful", "token": token}

@app.post("/create-incident/")
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    reporter = db.query(User).filter(User.id == incident.reporter_id).first()
    if not reporter:
        raise HTTPException(status_code=400, detail="Invalid reporter_id")
    db_incident = Incident(
        incident_id=generate_incident_id(),
        title=incident.title,
        description=incident.description,
        priority=incident.priority,
        status="Open",
        reported_at=datetime.now(),
        reporter_id=incident.reporter_id
    )
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
    return {"token": token}

@app.post("/reset-password/")
def reset_password(reset: PasswordReset, db: Session = Depends(get_db)):
    email = verify_reset_token(reset.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = get_password_hash(reset.new_password)
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

@app.get("/get-user-id/")
def get_user_id(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = authorization.split(" ")[1]
    user = get_user_from_token(token, db)
    return {"user_id": user.id}

@app.get("/")
def serve_frontend():
    return FileResponse('static/index.html')

@app.get("/incidents/")
def serve_incidents_page():
    return FileResponse('static/incidents.html')
