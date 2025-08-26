from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from database.database import SessionLocal
from database import crud
from bot.states.states import AddCarStates
from bot.keyboards.inline import garage_menu_keyboard, cars_keyboard, back_to_menu_keyboard
from bot.utils.helpers import format_car_info, validate_vin, format_currency, save_photo

router = Router()


@router.callback_query(F.data == "garage")
async def garage_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🚗 *Управление гаражом*\n\nВыберите действие:",
        reply_markup=garage_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "add_car")
async def start_add_car(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "➕ *Добавление новой машины*\n\n"
        "Введите марку автомобиля:",
        parse_mode="Markdown"
    )
    await state.set_state(AddCarStates.waiting_for_brand)


@router.message(AddCarStates.waiting_for_brand)
async def process_brand(message: Message, state: FSMContext):
    await state.update_data(brand=message.text.strip())
    await message.answer(
        "Введите модель автомобиля:",
        parse_mode="Markdown"
    )
    await state.set_state(AddCarStates.waiting_for_model)


@router.message(AddCarStates.waiting_for_model)
async def process_model(message: Message, state: FSMContext):
    await state.update_data(model=message.text.strip())
    await message.answer(
        "Введите VIN номер (17 символов):",
        parse_mode="Markdown"
    )
    await state.set_state(AddCarStates.waiting_for_vin)


@router.message(AddCarStates.waiting_for_vin)
async def process_vin(message: Message, state: FSMContext):
    vin = message.text.strip().upper()
    
    if not validate_vin(vin):
        await message.answer(
            "❌ Неверный VIN номер. VIN должен содержать ровно 17 символов.\n"
            "Попробуйте ещё раз:"
        )
        return
    
    # Check if VIN already exists
    db = SessionLocal()
    try:
        existing_car = db.query(crud.Car).filter(crud.Car.vin == vin).first()
        if existing_car:
            await message.answer(
                "❌ Машина с таким VIN уже существует в системе.\n"
                "Введите другой VIN:"
            )
            return
    finally:
        db.close()
    
    await state.update_data(vin=vin)
    await message.answer(
        "Введите государственный номер:",
        parse_mode="Markdown"
    )
    await state.set_state(AddCarStates.waiting_for_license_plate)


@router.message(AddCarStates.waiting_for_license_plate)
async def process_license_plate(message: Message, state: FSMContext):
    license_plate = message.text.strip().upper()
    
    # Check if license plate already exists
    db = SessionLocal()
    try:
        existing_car = db.query(crud.Car).filter(crud.Car.license_plate == license_plate).first()
        if existing_car:
            await message.answer(
                "❌ Машина с таким номером уже существует в системе.\n"
                "Введите другой номер:"
            )
            return
    finally:
        db.close()
    
    await state.update_data(license_plate=license_plate)
    await message.answer(
        "Введите стоимость аренды в день (в лари):",
        parse_mode="Markdown"
    )
    await state.set_state(AddCarStates.waiting_for_daily_rate)


@router.message(AddCarStates.waiting_for_daily_rate)
async def process_daily_rate(message: Message, state: FSMContext):
    try:
        daily_rate = float(message.text.strip())
        if daily_rate <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Неверная стоимость. Введите положительное число:"
        )
        return
    
    await state.update_data(daily_rate=daily_rate)
    await message.answer(
        "Отправьте фотографию автомобиля или нажмите /skip чтобы пропустить:",
        parse_mode="Markdown"
    )
    await state.set_state(AddCarStates.waiting_for_photo)


@router.message(AddCarStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    # Get the largest photo
    photo = message.photo[-1]
    
    # Download photo
    bot = message.bot
    file = await bot.get_file(photo.file_id)
    photo_data = await bot.download_file(file.file_path)
    
    # Save photo
    filename = f"car_{photo.file_id}.jpg"
    photo_path = save_photo(photo_data.read(), filename)
    
    await state.update_data(photo_path=photo_path)
    await save_car(message, state)


@router.message(AddCarStates.waiting_for_photo, F.text == "/skip")
async def skip_photo(message: Message, state: FSMContext):
    await save_car(message, state)


@router.message(AddCarStates.waiting_for_photo)
async def invalid_photo(message: Message):
    await message.answer(
        "❌ Пожалуйста, отправьте фотографию или нажмите /skip для пропуска."
    )


async def save_car(message: Message, state: FSMContext):
    data = await state.get_data()
    
    db = SessionLocal()
    try:
        car = crud.create_car(
            db=db,
            brand=data['brand'],
            model=data['model'],
            vin=data['vin'],
            license_plate=data['license_plate'],
            daily_rate=data['daily_rate'],
            photo_path=data.get('photo_path')
        )
        
        await message.answer(
            f"✅ *Машина успешно добавлена!*\n\n"
            f"{format_car_info(car)}",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при сохранении машины: {str(e)}",
            reply_markup=back_to_menu_keyboard()
        )
    finally:
        db.close()
        await state.clear()


@router.callback_query(F.data == "list_cars")
async def list_cars(callback: CallbackQuery):
    db = SessionLocal()
    try:
        cars = crud.get_cars(db)
        
        if not cars:
            await callback.message.edit_text(
                "🚗 В гараже пока нет машин.\n"
                "Добавьте первую машину!",
                reply_markup=garage_menu_keyboard()
            )
            return
        
        await callback.message.edit_text(
            f"🚗 *В гараже {len(cars)} машин(ы)*\n\n"
            "Выберите машину для подробной информации:",
            reply_markup=cars_keyboard(cars),
            parse_mode="Markdown"
        )
    finally:
        db.close()


@router.callback_query(F.data.startswith("car_"))
async def show_car_details(callback: CallbackQuery):
    car_id = int(callback.data.split("_")[1])
    
    db = SessionLocal()
    try:
        car = crud.get_car_by_id(db, car_id)
        if not car:
            await callback.answer("❌ Машина не найдена")
            return
        
        # Get car statistics
        total_expenses = sum(expense.amount for expense in car.expenses)
        total_income = sum(
            payment.amount 
            for rental in car.rentals 
            for payment in rental.payments
        )
        net_profit = total_income - total_expenses
        
        details = (
            f"{format_car_info(car)}\n\n"
            f"📊 *Финансовая статистика:*\n"
            f"💰 Общий доход: {format_currency(total_income)}\n"
            f"💸 Общие расходы: {format_currency(total_expenses)}\n"
            f"📈 Чистая прибыль: {format_currency(net_profit)}\n"
            f"📋 Количество аренд: {len(car.rentals)}"
        )
        
        if car.photo_path and os.path.exists(car.photo_path):
            with open(car.photo_path, 'rb') as photo:
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=photo,
                    caption=details,
                    reply_markup=back_to_menu_keyboard(),
                    parse_mode="Markdown"
                )
        else:
            await callback.message.edit_text(
                details,
                reply_markup=back_to_menu_keyboard(),
                parse_mode="Markdown"
            )
            
    finally:
        db.close()
