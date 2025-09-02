#!/usr/bin/env python3
"""
Startup script for Rental CRM
Handles database migration and starts both web and bot services
"""

import os
import sys
import subprocess
import asyncio
import signal
from multiprocessing import Process
from pathlib import Path

import config


def run_migrations():
    """Run database migrations with improved error handling"""
    print("🔄 Running database migrations...")
    
    try:
        # Проверяем, существует ли папка alembic/versions
        versions_dir = Path("alembic/versions")
        if not versions_dir.exists():
            print("📁 Creating alembic versions directory...")
            versions_dir.mkdir(parents=True, exist_ok=True)
        
        # Попытка обновления до последней миграции
        result = subprocess.run(
            ["alembic", "upgrade", "head"], 
            capture_output=True, 
            text=True,
            cwd='.'
        )
        
        # Всегда выводим результаты для отладки
        if result.stdout:
            print(f"Alembic stdout: {result.stdout}")
        if result.stderr:
            print(f"Alembic stderr: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
            return True
        else:
            # Если миграция не удалась, пробуем создать первую миграцию
            print("⚠️ Migration failed, checking if initial migration is needed...")
            
            # Проверяем, содержится ли ошибка о том, что нет script_location
            if "No 'script_location'" in result.stderr:
                print("❌ Alembic configuration error. Please ensure alembic.ini exists.")
                return False
            
            # Пробуем создать первую миграцию
            print("🔄 Attempting to create initial migration...")
            init_result = subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", "Initial migration"],
                capture_output=True,
                text=True,
                cwd='.'
            )
            
            if init_result.returncode == 0:
                print("✅ Initial migration created")
                # Применяем созданную миграцию
                apply_result = subprocess.run(
                    ["alembic", "upgrade", "head"],
                    capture_output=True,
                    text=True,
                    cwd='.'
                )
                if apply_result.returncode == 0:
                    print("✅ Initial migration applied successfully")
                    return True
                else:
                    print(f"❌ Failed to apply initial migration: {apply_result.stderr}")
                    return False
            else:
                print(f"❌ Failed to create initial migration: {init_result.stderr}")
                return False
                
    except FileNotFoundError:
        print("❌ Alembic not found. Make sure it's installed in requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return False


def start_web_server():
    """Start the web server"""
    print("🌐 Starting web server...")
    try:
        import uvicorn
        from web.main import app
        
        # Получаем порт из переменной окружения (для Render)
        port = int(os.getenv("PORT", 8000))
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error starting web server: {e}")


def start_bot():
    """Start the Telegram bot"""
    print("🤖 Starting Telegram bot...")
    try:
        from bot.main import main
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error starting bot: {e}")


def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ['BOT_TOKEN', 'ADMIN_ID', 'DATABASE_URL', 'SECRET_KEY', 'ADMIN_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment")
        return False
    
    print("✅ All required environment variables are set")
    return True


def create_uploads_dir():
    """Create uploads directory if it doesn't exist"""
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    print(f"📁 Uploads directory: {uploads_dir.absolute()}")


def check_alembic_config():
    """Check if Alembic configuration files exist"""
    alembic_ini = Path("alembic.ini")
    alembic_dir = Path("alembic")
    
    missing_files = []
    
    if not alembic_ini.exists():
        missing_files.append("alembic.ini")
    
    if not alembic_dir.exists():
        missing_files.append("alembic/ directory")
    elif not (alembic_dir / "env.py").exists():
        missing_files.append("alembic/env.py")
    
    if missing_files:
        print("⚠️ Missing Alembic configuration files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nAlembic migrations may fail. Consider running 'alembic init alembic' first.")
        return False
    
    print("✅ Alembic configuration files found")
    return True


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main function"""
    print("🚗 Starting Rental CRM...")
    print("=" * 50)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Create necessary directories
    create_uploads_dir()
    
    # Check Alembic configuration
    alembic_ok = check_alembic_config()
    if not alembic_ok:
        print("⚠️ Proceeding anyway, but migrations may fail...")
    
    # Run migrations
    if not run_migrations():
        print("❌ Database migration failed:")
        print("This might be because:")
        print("1. alembic.ini is missing or misconfigured")
        print("2. Database connection failed")
        print("3. Migration files are corrupted")
        print("4. First-time setup needs manual migration creation")
        sys.exit(1)
    
    print("🎯 All checks passed, starting services...")
    print("=" * 50)
    
    # Start services
    try:
        if len(sys.argv) > 1:
            service = sys.argv[1].lower()
            
            if service == "web":
                start_web_server()
            elif service == "bot":
                start_bot()
            elif service == "migrate":
                print("✅ Migrations completed")
            else:
                print(f"❌ Unknown service: {service}")
                print("Available services: web, bot, migrate")
                sys.exit(1)
        else:
            # Start both services
            print("🚀 Starting both web server and bot...")
            
            # Start web server in a separate process
            web_process = Process(target=start_web_server)
            web_process.start()
            
            # Start bot in main process
            try:
                start_bot()
            except KeyboardInterrupt:
                print("\n🛑 Shutting down...")
            finally:
                web_process.terminate()
                web_process.join()
    
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    
    print("👋 Rental CRM stopped")


if __name__ == "__main__":
    main()
