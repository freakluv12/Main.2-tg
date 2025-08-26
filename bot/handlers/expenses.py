from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.database import SessionLocal
from database import crud
from database.models import ExpenseType
from bot.states.states import AddExpenseStates
from bot.keyboards.inline import expenses_menu_keyboard, cars_keyboard, expense_type_keyboard, back_to_menu_keyboard
from bot.utils.helpers import format_expense_info, format_currency

router = Router()


@router.callback_query(F.data == "expenses")
async def expenses_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "💸 *Управление расходами*\n\nВыберите действие:",
        reply_markup=expenses_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "add_expense")
async def start_add_expense(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        cars = crud.get_cars(db)
        
        if not cars:
            await callback.message.edit_text(
                "❌ В гараже нет машин.\n"
                "Сначала добавьте машину в гараж.",
                reply_markup=expenses_menu_keyboard()
            )
            return
        
        await callback.message.edit_text(
            "💸 *Добавление расхода*\n\n"
            "Выберите машину:",
            reply_markup=cars_keyboard(cars),
            parse_mode="Markdown"
        )
        await state.set_state(AddExpenseStates.waiting_for_car_selection)
        
    finally:
        db.close()


@router.callback_query(AddExpenseStates.waiting_for_car_selection, F.data.startswith("car_"))
async def select_car_for_expense(callback: CallbackQuery, state: FSMContext):
    car_id = int(callback.data.split("_")[1])
    await state.update_data(car_id=car_id)
    
    await callback.message.edit_text(
        "💸 Выберите тип расхода:",
        reply_markup=expense_type_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddExpenseStates.waiting_for_expense_type)


@router.callback_query(AddExpenseStates.waiting_for_expense_type, F.data.startswith("expense_type_"))
async def select_expense_type(callback: CallbackQuery, state: FSMContext):
    expense_type_str = callback.data.split("_")[-1]
    expense_type = ExpenseType(expense_type_str)
    await state.update_data(expense_type=expense_type)
    
    type_names = {
        ExpenseType.MAINTENANCE: "техобслуживание",
        ExpenseType.REPAIR: "ремонт",
        ExpenseType.INSURANCE: "страховку",
        ExpenseType.FUEL: "бензин",
        ExpenseType.OTHER: "другие расходы"
    }
    
    type_name = type_names.get(expense_type, "расход")
    
    await callback.message.edit_text(
        f"💰 Введите сумму расхода на {type_name} (в лари):",
        parse_mode="Markdown"
    )
    await state.set_state(AddExpenseStates.waiting_for_amount)


@router.message(AddExpenseStates.waiting_for_amount)
async def process_expense_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Неверная сумма. Введите положительное число:"
        )
        return
    
    await state.update_data(amount=amount)
    await message.answer(
        "📝 Введите описание расхода (или нажмите /skip для пропуска):",
        parse_mode="Markdown"
    )
    await state.set_state(AddExpenseStates.waiting_for_description)


@router.message(AddExpenseStates.waiting_for_description, F.text == "/skip")
async def skip_expense_description(message: Message, state: FSMContext):
    await save_expense(message, state)


@router.message(AddExpenseStates.waiting_for_description)
async def process_expense_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await save_expense(message, state)


async def save_expense(message: Message, state: FSMContext):
    data = await state.get_data()
    
    db = SessionLocal()
    try:
        expense = crud.create_expense(
            db=db,
            car_id=data['car_id'],
            expense_type=data['expense_type'],
            amount=data['amount'],
            description=data.get('description')
        )
        
        await message.answer(
            f"✅ *Расход добавлен!*\n\n"
            f"{format_expense_info(expense)}",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при сохранении расхода: {str(e)}",
            reply_markup=back_to_menu_keyboard()
        )
    finally:
        db.close()
        await state.clear()


@router.callback_query(F.data == "expense_history")
async def show_expense_history(callback: CallbackQuery):
    db = SessionLocal()
    try:
        cars = crud.get_cars(db)
        
        if not cars:
            await callback.message.edit_text(
                "❌ В гараже нет машин.",
                reply_markup=expenses_menu_keyboard()
            )
            return
        
        # Calculate total expenses by car
        cars_with_expenses = []
        total_expenses = 0
        
        for car in cars:
            car_expenses = crud.get_car_expenses(db, car.id)
            car_total = sum(expense.amount for expense in car_expenses)
            total_expenses += car_total
            
            if car_expenses:  # Only include cars with expenses
                cars_with_expenses.append({
                    'car': car,
                    'total': car_total,
                    'count': len(car_expenses)
                })
        
        if not cars_with_expenses:
            await callback.message.edit_text(
                "📊 Расходов пока нет.",
                reply_markup=expenses_menu_keyboard()
            )
            return
        
        # Sort by total expenses descending
        cars_with_expenses.sort(key=lambda x: x['total'], reverse=True)
        
        history_text = f"💸 *История расходов*\n\n"
        history_text += f"📊 Общие расходы: {format_currency(total_expenses)}\n\n"
        
        for item in cars_with_expenses:
            car = item['car']
            history_text += (
                f"🚗 {car.brand} {car.model} ({car.license_plate})\n"
                f"💰 Расходы: {format_currency(item['total'])}\n"
                f"📋 Записей: {item['count']}\n\n"
            )
        
        await callback.message.edit_text(
            history_text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    finally:
        db.close()
