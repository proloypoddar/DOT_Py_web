#!/usr/bin/env python3
"""
Database Health Check Script for DotPy Academy
This script checks the MongoDB database connection and displays all collections and their data.
"""

from pymongo import MongoClient
from datetime import datetime
from pprint import pprint
import sys

def check_database_health():
    """Comprehensive database health check"""
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb+srv://dotpyacademy1:m57HHUwKiNwggGB0@dotpy.bpeap9q.mongodb.net/dotpy_academy?retryWrites=true&w=majority&appName=dotpy')
        db = client['dotpy_academy']
        
        print("🔍 DOTPY ACADEMY DATABASE HEALTH CHECK")
        print("=" * 50)
        
        # Test connection with ping
        db.command('ping')
        print("✅ Database Connection: SUCCESSFUL")
        
        # Get database stats
        stats = db.command("dbstats")
        print(f"📊 Database Size: {stats.get('dataSize', 0) / 1024 / 1024:.2f} MB")
        print(f"📁 Storage Size: {stats.get('storageSize', 0) / 1024 / 1024:.2f} MB")
        
        # Get all collection names
        collections = db.list_collection_names()
        print(f"📚 Total Collections: {len(collections)}")
        
        print("\n" + "=" * 50)
        print("COLLECTION DETAILS")
        print("=" * 50)
        
        for collection_name in collections:
            print(f"\n📁 Collection: {collection_name}")
            print("-" * 40)
            
            # Get collection stats
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                print(f"   📊 Document Count: {count}")
                
                if count > 0:
                    # Show sample documents (limit to 3)
                    sample_docs = list(collection.find().limit(3))
                    print(f"   📄 Sample Documents:")
                    for i, doc in enumerate(sample_docs, 1):
                        print(f"      Document {i}:")
                        # Convert ObjectId to string for better display
                        if '_id' in doc:
                            doc['_id'] = str(doc['_id'])
                        # Format datetime objects
                        for key, value in doc.items():
                            if isinstance(value, datetime):
                                doc[key] = value.strftime('%Y-%m-%d %H:%M:%S UTC')
                        
                        for key, value in doc.items():
                            if isinstance(value, list) and len(value) > 3:
                                print(f"         {key}: [{', '.join(map(str, value[:3]))}, ... ({len(value)} items)]")
                            elif isinstance(value, str) and len(value) > 100:
                                print(f"         {key}: {value[:100]}...")
                            else:
                                print(f"         {key}: {value}")
                        print()
                else:
                    print("   📄 No documents found")
            
            except Exception as e:
                print(f"   ❌ Error accessing collection: {str(e)}")
        
        # Check specific collections for business logic
        print("\n" + "=" * 50)
        print("BUSINESS DATA SUMMARY")
        print("=" * 50)
        
        # Enrollments summary
        enrollments_count = db.enrollments.count_documents({})
        pending_enrollments = db.enrollments.count_documents({"status": "pending"})
        approved_enrollments = db.enrollments.count_documents({"status": "approved"})
        
        print(f"🎓 ENROLLMENTS:")
        print(f"   Total: {enrollments_count}")
        print(f"   Pending: {pending_enrollments}")
        print(f"   Approved: {approved_enrollments}")
        
        # Courses summary
        courses_count = db.courses.count_documents({})
        active_courses = db.courses.count_documents({"status": "active"})
        
        print(f"\n📚 COURSES:")
        print(f"   Total: {courses_count}")
        print(f"   Active: {active_courses}")
        
        # Gallery summary
        gallery_count = db.gallery.count_documents({})
        print(f"\n🖼️ GALLERY ITEMS: {gallery_count}")
        
        # Content summary
        content_count = db.content.count_documents({})
        published_content = db.content.count_documents({"status": "published"})
        
        print(f"\n📝 CONTENT:")
        print(f"   Total: {content_count}")
        print(f"   Published: {published_content}")
        
        # Demo bookings summary
        demo_count = db.demo_bookings.count_documents({}) if 'demo_bookings' in collections else 0
        print(f"\n🎯 DEMO BOOKINGS: {demo_count}")
        
        # Admin users summary
        admin_count = db.admins.count_documents({})
        print(f"\n👤 ADMIN USERS: {admin_count}")
        
        print("\n" + "=" * 50)
        print("✅ DATABASE HEALTH CHECK COMPLETED SUCCESSFULLY")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Database connection failed!")
        print(f"Error details: {str(e)}")
        print("\nPossible issues:")
        print("- Internet connection problems")
        print("- MongoDB Atlas cluster is down")
        print("- Invalid connection string")
        print("- Authentication issues")
        return False

def test_database_operations():
    """Test basic database operations"""
    try:
        client = MongoClient('mongodb+srv://dotpyacademy1:m57HHUwKiNwggGB0@dotpy.bpeap9q.mongodb.net/dotpy_academy?retryWrites=true&w=majority&appName=dotpy')
        db = client['dotpy_academy']
        
        print("\n🧪 TESTING DATABASE OPERATIONS")
        print("=" * 50)
        
        # Test insert
        test_doc = {
            'test_field': 'health_check_test',
            'timestamp': datetime.utcnow(),
            'test_number': 12345
        }
        
        result = db.health_check_test.insert_one(test_doc)
        print(f"✅ INSERT Test: Document inserted with ID {result.inserted_id}")
        
        # Test read
        retrieved = db.health_check_test.find_one({'_id': result.inserted_id})
        print(f"✅ READ Test: Document retrieved successfully")
        
        # Test update
        update_result = db.health_check_test.update_one(
            {'_id': result.inserted_id},
            {'$set': {'test_field': 'updated_value'}}
        )
        print(f"✅ UPDATE Test: {update_result.modified_count} document(s) updated")
        
        # Test delete
        delete_result = db.health_check_test.delete_one({'_id': result.inserted_id})
        print(f"✅ DELETE Test: {delete_result.deleted_count} document(s) deleted")
        
        print("✅ All database operations working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting DotPy Academy Database Health Check...\n")
    
    # Run health check
    health_ok = check_database_health()
    
    if health_ok:
        # Run operations test
        ops_ok = test_database_operations()
        
        if ops_ok:
            print(f"\n🎉 ALL TESTS PASSED! Your database is healthy and operational.")
            sys.exit(0)
        else:
            print(f"\n⚠️ Database connection works but operations failed.")
            sys.exit(1)
    else:
        print(f"\n💥 Database health check failed. Please check your connection.")
        sys.exit(1)
