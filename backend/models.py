from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config # Import Config for standardized URI
import os
import logging

# Configure logging for models
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
# Use the standardized MONGO_URI from Config
client = MongoClient(Config.MONGO_URI)
db = client[Config.MONGO_DB_NAME] # Use the database name from Config

def get_database():
    """Returns the MongoDB database object."""
    # Ensure connection is active and return the database
    try:
        client.admin.command('ping') # Check if connection is active
        return db
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        return None

enrollments = db['enrollments']
admins = db['admins']
courses = db['courses']
gallery = db['gallery']
content = db['content']
teachers = db['teachers'] # Teachers collection (for future use)

# MongoDB schema for enrollment
enrollment_schema = {
    'student_name': str,
    'student_email': str,  # Added student email field
    'date_of_birth': datetime,
    'education_level': str,  # Added education level field
    'class_grade': str,
    'school_name': str,
    'student_phone': str,
    'hobby': str,
    'father_name': str,
    'mother_name': str,
    'parent_phone': str,
    'parent_email': str,
    'additional_info': str,
    'courses': list,  # Changed from 'course' to 'courses' to handle multiple courses
    'enrollment_date': datetime,
    'status': str  # pending, approved, rejected
}

# Admin user schema
admin_schema = {
    'username': str,
    'password_hash': str,
    'email': str,
    'role': str,  # 'super_admin' or 'admin'
    'created_at': datetime,
    'last_login': datetime
}

# Course schema definition
course_schema = {
    'title': str,
    'short_description': str,
    'long_description': str,
    'image_filename': str, # Storing filename, assuming images are in static/uploads/courses
    'video_url': str, # URL for the main course video
    'price': (int, float),
    'duration': str, # e.g., "8 weeks", "30 hours"
    'level': str, # e.g., "Beginner", "Intermediate", "Advanced"
    'syllabus': list, # List of strings or dicts for syllabus points/sections
    'content': list, # List of content item IDs or embedded content structure
    'teacher_id': (str, ObjectId, type(None)), # Allow None
    'created_at': datetime,
    'updated_at': datetime,
    'status': str # e.g., 'active', 'draft', 'archived'
}

# Teacher schema definition
teacher_schema = {
    'name': str,
    'bio': str,
    'image_filename': str,
    'contact_email': str,
    'created_at': datetime,
    'updated_at': datetime,
}

# Content schema definition
content_item_schema = {
    'title': str,
    'type': str, # e.g., 'text', 'video', 'image', 'file', 'quiz'
    'data': object, # Content data (text string, video URL, file path, quiz structure)
    'caption': str, # Caption for media types
    'course_id': (str, ObjectId, type(None)), # Reference to the course this content belongs to
    'order': int, # Order within the course or section
    'created_at': datetime,
    'updated_at': datetime,
}

def validate_enrollment(data):
    """
    Validate enrollment data before saving to MongoDB
    """
    required_fields = [
        'student_name', 'student_email', 'date_of_birth', 'education_level',
        'class_grade', 'school_name', 'father_name', 'mother_name',
        'parent_phone', 'parent_email', 'courses'
    ]

    # Check required fields
    for field in required_fields:
        if not data.get(field):
            return False, f"{field.replace('_', ' ').title()} is required"

    # Validate email formats
    if '@' not in data['parent_email'] or '.' not in data['parent_email']:
        return False, "Invalid parent email format"

    if '@' not in data['student_email'] or '.' not in data['student_email']:
        return False, "Invalid student email format"

    # Validate phone number format (basic validation)
    parent_phone = data.get('parent_phone', '').replace('-', '').replace(' ', '')
    if not parent_phone.isdigit() or len(parent_phone) < 10:
        return False, "Parent phone number must be at least 10 digits"

    if data.get('student_phone'):
        student_phone = data['student_phone'].replace('-', '').replace(' ', '')
        if not student_phone.isdigit() or len(student_phone) < 10:
            return False, "Student phone number must be at least 10 digits"

    # Validate date format
    try:
        if isinstance(data['date_of_birth'], str):
            data['date_of_birth'] = datetime.strptime(data['date_of_birth'], '%Y-%m-%d')
    except ValueError:
        return False, "Invalid date format for date of birth"

    # Validate course selection
    if not isinstance(data.get('courses'), list) or len(data.get('courses', [])) == 0:
        return False, "At least one course must be selected"

    # Validate education level
    valid_education_levels = ['Primary', 'Middle', 'High', 'College', 'University']
    if data.get('education_level') not in valid_education_levels:
        return False, "Please select a valid education level"

    return True, "Valid"

