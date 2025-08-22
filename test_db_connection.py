#!/usr/bin/env python3
"""
Test PostgreSQL database connection for Django project
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
from django.core.management.color import no_style

def test_database_connection():
    """Test the database connection and run basic queries"""
    try:
        # Test basic connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print("✅ Database connection successful!")
            print(f"PostgreSQL version: {version[0]}")
            
            # Test if our tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE 'accounts_easy_%'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"\n✅ Found {len(tables)} accounts_easy tables:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠️  No accounts_easy tables found. You may need to run migrations.")
            
            # Test basic table access
            cursor.execute("SELECT COUNT(*) FROM auth_user;")
            user_count = cursor.fetchone()[0]
            print(f"\n✅ auth_user table accessible: {user_count} users found")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_environment_variables():
    """Test that all required environment variables are loaded"""
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    print("🔍 Environment Variables:")
    all_present = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Hide password for security
            display_value = value if var != 'DB_PASSWORD' else '*' * len(value)
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: Not set")
            all_present = False
    
    return all_present

if __name__ == "__main__":
    print("🔬 Testing PostgreSQL Database Connection")
    print("=" * 50)
    
    # Test environment variables first
    if test_environment_variables():
        print("\n" + "=" * 50)
        # Test database connection
        test_database_connection()
    else:
        print("\n❌ Environment variables not properly configured")
        sys.exit(1)
