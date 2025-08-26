import os
from datetime import datetime, date
from typing import Optional
import config


def format_currency(amount: float) -> str:
    """Format amount in Georgian Lari"""
    return f"{amount:.2f} ₾"


def format_date(date_obj: date) -> str:
    """Format date for display"""
    return date_obj.strftime("%d.%m.%Y")


def format_datetime(datetime_obj: datetime) -> str:
    """Format datetime for display"""
    return datetime_obj.strftime("%d.%m.%Y %H:%M")


def parse_date(date_str: str) -> Optional[date]:
    """Parse date from string in format DD.MM.YYYY"""
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        return None


def save_photo(photo_data: bytes, filename: str) -> str:
    """Save photo and return path"""
    if not os.path.exists(config.UPLOAD_DIR):
        os.makedirs(config.UPLOAD_DIR)
    
    filepath = os.path.join(config.UPLOAD_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(photo_data)
    
    return filepath


def validate_vin(vin: str) -> bool:
    """Validate VIN number"""
    return len(vin) == 17 and vin.isalnum()


def validate_phone(phone: str) -> bool:
    """Basic phone validation"""
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    return len(digits) >= 9


def calculate_rental_days(start_date: date, end_date: date) -> int:
    """Calculate number of rental days"""
    return (end_date - start_date).days + 1


def format_car_info(car) -> str:
    """Format car information for display"""
    status_emoji = {
        "available": "✅",
        "rented": "🔴",
        "maintenance": "🔧"
    }
    
    emoji = status_emoji.get(car.status.value, "❓")
    
    return (
        f"{emoji} *{car.brand} {car.model}*\n"
        f"📋 Номер: `{car.license_plate}`\n"
        f"🆔 VIN: `{car.vin}`\n"
        f"💰 Тариф: {format_currency(car.daily_rate)}/день\n"
        f"📊 Статус: {get_status_text(car.status.value)}"
    )


def get_status_text(status: str) -> str:
    """Get status text in Russian"""
    status_map = {
        "available": "Доступна",
        "rented": "Сдана в аренду",
        "maintenance": "На обслуживании"
    }
    return status_map.get(status, "Неизвестно")


def format_rental_info(rental) -> str:
    """Format rental information for display"""
    car_info = f"{rental.car.brand} {rental.car.model} ({rental.car.license_plate})"
    renter_info = f"{rental.renter.name} ({rental.renter.phone})"
    
    rental_type = "Краткосрочная" if rental.rental_type.value == "short_term" else "Долгосрочная"
    
    days = calculate_rental_days(rental.start_date, rental.end_date)
    remaining_amount = rental.total_amount - rental.paid_amount
    
    status_text = ""
    if rental.is_overdue:
        status_text = f"⚠️ *Просрочка: {rental.overdue_days} дн.*\n"
    elif not rental.is_active:
        status_text = "✅ *Завершена*\n"
    
    return (
        f"📋 *Договор аренды №{rental.id}*\n\n"
        f"🚗 Машина: {car_info}\n"
        f"👤 Арендатор: {renter_info}\n"
        f"📅 Тип: {rental_type}\n"
        f"📆 Период: {format_date(rental.start_date)} - {format_date(rental.end_date)}\n"
        f"⏱ Дней: {days}\n"
        f"💰 Тариф: {format_currency(rental.daily_rate)}/день\n"
        f"💵 Общая сумма: {format_currency(rental.total_amount)}\n"
        f"✅ Оплачено: {format_currency(rental.paid_amount)}\n"
        f"❗ К доплате: {format_currency(remaining_amount)}\n"
        f"🛡 Залог: {format_currency(rental.deposit)}\n"
        f"{status_text}"
        f"📝 Создан: {format_datetime(rental.created_at)}"
    )


def format_expense_info(expense) -> str:
    """Format expense information for display"""
    expense_types = {
        "maintenance": "🔧 Техобслуживание",
        "repair": "🛠 Ремонт",
        "insurance": "🛡 Страховка",
        "fuel": "⛽ Бензин",
        "other": "📦 Другое"
    }
    
    expense_type = expense_types.get(expense.expense_type.value, "❓ Неизвестно")
    
    return (
        f"💸 *Расход*\n\n"
        f"🚗 Машина: {expense.car.brand} {expense.car.model}\n"
        f"📋 Тип: {expense_type}\n"
        f"💰 Сумма: {format_currency(expense.amount)}\n"
        f"📝 Описание: {expense.description or 'Не указано'}\n"
        f"📅 Дата: {format_datetime(expense.expense_date)}"
  )
