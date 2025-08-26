from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta

from database.database import SessionLocal
from database import crud
from bot.keyboards.inline import reports_menu_keyboard, back_to_menu_keyboard
from bot.utils.helpers import format_currency

router = Router()


@router.callback_query(F.data == "reports")
async def reports_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 *Отчёты и аналитика*\n\nВыберите тип отчёта:",
        reply_markup=reports_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "car_profitability")
async def show_car_profitability(callback: CallbackQuery):
    db = SessionLocal()
    try:
        cars = crud.get_cars(db)
        
        if not cars:
            await callback.message.edit_text(
                "❌ В гараже нет машин.",
                reply_markup=reports_menu_keyboard()
            )
            return
        
        report_text = "📊 *Доходность машин*\n\n"
        
        car_profits = []
        total_income = 0
        total_expenses = 0
        
        for car in cars:
            profitability = crud.get_car_profitability(db, car.id)
            if profitability:
                car_profits.append(profitability)
                total_income += profitability['total_income']
                total_expenses += profitability['total_expenses']
        
        if not car_profits:
            await callback.message.edit_text(
                "📊 Нет данных для расчёта доходности.\n"
                "Добавьте доходы и расходы.",
                reply_markup=reports_menu_keyboard()
            )
            return
        
        # Sort by net profit descending
        car_profits.sort(key=lambda x: x['net_profit'], reverse=True)
        
        total_profit = total_income - total_expenses
        
        report_text += f"📈 *Общая статистика:*\n"
        report_text += f"💰 Общий доход: {format_currency(total_income)}\n"
        report_text += f"💸 Общие расходы: {format_currency(total_expenses)}\n"
        report_text += f"📊 Чистая прибыль: {format_currency(total_profit)}\n\n"
        
        report_text += f"*По машинам:*\n\n"
        
        for i, profit_data in enumerate(car_profits, 1):
            profit_emoji = "📈" if profit_data['net_profit'] > 0 else "📉"
            roi_text = f"ROI: {profit_data['roi']:.1f}%" if profit_data['roi'] != 0 else "ROI: н/д"
            
            report_text += (
                f"{profit_emoji} *{i}. {profit_data['car_info']}*\n"
                f"💰 Доход: {format_currency(profit_data['total_income'])}\n"
                f"💸 Расходы: {format_currency(profit_data['total_expenses'])}\n"
                f"📊 Прибыль: {format_currency(profit_data['net_profit'])}\n"
                f"📈 {roi_text}\n\n"
            )
        
        await callback.message.edit_text(
            report_text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    finally:
        db.close()


@router.callback_query(F.data == "financial_report")
async def show_financial_report(callback: CallbackQuery):
    db = SessionLocal()
    try:
        current_date = datetime.now()
        
        # Current month
        current_month_income = crud.get_monthly_income(db, current_date.year, current_date.month)
        current_month_expenses = crud.get_monthly_expenses(db, current_date.year, current_date.month)
        
        # Previous month
        prev_month_date = current_date.replace(day=1) - timedelta(days=1)
        prev_month_income = crud.get_monthly_income(db, prev_month_date.year, prev_month_date.month)
        prev_month_expenses = crud.get_monthly_expenses(db, prev_month_date.year, prev_month_date.month)
        
        # Current year totals
        year_income = 0
        year_expenses = 0
        for month in range(1, current_date.month + 1):
            year_income += crud.get_monthly_income(db, current_date.year, month)
            year_expenses += crud.get_monthly_expenses(db, current_date.year, month)
        
        # Active rentals statistics
        active_rentals = crud.get_active_rentals(db)
        overdue_rentals = [r for r in active_rentals if r.is_overdue]
        
        # Cars statistics
        cars = crud.get_cars(db)
        available_cars = crud.get_available_cars(db)
        rented_cars = len(cars) - len(available_cars)
        
        current_month_profit = current_month_income - current_month_expenses
        prev_month_profit = prev_month_income - prev_month_expenses
        year_profit = year_income - year_expenses
        
        months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        
        current_month_name = months[current_date.month - 1]
        prev_month_name = months[prev_month_date.month - 1]
        
        report_text = f"📈 *Финансовый отчёт*\n\n"
        
        # Current month
        profit_emoji = "📈" if current_month_profit > 0 else "📉"
        report_text += f"📅 *{current_month_name} {current_date.year}:*\n"
        report_text += f"💰 Доходы: {format_currency(current_month_income)}\n"
        report_text += f"💸 Расходы: {format_currency(current_month_expenses)}\n"
        report_text += f"{profit_emoji} Прибыль: {format_currency(current_month_profit)}\n\n"
        
        # Previous month comparison
        if prev_month_income > 0 or prev_month_expenses > 0:
            prev_profit_emoji = "📈" if prev_month_profit > 0 else "📉"
            
            income_change = current_month_income - prev_month_income
            expense_change = current_month_expenses - prev_month_expenses
            profit_change = current_month_profit - prev_month_profit
            
            income_trend = "📈" if income_change > 0 else "📉" if income_change < 0 else "➡️"
            expense_trend = "📈" if expense_change > 0 else "📉" if expense_change < 0 else "➡️"
            profit_trend = "📈" if profit_change > 0 else "📉" if profit_change < 0 else "➡️"
            
            report_text += f"📅 *{prev_month_name} (сравнение):*\n"
            report_text += f"💰 Доходы: {format_currency(prev_month_income)} {income_trend}\n"
            report_text += f"💸 Расходы: {format_currency(prev_month_expenses)} {expense_trend}\n"
            report_text += f"{prev_profit_emoji} Прибыль: {format_currency(prev_month_profit)} {profit_trend}\n\n"
        
        # Year totals
        year_profit_emoji = "📈" if year_profit > 0 else "📉"
        report_text += f"📅 *Год {current_date.year} (всего):*\n"
        report_text += f"💰 Доходы: {format_currency(year_income)}\n"
        report_text += f"💸 Расходы: {format_currency(year_expenses)}\n"
        report_text += f"{year_profit_emoji} Прибыль: {format_currency(year_profit)}\n\n"
        
        # Fleet statistics
        report_text += f"🚗 *Статистика автопарка:*\n"
        report_text += f"📋 Всего машин: {len(cars)}\n"
        report_text += f"✅ Доступно: {len(available_cars)}\n"
        report_text += f"🔴 Сдано в аренду: {rented_cars}\n"
        report_text += f"📝 Активных договоров: {len(active_rentals)}\n"
        
        if overdue_rentals:
            report_text += f"⚠️ Просрочек: {len(overdue_rentals)}\n"
        
        # Average daily income
        days_in_month = current_date.day
        if days_in_month > 0 and current_month_income > 0:
            avg_daily_income = current_month_income / days_in_month
            report_text += f"\n📊 Средний дневной доход: {format_currency(avg_daily_income)}"
        
        await callback.message.edit_text(
            report_text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    finally:
        db.close()
