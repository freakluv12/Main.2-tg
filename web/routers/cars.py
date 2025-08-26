from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database.database import get_db
from database import crud
from database.models import RentalStatus
from web.routers.auth import get_current_user

router = APIRouter()


class CarResponse(BaseModel):
    id: int
    brand: str
    model: str
    vin: str
    license_plate: str
    daily_rate: float
    status: str
    photo_path: Optional[str]
    total_income: float
    total_expenses: float
    net_profit: float
    rental_count: int

    class Config:
        from_attributes = True


class CarCreate(BaseModel):
    brand: str
    model: str
    vin: str
    license_plate: str
    daily_rate: float
    photo_path: Optional[str] = None


@router.get("/", response_model=List[CarResponse])
async def get_cars(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of cars with optional filtering"""
    cars = crud.get_cars(db, skip=skip, limit=limit)
    
    # Filter by status if provided
    if status:
        try:
            status_enum = RentalStatus(status)
            cars = [car for car in cars if car.status == status_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    # Calculate additional data for each car
    cars_response = []
    for car in cars:
        # Calculate total income from payments
        total_income = sum(
            payment.amount 
            for rental in car.rentals 
            for payment in rental.payments
        )
        
        # Calculate total expenses
        total_expenses = sum(expense.amount for expense in car.expenses)
        
        # Net profit
        net_profit = total_income - total_expenses
        
        # Rental count
        rental_count = len(car.rentals)
        
        cars_response.append(CarResponse(
            id=car.id,
            brand=car.brand,
            model=car.model,
            vin=car.vin,
            license_plate=car.license_plate,
            daily_rate=car.daily_rate,
            status=car.status.value,
            photo_path=car.photo_path,
            total_income=total_income,
            total_expenses=total_expenses,
            net_profit=net_profit,
            rental_count=rental_count
        ))
    
    return cars_response


@router.get("/{car_id}", response_model=CarResponse)
async def get_car(
    car_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific car by ID"""
    car = crud.get_car_by_id(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    # Calculate additional data
    total_income = sum(
        payment.amount 
        for rental in car.rentals 
        for payment in rental.payments
    )
    total_expenses = sum(expense.amount for expense in car.expenses)
    net_profit = total_income - total_expenses
    rental_count = len(car.rentals)
    
    return CarResponse(
        id=car.id,
        brand=car.brand,
        model=car.model,
        vin=car.vin,
        license_plate=car.license_plate,
        daily_rate=car.daily_rate,
        status=car.status.value,
        photo_path=car.photo_path,
        total_income=total_income,
        total_expenses=total_expenses,
        net_profit=net_profit,
        rental_count=rental_count
    )


@router.post("/", response_model=CarResponse)
async def create_car(
    car_data: CarCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new car"""
    # Check if VIN already exists
    existing_car = db.query(crud.Car).filter(crud.Car.vin == car_data.vin).first()
    if existing_car:
        raise HTTPException(status_code=400, detail="Car with this VIN already exists")
    
    # Check if license plate already exists
    existing_plate = db.query(crud.Car).filter(crud.Car.license_plate == car_data.license_plate).first()
    if existing_plate:
        raise HTTPException(status_code=400, detail="Car with this license plate already exists")
    
    car = crud.create_car(
        db=db,
        brand=car_data.brand,
        model=car_data.model,
        vin=car_data.vin,
        license_plate=car_data.license_plate,
        daily_rate=car_data.daily_rate,
        photo_path=car_data.photo_path
    )
    
    return CarResponse(
        id=car.id,
        brand=car.brand,
        model=car.model,
        vin=car.vin,
        license_plate=car.license_plate,
        daily_rate=car.daily_rate,
        status=car.status.value,
        photo_path=car.photo_path,
        total_income=0.0,
        total_expenses=0.0,
        net_profit=0.0,
        rental_count=0
    )


@router.get("/{car_id}/history")
async def get_car_history(
    car_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get rental history for a specific car"""
    car = crud.get_car_by_id(db, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    rentals = crud.get_car_rental_history(db, car_id)
    
    history = []
    for rental in rentals:
        history.append({
            "id": rental.id,
            "renter_name": rental.renter.name,
            "renter_phone": rental.renter.phone,
            "start_date": rental.start_date.isoformat(),
            "end_date": rental.end_date.isoformat(),
            "rental_type": rental.rental_type.value,
            "daily_rate": rental.daily_rate,
            "total_amount": rental.total_amount,
            "paid_amount": rental.paid_amount,
            "is_active": rental.is_active,
            "is_overdue": rental.is_overdue,
            "overdue_days": rental.overdue_days,
            "created_at": rental.created_at.isoformat()
        })
    
    return {"car_id": car_id, "history": history}
