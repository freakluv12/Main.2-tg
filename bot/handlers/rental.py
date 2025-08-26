from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session
from datetime import datetime, date

from database.database import SessionLocal
from database import crud
from database.models import RentalType, RentalStatus
from bot.states.states import CreateRentalStates, AddRenterStates, AddPaymentStates, AddFineStates
from bot.keyboards.inline import (
    rental_menu_keyboard, cars_keyboard, renters_keyboard, 
    rental_type_keyboard, rentals_keyboard, back_to_menu_keyboard
)
from bot.utils.helpers import (
    format_rental_info, parse_date, format_currency, 
    calculate_rental_days, validate_phone
)

router = Router()


@router.callback_query(F.data == "rental")
async def rental_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📋 *Управление арендой*\n\nВыберите действие:",
        reply_markup=rental_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "create_rental")
async def start_create_rental(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        available_cars = crud.get_available_cars(db)
        
        if not available_cars:
            await callback.message.edit_text(
                "❌ Нет доступных машин для аренды.\n"
                "Все машины сданы в аренду или на обслуживании.",
                reply_markup=rental_menu_keyboard()
            )
            return
        
        await callback.message.edit_text(
            "🚗 *Создание договора аренды*\n\n"
            "Выберите машину:",
            reply_markup=cars_keyboard(available_cars),
            parse_mode="Markdown"
        )
        await state.set_state(CreateRentalStates.waiting_for_car_selection)
        
    finally:
        db.close()


@router.callback_query(CreateRentalStates.waiting_for_car_selection, F.data.startswith("car_"))
async def select_car_for_rental(callback: CallbackQuery, state: FSMContext):
    car_id = int(callback.data.split("_")[1])
    await state.update_data(car_id=car_id)
    
    db = SessionLocal()
    try:
        renters = crud.get_renters(db)
        
        await callback.message.edit_text(
            "👤 *Выберите арендатора*\n\n"
            "Выберите из существующих или добавьте нового:",
            reply_markup=renters_keyboard(renters),
            parse_mode="Markdown"
        )
        await state.set_state(CreateRentalStates.waiting_for_renter_selection)
        
    finally:
        db.close()


@router.callback_query(F.data == "add_renter")
async def start_add_renter(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "👤 *Добавление нового арендатора*\n\n"
        "Введите ФИО:",
        parse_mode="Markdown"
    )
    await state.set_state(AddRenterStates.waiting_for_name)


@router.message(AddRenterStates.waiting_for_name)
async def process_renter_name(message: Message, state: FSMContext):
    await state.update_data(renter_name=message.text.strip())
    await message.answer(
        "Введите номер телефона:",
        parse_mode="Markdown"
    )
    await state.set_state(AddRenterStates.waiting_for_phone)


@router.message(AddRenterStates.waiting_for_phone)
async def process_renter_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    
    if not validate_phone(phone):
        await message.answer(
            "❌ Неверный формат телефона. Попробуйте ещё раз:"
        )
        return
    
    await state.update_data(renter_phone=phone)
    await message.answer(
        "Введите email (или нажмите /skip для пропуска):",
        parse_mode="Markdown"
    )
    await state.set_state(AddRenterStates.waiting_for_email)


@router.message(AddRenterStates.waiting_for_email, F.text == "/skip")
async def skip_renter_email(message: Message, state: FSMContext):
    await message.answer(
        "Введите данные паспорта (или нажмите /skip для пропуска):",
        parse_mode="Markdown"
    )
    await state.set_state(AddRenterStates.waiting_for_passport)


@router.message(AddRenterStates.waiting_for_email)
async def process_renter_email(message: Message, state: FSMContext):
    await state.update_data(renter_email=message.text.strip())
    await message.answer(
        "Введите данные паспорта (или нажмите /skip для пропуска):",
        parse_mode="Markdown"
    )
    await state.set_state(AddRenterStates.waiting_for_passport)


@router.message(AddRenterStates.waiting_for_passport, F.text == "/skip")
async def skip_renter_passport(message: Message, state: FSMContext):
    await message.answer(
        "Введите заметки (или нажмите /skip для пропуска):",
        parse_mode="Markdown"
    )
    await state.set_state(AddRenterStates.waiting_for_notes)


@router.message(AddRenterStates.waiting_for_passport)
async def process_renter_passport(message: Message, state: FSMContext):
    await state.update_data(renter_passport=message.text.strip())
    await message.answer(
        "Введите заметки (или нажмите /skip для пропуска):",
        parse_mode="Markdown"
    )
    await state.set_state(AddRenterStates.waiting_for_notes)


@router.message(AddRenterStates.waiting_for_notes, F.text == "/skip")
async def skip_renter_notes(message: Message, state: FSMContext):
    await save_renter_and_continue(message, state)


@router.message(AddRenterStates.waiting_for_notes)
async def process_renter_notes(message: Message, state: FSMContext):
    await state.update_data(renter_notes=message.text.strip())
    await save_renter_and_continue(message, state)


async def save_renter_and_continue(message: Message, state: FSMContext):
    data = await state.get_data()
    
    db = SessionLocal()
    try:
        renter = crud.create_renter(
            db=db,
            name=data['renter_name'],
            phone=data['renter_phone'],
            email=data.get('renter_email'),
            passport=data.get('renter_passport'),
            notes=data.get('renter_notes')
        )
        
        await state.update_data(renter_id=renter.id)
        await message.answer(
            f"✅ Арендатор добавлен: {renter.name}\n\n"
            "📅 Выберите тип аренды:",
            reply_markup=rental_type_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(CreateRentalStates.waiting_for_rental_type)
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при сохранении арендатора: {str(e)}",
            reply_markup=back_to_menu_keyboard()
        )
        await state.clear()
    finally:
        db.close()


@router.callback_query(CreateRentalStates.waiting_for_renter_selection, F.data.startswith("renter_"))
async def select_renter(callback: CallbackQuery, state: FSMContext):
    renter_id = int(callback.data.split("_")[1])
    await state.update_data(renter_id=renter_id)
    
    await callback.message.edit_text(
        "📅 Выберите тип аренды:",
        reply_markup=rental_type_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateRentalStates.waiting_for_rental_type)


@router.callback_query(CreateRentalStates.waiting_for_rental_type, F.data.startswith("rental_type_"))
async def select_rental_type(callback: CallbackQuery, state: FSMContext):
    rental_type_str = callback.data.split("_")[-1]
    rental_type = RentalType.SHORT_TERM if rental_type_str == "short_term" else RentalType.LONG_TERM
    await state.update_data(rental_type=rental_type)
    
    await callback.message.edit_text(
        "📅 Введите дату начала аренды в формате ДД.ММ.ГГГГ\n"
        "Например: 25.12.2024",
        parse_mode="Markdown"
    )
    await state.set_state(CreateRentalStates.waiting_for_start_date)


@router.message(CreateRentalStates.waiting_for_start_date)
async def process_start_date(message: Message, state: FSMContext):
    start_date = parse_date(message.text.strip())
    
    if not start_date:
        await message.answer(
            "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n"
            "Например: 25.12.2024"
        )
        return
    
    if start_date < date.today():
        await message.answer(
            "❌ Дата начала не может быть в прошлом. Введите корректную дату:"
        )
        return
    
    await state.update_data(start_date=start_date)
    await message.answer(
        "📅 Введите дату окончания аренды в формате ДД.ММ.ГГГГ\n"
        "Например: 30.12.2024"
    )
    await state.set_state(CreateRentalStates.waiting_for_end_date)


@router.message(CreateRentalStates.waiting_for_end_date)
async def process_end_date(message: Message, state: FSMContext):
    end_date = parse_date(message.text.strip())
    
    if not end_date:
        await message.answer(
            "❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ\n"
            "Например: 30.12.2024"
        )
        return
    
    data = await state.get_data()
    start_date = data['start_date']
    
    if end_date <= start_date:
        await message.answer(
            "❌ Дата окончания должна быть позже даты начала. Введите корректную дату:"
        )
        return
    
    await state.update_data(end_date=end_date)
    await message.answer(
        "💰 Введите сумму залога в лари (или 0 если залог не берётся):"
    )
    await state.set_state(CreateRentalStates.waiting_for_deposit)


@router.message(CreateRentalStates.waiting_for_deposit)
async def process_deposit(message: Message, state: FSMContext):
    try:
        deposit = float(message.text.strip())
        if deposit < 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Неверная сумма залога. Введите число (0 или больше):"
        )
        return
    
    await state.update_data(deposit=deposit)
    await message.answer(
        "📝 Введите заметки к договору (или нажмите /skip для пропуска):"
    )
    await state.set_state(CreateRentalStates.waiting_for_notes)


