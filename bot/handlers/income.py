from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.database import SessionLocal
from database import crud
from bot.states.states import AddPaymentStates, AddFineStates
from bot.keyboards.inline import income_menu_keyboard, rentals_keyboard, back_to_menu_keyboard
from bot.utils.helpers import format_currency, format_datetime

router = Router()


@router.callback_query(F.data == "income")
async def income_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 *Управление доходами*\n\nВыберите действие:",
        reply_markup=income_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "add_payment")
async def start_add_payment(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        active_rentals = crud.get_active_rentals(db)
        
        if not active_rentals:
            await callback.message.edit_text(
                "❌ Нет активных договоров аренды.\n"
                "Сначала создайте договор аренды.",
                reply_markup=income_menu_keyboard()
            )
            return
        
        await callback.message.edit_text(
            "💰 *Добавление платежа*\n\n"
            "Выберите договор аренды:",
            reply_markup=rentals_keyboard(active_rentals),
            parse_mode="Markdown"
        )
        await state.set_state(AddPaymentStates.waiting_for_rental_selection)
        
    finally:
        db.close()


@router.callback_query(AddPaymentStates.waiting_for_rental_selection, F.data.startswith("rental_"))
async def select_rental_for_payment(callback: CallbackQuery, state: FSMContext):
    rental_id = int(callback.data.split("_")[1])
    
    db = SessionLocal()
    try:
        rental = crud.get_rental_by_id(db, rental_id)
        if not rental:
            await callback.answer("❌ Договор не найден")
            return
        
        remaining_amount = rental.total_amount - rental.paid_amount
        
        await state.update_data(rental_id=rental_id)
        await callback.message.edit_text(
            f"💰 *Платёж по договору №{rental_id}*\n\n"
            f"🚗 {rental.car.brand} {rental.car.model}\n"
            f"👤 {rental.renter.name}\n\n"
            f"💵 Общая сумма: {format_currency(rental.total_amount)}\n"
            f"✅ Оплачено: {format_currency(rental.paid_amount)}\n"
            f"❗ К доплате: {format_currency(remaining_amount)}\n\n"
            f"Введите сумму платежа:",
            parse_mode="Markdown"
        )
        await state.set_state(AddPaymentStates.waiting_for_amount)
        
    finally:
        db.close()


@router.message(AddPaymentStates.waiting_for_amount)
async def process_payment_amount(message: Message, state: FSMContext):
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
        "📝 Введите заметки к платежу (или нажмите /skip для пропуска):",
        parse_mode="Markdown"
    )
    await state.set_state(AddPaymentStates.waiting_for_notes)


@router.message(AddPaymentStates.waiting_for_notes, F.text == "/skip")
async def skip_payment_notes(message: Message, state: FSMContext):
    await save_payment(message, state)


@router.message(AddPaymentStates.waiting_for_notes)
async def process_payment_notes(message: Message, state: FSMContext):
    await state.update_data(notes=message.text.strip())
    await save_payment(message, state)


async def save_payment(message: Message, state: FSMContext):
    data = await state.get_data()
    
    db = SessionLocal()
    try:
        payment = crud.create_payment(
            db=db,
            rental_id=data['rental_id'],
            amount=data['amount'],
            notes=data.get('notes')
        )
        
        # Get updated rental info
        rental = crud.get_rental_by_id(db, data['rental_id'])
        remaining_amount = rental.total_amount - rental.paid_amount
        
        await message.answer(
            f"✅ *Платёж добавлен!*\n\n"
            f"💰 Сумма: {format_currency(payment.amount)}\n"
            f"📅 Дата: {format_datetime(payment.payment_date)}\n"
            f"📝 Заметки: {payment.notes or 'Нет'}\n\n"
            f"📊 *Статус оплаты:*\n"
            f"✅ Оплачено: {format_currency(rental.paid_amount)}\n"
            f"❗ Остаток: {format_currency(remaining_amount)}",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при сохранении платежа: {str(e)}",
            reply_markup=back_to_menu_keyboard()
        )
    finally:
        db.close()
        await state.clear()


@router.callback_query(F.data == "payment_history")
async def show_payment_history(callback: CallbackQuery):
    db = SessionLocal()
    try:
        # Get all payments from all rentals
        all_payments = []
        total_income = 0
        
        active_rentals = crud.get_active_rentals(db)
        for rental in active_rentals:
            payments = crud.get_rental_payments(db, rental.id)
            for payment in payments:
                all_payments.append({
                    'payment': payment,
                    'rental': rental
                })
                total_income += payment.amount
        
        # Also get payments from completed rentals
        db_session = db
        completed_rentals = db_session.query(crud.Rental).filter(crud.Rental.is_active == False).all()
        for rental in completed_rentals:
            payments = crud.get_rental_payments(db, rental.id)
            for payment in payments:
                all_payments.append({
                    'payment': payment,
                    'rental': rental
                })
                total_income += payment.amount
        
        if not all_payments:
            await callback.message.edit_text(
                "💰 История платежей пуста.",
                reply_markup=income_menu_keyboard()
            )
            return
        
        # Sort by payment date descending
        all_payments.sort(key=lambda x: x['payment'].payment_date, reverse=True)
        
        # Show last 10 payments
        recent_payments = all_payments[:10]
        
        history_text = f"💰 *История платежей*\n\n"
        history_text += f"📊 Общий доход: {format_currency(total_income)}\n"
        history_text += f"📋 Всего платежей: {len(all_payments)}\n\n"
        history_text += f"*Последние платежи:*\n\n"
        
        for item in recent_payments:
            payment = item['payment']
            rental = item['rental']
            
            history_text += (
                f"💰 {format_currency(payment.amount)}\n"
                f"🚗 {rental.car.brand} {rental.car.model}\n"
                f"👤 {rental.renter.name}\n"
                f"📅 {format_datetime(payment.payment_date)}\n"
            )
            
            if payment.notes:
                history_text += f"📝 {payment.notes}\n"
            
            history_text += "\n"
        
        if len(all_payments) > 10:
            history_text += f"... и ещё {len(all_payments) - 10} платежей"
        
        await callback.message.edit_text(
            history_text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    finally:
        db.close()


@router.callback_query(F.data == "fines")
async def fines_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🚫 *Управление штрафами*\n\n"
        "Выберите действие:",
        reply_markup=income_menu_keyboard(),  # We'll add fine management later
        parse_mode="Markdown"
    )
