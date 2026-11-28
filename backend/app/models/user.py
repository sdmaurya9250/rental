

from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Union, Any, Dict


class PreferredLocation(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class LoginRequest(BaseModel):
    """Login with mobile + password."""
    mobile: Optional[str] = None
    password: str = Field(..., min_length=6)


class FeedRequest(BaseModel):
    lat: float
    lng: float
    city: Optional[str] = None
    area: Optional[str] = None
    user_id: Optional[str] = None
    radius_km: Optional[float] = None
    expand: Optional[bool] = True


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
    locations: Optional[List[str]] = None
    preferred_locations: Optional[List[PreferredLocation]] = None
    interests: Optional[List[str]] = None
    available_time: Optional[Dict[str, Any]] = None
    availableTime: Optional[Dict[str, Any]] = None
    time_slots: Optional[List[Any]] = None
    timeSlots: Optional[List[Any]] = None


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
    availableTime: Optional[Union[str, dict, list]] = None
    languages: Optional[Union[str, List[str]]] = None
    interests: Optional[Union[str, List[str]]] = None
    services: Optional[List[ServiceItem]] = None
    gallery: Optional[List[str]] = None
    preferred_locations: Optional[List[PreferredLocation]] = None
    preferredLocations: Optional[List[PreferredLocation]] = None


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
    # Money fields from the client are ignored; the server recalculates them
    # from the companion's saved service price.
    price: Optional[int] = None
    platform_fee: Optional[int] = None
    total_amount: Optional[int] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_category: Optional[str] = None
    # One key per booking attempt. Same key again returns the same booking.
    idempotency_key: Optional[str] = Field(None, min_length=8, max_length=64)


class BookingReject(BaseModel):
    rejection_message: Optional[str] = None


class MessageCreate(BaseModel):
    receiver_id: Optional[str] = None
    to_user_id: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    text: Optional[str] = None
    message: Optional[str] = None


class VerifyOtpRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6)


class WalletTopUpRequest(BaseModel):
    amount: float = Field(..., ge=1)
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


class CompanionServiceItem(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    price: int = Field(..., ge=0)
    duration: Optional[str] = "1 hr"
    title: Optional[str] = None
    locations: Optional[List[str]] = None
    preferred_locations: Optional[List[PreferredLocation]] = None
    interests: Optional[List[str]] = None
    available_time: Optional[Dict[str, Any]] = None
    availableTime: Optional[Dict[str, Any]] = None
    time_slots: Optional[List[Any]] = None
    timeSlots: Optional[List[Any]] = None


class CompanionServicesReplace(BaseModel):
    services: List[CompanionServiceItem]
