from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------- Users ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Rooms ----------
class RoomCreate(BaseModel):
    number: str
    room_type: str
    price_per_night: float = Field(gt=0)


class RoomOut(BaseModel):
    id: int
    number: str
    room_type: str
    price_per_night: float
    is_active: bool

    model_config = {"from_attributes": True}


# ---------- Reservations ----------
class ReservationCreate(BaseModel):
    room_id: int
    check_in: date
    check_out: date

    @field_validator("check_out")
    @classmethod
    def check_out_after_check_in(cls, v, info):
        check_in = info.data.get("check_in")
        if check_in and v <= check_in:
            raise ValueError("check_out must be after check_in")
        return v


class ReservationOut(BaseModel):
    id: int
    room_id: int
    user_id: int
    check_in: date
    check_out: date
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
