from pydantic import BaseModel, EmailStr

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
    reporter_id: int

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
