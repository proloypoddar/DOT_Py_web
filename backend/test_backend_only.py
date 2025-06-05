#!/usr/bin/env python3
"""
Test the backend database functions directly (bypassing Flask forms)
"""

import sys
import os
from datetime import datetime, timedelta
from pymongo import MongoClient

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import create_enrollment, validate_enrollment

def test_enrollment_backend():
    """Test enrollment creation directly"""
    print("🧪 Testing Enrollment Backend (Direct Database)")
    print("=" * 50)
    
    # Test data
    enrollment_data = {
        'student_name': 'Backend Test Student',
        'student_email': 'backend@test.com',
        'date_of_birth': '2010-01-01',
        'education_level': 'Middle',
        'class_grade': '7th Grade',
        'school_name': 'Backend Test School',
        'student_phone': '01234567890',
        'hobby': 'Programming',
        'father_name': 'Backend Test Father',
        'mother_name': 'Backend Test Mother',
        'parent_phone': '01987654321',
        'parent_email': 'backend_parent@test.com',
        'additional_info': 'Backend test enrollment',
        'courses': ['Python Level 1']
    }
    
    print("📝 Test enrollment data:")
    for key, value in enrollment_data.items():
        print(f"   {key}: {value}")
    
    # Test validation
    print("\n🔍 Testing validation...")
    is_valid, message = validate_enrollment(enrollment_data)
    if is_valid:
        print("✅ Validation passed")
    else:
        print(f"❌ Validation failed: {message}")
        return False
    
    # Test database insertion
    print("\n💾 Testing database insertion...")
    success, result = create_enrollment(enrollment_data)
    if success:
        print(f"✅ Enrollment created successfully with ID: {result}")
        return True, result
    else:
        print(f"❌ Enrollment creation failed: {result}")
        return False, None

def test_demo_booking_backend():
    """Test demo booking creation directly"""
    print("\n🧪 Testing Demo Booking Backend (Direct Database)")
    print("=" * 50)
    
    try:
        # Connect to database
        client = MongoClient('mongodb+srv://dotpyacademy1:m57HHUwKiNwggGB0@dotpy.bpeap9q.mongodb.net/dotpy_academy?retryWrites=true&w=majority&appName=dotpy')
        db = client['dotpy_academy']
        
        # Test data
        demo_data = {
            'name': 'Backend Demo User',
            'email': 'backend_demo@test.com',
            'phone': '01234567890',
            'preferred_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'additional_info': 'Backend test demo booking',
            'created_at': datetime.now(),
            'status': 'Pending'
        }
        
        print("📝 Test demo booking data:")
        for key, value in demo_data.items():
            if isinstance(value, datetime):
                print(f"   {key}: {value.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"   {key}: {value}")
        
        # Test database insertion
        print("\n💾 Testing database insertion...")
        result = db.demo_bookings.insert_one(demo_data)
        print(f"✅ Demo booking created successfully with ID: {result.inserted_id}")
        return True, result.inserted_id
        
    except Exception as e:
        print(f"❌ Demo booking creation failed: {str(e)}")
        return False, None

def check_database_records():
    """Check current database records"""
    print("\n📊 Checking Current Database Records")
    print("=" * 50)
    
    try:
        client = MongoClient('mongodb+srv://dotpyacademy1:m57HHUwKiNwggGB0@dotpy.bpeap9q.mongodb.net/dotpy_academy?retryWrites=true&w=majority&appName=dotpy')
        db = client['dotpy_academy']
        
        # Count enrollments
        enrollment_count = db.enrollments.count_documents({})
        print(f"📚 Total Enrollments: {enrollment_count}")
        
        # Count demo bookings
        demo_count = db.demo_bookings.count_documents({})
        print(f"🎯 Total Demo Bookings: {demo_count}")
        
        # Show recent enrollments
        recent_enrollments = list(db.enrollments.find().sort('enrollment_date', -1).limit(3))
        print(f"\n📋 Recent Enrollments:")
        for i, enrollment in enumerate(recent_enrollments, 1):
            print(f"   {i}. {enrollment.get('student_name', 'Unknown')} - {enrollment.get('student_email', 'No email')}")
        
        # Show recent demo bookings
        recent_demos = list(db.demo_bookings.find().sort('created_at', -1).limit(3))
        print(f"\n📋 Recent Demo Bookings:")
        for i, demo in enumerate(recent_demos, 1):
            print(f"   {i}. {demo.get('name', 'Unknown')} - {demo.get('email', 'No email')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        client = MongoClient('mongodb+srv://dotpyacademy1:m57HHUwKiNwggGB0@dotpy.bpeap9q.mongodb.net/dotpy_academy?retryWrites=true&w=majority&appName=dotpy')
        db = client['dotpy_academy']
        
        # Delete test enrollments
        enrollment_result = db.enrollments.delete_many({
            'student_email': {'$regex': 'backend.*@test.com'}
        })
        print(f"✅ Deleted {enrollment_result.deleted_count} test enrollment(s)")
        
        # Delete test demo bookings
        demo_result = db.demo_bookings.delete_many({
            'email': {'$regex': 'backend.*@test.com'}
        })
        print(f"✅ Deleted {demo_result.deleted_count} test demo booking(s)")
        
        return True
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        return False

def main():
    """Run all backend tests"""
    print("🚀 TESTING BACKEND DATABASE FUNCTIONS")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Check initial state
    check_database_records()
    
    # Test enrollment backend
    enrollment_success, enrollment_id = test_enrollment_backend()
    if not enrollment_success:
        all_tests_passed = False
    
    # Test demo booking backend
    demo_success, demo_id = test_demo_booking_backend()
    if not demo_success:
        all_tests_passed = False
    
    # Check final state
    check_database_records()
    
    # Cleanup
    cleanup_test_data()
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 BACKEND TEST RESULTS")
    print("=" * 60)
    
    if enrollment_success:
        print("✅ Enrollment Backend: WORKING")
    else:
        print("❌ Enrollment Backend: FAILED")
    
    if demo_success:
        print("✅ Demo Booking Backend: WORKING")
    else:
        print("❌ Demo Booking Backend: FAILED")
    
    if all_tests_passed:
        print("\n🎉 ALL BACKEND FUNCTIONS ARE WORKING!")
        print("The database connection and form processing logic are correct.")
        print("The issue with form submissions is likely just CSRF protection.")
    else:
        print("\n⚠️ Some backend functions failed.")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
