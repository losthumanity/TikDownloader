#!/usr/bin/env python3
"""
Test script to validate deployment readiness
Run this before deploying to Render
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

def test_environment():
    """Test environment variables and configuration"""
    print("🔍 Testing Environment Configuration...")
    
    load_dotenv()
    
    # Check required environment variables
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN is missing!")
        return False
    print("✅ TELEGRAM_BOT_TOKEN is configured")
    
    return True

def test_imports():
    """Test all critical imports"""
    print("\n📦 Testing Module Imports...")
    
    try:
        from bot import TikTokBot
        print("✅ Bot module imports successfully")
        
        from health_server import app
        print("✅ Health server imports successfully")
        
        from tiktok_downloader import TikTokDownloader
        print("✅ TikTok downloader imports successfully")
        
        import telegram
        print(f"✅ python-telegram-bot v{telegram.__version__}")
        
        import aiohttp
        print(f"✅ aiohttp v{aiohttp.__version__}")
        
        import flask
        print(f"✅ Flask v{flask.__version__}")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_bot_initialization():
    """Test bot initialization"""
    print("\n🤖 Testing Bot Initialization...")
    
    try:
        from bot import TikTokBot
        bot = TikTokBot()
        print("✅ Bot initializes successfully")
        print(f"✅ Max file size: {bot.max_file_size / (1024*1024):.0f}MB")
        return True
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return False

def test_flask_endpoints():
    """Test Flask endpoints"""
    print("\n🌐 Testing Flask Endpoints...")
    
    try:
        from health_server import app
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ /health endpoint working")
            else:
                print(f"❌ /health endpoint failed: {response.status_code}")
                return False
            
            # Test root endpoint
            response = client.get('/')
            if response.status_code == 200:
                print("✅ / root endpoint working")
            else:
                print(f"❌ / root endpoint failed: {response.status_code}")
                return False
                
            # Test ping endpoint
            response = client.get('/ping')
            if response.status_code == 200:
                print("✅ /ping endpoint working")
            else:
                print(f"❌ /ping endpoint failed: {response.status_code}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Flask test failed: {e}")
        return False

def test_production_mode():
    """Test production mode configuration"""
    print("\n🏭 Testing Production Mode...")
    
    # Temporarily set production environment
    original_render = os.getenv('RENDER')
    os.environ['RENDER'] = 'true'
    os.environ['WEBHOOK_URL'] = 'https://tikdownloader.onrender.com'
    
    try:
        from main import main
        print("✅ Production mode configuration loads successfully")
        
        # Test webhook URL construction
        from bot import TikTokBot
        bot = TikTokBot()
        webhook_url = os.getenv('WEBHOOK_URL')
        print(f"✅ Webhook URL: {webhook_url}")
        
        return True
    except Exception as e:
        print(f"❌ Production mode test failed: {e}")
        return False
    finally:
        # Restore original environment
        if original_render:
            os.environ['RENDER'] = original_render
        else:
            os.environ.pop('RENDER', None)

def main():
    """Run all tests"""
    print("🚀 TikTok Bot Deployment Readiness Test")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_imports,
        test_bot_initialization,
        test_flask_endpoints,
        test_production_mode
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT! 🚀")
        print("\nNext steps:")
        print("1. Push changes to GitHub")
        print("2. Connect repository to Render")
        print("3. Set TELEGRAM_BOT_TOKEN environment variable in Render")
        print("4. Deploy!")
        return True
    else:
        print("❌ SOME TESTS FAILED - FIX ISSUES BEFORE DEPLOYMENT")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)