def create_enrollment(data):
    """
    Create a new enrollment record in MongoDB
    """
    try:
        # Convert date string to datetime if needed
        if isinstance(data.get('date_of_birth'), str):
            data['date_of_birth'] = datetime.strptime(data['date_of_birth'], '%Y-%m-%d')
        
        # Add timestamps and default values
        data['enrollment_date'] = datetime.utcnow()
        data['status'] = 'pending'  # Default status
        
        # Store courses as a list
        if isinstance(data.get('courses'), list):
            data['courses'] = data['courses']  # Keep as list
        else:
            data['courses'] = [data.get('course', '')]  # Convert single course to list
        
        # Validate data
        is_valid, message = validate_enrollment(data)
        if not is_valid:
            return False, message
        
        # Insert into MongoDB
        result = enrollments.insert_one(data)
        return True, str(result.inserted_id)
    except Exception as e:
        print(f"Error creating enrollment: {str(e)}")  # Add logging
        return False, f"Database error: {str(e)}"

def get_enrollment(enrollment_id):
    """
    Get an enrollment record by ID
    """
    try:
        return enrollments.find_one({'_id': ObjectId(enrollment_id)})
    except:
        return None

def get_all_enrollments():
    """
    Get all enrollment records
    """
    return list(enrollments.find())

def update_enrollment_status(enrollment_id, status):
    """
    Update the status of an enrollment
    """
    try:
        result = enrollments.update_one(
            {'_id': ObjectId(enrollment_id)},
            {'$set': {'status': status}}
        )
        return result.modified_count > 0
    except:
        return False

def create_admin(username, password, email, role='admin'):
    """Create a new admin user"""
    if admins.find_one({'username': username}):
        return False, "Username already exists"
    
    if admins.find_one({'email': email}):
        return False, "Email already exists"
    
    admin = {
        'username': username,
        'password_hash': generate_password_hash(password),
        'email': email,
        'role': role,
        'created_at': datetime.utcnow(),
        'last_login': None
    }
    
    try:
        admins.insert_one(admin)
        return True, "Admin created successfully"
    except Exception as e:
        return False, str(e)

