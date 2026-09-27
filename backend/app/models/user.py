from pydantic import BaseModel, Field
from typing import Literal


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