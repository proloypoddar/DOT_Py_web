from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# MongoDB connection
client = MongoClient('mongodb+srv://dotpyacademy1:m57HHUwKiNwggGB0@dotpy.bpeap9q.mongodb.net/dotpy_academy?retryWrites=true&w=majority&appName=dotpy')
db = client['dotpy_academy']
enrollments = db['enrollments']
admins = db['admins']
courses = db['courses']
gallery = db['gallery']
content = db['content']

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

# Course management functions
def create_course(data):
    """Create a new course"""
    try:
        course = {
            'title': data['title'],
            'description': data['description'],
            'duration': data['duration'],
            'price': data['price'],
            'image_url': data.get('image_url'),
            'syllabus': data.get('syllabus', []),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'active'
        }
        result = courses.insert_one(course)
        return True, str(result.inserted_id)
    except Exception as e:
        return False, str(e)

def update_course(course_id, data):
    """Update an existing course"""
    try:
        update_data = {
            '$set': {
                'title': data.get('title'),
                'description': data.get('description'),
                'duration': data.get('duration'),
                'price': data.get('price'),
                'image_url': data.get('image_url'),
                'syllabus': data.get('syllabus'),
                'updated_at': datetime.utcnow()
            }
        }
        result = courses.update_one(
            {'_id': ObjectId(course_id)},
            update_data
        )
        return result.modified_count > 0, "Course updated successfully"
    except Exception as e:
        return False, str(e)

def delete_course(course_id):
    """Delete a course"""
    try:
        result = courses.delete_one({'_id': ObjectId(course_id)})
        return result.deleted_count > 0, "Course deleted successfully"
    except Exception as e:
        return False, str(e)

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