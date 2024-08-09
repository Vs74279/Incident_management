from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

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
