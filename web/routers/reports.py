from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from database.database import get_db
from database import crud
from web.routers.auth import get_current_user

router = APIRouter()


@router.get("/profitability")
async def get_cars_profitability(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profitability report for all cars"""
    cars = crud.get_cars(db)
    
    if not cars:
        return {"cars": [], "totals": {"total_income": 0, "total_expenses": 0, "net_profit": 0}}
    
    cars_profitability = []
    total_income = 0
    total_expenses = 0
    
    for car in cars:
        profitability = crud.get_car_profitability(db, car.id)
        if profitability:
            cars_profitability.append(profitability)
            total_income += profitability['total_income']
            total_expenses += profitability['total_expenses']
    
    net_profit = total_income - total_expenses
    
    # Sort by net profit descending
    cars_profitability.sort(key=lambda x: x['net_profit'], reverse=True)
    
    return {
        "cars": cars_profitability,
        "totals": {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_profit": net_profit
        }
    }


@router.get("/financial")
async def get_financial_report(
    months: int = Query(12, ge=1, le=24),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get financial report for the last N months"""
    current_date = datetime.now()
    
    monthly_data = []
    total_income = 0
    total_expenses = 0
    
    for i in range(months):
        # Calculate date for i months ago
        if current_date.month - i <= 0:
            month = current_date.month - i + 12
            year = current_date.year - 1
        else:
            month = current_date.month - i
            year = current_date.year
        
        month_income = crud.get_monthly_income(db, year, month)
        month_expenses = crud.get_monthly_expenses(db, year, month)
        month_profit = month_income - month_expenses
        
        total_income += month_income
        total_expenses += month_expenses
        
        month_names = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        
        monthly_data.append({
            "year": year,
            "month": month,
            "month_name": month_names[month - 1],
            "income": month_income,
            "expenses": month_expenses,
            "profit": month_profit
        })
    
    # Reverse to show oldest first
    monthly_data.reverse()
    
    return {
        "monthly_data": monthly_data,
        "totals": {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_profit": total_income - total_expenses
        },
        "period": f"За последние {months} месяцев"
    }


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary data"""
    # Cars statistics
    cars = crud.get_cars(db)
    available_cars = crud.get_available_cars(db)
    
    # Rentals statistics
    active_rentals = crud.get_active_rentals(db)
    crud.check_overdue_rentals(db)  # Update overdue status
    overdue_rentals = [r for r in active_rentals if r.is_overdue]
    
    # Financial data for current month
    current_date = datetime.now()
    current_month_income = crud.get_monthly_income(db, current_date.year, current_date.month)
    current_month_expenses = crud.get_monthly_expenses(db, current_date.year, current_date.month)
    current_month_profit = current_month_income - current_month_expenses
    
    # Previous month for comparison
    prev_month_date = current_date.replace(day=1) - timedelta(days=1)
    prev_month_income = crud.get_monthly_income(db, prev_month_date.year, prev_month_date.month)
    prev_month_expenses = crud.get_monthly_expenses(db, prev_month_date.year, prev_month_date.month)
    prev_month_profit = prev_month_income - prev_month_expenses
    
    # Calculate changes
    income_change = ((current_month_income - prev_month_income) / prev_month_income * 100) if prev_month_income > 0 else 0
    expense_change = ((current_month_expenses - prev_month_expenses) / prev_month_expenses * 100) if prev_month_expenses > 0 else 0
    profit_change = ((current_month_profit - prev_month_profit) / prev_month_profit * 100) if prev_month_profit != 0 else 0
    
    # Top performing cars
    cars_profitability = []
    for car in cars:
        profitability = crud.get_car_profitability(db, car.id)
        if profitability and profitability['net_profit'] > 0:
            cars_profitability.append(profitability)
    
    cars_profitability.sort(key=lambda x: x['net_profit'], reverse=True)
    top_cars = cars_profitability[:5]  # Top 5 cars
    
    return {
        "fleet_stats": {
            "total_cars": len(cars),
            "available_cars": len(available_cars),
            "rented_cars": len(cars) - len(available_cars)
        },
        "rental_stats": {
            "active_rentals": len(active_rentals),
            "overdue_rentals": len(overdue_rentals)
        },
        "financial_current": {
            "income": current_month_income,
            "expenses": current_month_expenses,
            "profit": current_month_profit,
            "income_change": round(income_change, 1),
            "expense_change": round(expense_change, 1),
            "profit_change": round(profit_change, 1)
        },
        "top_cars": top_cars
    }


@router.get("/chart-data")
async def get_chart_data(
    months: int = Query(6, ge=3, le=12),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get data for charts"""
    current_date = datetime.now()
    
    # Monthly income/expense chart data
    chart_data = []
    
    for i in range(months):
        # Calculate date for i months ago
        if current_date.month - i <= 0:
            month = current_date.month - i + 12
            year = current_date.year - 1
        else:
            month = current_date.month - i
            year = current_date.year
        
        month_income = crud.get_monthly_income(db, year, month)
        month_expenses = crud.get_monthly_expenses(db, year, month)
        
        month_names = [
            "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
            "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"
        ]
        
        chart_data.append({
            "month": f"{month_names[month - 1]} {year}",
            "income": month_income,
            "expenses": month_expenses,
            "profit": month_income - month_expenses
        })
    
    # Reverse to show chronological order
    chart_data.reverse()
    
    # Car profitability pie chart data
    cars_data = []
    for car in crud.get_cars(db):
        profitability = crud.get_car_profitability(db, car.id)
        if profitability and profitability['total_income'] > 0:
            cars_data.append({
                "name": f"{car.brand} {car.model}",
                "value": profitability['total_income']
            })
    
    cars_data.sort(key=lambda x: x['value'], reverse=True)
    
    return {
        "monthly_chart": chart_data,
        "cars_income_chart": cars_data[:10]  # Top 10 cars by income
    }
