from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, date, timedelta
from database.models import Car, Renter, Rental, Payment, Fine, Expense, RentalStatus, RentalType, ExpenseType
from typing import List, Optional, Dict, Any


# Car CRUD
def create_car(db: Session, brand: str, model: str, vin: str, license_plate: str, 
               daily_rate: float, photo_path: Optional[str] = None) -> Car:
    car = Car(
        brand=brand,
        model=model,
        vin=vin,
        license_plate=license_plate,
        daily_rate=daily_rate,
        photo_path=photo_path
    )
    db.add(car)
    db.commit()
    db.refresh(car)
    return car


def get_cars(db: Session, skip: int = 0, limit: int = 100) -> List[Car]:
    return db.query(Car).offset(skip).limit(limit).all()


def get_car_by_id(db: Session, car_id: int) -> Optional[Car]:
    return db.query(Car).filter(Car.id == car_id).first()


def get_available_cars(db: Session) -> List[Car]:
    return db.query(Car).filter(Car.status == RentalStatus.AVAILABLE).all()


def update_car_status(db: Session, car_id: int, status: RentalStatus):
    db.query(Car).filter(Car.id == car_id).update({Car.status: status})
    db.commit()


# Renter CRUD
def create_renter(db: Session, name: str, phone: str, email: Optional[str] = None, 
                  passport: Optional[str] = None, notes: Optional[str] = None) -> Renter:
    renter = Renter(
        name=name,
        phone=phone,
        email=email,
        passport=passport,
        notes=notes
    )
    db.add(renter)
    db.commit()
    db.refresh(renter)
    return renter


def get_renters(db: Session) -> List[Renter]:
    return db.query(Renter).all()


def get_renter_by_phone(db: Session, phone: str) -> Optional[Renter]:
    return db.query(Renter).filter(Renter.phone == phone).first()


# Rental CRUD
def create_rental(db: Session, car_id: int, renter_id: int, rental_type: RentalType,
                  start_date: date, end_date: date, daily_rate: float,
                  deposit: float = 0.0, contract_notes: Optional[str] = None) -> Rental:
    
    days = (end_date - start_date).days + 1
    total_amount = daily_rate * days
    
    rental = Rental(
        car_id=car_id,
        renter_id=renter_id,
        rental_type=rental_type,
        start_date=start_date,
        end_date=end_date,
        daily_rate=daily_rate,
        total_amount=total_amount,
        deposit=deposit,
        contract_notes=contract_notes
    )
    db.add(rental)
    db.commit()
    db.refresh(rental)
    
    # Update car status
    update_car_status(db, car_id, RentalStatus.RENTED)
    
    return rental


def get_active_rentals(db: Session) -> List[Rental]:
    return db.query(Rental).filter(Rental.is_active == True).all()


def get_rental_by_id(db: Session, rental_id: int) -> Optional[Rental]:
    return db.query(Rental).filter(Rental.id == rental_id).first()


def get_car_rental_history(db: Session, car_id: int) -> List[Rental]:
    return db.query(Rental).filter(Rental.car_id == car_id).order_by(desc(Rental.created_at)).all()


def check_overdue_rentals(db: Session):
    """Check and update overdue rentals"""
    today = date.today()
    overdue_rentals = db.query(Rental).filter(
        and_(
            Rental.is_active == True,
            Rental.end_date < today
        )
    ).all()
    
    for rental in overdue_rentals:
        overdue_days = (today - rental.end_date).days
        rental.is_overdue = True
        rental.overdue_days = overdue_days
    
    db.commit()
    return overdue_rentals


def end_rental(db: Session, rental_id: int):
    """End rental and free up the car"""
    rental = get_rental_by_id(db, rental_id)
    if rental:
        rental.is_active = False
        update_car_status(db, rental.car_id, RentalStatus.AVAILABLE)
        db.commit()


# Payment CRUD
def create_payment(db: Session, rental_id: int, amount: float, notes: Optional[str] = None) -> Payment:
    payment = Payment(
        rental_id=rental_id,
        amount=amount,
        notes=notes
    )
    db.add(payment)
    
    # Update paid amount in rental
    rental = get_rental_by_id(db, rental_id)
    if rental:
        rental.paid_amount += amount
    
    db.commit()
    db.refresh(payment)
    return payment


def get_rental_payments(db: Session, rental_id: int) -> List[Payment]:
    return db.query(Payment).filter(Payment.rental_id == rental_id).all()


# Fine CRUD
def create_fine(db: Session, rental_id: int, amount: float, reason: str) -> Fine:
    fine = Fine(
        rental_id=rental_id,
        amount=amount,
        reason=reason
    )
    db.add(fine)
    db.commit()
    db.refresh(fine)
    return fine


def get_rental_fines(db: Session, rental_id: int) -> List[Fine]:
    return db.query(Fine).filter(Fine.rental_id == rental_id).all()


# Expense CRUD
def create_expense(db: Session, car_id: int, expense_type: ExpenseType,
                   amount: float, description: Optional[str] = None) -> Expense:
    expense = Expense(
        car_id=car_id,
        expense_type=expense_type,
        amount=amount,
        description=description
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def get_car_expenses(db: Session, car_id: int) -> List[Expense]:
    return db.query(Expense).filter(Expense.car_id == car_id).all()


def get_expenses_by_period(db: Session, start_date: datetime, end_date: datetime) -> List[Expense]:
    return db.query(Expense).filter(
        and_(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        )
    ).all()


# Analytics
def get_car_profitability(db: Session, car_id: int) -> Dict[str, Any]:
    """Calculate car profitability"""
    car = get_car_by_id(db, car_id)
    if not car:
        return {}
    
    # Total income (payments)
    total_income = db.query(func.sum(Payment.amount)).join(Rental).filter(
        Rental.car_id == car_id
    ).scalar() or 0
    
    # Total expenses
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.car_id == car_id
    ).scalar() or 0
    
    # Net profit
    net_profit = total_income - total_expenses
    
    # ROI calculation (assuming initial investment as yearly expenses)
    roi = (net_profit / total_expenses * 100) if total_expenses > 0 else 0
    
    return {
        "car_id": car_id,
        "car_info": f"{car.brand} {car.model} ({car.license_plate})",
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "roi": roi
    }


def get_monthly_income(db: Session, year: int, month: int) -> float:
    """Get total income for a specific month"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    return db.query(func.sum(Payment.amount)).filter(
        and_(
            Payment.payment_date >= start_date,
            Payment.payment_date < end_date
        )
    ).scalar() or 0


def get_monthly_expenses(db: Session, year: int, month: int) -> float:
    """Get total expenses for a specific month"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    return db.query(func.sum(Expense.amount)).filter(
        and_(
            Expense.expense_date >= start_date,
            Expense.expense_date < end_date
        )
    ).scalar() or 0
