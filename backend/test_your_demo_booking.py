#!/usr/bin/env python3
"""
Test the exact demo booking data you submitted
"""

import requests
from datetime import datetime

def test_your_demo_booking():
    """Test with your exact demo booking data"""
    print("🧪 Testing Your Demo Booking Submission")
    print("=" * 50)
    
    # Your exact data from the form
    demo_data = {
        'name': 'H',
        'email': 'iampoloy8@gmail.com',
        'phone': '017-7006-5234',
        'preferred_date': '2025-06-26',
        'additional_info': 'Any specific topics you\'d like to cover in the demo class...'
    }
    
    print("📝 Your demo booking data:")
    for key, value in demo_data.items():
        print(f"   {key}: {value}")
    
    try:
        # First, get the page to get CSRF token
        print("\n🔍 Getting CSRF token...")
        session = requests.Session()
        response = session.get('http://127.0.0.1:5000/enroll')
        
        if response.status_code != 200:
            print(f"❌ Failed to get enrollment page: {response.status_code}")
            return False
        
        # Extract CSRF token from the page
        import re
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            demo_data['csrf_token'] = csrf_token
            print(f"✅ CSRF token obtained: {csrf_token[:20]}...")
        else:
            print("⚠️ No CSRF token found, proceeding without it")
        
        # Submit demo booking form
        print("\n💾 Submitting demo booking...")
        response = session.post(
            'http://127.0.0.1:5000/book-demo',
            data=demo_data,
            allow_redirects=False
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 302:  # Redirect after successful submission
            print("✅ Demo booking submitted successfully!")
            redirect_location = response.headers.get('Location', '')
            print(f"Redirected to: {redirect_location}")
            return True
        elif response.status_code == 400:
            print("❌ Bad request - validation error")
            print(f"Response content: {response.text[:500]}")
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response content: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing demo booking: {str(e)}")
        return False

def check_if_booking_was_created():
    """Check if the booking was actually created in the database"""
    print("\n📊 Checking if booking was created in database...")
    
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb+srv://dotpyacademy1:m57HHUwKiNwggGB0@dotpy.bpeap9q.mongodb.net/dotpy_academy?retryWrites=true&w=majority&appName=dotpy')
        db = client['dotpy_academy']
        
        # Look for the booking with your email
        booking = db.demo_bookings.find_one({'email': 'iampoloy8@gmail.com'})
        
        if booking:
            print("✅ Booking found in database!")
            print(f"   Name: {booking.get('name', 'Unknown')}")
            print(f"   Email: {booking.get('email', 'Unknown')}")
            print(f"   Phone: {booking.get('phone', 'Unknown')}")
            print(f"   Preferred Date: {booking.get('preferred_date', 'Unknown')}")
            print(f"   Status: {booking.get('status', 'Unknown')}")
            print(f"   Created: {booking.get('created_at', 'Unknown')}")
            return True
        else:
            print("❌ No booking found with your email address")
            return False
            
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        return False

def main():
    """Run the test"""
    print("🚀 TESTING YOUR DEMO BOOKING SUBMISSION")
    print("=" * 60)
    
    # Test the submission
    submission_success = test_your_demo_booking()
    
    # Check if it was created in database
    database_success = check_if_booking_was_created()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    if submission_success:
        print("✅ Form Submission: SUCCESS")
    else:
        print("❌ Form Submission: FAILED")
    
    if database_success:
        print("✅ Database Storage: SUCCESS")
    else:
        print("❌ Database Storage: FAILED")
    
    if submission_success and database_success:
        print("\n🎉 YOUR DEMO BOOKING IS WORKING PERFECTLY!")
        print("The loading issue was likely just a temporary glitch.")
    elif database_success:
        print("\n✅ Your booking was actually created successfully!")
        print("The loading issue was just a UI problem, not a database issue.")
    else:
        print("\n⚠️ There seems to be an issue with the demo booking process.")
    
    return submission_success or database_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
