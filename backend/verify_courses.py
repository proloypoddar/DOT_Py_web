from pymongo import MongoClient
from config import Config
import json
from datetime import datetime

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError(f"Object of type {type(x)} is not JSON serializable")

def main():
    # Connect to MongoDB
    client = MongoClient(Config.MONGO_URI)
    db = client[Config.MONGO_DB_NAME]
    
    # Get all courses
    courses = list(db.courses.find())
    
    print(f"\nFound {len(courses)} courses in the database:\n")
    
    # Print each course's details
    for course in courses:
        print("=" * 80)
        print(f"Title: {course['title']}")
        print(f"ID: {course['_id']}")
        print(f"Price: ${course['price']}")
        print(f"Duration: {course['duration']}")
        print(f"Level: {course['level']}")
        print(f"Status: {course['status']}")
        print("\nSyllabus:")
        for i, topic in enumerate(course['syllabus'], 1):
            print(f"{i}. {topic}")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    main() 