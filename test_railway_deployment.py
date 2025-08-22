#!/usr/bin/env python3
"""
Test deployed Railway application
"""

import requests
import time

def test_railway_deployment(url="https://accountease-production.up.railway.app"):
    """Test the deployed Railway application"""
    print(f"🔗 Testing Railway deployment at: {url}")
    print("=" * 60)
    
    try:
        # Test basic connectivity
        print("🔍 Testing basic connectivity...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Application is responding (Status: {response.status_code})")
            
            # Check if it's a Django response
            if 'django' in response.headers.get('Server', '').lower() or 'csrftoken' in response.text.lower():
                print("✅ Django application detected")
            else:
                print("ℹ️  Application is running but Django-specific features not detected")
                
        elif response.status_code == 500:
            print(f"❌ Internal Server Error (Status: {response.status_code})")
            print("   This might indicate a configuration issue")
            
        elif response.status_code == 404:
            print(f"⚠️  Not Found (Status: {response.status_code})")
            print("   Check if the URL is correct")
            
        else:
            print(f"⚠️  Unexpected response (Status: {response.status_code})")
            
        # Test specific endpoints
        endpoints_to_test = [
            "/admin/",
            "/login/",
        ]
        
        print("\n🔍 Testing specific endpoints...")
        for endpoint in endpoints_to_test:
            try:
                test_response = requests.get(f"{url}{endpoint}", timeout=10)
                if test_response.status_code in [200, 302, 301]:
                    print(f"✅ {endpoint:<10} - Accessible (Status: {test_response.status_code})")
                else:
                    print(f"⚠️  {endpoint:<10} - Status: {test_response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint:<10} - Error: {e}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - application might be down or URL incorrect")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout - application might be slow to respond")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🚀 RAILWAY DEPLOYMENT TEST")
    print("=" * 60)
    
    # Wait a moment for deployment to complete
    print("⏳ Waiting 10 seconds for deployment to stabilize...")
    time.sleep(10)
    
    success = test_railway_deployment()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Deployment test completed!")
        print("\n📋 If your application is working:")
        print("- Visit your Railway app URL to see it live")
        print("- Check Railway logs for any additional issues")
        print("- Your Django app should be fully functional")
    else:
        print("⚠️  Deployment test found issues.")
        print("\n🔧 Troubleshooting tips:")
        print("- Check Railway deployment logs")
        print("- Verify environment variables are set correctly")
        print("- Ensure database migrations completed successfully")

if __name__ == "__main__":
    main()
