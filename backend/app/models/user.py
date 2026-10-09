# from pydantic import BaseModel, Field
# from typing import Literal, List, Optional
#
# class RegisterRequest(BaseModel):
#     country: str
#     city: str
#     pincode: str = Field(..., min_length=6, max_length=6)
#     gender: Literal["Male", "Female", "Other"]
#     want_to: Literal["Find a RentPeople", "Become a RentPeople", "Both"]
#     mobile: str = Field(..., min_length=10, max_length=10)
#     email: str
#     password: str = Field(..., min_length=6)
#     # NEW — optional at register (frontend can send after geolocation)
#     lat: Optional[float] = None
#     lng: Optional[float] = None
#
#
# class LoginRequest(BaseModel):
#     email: str
#     password: str
#
#
# class FeedRequest(BaseModel):
#     lat: float
#     lng: float
#     city: Optional[str] = None
#     user_id: Optional[str] = None
#     radius_km: Optional[float] = None  # optional — if None, no hard radius cut (still sorted by distance)
#
# class UserResponse(BaseModel):
#     id: str
#     email: str
#     mobile: str
#     country: str
#     city: str
#     gender: str
#     want_to: str
#     message: str
#     lat: Optional[float] = None
#     lng: Optional[float] = None
#
#
# class TokenResponse(BaseModel):
#     access_token: str
#     token_type: str = "bearer"
#     user: dict
#
#
# class ServiceItem(BaseModel):
#     id: Optional[str] = None
#     name: str
#     price: int = 0
#
#
# class ProfileUpdate(BaseModel):
#     fullName: Optional[str] = None
#     phone: Optional[str] = None
#     city: Optional[str] = None
#     lat: Optional[float] = None
#     lng: Optional[float] = None
#     gender: Optional[str] = None
#     price: Optional[int] = None
#     bio: Optional[str] = None
#     image: Optional[str] = None
#     isAvailable: Optional[bool] = None
#     availableTime: Optional[str] = None
#     languages: Optional[str] = None
#     interests: Optional[str] = None
#     services: Optional[List[ServiceItem]] = None   # ← now accepts objects
#     gallery: Optional[List[str]] = None
#
# class BookingCreate(BaseModel):
#     booking_date: str
#     start_time: str
#     end_time: str
#     timezone: Optional[str] = "Asia/Kolkata"
#     duration_minutes: int
#     location_type: Literal["in_person", "online"]
#     location: Optional[str] = None
#     service_id: Optional[str] = None
#     service_name: Optional[str] = None
#     rent_person_id: str
#     special_requirements: Optional[str] = None
#     customer_note: Optional[str] = None
#     price: int
#     platform_fee: int
#     total_amount: int
#
#
# class BookingReject(BaseModel):
#     rejection_message: Optional[str] = None
#
# class MessageCreate(BaseModel):
#     receiver_id: str
#     content: str = Field(..., min_length=1, max_length=2000)
#
# class ForgotPasswordRequest(BaseModel):
#     email: str
#
#
# class ResetPasswordRequest(BaseModel):
#     token: str
#     new_password: str = Field(..., min_length=6)
#
# class VerifyOtpRequest(BaseModel):
#     otp: str = Field(..., min_length=6, max_length=6)
#
# class WalletTopUpRequest(BaseModel):
#     amount: float = Field(..., ge=100)
#     method: Optional[str] = "UPI"  # UPI | Card | etc.
#
# class RatingCreate(BaseModel):
#     stars: int = Field(..., ge=1, le=5)
#     message: Optional[str] = Field(None, max_length=1000)


from pydantic import BaseModel, Field
from typing import Literal, List, Optional


class RegisterRequest(BaseModel):
    name: Optional[str] = None
    fullName: Optional[str] = None
    country: str
    city: str
    pincode: str = Field(..., min_length=6, max_length=6)
    gender: Literal["Male", "Female", "Other"]
    want_to: Literal["finder", "companion"]
    mobile: str = Field(..., min_length=10, max_length=10)
    email: str
    password: str = Field(..., min_length=6)
    lat: Optional[float] = None
    lng: Optional[float] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class FeedRequest(BaseModel):
    lat: float
    lng: float
    city: Optional[str] = None
    user_id: Optional[str] = None
    radius_km: Optional[float] = None


class UserResponse(BaseModel):
    id: str
    account_id: Optional[str] = None
    email: str
    mobile: str
    country: str
    city: str
    gender: str
    want_to: str
    role: Optional[str] = None
    name: Optional[str] = None
    fullName: Optional[str] = None
    message: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class TokenResponse(BaseModel):
    access_token: str
    token: Optional[str] = None
    token_type: str = "bearer"
    user: dict


class ServiceItem(BaseModel):
    id: Optional[str] = None
    name: str
    price: int = 0
    title: Optional[str] = None
    duration: Optional[str] = None


class ProfileUpdate(BaseModel):
    fullName: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    gender: Optional[str] = None
    price: Optional[int] = None
    bio: Optional[str] = None
    image: Optional[str] = None
    isAvailable: Optional[bool] = None
    availableTime: Optional[str] = None
    languages: Optional[str] = None
    interests: Optional[str] = None
    services: Optional[List[ServiceItem]] = None
    gallery: Optional[List[str]] = None


class BookingCreate(BaseModel):
    booking_date: str
    start_time: str
    end_time: str
    timezone: Optional[str] = "Asia/Kolkata"
    duration_minutes: int
    location_type: Literal["in_person", "online"]
    location: Optional[str] = None
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    rent_person_id: str
    special_requirements: Optional[str] = None
    customer_note: Optional[str] = None
    price: int
    platform_fee: int
    total_amount: int


class BookingReject(BaseModel):
    rejection_message: Optional[str] = None


class MessageCreate(BaseModel):
    receiver_id: Optional[str] = None
    to_user_id: Optional[str] = None  # Flutter alias
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    text: Optional[str] = None        # Flutter alias
    message: Optional[str] = None     # Flutter alias


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)
    email: Optional[str] = None  # Flutter may send; optional


class VerifyOtpRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6)


class WalletTopUpRequest(BaseModel):
    amount: float = Field(..., ge=100)
    method: Optional[str] = "UPI"


class WalletWithdrawRequest(BaseModel):
    amount: float = Field(..., ge=100)
    note: Optional[str] = None


class RatingCreate(BaseModel):
    stars: int = Field(..., ge=1, le=5)
    message: Optional[str] = Field(None, max_length=1000)


class ReviewCreate(BaseModel):
    booking_id: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    stars: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    message: Optional[str] = Field(None, max_length=1000)


class KycSubmitRequest(BaseModel):
    doc_type: Optional[str] = None
    doc_number: Optional[str] = None
    document_url: Optional[str] = None
    selfie_url: Optional[str] = None
    docType: Optional[str] = None
    docNumber: Optional[str] = None
    documentUrl: Optional[str] = None
    selfieUrl: Optional[str] = None

class PayoutMethodCreate(BaseModel):
    type: Literal["upi", "bank"]
    upi_id: Optional[str] = None
    account_holder: Optional[str] = None
    account_number: Optional[str] = None
    ifsc: Optional[str] = None
    bank_name: Optional[str] = None
    is_default: Optional[bool] = False