@router.message(CreateRentalStates.waiting_for_notes, F.text == "/skip")
async def skip_rental_notes(message: Message, state: FSMContext):
    await create_rental_contract(message, state)


@router.message(CreateRentalStates.waiting_for_notes)
async def process_rental_notes(message: Message, state: FSMContext):
    await state.update_data(contract_notes=message.text.strip())
    await create_rental_contract(message, state)


async def create_rental_contract(message: Message, state: FSMContext):
    data = await state.get_data()
    
    db = SessionLocal()
    try:
        # Get car info for daily rate
        car = crud.get_car_by_id(db, data['car_id'])
        
        rental = crud.create_rental(
            db=db,
            car_id=data['car_id'],
            renter_id=data['renter_id'],
            rental_type=data['rental_type'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            daily_rate=car.daily_rate,
            deposit=data['deposit'],
            contract_notes=data.get('contract_notes')
        )
        
        await message.answer(
            f"✅ *Договор аренды создан!*\n\n"
            f"{format_rental_info(rental)}",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при создании договора: {str(e)}",
            reply_markup=back_to_menu_keyboard()
        )
    finally:
        db.close()
        await state.clear()


@router.callback_query(F.data == "active_rentals")
async def show_active_rentals(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Check for overdue rentals first
        crud.check_overdue_rentals(db)
        
        active_rentals = crud.get_active_rentals(db)
        
        if not active_rentals:
            await callback.message.edit_text(
                "📋 Нет активных договоров аренды.",
                reply_markup=rental_menu_keyboard()
            )
            return
        
        await callback.message.edit_text(
            f"📋 *Активные аренды ({len(active_rentals)})*\n\n"
            "Выберите договор для подробной информации:",
            reply_markup=rentals_keyboard(active_rentals),
            parse_mode="Markdown"
        )
        
    finally:
        db.close()


@router.callback_query(F.data.startswith("rental_"))
async def show_rental_details(callback: CallbackQuery):
    rental_id = int(callback.data.split("_")[1])
    
    db = SessionLocal()
    try:
        rental = crud.get_rental_by_id(db, rental_id)
        if not rental:
            await callback.answer("❌ Договор не найден")
            return
        
        await callback.message.edit_text(
            format_rental_info(rental),
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    finally:
        db.close()


@router.callback_query(F.data == "overdue_rentals")
async def show_overdue_rentals(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Update overdue status
        overdue_rentals = crud.check_overdue_rentals(db)
        
        if not overdue_rentals:
            await callback.message.edit_text(
                "✅ Нет просроченных договоров.",
                reply_markup=rental_menu_keyboard()
            )
            return
        
        rentals_text = "⚠️ *Просроченные договоры:*\n\n"
        for rental in overdue_rentals:
            rentals_text += (
                f"🚗 {rental.car.brand} {rental.car.model}\n"
                f"👤 {rental.renter.name}\n"
                f"📞 {rental.renter.phone}\n"
                f"📅 Просрочка: {rental.overdue_days} дн.\n"
                f"💰 К доплате: {format_currency(rental.total_amount - rental.paid_amount)}\n\n"
            )
        
        await callback.message.edit_text(
            rentals_text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    finally:
        db.close()


@router.callback_query(F.data == "renters")
async def show_renters(callback: CallbackQuery):
    db = SessionLocal()
    try:
        renters = crud.get_renters(db)
        
        if not renters:
            await callback.message.edit_text(
                "👥 Список арендаторов пуст.",
                reply_markup=rental_menu_keyboard()
            )
            return
        
        renters_text = f"👥 *Арендаторы ({len(renters)})*\n\n"
        for renter in renters:
            active_rentals = [r for r in renter.rentals if r.is_active]
            status = f"({len(active_rentals)} активных)" if active_rentals else "(нет активных)"
            
            renters_text += (
                f"👤 {renter.name}\n"
                f"📞 {renter.phone}\n"
                f"📊 {status}\n\n"
            )
        
        await callback.message.edit_text(
            renters_text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    finally:
        db.close()
