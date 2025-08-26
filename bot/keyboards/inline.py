from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Car, Rental, ExpenseType, RentalType
from typing import List


def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Гараж", callback_data="garage")],
        [InlineKeyboardButton(text="💰 Доходы", callback_data="income"),
         InlineKeyboardButton(text="💸 Расходы", callback_data="expenses")],
        [InlineKeyboardButton(text="📋 Аренда", callback_data="rental")],
        [InlineKeyboardButton(text="📊 Отчёты", callback_data="reports")],
    ])
    return keyboard


def garage_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить машину", callback_data="add_car")],
        [InlineKeyboardButton(text="📋 Список машин", callback_data="list_cars")],
        [InlineKeyboardButton(text="🔧 Обслуживание", callback_data="maintenance")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])
    return keyboard


def expenses_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить расход", callback_data="add_expense")],
        [InlineKeyboardButton(text="📋 История расходов", callback_data="expense_history")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])
    return keyboard


def income_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Добавить платёж", callback_data="add_payment")],
        [InlineKeyboardButton(text="📋 История платежей", callback_data="payment_history")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])
    return keyboard


def rental_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать договор", callback_data="create_rental")],
        [InlineKeyboardButton(text="📋 Активные аренды", callback_data="active_rentals")],
        [InlineKeyboardButton(text="👥 Арендаторы", callback_data="renters")],
        [InlineKeyboardButton(text="⚠️ Просрочки", callback_data="overdue_rentals")],
        [InlineKeyboardButton(text="🚫 Штрафы", callback_data="fines")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])
    return keyboard


def reports_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Доходность машин", callback_data="car_profitability")],
        [InlineKeyboardButton(text="📈 Финансовый отчёт", callback_data="financial_report")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
    ])
    return keyboard


def cars_keyboard(cars: List[Car]):
    keyboard = []
    for car in cars:
        text = f"{car.brand} {car.model} ({car.license_plate})"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"car_{car.id}")])
    
    keyboard.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def expense_type_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🔧 Техобслуживание", callback_data=f"expense_type_{ExpenseType.MAINTENANCE.value}")],
        [InlineKeyboardButton(text="🛠 Ремонт", callback_data=f"expense_type_{ExpenseType.REPAIR.value}")],
        [InlineKeyboardButton(text="🛡 Страховка", callback_data=f"expense_type_{ExpenseType.INSURANCE.value}")],
        [InlineKeyboardButton(text="⛽ Бензин", callback_data=f"expense_type_{ExpenseType.FUEL.value}")],
        [InlineKeyboardButton(text="📦 Другое", callback_data=f"expense_type_{ExpenseType.OTHER.value}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def rental_type_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="📅 Краткосрочная", callback_data=f"rental_type_{RentalType.SHORT_TERM.value}")],
        [InlineKeyboardButton(text="📆 Долгосрочная", callback_data=f"rental_type_{RentalType.LONG_TERM.value}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def rentals_keyboard(rentals: List[Rental]):
    keyboard = []
    for rental in rentals:
        text = f"{rental.car.brand} {rental.car.model} - {rental.renter.name}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"rental_{rental.id}")])
    
    keyboard.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def renters_keyboard(renters):
    keyboard = []
    for renter in renters:
        text = f"{renter.name} ({renter.phone})"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"renter_{renter.id}")])
    
    keyboard.append([InlineKeyboardButton(text="➕ Добавить нового", callback_data="add_renter")])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def confirm_keyboard(confirm_data: str):
    keyboard = [
        [InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{confirm_data}"),
         InlineKeyboardButton(text="❌ Нет", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_to_menu_keyboard():
    keyboard = [[InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
