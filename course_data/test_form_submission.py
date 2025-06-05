#!/usr/bin/env python3
"""
Test script to simulate form submissions to check if the database connection is working
"""

import requests
import json
from datetime import datetime, timedelta

def test_demo_booking():
    """Test demo booking form submission"""
    print("🧪 Testing Demo Booking Form Submission")
    print("=" * 50)
    
    # Demo booking data
    demo_data = {
        'name': 'Test Demo User',
        'email': 'demo@test.com',
        'phone': '01234567890',
        'preferred_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        'additional_info': 'Test demo booking submission'
    }
    
    try:
        # Submit demo booking form
        response = requests.post(
            'http://127.0.0.1:5000/book-demo',
            data=demo_data,
            allow_redirects=False
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 302:  # Redirect after successful submission
            print("✅ Demo booking form submitted successfully (redirected)")
            return True
        else:
            print(f"❌ Demo booking failed with status: {response.status_code}")
            print(f"Response content: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing demo booking: {str(e)}")
        return False

def test_enrollment_form():
    """Test enrollment form submission"""
    print("\n🧪 Testing Enrollment Form Submission")
    print("=" * 50)
    
    # Enrollment data
    enrollment_data = {
        'student_name': 'Test Student',
        'student_email': 'student@test.com',
        'date_of_birth': '2010-01-01',
        'education_level': 'Middle',
        'class_grade': '7th Grade',
        'school_name': 'Test School',
        'student_phone': '01234567890',
        'hobby': 'Programming',
        'father_name': 'Test Father',
        'mother_name': 'Test Mother',
        'parent_phone': '01987654321',
        'parent_email': 'parent@test.com',
        'additional_info': 'Test enrollment submission',
        'courses': ['Python Level 1']
    }
    
    try:
        # Submit enrollment form
        response = requests.post(
            'http://127.0.0.1:5000/enroll',
            data=enrollment_data,
            allow_redirects=False
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 302:  # Redirect after successful submission
            print("✅ Enrollment form submitted successfully (redirected)")
            return True
        else:
            print(f"❌ Enrollment failed with status: {response.status_code}")
            print(f"Response content: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing enrollment: {str(e)}")
        return False

def check_server_status():
    """Check if the Flask server is running"""
    print("🔍 Checking Flask Server Status")
    print("=" * 50)
    
    try:
        response = requests.get('http://127.0.0.1:5000/enroll', timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is running and responding")
            return True
        else:
            print(f"❌ Flask server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 TESTING FORM SUBMISSIONS TO DATABASE")
    print("=" * 60)
    
    # Check if server is running
    if not check_server_status():
        print("\n💥 Cannot proceed without Flask server running.")
        print("Please start the server with: python app.py")
        return False
    
    # Test demo booking
    demo_success = test_demo_booking()
    
    # Test enrollment
    enrollment_success = test_enrollment_form()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if demo_success:
        print("✅ Demo Booking Form: WORKING")
    else:
        print("❌ Demo Booking Form: FAILED")
    
    if enrollment_success:
        print("✅ Enrollment Form: WORKING")
    else:
        print("❌ Enrollment Form: FAILED")
    
    if demo_success and enrollment_success:
        print("\n🎉 ALL FORMS ARE WORKING! Database connection is successful.")
    else:
        print("\n⚠️ Some forms failed. Check the Flask server logs for details.")
    
    return demo_success and enrollment_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
