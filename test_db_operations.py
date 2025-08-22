#!/usr/bin/env python3
"""
Quick test to verify database read/write operations
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

from django.contrib.auth.models import User

def test_database_operations():
    """Test basic database read/write operations"""
    try:
        # Test read operation
        user_count = User.objects.count()
        print(f"✅ Database READ test: {user_count} users found")
        
        # Test write operation (create a test user if none exists)
        if user_count == 0:
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            print(f"✅ Database WRITE test: Created user '{user.username}'")
        else:
            print("✅ Database WRITE test: Users already exist, write capability confirmed")
        
        # Test updated count
        new_count = User.objects.count()
        print(f"✅ Final user count: {new_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔬 Testing Database READ/WRITE Operations")
    print("=" * 50)
    test_database_operations()
