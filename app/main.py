from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hotel Reservation API",
    description="A small REST API for managing hotel rooms and reservations, "
    "built to demonstrate clean CRUD design, authentication, and testing.",
    version="1.0.0",
)


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok"}


# ---------------- Auth ----------------
@app.post("/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=user_in.email,
        hashed_password=auth.hash_password(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.create_access_token(data={"sub": user.email})
    return schemas.Token(access_token=token)


@app.get("/users/me", response_model=schemas.UserOut, tags=["auth"])
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# ---------------- Rooms ----------------
@app.post("/rooms", response_model=schemas.RoomOut, status_code=status.HTTP_201_CREATED, tags=["rooms"])
def create_room(
    room_in: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    existing = db.query(models.Room).filter(models.Room.number == room_in.number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Room number already exists")

    room = models.Room(**room_in.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@app.get("/rooms", response_model=list[schemas.RoomOut], tags=["rooms"])
def list_rooms(db: Session = Depends(get_db), active_only: bool = True):
    query = db.query(models.Room)
    if active_only:
        query = query.filter(models.Room.is_active.is_(True))
    return query.all()


@app.get("/rooms/{room_id}", response_model=schemas.RoomOut, tags=["rooms"])
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@app.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["rooms"])
def deactivate_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    room.is_active = False
    db.commit()
    return None


# ---------------- Reservations ----------------
def _rooms_overlap(existing_check_in, existing_check_out, new_check_in, new_check_out) -> bool:
    return existing_check_in < new_check_out and new_check_in < existing_check_out


@app.post(
    "/reservations", response_model=schemas.ReservationOut, status_code=status.HTTP_201_CREATED, tags=["reservations"]
)
def create_reservation(
    res_in: schemas.ReservationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    room = db.query(models.Room).filter(models.Room.id == res_in.room_id, models.Room.is_active.is_(True)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or inactive")

    conflicting = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.room_id == res_in.room_id,
            models.Reservation.status == "confirmed",
        )
        .all()
    )
    for existing in conflicting:
        if _rooms_overlap(existing.check_in, existing.check_out, res_in.check_in, res_in.check_out):
            raise HTTPException(status_code=409, detail="Room is not available for the selected dates")

    reservation = models.Reservation(
        room_id=res_in.room_id,
        user_id=current_user.id,
        check_in=res_in.check_in,
        check_out=res_in.check_out,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@app.get("/reservations/me", response_model=list[schemas.ReservationOut], tags=["reservations"])
def list_my_reservations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return db.query(models.Reservation).filter(models.Reservation.user_id == current_user.id).all()


@app.post("/reservations/{reservation_id}/cancel", response_model=schemas.ReservationOut, tags=["reservations"])
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    reservation = (
        db.query(models.Reservation)
        .filter(models.Reservation.id == reservation_id, models.Reservation.user_id == current_user.id)
        .first()
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    reservation.status = "cancelled"
    db.commit()
    db.refresh(reservation)
    return reservation
