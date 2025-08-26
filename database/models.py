from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class RentalStatus(enum.Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"


class RentalType(enum.Enum):
    SHORT_TERM = "short_term"  # Краткосрочная
    LONG_TERM = "long_term"    # Долгосрочная


class ExpenseType(enum.Enum):
    MAINTENANCE = "maintenance"  # ТО
    REPAIR = "repair"           # Ремонт
    INSURANCE = "insurance"     # Страховка
    FUEL = "fuel"              # Бензин
    OTHER = "other"            # Другое


class Car(Base):
    __tablename__ = "cars"
    
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(100), nullable=False)  # Марка
    model = Column(String(100), nullable=False)  # Модель
    vin = Column(String(17), unique=True, nullable=False)  # VIN
    license_plate = Column(String(20), unique=True, nullable=False)  # Госномер
    daily_rate = Column(Float, nullable=False)  # Стоимость в день
    photo_path = Column(String(500))  # Путь к фото
    status = Column(Enum(RentalStatus), default=RentalStatus.AVAILABLE)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    expenses = relationship("Expense", back_populates="car")
    rentals = relationship("Rental", back_populates="car")


class Renter(Base):
    __tablename__ = "renters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)  # ФИО
    phone = Column(String(20), nullable=False)  # Телефон
    email = Column(String(100))  # Email
    passport = Column(String(50))  # Паспорт
    notes = Column(Text)  # Заметки
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rentals = relationship("Rental", back_populates="renter")


class Rental(Base):
    __tablename__ = "rentals"
    
    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    renter_id = Column(Integer, ForeignKey("renters.id"), nullable=False)
    
    rental_type = Column(Enum(RentalType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    daily_rate = Column(Float, nullable=False)  # Фиксированная ставка на момент аренды
    
    total_amount = Column(Float, nullable=False)  # Общая сумма
    paid_amount = Column(Float, default=0.0)  # Оплачено
    deposit = Column(Float, default=0.0)  # Залог
    
    is_active = Column(Boolean, default=True)
    is_overdue = Column(Boolean, default=False)  # Просрочка
    overdue_days = Column(Integer, default=0)  # Дни просрочки
    
    contract_notes = Column(Text)  # Заметки к договору
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    car = relationship("Car", back_populates="rentals")
    renter = relationship("Renter", back_populates="rentals")
    payments = relationship("Payment", back_populates="rental")
    fines = relationship("Fine", back_populates="rental")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    rental_id = Column(Integer, ForeignKey("rentals.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Сумма платежа
    payment_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)  # Заметки
    
    # Relationships
    rental = relationship("Rental", back_populates="payments")


class Fine(Base):
    __tablename__ = "fines"
    
    id = Column(Integer, primary_key=True, index=True)
    rental_id = Column(Integer, ForeignKey("rentals.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Сумма штрафа
    reason = Column(String(500), nullable=False)  # Причина штрафа
    fine_date = Column(DateTime, default=datetime.utcnow)
    is_paid = Column(Boolean, default=False)
    
    # Relationships
    rental = relationship("Rental", back_populates="fines")


class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False)
    expense_type = Column(Enum(ExpenseType), nullable=False)
    amount = Column(Float, nullable=False)  # Сумма расхода
    description = Column(Text)  # Описание
    expense_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    car = relationship("Car", back_populates="expenses")
