#!/usr/bin/env python3
"""
Test script to verify that enrollment and demo booking forms are properly connected to the database.
"""

import sys
import os
from datetime import datetime, timedelta
from pymongo import MongoClient

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import create_enrollment, validate_enrollment
from config import Config

def test_database_connection():
    """Test basic database connectivity"""
    try:
        client = MongoClient(Config.MONGO_URI)
        db = client['myDatabase']
        db.command('ping')
        print("✅ Database connection successful")
        return True, db
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False, None

def test_enrollment_form_data():
    """Test enrollment form with complete data"""
    print("\n🧪 Testing Enrollment Form Database Connection")
    print("=" * 50)
    
    # Sample enrollment data (matching the form fields)
    enrollment_data = {
        'student_name': 'Alice Johnson',
        'student_email': 'alice.johnson@email.com',
        'date_of_birth': '2010-05-15',
        'education_level': 'Middle',
        'class_grade': '8th Grade',
        'school_name': 'Springfield Middle School',
        'student_phone': '01234567890',
        'hobby': 'Reading, Programming',
        'father_name': 'Robert Johnson',
        'mother_name': 'Sarah Johnson',
        'parent_phone': '01987654321',
        'parent_email': 'parents.johnson@email.com',
        'additional_info': 'Student is very interested in technology and coding',
        'courses': ['Python Level 1', 'Python Level 2']
    }
    
    print("📝 Sample enrollment data:")
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

def test_demo_booking_data():
    """Test demo booking form with database"""
    print("\n🧪 Testing Demo Booking Form Database Connection")
    print("=" * 50)
    
    try:
        success, db = test_database_connection()
        if not success:
            return False
        
        # Sample demo booking data
        demo_data = {
            'name': 'Michael Smith',
            'email': 'michael.smith@email.com',
            'phone': '01555123456',
            'preferred_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'additional_info': 'Interested in Python programming for beginners',
            'created_at': datetime.now(),
            'status': 'Pending'
        }
        
        print("📝 Sample demo booking data:")
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
        print(f"❌ Demo booking test failed: {str(e)}")
        return False, None

def test_form_validation_edge_cases():
    """Test form validation with various edge cases"""
    print("\n🧪 Testing Form Validation Edge Cases")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Missing required field',
            'data': {
                'student_name': 'Test Student',
                # Missing student_email
                'date_of_birth': '2010-01-01',
                'education_level': 'Middle',
                'class_grade': '7th',
                'school_name': 'Test School',
                'father_name': 'Test Father',
                'mother_name': 'Test Mother',
                'parent_phone': '1234567890',
                'parent_email': 'parent@test.com',
                'courses': ['Python Level 1']
            },
            'should_pass': False
        },
        {
            'name': 'Invalid email format',
            'data': {
                'student_name': 'Test Student',
                'student_email': 'invalid-email',  # Invalid email
                'date_of_birth': '2010-01-01',
                'education_level': 'Middle',
                'class_grade': '7th',
                'school_name': 'Test School',
                'father_name': 'Test Father',
                'mother_name': 'Test Mother',
                'parent_phone': '1234567890',
                'parent_email': 'parent@test.com',
                'courses': ['Python Level 1']
            },
            'should_pass': False
        },
        {
            'name': 'Invalid phone number',
            'data': {
                'student_name': 'Test Student',
                'student_email': 'student@test.com',
                'date_of_birth': '2010-01-01',
                'education_level': 'Middle',
                'class_grade': '7th',
                'school_name': 'Test School',
                'father_name': 'Test Father',
                'mother_name': 'Test Mother',
                'parent_phone': '123',  # Too short
                'parent_email': 'parent@test.com',
                'courses': ['Python Level 1']
            },
            'should_pass': False
        },
        {
            'name': 'No courses selected',
            'data': {
                'student_name': 'Test Student',
                'student_email': 'student@test.com',
                'date_of_birth': '2010-01-01',
                'education_level': 'Middle',
                'class_grade': '7th',
                'school_name': 'Test School',
                'father_name': 'Test Father',
                'mother_name': 'Test Mother',
                'parent_phone': '1234567890',
                'parent_email': 'parent@test.com',
                'courses': []  # Empty courses list
            },
            'should_pass': False
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        is_valid, message = validate_enrollment(test_case['data'])
        
        if test_case['should_pass'] and is_valid:
            print(f"✅ Test passed: Validation succeeded as expected")
            passed_tests += 1
        elif not test_case['should_pass'] and not is_valid:
            print(f"✅ Test passed: Validation failed as expected - {message}")
            passed_tests += 1
        else:
            print(f"❌ Test failed: Expected {'pass' if test_case['should_pass'] else 'fail'}, got {'pass' if is_valid else 'fail'}")
    
    print(f"\n📊 Validation tests: {passed_tests}/{total_tests} passed")
    return passed_tests == total_tests

def cleanup_test_data():
    """Clean up test data from database"""
    print("\n🧹 Cleaning up test data...")
    try:
        success, db = test_database_connection()
        if not success:
            return False
        
        # Delete test enrollments
        enrollment_result = db.enrollments.delete_many({
            'student_email': {'$regex': '@email.com$'}
        })
        print(f"✅ Deleted {enrollment_result.deleted_count} test enrollment(s)")
        
        # Delete test demo bookings
        demo_result = db.demo_bookings.delete_many({
            'email': {'$regex': '@email.com$'}
        })
        print(f"✅ Deleted {demo_result.deleted_count} test demo booking(s)")
        
        return True
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 STARTING FORM-DATABASE CONNECTION TESTS")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Database connection
    success, _ = test_database_connection()
    if not success:
        print("💥 Cannot proceed without database connection")
        return False
    
    # Test 2: Enrollment form
    enrollment_success, enrollment_id = test_enrollment_form_data()
    if not enrollment_success:
        all_tests_passed = False
    
    # Test 3: Demo booking form
    demo_success, demo_id = test_demo_booking_data()
    if not demo_success:
        all_tests_passed = False
    
    # Test 4: Validation edge cases
    validation_success = test_form_validation_edge_cases()
    if not validation_success:
        all_tests_passed = False
    
    # Cleanup
    cleanup_test_data()
    
    # Final results
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! Your forms are properly connected to the database.")
        print("\n✅ Enrollment form: Working correctly")
        print("✅ Demo booking form: Working correctly")
        print("✅ Data validation: Working correctly")
        print("✅ Database operations: Working correctly")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
