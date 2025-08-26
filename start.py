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
    """Run database migrations"""
    print("🔄 Running database migrations...")
    try:
        result = subprocess.run(["alembic", "upgrade", "head"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
        else:
            print("❌ Database migration failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False
    
    return True


def start_web_server():
    """Start the web server"""
    print("🌐 Starting web server...")
    try:
        import uvicorn
        from web.main import app
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
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
    
    return True


def create_uploads_dir():
    """Create uploads directory if it doesn't exist"""
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    print(f"📁 Uploads directory: {uploads_dir.absolute()}")


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
    
    # Run migrations
    if not run_migrations():
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
