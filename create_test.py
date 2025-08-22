#!/usr/bin/env python3
"""
Create a minimal Django test to identify Railway deployment issues
"""

def create_minimal_test():
    """Create minimal test files for Railway deployment debugging"""
    
    # Create a simple test view
    test_view_content = """
from django.http import HttpResponse
from django.db import connection
import os

def simple_test(request):
    '''Minimal test view to check Railway deployment'''
    try:
        # Test basic response
        response_data = {
            'status': 'OK',
            'django_working': True,
            'environment': {
                'DEBUG': os.getenv('DEBUG', 'Not set'),
                'DB_HOST': os.getenv('DB_HOST', 'Not set'),
                'DB_NAME': os.getenv('DB_NAME', 'Not set'),
                'PORT': os.getenv('PORT', 'Not set'),
                'PYTHONPATH': os.getenv('PYTHONPATH', 'Not set')[:100] + '...' if os.getenv('PYTHONPATH') else 'Not set',
            }
        }
        
        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                response_data['database'] = 'Connected'
        except Exception as e:
            response_data['database'] = f'Error: {str(e)}'
        
        # Format response
        html = '<h1>Railway Deployment Test</h1>'
        for key, value in response_data.items():
            if isinstance(value, dict):
                html += f'<h2>{key}:</h2><ul>'
                for k, v in value.items():
                    html += f'<li><strong>{k}:</strong> {v}</li>'
                html += '</ul>'
            else:
                html += f'<p><strong>{key}:</strong> {value}</p>'
        
        return HttpResponse(html)
        
    except Exception as e:
        return HttpResponse(f'<h1>Error</h1><p>{str(e)}</p>', status=500)
"""
    
    with open('/Users/gregorygrant/Desktop/Websites/Python/Django Web App/accounts_easy/accounts_easy/test_views.py', 'w') as f:
        f.write(test_view_content)
    
    print("✅ Created test_views.py")
    
    # Instructions for adding to URLs
    url_addition = """
# Add this to your accounts_easy/urls.py:
from .test_views import simple_test

# Add this to urlpatterns:
path('test/', simple_test, name='simple_test'),
"""
    
    print("📋 To use this test:")
    print(url_addition)

if __name__ == "__main__":
    create_minimal_test()
