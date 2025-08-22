#!/usr/bin/env python3
"""
Railway Deployment Verification Script
This script helps verify that all deployment requirements are met
"""

import os
from pathlib import Path

def check_deployment_files():
    """Check if all required deployment files exist"""
    base_dir = Path(__file__).parent
    files_to_check = {
        'Procfile': 'Process file for Railway',
        'requirements.txt': 'Python dependencies',
        'runtime.txt': 'Python version specification (optional)',
        '.env': 'Environment variables (local only)',
        'accounts_easy_project/settings.py': 'Django settings',
        'accounts_easy_project/wsgi.py': 'WSGI application'
    }
    
    print("🔍 Checking deployment files:")
    print("=" * 50)
    
    all_good = True
    for file_path, description in files_to_check.items():
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path:<25} - {description}")
        else:
            print(f"❌ {file_path:<25} - {description} (MISSING)")
            if file_path != 'runtime.txt':  # runtime.txt is optional
                all_good = False
    
    return all_good

def check_requirements():
    """Check requirements.txt for essential packages"""
    base_dir = Path(__file__).parent
    req_file = base_dir / 'requirements.txt'
    
    print("\n🔍 Checking requirements.txt:")
    print("=" * 50)
    
    if not req_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    with open(req_file, 'r') as f:
        requirements = f.read()
    
    essential_packages = [
        'Django',
        'psycopg2-binary',
        'gunicorn',
        'whitenoise',
        'python-dotenv'
    ]
    
    all_good = True
    for package in essential_packages:
        if package.lower() in requirements.lower():
            print(f"✅ {package:<20} - Found")
        else:
            print(f"❌ {package:<20} - Missing")
            all_good = False
    
    return all_good

def check_procfile():
    """Check Procfile configuration"""
    base_dir = Path(__file__).parent
    procfile = base_dir / 'Procfile'
    
    print("\n🔍 Checking Procfile:")
    print("=" * 50)
    
    if not procfile.exists():
        print("❌ Procfile not found!")
        return False
    
    with open(procfile, 'r') as f:
        content = f.read().strip()
    
    print(f"Content: {content}")
    
    if 'web:' in content and 'gunicorn' in content and 'accounts_easy_project.wsgi' in content:
        print("✅ Procfile looks correct")
        return True
    else:
        print("❌ Procfile may have issues")
        return False

def check_settings():
    """Check Django settings for production readiness"""
    print("\n🔍 Checking Django settings:")
    print("=" * 50)
    
    # Import Django settings
    import sys
    sys.path.append(str(Path(__file__).parent))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accounts_easy_project.settings')
    
    try:
        import django
        django.setup()
        from django.conf import settings
        
        checks = [
            ('ALLOWED_HOSTS', lambda: len(settings.ALLOWED_HOSTS) > 0 and settings.ALLOWED_HOSTS != ['*']),
            ('DATABASE_ENGINE', lambda: settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql'),
            ('STATIC_ROOT', lambda: hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT),
            ('WHITENOISE_MIDDLEWARE', lambda: 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE),
            ('DEBUG_SETTING', lambda: not settings.DEBUG or os.getenv('DEBUG', 'False').lower() == 'true'),
        ]
        
        all_good = True
        for check_name, check_func in checks:
            try:
                if check_func():
                    print(f"✅ {check_name:<20} - Configured correctly")
                else:
                    print(f"❌ {check_name:<20} - Needs attention")
                    all_good = False
            except Exception as e:
                print(f"❌ {check_name:<20} - Error: {e}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Django settings check failed: {e}")
        return False

def main():
    print("🚀 RAILWAY DEPLOYMENT VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Deployment Files", check_deployment_files),
        ("Requirements", check_requirements),
        ("Procfile", check_procfile),
        ("Django Settings", check_settings),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! Your app should deploy successfully to Railway.")
        print("\n📋 Next steps:")
        print("1. Ensure your Railway project has the correct environment variables set")
        print("2. Push your code to the connected GitHub repository")
        print("3. Railway will automatically deploy your application")
    else:
        print("⚠️  Some issues found. Please fix them before deploying.")
    
    print("\n🔗 Railway Environment Variables to Set:")
    print("- DB_NAME")
    print("- DB_USER") 
    print("- DB_PASSWORD")
    print("- DB_HOST")
    print("- DB_PORT")
    print("- SECRET_KEY")
    print("- DEBUG (optional, set to 'false' for production)")

if __name__ == "__main__":
    main()
