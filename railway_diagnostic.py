#!/usr/bin/env python3
"""
Railway Deployment Diagnostic Script
"""

def check_railway_config():
    """Check Railway configuration files"""
    import os
    from pathlib import Path
    
    base_dir = Path(__file__).parent
    
    print("🔍 RAILWAY CONFIGURATION DIAGNOSTIC")
    print("=" * 50)
    
    # Check Procfile
    procfile = base_dir / 'Procfile'
    if procfile.exists():
        with open(procfile, 'r') as f:
            content = f.read().strip()
            print(f"✅ Procfile exists: {content}")
    else:
        print("❌ Procfile missing!")
    
    # Check railway.json
    railway_json = base_dir / 'railway.json'
    if railway_json.exists():
        print("✅ railway.json exists")
    else:
        print("ℹ️  railway.json not found (optional)")
    
    # Check requirements.txt
    req_file = base_dir / 'requirements.txt'
    if req_file.exists():
        with open(req_file, 'r') as f:
            reqs = f.read()
            essential_deps = ['Django', 'gunicorn', 'psycopg2']
            for dep in essential_deps:
                if dep.lower() in reqs.lower():
                    print(f"✅ {dep} found in requirements.txt")
                else:
                    print(f"❌ {dep} missing from requirements.txt")
    else:
        print("❌ requirements.txt missing!")
    
    # Check settings.py
    settings_file = base_dir / 'accounts_easy_project' / 'settings.py'
    if settings_file.exists():
        print("✅ Django settings.py exists")
        
        # Check for potential issues
        with open(settings_file, 'r') as f:
            settings_content = f.read()
            
            checks = {
                'ALLOWED_HOSTS': 'ALLOWED_HOSTS' in settings_content and 'railway.app' in settings_content,
                'DATABASE': 'postgresql' in settings_content,
                'STATIC_ROOT': 'STATIC_ROOT' in settings_content,
                'WHITENOISE': 'whitenoise' in settings_content.lower(),
            }
            
            for check, status in checks.items():
                if status:
                    print(f"✅ {check} configured")
                else:
                    print(f"⚠️  {check} might need attention")
    else:
        print("❌ Django settings.py missing!")

def suggest_fixes():
    """Suggest potential fixes for 502 errors"""
    print("\n🔧 POTENTIAL FIXES FOR 502 ERRORS")
    print("=" * 50)
    
    fixes = [
        "1. Environment Variables: Ensure all required env vars are set in Railway dashboard",
        "2. Database Connection: Verify DATABASE_URL or individual DB_* variables",
        "3. Port Binding: Make sure gunicorn binds to 0.0.0.0:$PORT",
        "4. Dependencies: Check if all packages install correctly",
        "5. Static Files: Ensure STATIC_ROOT is properly configured",
        "6. Django Check: Run 'python manage.py check' locally",
        "7. Railway Logs: Check Railway deployment logs for specific errors"
    ]
    
    for fix in fixes:
        print(f"  {fix}")
    
    print("\n📋 RAILWAY ENVIRONMENT VARIABLES TO CHECK:")
    env_vars = [
        "DATABASE_URL (or DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)",
        "SECRET_KEY",
        "DEBUG=false",
        "PORT (automatically set by Railway)"
    ]
    
    for var in env_vars:
        print(f"  - {var}")

if __name__ == "__main__":
    check_railway_config()
    suggest_fixes()
    
    print("\n🎯 IMMEDIATE NEXT STEPS:")
    print("1. Check Railway deployment logs in your Railway dashboard")
    print("2. Verify environment variables are set correctly")
    print("3. Test the application locally with 'python manage.py runserver'")
    print("4. If local works, the issue is likely in Railway configuration")
