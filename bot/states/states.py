from aiogram.fsm.state import State, StatesGroup


class AddCarStates(StatesGroup):
    waiting_for_brand = State()
    waiting_for_model = State()
    waiting_for_vin = State()
    waiting_for_license_plate = State()
    waiting_for_daily_rate = State()
    waiting_for_photo = State()


class AddExpenseStates(StatesGroup):
    waiting_for_car_selection = State()
    waiting_for_expense_type = State()
    waiting_for_amount = State()
    waiting_for_description = State()


class AddRenterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_email = State()
    waiting_for_passport = State()
    waiting_for_notes = State()


class CreateRentalStates(StatesGroup):
    waiting_for_car_selection = State()
    waiting_for_renter_selection = State()
    waiting_for_rental_type = State()
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    waiting_for_deposit = State()
    waiting_for_notes = State()


class AddPaymentStates(StatesGroup):
    waiting_for_rental_selection = State()
    waiting_for_amount = State()
    waiting_for_notes = State()


class AddFineStates(StatesGroup):
    waiting_for_rental_selection = State()
    waiting_for_amount = State()
    waiting_for_reason = State()
