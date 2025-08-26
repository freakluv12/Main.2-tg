from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import os

import config
from database.database import get_db, engine
from database.models import Base
from web.routers import auth, cars, rental, reports

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rental CRM", description="CRM система для автопроката")

# Mount static files
if not os.path.exists("web/static"):
    os.makedirs("web/static")
    os.makedirs("web/static/css")
    os.makedirs("web/static/js")

app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web/templates")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(cars.router, prefix="/api/cars", tags=["cars"])
app.include_router(rental.router, prefix="/api/rental", tags=["rental"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/cars", response_class=HTMLResponse)
async def cars_page(request: Request):
    """Cars management page"""
    return templates.TemplateResponse("cars.html", {"request": request})


@app.get("/rental", response_class=HTMLResponse)
async def rental_page(request: Request):
    """Rental management page"""
    return templates.TemplateResponse("rental.html", {"request": request})


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports page"""
    return templates.TemplateResponse("reports.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
