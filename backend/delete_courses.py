from backend.config import Config
from backend.models import get_database
from pymongo.errors import ConnectionFailure

def delete_all_courses():
    """Deletes all courses from the database."""
    try:
        db = get_database()
        if 'courses' in db.list_collection_names():
            db.drop_collection('courses')
            print("All courses deleted successfully.")
        else:
            print("Courses collection does not exist.")
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    delete_all_courses() 