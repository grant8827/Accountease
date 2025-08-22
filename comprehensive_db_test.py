#!/usr/bin/env python3
"""
Comprehensive PostgreSQL Railway Database Connection Test
"""

import os
import sys
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
sys.path.append('/Users/gregorygrant/Desktop/Websites/Python/Django Web App/accounts_easy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accounts_easy_project.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User

def comprehensive_test():
    """Run comprehensive database tests"""
    results = []
    
    try:
        # Test 1: Connection and version
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            results.append(("✅ Database Connection", f"Connected to {version.split(',')[0]}"))
    except Exception as e:
        results.append(("❌ Database Connection", f"Failed: {e}"))
        return results
    
    try:
        # Test 2: Environment variables
        db_config = {
            'Host': os.getenv('DB_HOST'),
            'Database': os.getenv('DB_NAME'),
            'User': os.getenv('DB_USER'),
            'Port': os.getenv('DB_PORT')
        }
        config_str = f"Host: {db_config['Host']}, DB: {db_config['Database']}, User: {db_config['User']}, Port: {db_config['Port']}"
        results.append(("✅ Configuration", config_str))
    except Exception as e:
        results.append(("❌ Configuration", f"Failed: {e}"))
    
    try:
        # Test 3: Django tables
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE 'django_%'
            """)
            django_tables = cursor.fetchone()[0]
            results.append(("✅ Django Tables", f"{django_tables} Django system tables found"))
    except Exception as e:
        results.append(("❌ Django Tables", f"Failed: {e}"))
    
    try:
        # Test 4: App tables
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE 'accounts_easy_%'
            """)
            app_tables = cursor.fetchone()[0]
            results.append(("✅ App Tables", f"{app_tables} accounts_easy tables found"))
    except Exception as e:
        results.append(("❌ App Tables", f"Failed: {e}"))
    
    try:
        # Test 5: User model operations
        user_count = User.objects.count()
        results.append(("✅ Read Operations", f"{user_count} users in database"))
    except Exception as e:
        results.append(("❌ Read Operations", f"Failed: {e}"))
    
    try:
        # Test 6: Write operations (create test user if needed)
        test_user_exists = User.objects.filter(username='db_test_user').exists()
        if not test_user_exists:
            User.objects.create_user(
                username='db_test_user',
                email='dbtest@example.com',
                password='testpass123'
            )
            results.append(("✅ Write Operations", "Test user created successfully"))
        else:
            results.append(("✅ Write Operations", "Test user already exists"))
    except Exception as e:
        results.append(("❌ Write Operations", f"Failed: {e}"))
    
    return results

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE RAILWAY POSTGRESQL CONNECTION TEST")
    print("=" * 60)
    
    results = comprehensive_test()
    
    for status, description in results:
        print(f"{status} {description}")
    
    # Summary
    passed = len([r for r in results if r[0].startswith("✅")])
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Railway PostgreSQL database is fully functional!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
