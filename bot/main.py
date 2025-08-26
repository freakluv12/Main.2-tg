import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database.database import engine
from database.models import Base
from bot.keyboards.inline import main_menu_keyboard, back_to_menu_keyboard
from bot.handlers import garage, rental, expenses, income, reports

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def start_command(message: Message):
    """Handle /start command"""
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этому боту.")
        return
    
    welcome_text = (
        f"🚗 *Добро пожаловать в CRM для автопроката!*\n\n"
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Этот бот поможет вам управлять:\n"
        f"• 🚗 Автопарком\n"
        f"• 💰 Доходами и расходами\n"
        f"• 📋 Договорами аренды\n"
        f"• 📊 Отчётностью\n\n"
        f"Выберите действие:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def main_menu_callback(callback):
    """Handle main menu callback"""
    await callback.message.edit_text(
        "🏠 *Главное меню*\n\nВыберите действие:",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


async def setup_database():
    """Create database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def main():
    """Main function to run the bot"""
    # Check if bot token is provided
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not provided in environment variables")
        return
    
    if not config.ADMIN_ID:
        logger.error("ADMIN_ID not provided in environment variables")
        return
    
    # Setup database
    await setup_database()
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    dp.message.register(start_command, CommandStart())
    
    # Register callback handlers
    dp.callback_query.register(main_menu_callback, lambda c: c.data == "main_menu")
    
    # Include routers from different modules
    dp.include_router(garage.router)
    dp.include_router(rental.router)
    dp.include_router(expenses.router)
    dp.include_router(income.router)
    dp.include_router(reports.router)
    
    # Add middleware to check admin access
    @dp.message.middleware()
    async def check_admin_middleware(handler, event, data):
        if event.from_user.id != config.ADMIN_ID:
            await event.answer("❌ У вас нет доступа к этому боту.")
            return
        return await handler(event, data)
    
    @dp.callback_query.middleware()
    async def check_admin_callback_middleware(handler, event, data):
        if event.from_user.id != config.ADMIN_ID:
            await event.answer("❌ У вас нет доступа к этому боту.", show_alert=True)
            return
        return await handler(event, data)
    
    # Start polling
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Program error: {e}")