def verify_admin(username, password):
    """Verify admin credentials"""
    admin = admins.find_one({'username': username})
    if not admin:
        return False, None
    
    if check_password_hash(admin['password_hash'], password):
        # Update last login
        admins.update_one(
            {'_id': admin['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        return True, admin
    return False, None

def get_admin_by_username(username):
    """Get an admin user by username"""
    try:
        return admins.find_one({'username': username})
    except Exception as e:
        logger.error(f"Error getting admin by username: {e}")
        return None

def update_admin(admin_id, data):
    """Update an admin user's information"""
    try:
        # Ensure ObjectId is valid if provided as string
        if isinstance(admin_id, str):
            admin_id = ObjectId(admin_id)

        # Remove fields that should not be updated this way (like password_hash, role, created_at)
        data.pop('password_hash', None)
        data.pop('role', None)
        data.pop('created_at', None)
        data.pop('_id', None) # Prevent updating the ID

        result = admins.update_one(
            {'__id': admin_id},
            {'$set': data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating admin: {e}")
        return False

# Course management functions
def create_course(data):
    """Create a new course record in MongoDB"""
    try:
        # Basic validation (can be expanded)
        if not data.get('title') or not data.get('short_description') or not data.get('price'):
            return False, "Title, short description, and price are required."

        course = {
            'title': data.get('title'),
            'short_description': data.get('short_description'),
            'long_description': data.get('long_description', ''),
            'image_filename': data.get('image_filename', ''),
            'video_url': data.get('video_url', ''),
            'price': float(data.get('price', 0)), # Ensure price is float
            'duration': data.get('duration', ''),
            'level': data.get('level', 'Beginner'),
            'syllabus': data.get('syllabus', []), # Expecting a list
            'content': data.get('content', []),   # Expecting a list of content references/embeds
            'teacher_id': data.get('teacher_id'), # Expecting ObjectId or str or None
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': data.get('status', 'draft')
        }

        result = courses.insert_one(course)
        return True, str(result.inserted_id)
    except Exception as e:
        print(f"Error creating course: {str(e)}")
        return False, f"Database error: {str(e)}"

def get_course_by_id(course_id):
    """Get a single course by its ID"""
    try:
        # Convert string ID to ObjectId
        course_id_obj = ObjectId(course_id)
        return courses.find_one({'_id': course_id_obj})
    except Exception as e:
        print(f"Error getting course by ID {course_id}: {str(e)}")
        return None

def get_all_courses():
    """Get all course records"""
    try:
        return list(courses.find().sort('created_at', -1))
    except Exception as e:
        print(f"Error getting all courses: {str(e)}")
        return []

def update_course(course_id, data):
    """Update an existing course record"""
    try:
        # Convert string ID to ObjectId
        course_id_obj = ObjectId(course_id)

        update_data = {
            '$set': {
                'title': data.get('title'),
                'short_description': data.get('short_description'),
                'long_description': data.get('long_description', ''),
                'image_filename': data.get('image_filename', ''),
                'video_url': data.get('video_url', ''),
                'price': float(data.get('price', 0)), # Ensure price is float
                'duration': data.get('duration', ''),
                'level': data.get('level', 'Beginner'),
                'syllabus': data.get('syllabus', []), # Expecting a list
                'content': data.get('content', []),   # Expecting a list
                'teacher_id': data.get('teacher_id'), # Expecting ObjectId or str or None
                'updated_at': datetime.utcnow(),
                'status': data.get('status', 'draft')
            }
            # Consider using $unset for fields that can be emptied
        }

        result = courses.update_one(
            {'_id': course_id_obj},
            update_data
        )

        if result.modified_count > 0:
            return True, "Course updated successfully"
        else:
            # Check if the course exists even if not modified
            if courses.count_documents({'_id': course_id_obj}) == 0:
                 return False, "Course not found."
            return False, "Course data was the same or update failed."

    except Exception as e:
        print(f"Error updating course {course_id}: {str(e)}")
        return False, f"Database error: {str(e)}"

def delete_course(course_id):
    """Delete a course record from MongoDB"""
    try:
        # Convert string ID to ObjectId
        course_id_obj = ObjectId(course_id)

        result = courses.delete_one({'_id': course_id_obj})

        if result.deleted_count > 0:
            return True, "Course deleted successfully"
        else:
            return False, "Course not found."

    except Exception as e:
        print(f"Error deleting course {course_id}: {str(e)}")
        return False, f"Database error: {str(e)}"

# Gallery management functions
def add_gallery_item(data):
    """Add a new item to the gallery"""
    try:
        item = {
            'title': data['title'],
            'description': data.get('description'),
            'image_url': data['image_url'],
            'category': data.get('category', 'general'),
            'created_at': datetime.utcnow()
        }
        result = gallery.insert_one(item)
        return True, str(result.inserted_id)
    except Exception as e:
        return False, str(e)

def delete_gallery_item(item_id):
    """Delete a gallery item"""
    try:
        result = gallery.delete_one({'_id': ObjectId(item_id)})
        return result.deleted_count > 0, "Gallery item deleted successfully"
    except Exception as e:
        return False, str(e)

# Content management functions
def create_content(data):
    """Create new content (blog post, announcement, etc.)"""
    try:
        content_item = {
            'title': data['title'],
            'content': data['content'],
            'type': data['type'],  # 'blog', 'announcement', etc.
            'author': data['author'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'published'
        }
        result = content.insert_one(content_item)
        return True, str(result.inserted_id)
    except Exception as e:
        return False, str(e)

def update_content(content_id, data):
    """Update existing content"""
    try:
        update_data = {
            '$set': {
                'title': data.get('title'),
                'content': data.get('content'),
                'type': data.get('type'),
                'updated_at': datetime.utcnow(),
                'status': data.get('status', 'published')
            }
        }
        result = content.update_one(
            {'_id': ObjectId(content_id)},
            update_data
        )
        return result.modified_count > 0, "Content updated successfully"
    except Exception as e:
        return False, str(e)

def delete_content(content_id):
    """Delete content"""
    try:
        result = content.delete_one({'_id': ObjectId(content_id)})
        return result.deleted_count > 0, "Content deleted successfully"
    except Exception as e:
        return False, str(e)

def delete_all_admins():
    """Delete all admin users from the admins collection."""
    try:
        result = admins.delete_many({})
        return result.deleted_count, "All admins deleted successfully"
    except Exception as e:
        return 0, str(e)

def create_content_item(data):
    """Create a new content item record in MongoDB"""
    try:
        # Basic validation
        if not data.get('title') or not data.get('type') or data.get('data') is None:
             return False, "Title, type, and data are required."

        content_item = {
            'title': data.get('title'),
            'type': data.get('type'),
            'data': data.get('data'),
            'caption': data.get('caption', ''),
            'course_id': data.get('course_id'), # Expecting ObjectId or str or None
            'order': int(data.get('order', 0)), # Ensure order is an integer
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }

        result = content.insert_one(content_item)
        logger.info(f"Content item created with ID: {result.inserted_id}")
        return True, str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error creating content item: {str(e)}")
        return False, f"Database error: {str(e)}"

def get_content_item_by_id(item_id):
    """Get a single content item by its ID"""
    try:
        item_id_obj = ObjectId(item_id)
        content_item = content.find_one({'_id': item_id_obj})
        if content_item:
            logger.info(f"Found content item with ID: {item_id}")
        else:
            logger.warning(f"Content item not found with ID: {item_id}")
        return content_item
    except Exception as e:
        logger.error(f"Error getting content item by ID {item_id}: {str(e)}")
        return None

def get_content_items_by_course(course_id):
    """Get all content items for a specific course, ordered by order field"""
    try:
        # Allow getting content for None (unassigned) course_id
        if course_id is not None:
            course_id_filter = ObjectId(course_id) if isinstance(course_id, str) else course_id
            query = {'course_id': course_id_filter}
        else:
            query = {'course_id': None}

        content_list = list(content.find(query).sort('order', 1))
        logger.info(f"Retrieved {len(content_list)} content items for course ID: {course_id}")
        return content_list
    except Exception as e:
        logger.error(f"Error getting content items for course {course_id}: {str(e)}")
        return []

def get_all_content_items():
    """Get all content item records"""
    try:
        content_list = list(content.find().sort('created_at', -1))
        logger.info(f"Retrieved {len(content_list)} content items.")
        return content_list
    except Exception as e:
        logger.error(f"Error getting all content items: {str(e)}")
        return []

def update_content_item(item_id, data):
    """Update an existing content item record"""
    try:
        item_id_obj = ObjectId(item_id)

        update_data = {
            '$set': {
                'title': data.get('title'),
                'type': data.get('type'),
                'data': data.get('data'),
                'caption': data.get('caption', ''),
                'course_id': data.get('course_id'), # Expecting ObjectId or str or None
                'order': int(data.get('order', 0)), # Ensure order is an integer
                'updated_at': datetime.utcnow(),
            }
        }

        result = content.update_one(
            {'_id': item_id_obj},
            update_data
        )

        if result.modified_count > 0:
            logger.info(f"Content item updated successfully: {item_id}")
            return True, "Content item updated successfully"
        else:
            if content.count_documents({'_id': item_id_obj}) == 0:
                 logger.warning(f"Content item not found for update: {item_id}")
                 return False, "Content item not found."
            logger.info(f"Content item data was the same for ID: {item_id}")
            return False, "Content item data was the same or update failed."

    except Exception as e:
        logger.error(f"Error updating content item {item_id}: {str(e)}")
        return False, f"Database error: {str(e)}"

def delete_content_item(item_id):
    """Delete a content item record from MongoDB"""
    try:
        item_id_obj = ObjectId(item_id)

        result = content.delete_one({'_id': item_id_obj})

        if result.deleted_count > 0:
            logger.info(f"Content item deleted successfully: {item_id}")
            return True, "Content item deleted successfully"
        else:
            logger.warning(f"Content item not found for deletion: {item_id}")
            return False, "Content item not found."

    except Exception as e:
        logger.error(f"Error deleting content item {item_id}: {str(e)}")
        return False, f"Database error: {str(e)}" 