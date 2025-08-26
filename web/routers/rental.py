from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from database.database import get_db
from database import crud
from database.models import RentalType
from web.routers.auth import get_current_user

router = APIRouter()


class RenterResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str]
    passport: Optional[str]
    notes: Optional[str]
    active_rentals: int

    class Config:
        from_attributes = True


class RentalResponse(BaseModel):
    id: int
    car_id: int
    car_info: str
    renter_id: int
    renter_info: str
    rental_type: str
    start_date: str
    end_date: str
    daily_rate: float
    total_amount: float
    paid_amount: float
    deposit: float
    is_active: bool
    is_overdue: bool
    overdue_days: int
    contract_notes: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class RenterCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    passport: Optional[str] = None
    notes: Optional[str] = None


class RentalCreate(BaseModel):
    car_id: int
    renter_id: int
    rental_type: str  # "short_term" or "long_term"
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    deposit: float = 0.0
    contract_notes: Optional[str] = None


@router.get("/renters", response_model=List[RenterResponse])
async def get_renters(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all renters"""
    renters = crud.get_renters(db)
    
    renters_response = []
    for renter in renters:
        active_rentals = len([r for r in renter.rentals if r.is_active])
        
        renters_response.append(RenterResponse(
            id=renter.id,
            name=renter.name,
            phone=renter.phone,
            email=renter.email,
            passport=renter.passport,
            notes=renter.notes,
            active_rentals=active_rentals
        ))
    
    return renters_response


@router.post("/renters", response_model=RenterResponse)
async def create_renter(
    renter_data: RenterCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new renter"""
    # Check if phone already exists
    existing_renter = crud.get_renter_by_phone(db, renter_data.phone)
    if existing_renter:
        raise HTTPException(status_code=400, detail="Renter with this phone already exists")
    
    renter = crud.create_renter(
        db=db,
        name=renter_data.name,
        phone=renter_data.phone,
        email=renter_data.email,
        passport=renter_data.passport,
        notes=renter_data.notes
    )
    
    return RenterResponse(
        id=renter.id,
        name=renter.name,
        phone=renter.phone,
        email=renter.email,
        passport=renter.passport,
        notes=renter.notes,
        active_rentals=0
    )


@router.get("/rentals", response_model=List[RentalResponse])
async def get_rentals(
    active_only: bool = Query(False),
    overdue_only: bool = Query(False),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get rentals with optional filtering"""
    # Check for overdue rentals first
    crud.check_overdue_rentals(db)
    
    if active_only:
        rentals = crud.get_active_rentals(db)
    else:
        # Get all rentals
        rentals = db.query(crud.Rental).order_by(crud.Rental.created_at.desc()).all()
    
    if overdue_only:
        rentals = [r for r in rentals if r.is_overdue]
    
    rentals_response = []
    for rental in rentals:
        car_info = f"{rental.car.brand} {rental.car.model} ({rental.car.license_plate})"
        renter_info = f"{rental.renter.name} ({rental.renter.phone})"
        
        rentals_response.append(RentalResponse(
            id=rental.id,
            car_id=rental.car_id,
            car_info=car_info,
            renter_id=rental.renter_id,
            renter_info=renter_info,
            rental_type=rental.rental_type.value,
            start_date=rental.start_date.isoformat(),
            end_date=rental.end_date.isoformat(),
            daily_rate=rental.daily_rate,
            total_amount=rental.total_amount,
            paid_amount=rental.paid_amount,
            deposit=rental.deposit,
            is_active=rental.is_active,
            is_overdue=rental.is_overdue,
            overdue_days=rental.overdue_days,
            contract_notes=rental.contract_notes,
            created_at=rental.created_at.isoformat()
        ))
    
    return rentals_response


@router.post("/rentals", response_model=RentalResponse)
async def create_rental(
    rental_data: RentalCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new rental"""
    # Validate car exists and is available
    car = crud.get_car_by_id(db, rental_data.car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    if car.status != crud.RentalStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Car is not available")
    
    # Validate renter exists
    renter = db.query(crud.Renter).filter(crud.Renter.id == rental_data.renter_id).first()
    if not renter:
        raise HTTPException(status_code=404, detail="Renter not found")
    
    # Parse dates
    try:
        start_date = date.fromisoformat(rental_data.start_date)
        end_date = date.fromisoformat(rental_data.end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    # Validate rental type
    try:
        rental_type = RentalType(rental_data.rental_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rental type")
    
    rental = crud.create_rental(
        db=db,
        car_id=rental_data.car_id,
        renter_id=rental_data.renter_id,
        rental_type=rental_type,
        start_date=start_date,
        end_date=end_date,
        daily_rate=car.daily_rate,
        deposit=rental_data.deposit,
        contract_notes=rental_data.contract_notes
    )
    
    car_info = f"{rental.car.brand} {rental.car.model} ({rental.car.license_plate})"
    renter_info = f"{rental.renter.name} ({rental.renter.phone})"
    
    return RentalResponse(
        id=rental.id,
        car_id=rental.car_id,
        car_info=car_info,
        renter_id=rental.renter_id,
        renter_info=renter_info,
        rental_type=rental.rental_type.value,
        start_date=rental.start_date.isoformat(),
        end_date=rental.end_date.isoformat(),
        daily_rate=rental.daily_rate,
        total_amount=rental.total_amount,
        paid_amount=rental.paid_amount,
        deposit=rental.deposit,
        is_active=rental.is_active,
        is_overdue=rental.is_overdue,
        overdue_days=rental.overdue_days,
        contract_notes=rental.contract_notes,
        created_at=rental.created_at.isoformat()
    )


@router.get("/rentals/{rental_id}")
async def get_rental(
    rental_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get rental details with payments and fines"""
    rental = crud.get_rental_by_id(db, rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    payments = crud.get_rental_payments(db, rental_id)
    fines = crud.get_rental_fines(db, rental_id)
    
    car_info = f"{rental.car.brand} {rental.car.model} ({rental.car.license_plate})"
    renter_info = f"{rental.renter.name} ({rental.renter.phone})"
    
    return {
        "rental": RentalResponse(
            id=rental.id,
            car_id=rental.car_id,
            car_info=car_info,
            renter_id=rental.renter_id,
            renter_info=renter_info,
            rental_type=rental.rental_type.value,
            start_date=rental.start_date.isoformat(),
            end_date=rental.end_date.isoformat(),
            daily_rate=rental.daily_rate,
            total_amount=rental.total_amount,
            paid_amount=rental.paid_amount,
            deposit=rental.deposit,
            is_active=rental.is_active,
            is_overdue=rental.is_overdue,
            overdue_days=rental.overdue_days,
            contract_notes=rental.contract_notes,
            created_at=rental.created_at.isoformat()
        ),
        "payments": [
            {
                "id": payment.id,
                "amount": payment.amount,
                "payment_date": payment.payment_date.isoformat(),
                "notes": payment.notes
            }
            for payment in payments
        ],
        "fines": [
            {
                "id": fine.id,
                "amount": fine.amount,
                "reason": fine.reason,
                "fine_date": fine.fine_date.isoformat(),
                "is_paid": fine.is_paid
            }
            for fine in fines
        ]
    }


@router.post("/rentals/{rental_id}/payments")
async def add_payment(
    rental_id: int,
    amount: float,
    notes: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add payment to rental"""
    rental = crud.get_rental_by_id(db, rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")
    
    payment = crud.create_payment(db, rental_id, amount, notes)
    
    return {
        "id": payment.id,
        "amount": payment.amount,
        "payment_date": payment.payment_date.isoformat(),
        "notes": payment.notes
    }


@router.post("/rentals/{rental_id}/fines")
async def add_fine(
    rental_id: int,
    amount: float,
    reason: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add fine to rental"""
    rental = crud.get_rental_by_id(db, rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Fine amount must be positive")
    
    if not reason.strip():
        raise HTTPException(status_code=400, detail="Fine reason is required")
    
    fine = crud.create_fine(db, rental_id, amount, reason)
    
    return {
        "id": fine.id,
        "amount": fine.amount,
        "reason": fine.reason,
        "fine_date": fine.fine_date.isoformat(),
        "is_paid": fine.is_paid
    }


@router.put("/rentals/{rental_id}/end")
async def end_rental(
    rental_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End rental and free up the car"""
    rental = crud.get_rental_by_id(db, rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    if not rental.is_active:
        raise HTTPException(status_code=400, detail="Rental is already ended")
    
    crud.end_rental(db, rental_id)
    
    return {"message": "Rental ended successfully"}
