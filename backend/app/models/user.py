from pydantic import BaseModel, Field
from typing import Literal, List, Optional


class RegisterRequest(BaseModel):
    country: str
    city: str
    pincode: str = Field(..., min_length=6, max_length=6)
    gender: Literal["Male", "Female", "Other"]
    want_to: Literal["Find a RentPeople", "Become a RentPeople", "Both"]
    mobile: str = Field(..., min_length=10, max_length=10)
    email: str
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    mobile: str
    country: str
    city: str
    gender: str
    want_to: str
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ServiceItem(BaseModel):
    id: Optional[str] = None
    name: str
    price: int = 0


class ProfileUpdate(BaseModel):
    fullName: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    gender: Optional[str] = None
    price: Optional[int] = None
    bio: Optional[str] = None
    image: Optional[str] = None
    isAvailable: Optional[bool] = None
    availableTime: Optional[str] = None
    languages: Optional[str] = None
    interests: Optional[str] = None
    services: Optional[List[ServiceItem]] = None   # ← now accepts objects
    gallery: Optional[List[str]] = None