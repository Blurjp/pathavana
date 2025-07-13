#!/usr/bin/env python3
"""
Test script to verify Pathavana backend is production ready.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testing Pathavana Production Readiness")
print("=" * 50)

# Test 1: Configuration loading
try:
    from app.core.config import settings
    print("✅ Configuration: PASSED")
    print(f"   📋 App: {settings.APP_NAME}")
    print(f"   🌐 API: {settings.API_V1_STR}")
    print(f"   🔗 CORS: {len(settings.get_cors_origins())} origins")
    print(f"   🗄️ Database: {settings.DATABASE_URL}")
    config_ok = True
except Exception as e:
    print(f"❌ Configuration: FAILED - {e}")
    config_ok = False

# Test 2: Models loading
try:
    from app.models import UnifiedTravelSession, User, UnifiedBooking
    print("✅ Models: PASSED")
    print("   📊 Available: UnifiedTravelSession, User, UnifiedBooking, etc.")
    models_ok = True
except Exception as e:
    print(f"❌ Models: FAILED - {e}")
    models_ok = False

# Test 3: FastAPI availability
try:
    import fastapi
    import uvicorn
    print("✅ FastAPI: AVAILABLE")
    print(f"   📦 FastAPI version: {fastapi.__version__}")
    fastapi_ok = True
except ImportError:
    print("⚠️  FastAPI: NOT AVAILABLE (will use fallback mode)")
    fastapi_ok = False

# Test 4: Main application loading
try:
    from app.main_production import FASTAPI_AVAILABLE
    if FASTAPI_AVAILABLE:
        from app.main_production import app
        print("✅ Main App: PRODUCTION MODE")
        print("   🚀 FastAPI application ready")
    else:
        print("✅ Main App: FALLBACK MODE")
        print("   🔧 HTTP server fallback ready")
    app_ok = True
except Exception as e:
    print(f"❌ Main App: FAILED - {e}")
    app_ok = False

# Test 5: Environment file
env_file = ".env"
if os.path.exists(env_file):
    print("✅ Environment: CONFIGURED")
    print(f"   📁 File: {env_file}")
    env_ok = True
else:
    print("⚠️  Environment: .env file missing")
    env_ok = False

# Test 6: Directory structure
required_dirs = ['app', 'app/api', 'app/models', 'app/services', 'app/core']
missing_dirs = [d for d in required_dirs if not os.path.exists(d)]

if not missing_dirs:
    print("✅ Structure: COMPLETE")
    print("   📁 All required directories present")
    structure_ok = True
else:
    print(f"❌ Structure: MISSING - {missing_dirs}")
    structure_ok = False

# Summary
print("\n📋 Production Readiness Summary")
print("=" * 35)

tests = [
    ("Configuration", config_ok),
    ("Database Models", models_ok),
    ("FastAPI Framework", fastapi_ok),
    ("Main Application", app_ok),
    ("Environment Setup", env_ok),
    ("Directory Structure", structure_ok)
]

passed = sum(1 for _, ok in tests if ok)
total = len(tests)

for name, ok in tests:
    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"  {name:<20} {status}")

print(f"\n🎯 Score: {passed}/{total} tests passed")

if passed == total:
    print("\n🎉 PRODUCTION READY!")
    print("   Ready to start with: ./start_production.sh")
elif passed >= 4:
    print("\n⚠️  MOSTLY READY")
    print("   Can run in development mode")
else:
    print("\n❌ NEEDS ATTENTION")
    print("   Please fix failed tests")

print(f"\n🚀 Next Steps:")
print(f"   1. cd /Users/jianphua/projects/pathavana/backend")
print(f"   2. source venv/bin/activate")
print(f"   3. ./start_production.sh")
print(f"   4. Open frontend: cd ../frontend && ./start_frontend.sh")