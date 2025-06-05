from flask import Flask, render_template, url_for, request, jsonify, flash, redirect, session, send_from_directory, current_app
from flask_pymongo import PyMongo
from flask_wtf import CSRFProtect
from datetime import datetime, timedelta
import os
from config import config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import (
    # Enrollment functions
    validate_enrollment, create_enrollment, get_enrollment, get_all_enrollments, update_enrollment_status,
    # Admin functions (although admin creation is separate)
    create_admin, verify_admin, get_admin_by_username, update_admin,
    # Course Management Functions
    create_course, get_course_by_id, get_all_courses, update_course, delete_course,
    # Content Management Functions
    create_content_item, get_content_item_by_id, get_content_items_by_course, get_all_content_items, update_content_item, delete_content_item,
    # Gallery Management Functions
    add_gallery_item, delete_gallery_item,
    # Placeholder for other models (Teachers, Posts, etc.)
    # create_teacher, get_teacher, update_teacher, delete_teacher,
    # create_post, get_post, update_post, delete_post,
)
import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask extensions
mongo = PyMongo()
# csrf = CSRFProtect()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def format_price_filter(price):
    """Jinja2 filter to format price."""
    if price is None:
        return "N/A"
    try:
        # Format as currency, e.g., $100.00
        return f"${price:.2f}"
    except (ValueError, TypeError):
        return str(price) # Return as string if formatting fails

def create_app(config_name='default'):
    app = Flask(__name__,
                template_folder='../frontend/templates',
                static_folder='../frontend/static')

    # Load configuration
    if config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.Config')

    # Set session configuration
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SECRET_KEY'] = app.config.get('SECRET_KEY', 'a_default_secret_key') # Ensure SECRET_KEY is set for sessions

    # Initialize MongoDB with error handling
    try:
        mongo.init_app(app)
        # Test the connection
        with app.app_context():
            mongo.db.command('ping')
            logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        # raise RuntimeError("Database connection failed. Please check your MongoDB configuration.")
        # Allow app to run without DB for development, handle errors in routes
        pass

    # Initialize other extensions
    # csrf = CSRFProtect(app) # Initialize with app
    # csrf.exempt('admin_login') # Exempt after init

    # Create upload folders if they don't exist
    upload_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'uploads')
    os.makedirs(upload_base, exist_ok=True)
    os.makedirs(os.path.join(upload_base, 'courses'), exist_ok=True)
    os.makedirs(os.path.join(upload_base, 'gallery'), exist_ok=True)
    os.makedirs(os.path.join(upload_base, 'content'), exist_ok=True)

    # Register custom Jinja2 filters
    app.jinja_env.filters['format_price'] = format_price_filter

    # Public routes
    @app.route('/')
    def index():
        try:
            # Fetch all courses from the database
            courses = get_all_courses()
            # Pass the courses to the index.html template
            return render_template('index.html', courses=courses)
        except Exception as e:
            current_app.logger.error(f"Error fetching courses for home page: {e}")
            # Render index.html even if there's an error, maybe with an empty courses list or an error message
            return render_template('index.html', courses=[])
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/courses')
    def courses():
        try:
            # Get all courses from database
            courses = list(mongo.db.courses.find().sort('created_at', -1))
            return render_template('courses.html', courses=courses)
        except Exception as e:
            logger.error(f"Error in courses route: {str(e)}")
            flash('An error occurred while loading courses.', 'danger')
            return render_template('courses.html', courses=[])
    
    @app.route('/courses/<course_id>')
    def course_detail(course_id):
        try:
            course = mongo.db.courses.find_one({'_id': ObjectId(course_id)})
            if not course:
                flash('Course not found.', 'danger')
                return redirect(url_for('courses'))
            return render_template('course_detail.html', course=course)
        except Exception as e:
            logger.error(f"Error in course_detail route: {str(e)}")
            flash('An error occurred while loading the course details.', 'danger')
            return redirect(url_for('courses'))

    def send_to_google_sheets(data):
        try:
            response = requests.post(
                app.config['GOOGLE_SCRIPT_URL'],
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error sending data to Google Sheets: {str(e)}")
            return False

    @app.route('/enroll', methods=['GET', 'POST'])
    def enroll():
        if request.method == 'POST':
            try:
                data = {
                    'name': request.form.get('name'),
                    'email': request.form.get('email'),
                    'phone': request.form.get('phone'),
                    'course_id': request.form.get('course_id'),
                    'message': request.form.get('message'),
                    'enrollment_date': datetime.utcnow(),
                    'status': 'pending'
                }
                
                # Validate enrollment data
                # if not validate_enrollment(data):
                #     flash('Please fill in all required fields.', 'danger')
                #     return redirect(url_for('enroll'))
                
                # Create enrollment
                result = mongo.db.enrollments.insert_one(data)
                if result.inserted_id:
                    # Send to Google Sheets
                    send_to_google_sheets(data)
                    flash('Enrollment submitted successfully! We will contact you soon.', 'success')
                    return redirect(url_for('courses'))
                else:
                    flash('Error submitting enrollment.', 'danger')
            except Exception as e:
                logger.error(f"Error in enroll route: {str(e)}")
                flash('An error occurred while processing your enrollment.', 'danger')
        
        try:
            # Get courses for the form
            courses = list(mongo.db.courses.find().sort('title', 1))
            return render_template('enroll.html', courses=courses)
        except Exception as e:
            logger.error(f"Error loading courses for enrollment form: {str(e)}")
            flash('An error occurred while loading the enrollment form.', 'danger')
            return render_template('enroll.html', courses=[])
    
    @app.route('/book-demo')
    def book_demo():
        return render_template('book_demo.html')
    
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        if request.method == 'POST':
            try:
                data = {
                    'name': request.form.get('name'),
                    'email': request.form.get('email'),
                    'phone': request.form.get('phone'),
                    'message': request.form.get('message'),
                    'created_at': datetime.utcnow()
                }
                
                # Save to database
                result = mongo.db.contacts.insert_one(data)
                if result.inserted_id:
                    # Send to Google Sheets
                    send_to_google_sheets(data)
                    flash('Message sent successfully! We will contact you soon.', 'success')
                    return redirect(url_for('contact'))
                else:
                    flash('Error sending message.', 'danger')
            except Exception as e:
                logger.error(f"Error in contact route: {str(e)}")
                flash('An error occurred while sending your message.', 'danger')
        
        return render_template('contact.html')

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        except Exception as e:
            logger.error(f"Error serving uploaded file {filename}: {str(e)}")
            return "File not found", 404

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {str(error)}")
        return render_template('errors/500.html'), 500

    # Admin routes
    @app.route('/admin')
    def admin():
        return redirect(url_for('admin_dashboard')) # Redirect /admin to dashboard

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            logger.info(f"Login attempt for email: {email}")
            
            if not email or not password:
                logger.warning("Login attempt with missing email or password")
                flash('Please enter both email and password.', 'danger')
                return render_template('admin/login.html')
            
            try:
                admin = mongo.db.admins.find_one({'email': email})
                if admin:
                    logger.info(f"Found admin user: {email}")
                    if check_password_hash(admin['password'], password):
                        logger.info(f"Successful login for: {email}")
                        session.permanent = True
                        session['admin_id'] = str(admin['_id'])
                        session['admin_email'] = admin['email']
                        flash('Welcome back!', 'success')
                        return redirect(url_for('admin_dashboard'))
                    else:
                        logger.warning(f"Invalid password for: {email}")
                        flash('Invalid email or password.', 'danger')
                else:
                    logger.warning(f"Admin user not found: {email}")
                    flash('Invalid email or password.', 'danger')
            except Exception as e:
                logger.error(f"Login error for {email}: {str(e)}")
                flash('An error occurred during login. Please try again.', 'danger')
        
        return render_template('admin/login.html')

    @app.route('/admin/logout')
    def admin_logout():
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('admin_login'))

    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        try:
            # Get counts for dashboard
            stats = {
                'courses': mongo.db.courses.count_documents({}),
                'enrollments': mongo.db.enrollments.count_documents({}),
                'contacts': mongo.db.contacts.count_documents({}),
                'recent_enrollments': list(mongo.db.enrollments.find().sort('enrollment_date', -1).limit(5)),
                'recent_contacts': list(mongo.db.contacts.find().sort('created_at', -1).limit(5))
            }
            return render_template('admin/dashboard.html', stats=stats)
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            flash('Error loading dashboard data.', 'danger')
            # Redirect to login if dashboard data loading fails (e.g., DB issue)
            return redirect(url_for('admin_login'))

    # Admin Course Management Routes
    @app.route('/admin/courses')
    @login_required
    def admin_courses():
        try:
            courses = list(mongo.db.courses.find().sort('title', 1))
            return render_template('admin/courses.html', courses=courses)
        except Exception as e:
            logger.error(f"Error loading courses: {str(e)}")
            flash('Error loading courses.', 'danger')
            return render_template('admin/courses.html', courses=[], error=str(e))

    @app.route('/admin/courses/add', methods=['GET', 'POST'])
    @login_required
    def admin_add_course():
        if request.method == 'POST':
            try:
                # Extract form data and handle file uploads
                title = request.form.get('title')
                short_description = request.form.get('short_description')
                long_description = request.form.get('long_description')
                price = request.form.get('price')
                duration = request.form.get('duration')
                level = request.form.get('level')
                video_url = request.form.get('video_url')
                syllabus_text = request.form.get('syllabus')
                teacher_id = request.form.get('teacher_id')
                status = request.form.get('status')
                image_file = request.files.get('image')

                # Process syllabus text into a list
                syllabus = [line.strip() for line in syllabus_text.split('\n') if line.strip()]

                image_filename = ''
                if image_file and image_file.filename:
                    # Sanitize filename and save file
                    filename = secure_filename(image_file.filename)
                    # Ensure the filename is unique if necessary, e.g., by prepending a timestamp or UUID
                    image_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
                    image_path = os.path.join(app.static_folder, 'uploads', 'courses', image_filename)
                    image_file.save(image_path)
                    logger.info(f"Saved course image: {image_filename} to {image_path}")
                else:
                    logger.info("No image file provided for new course.")

                course_data = {
                    'title': title,
                    'short_description': short_description,
                    'long_description': long_description,
                    'price': price,
                    'duration': duration,
                    'level': level,
                    'video_url': video_url,
                    'syllabus': syllabus,
                    'teacher_id': teacher_id, # Consider converting to ObjectId if teachers are in DB
                    'status': status,
                    'image_filename': image_filename
                }

                # Call the model function to create the course
                success, message = create_course(course_data)

                if success:
                    flash('Course added successfully!', 'success')
                    return redirect(url_for('admin_courses'))
                else:
                    flash(f'Error adding course: {message}', 'danger')
                    logger.error(f"Error creating course in DB: {message}")
                    # Re-render the form with existing data and error message
                    return render_template('admin/add_course.html', course=course_data)

            except Exception as e:
                logger.error(f"Exception occurred while adding course: {str(e)}")
                flash(f'An unexpected error occurred: {str(e)}', 'danger')
                return render_template('admin/add_course.html', course=request.form)

        return render_template('admin/add_course.html')

    @app.route('/admin/courses/edit/<course_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_course(course_id):
        try:
            # Use the model function to get the course
            course = get_course_by_id(course_id)
            
            if not course:
                flash('Course not found.', 'danger')
                return redirect(url_for('admin_courses'))
            
            if request.method == 'POST':
                # Extract form data and handle file uploads
                title = request.form.get('title')
                short_description = request.form.get('short_description')
                long_description = request.form.get('long_description')
                price = request.form.get('price')
                duration = request.form.get('duration')
                level = request.form.get('level')
                video_url = request.form.get('video_url')
                syllabus_text = request.form.get('syllabus')
                teacher_id = request.form.get('teacher_id')
                status = request.form.get('status')
                image_file = request.files.get('image')
                remove_image = request.form.get('remove_image') # Check if the remove image checkbox was checked

                # Process syllabus text into a list
                syllabus = [line.strip() for line in syllabus_text.split('\n') if line.strip()]

                image_filename = course.get('image_filename', '') # Start with existing filename

                # Handle image update or removal
                if remove_image == '1':
                    # Remove existing image file if it exists
                    if image_filename:
                        old_image_path = os.path.join(app.static_folder, 'uploads', 'courses', image_filename)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                            logger.info(f"Removed old course image: {image_filename}")
                    image_filename = '' # Clear filename in DB
                elif image_file and image_file.filename:
                    # New image uploaded, remove old one if exists
                    if image_filename:
                         old_image_path = os.path.join(app.static_folder, 'uploads', 'courses', image_filename)
                         if os.path.exists(old_image_path):
                             os.remove(old_image_path)
                             logger.info(f"Removed old course image before uploading new: {image_filename}")

                    # Sanitize new filename and save file
                    filename = secure_filename(image_file.filename)
                    image_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
                    image_path = os.path.join(app.static_folder, 'uploads', 'courses', image_filename)
                    image_file.save(image_path)
                    logger.info(f"Saved new course image: {image_filename} to {image_path}")
                # If no new image and not removing, image_filename remains the old one


                course_data = {
                    'title': title,
                    'short_description': short_description,
                    'long_description': long_description,
                    'price': price,
                    'duration': duration,
                    'level': level,
                    'video_url': video_url,
                    'syllabus': syllabus,
                    'teacher_id': teacher_id, # Consider converting to ObjectId
                    'status': status,
                    'image_filename': image_filename
                }

                # Call the model function to update the course
                success, message = update_course(course_id, course_data)

                if success:
                    flash('Course updated successfully!', 'success')
                    return redirect(url_for('admin_courses'))
                else:
                    flash(f'Error updating course: {message}', 'danger')
                    logger.error(f"Error updating course in DB {course_id}: {message}")
                    # Re-render the form with existing data and error message
                    # Fetch the course again to get the latest data if update failed
                    updated_course = get_course_by_id(course_id)
                    return render_template('admin/edit_course.html', course=updated_course if updated_course else course)

            # If it's a GET request, render the edit form with existing data
            return render_template('admin/edit_course.html', course=course)

        except Exception as e:
            logger.error(f"Exception occurred while editing course {course_id}: {str(e)}")
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            return redirect(url_for('admin_courses'))

    @app.route('/admin/courses/delete/<course_id>', methods=['POST'])
    @login_required
    def admin_delete_course(course_id):
        try:
            # Call the model function to delete the course
            success, message = delete_course(course_id)

            if success:
                flash('Course deleted successfully!', 'success')
            else:
                flash(f'Error deleting course: {message}', 'danger')
                logger.error(f"Error deleting course from DB {course_id}: {message}")

        except Exception as e:
            logger.error(f"Exception occurred while deleting course {course_id}: {str(e)}")
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

        return redirect(url_for('admin_courses'))

    @app.route('/admin/enrollments')
    @login_required
    def admin_enrollments():
        try:
            enrollments = list(mongo.db.enrollments.find().sort('enrollment_date', -1))
            return render_template('admin/enrollments.html', enrollments=enrollments)
        except Exception as e:
            logger.error(f"Error loading enrollments: {str(e)}")
            flash('Error loading enrollments.', 'danger')
            return render_template('admin/enrollments.html', enrollments=[], error=str(e))

    @app.route('/admin/contacts')
    @login_required
    def admin_contacts():
        try:
            contacts = list(mongo.db.contacts.find().sort('name', 1))
            return render_template('admin/contacts.html', contacts=contacts)
        except Exception as e:
            logger.error(f"Error loading contacts: {str(e)}")
            flash('Error loading contacts.', 'danger')
            return render_template('admin/contacts.html', contacts=[], error=str(e))

    # Admin Content Management Routes
    @app.route('/admin/content')
    @login_required
    def admin_content():
        try:
            # Get all content items using the model function
            content_items = get_all_content_items()
            return render_template('admin/content.html', content_items=content_items)
        except Exception as e:
            logger.error(f"Error loading content items: {str(e)}")
            flash('Error loading content items.', 'danger')
            return render_template('admin/content.html', content_items=[], error=str(e))

    @app.route('/admin/content/add', methods=['GET', 'POST'])
    @login_required
    def admin_add_content():
        if request.method == 'POST':
            try:
                # Extract form data
                title = request.form.get('title')
                item_type = request.form.get('type')
                data = request.form.get('data') # This will depend on the type (text, URL, etc.)
                caption = request.form.get('caption')
                course_id = request.form.get('course_id') # Can be None or a Course ID
                order = request.form.get('order', 0)

                # Handle file uploads if type is 'file' or 'image'
                if item_type in ['file', 'image']:
                    uploaded_file = request.files.get('data_file') # Assuming input name is 'data_file'
                    if uploaded_file and uploaded_file.filename:
                        filename = secure_filename(uploaded_file.filename)
                        # Store file in appropriate upload directory (e.g., content/)
                        file_path = os.path.join(app.static_folder, 'uploads', 'content', filename)
                        uploaded_file.save(file_path)
                        data = f'uploads/content/{filename}' # Store relative path in DB
                        logger.info(f"Saved content file: {filename} to {file_path}")
                    else:
                         flash(f'Error adding content: File upload missing.', 'danger')
                         return render_template('admin/add_content.html', item=request.form)

                # Convert course_id to ObjectId if provided
                if course_id:
                    try:
                        course_id = ObjectId(course_id)
                    except Exception:
                         flash(f'Error adding content: Invalid Course ID format.', 'danger')
                         return render_template('admin/add_content.html', item=request.form)
                else:
                    course_id = None # Assign to no course if not provided

                content_data = {
                    'title': title,
                    'type': item_type,
                    'data': data,
                    'caption': caption,
                    'course_id': course_id,
                    'order': order
                }

                # Call the model function to create the content item
                success, message = create_content_item(content_data)

                if success:
                    flash('Content item added successfully!', 'success')
                    return redirect(url_for('admin_content'))
                else:
                    flash(f'Error adding content item: {message}', 'danger')
                    logger.error(f"Error creating content item in DB: {message}")
                    return render_template('admin/add_content.html', item=content_data)

            except Exception as e:
                logger.error(f"Exception occurred while adding content item: {str(e)}")
                flash(f'An unexpected error occurred: {str(e)}', 'danger')
                return render_template('admin/add_content.html', item=request.form)

        # For GET request, render the add form
        return render_template('admin/add_content.html')

    @app.route('/admin/content/edit/<item_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_content(item_id):
        try:
            # Use the model function to get the content item
            content_item = get_content_item_by_id(item_id)

            if not content_item:
                flash('Content item not found.', 'danger')
                return redirect(url_for('admin_content'))

            if request.method == 'POST':
                # Extract form data
                title = request.form.get('title')
                item_type = request.form.get('type')
                data = request.form.get('data') # This will depend on the type
                caption = request.form.get('caption')
                course_id = request.form.get('course_id')
                order = request.form.get('order', 0)
                remove_file = request.form.get('remove_file') # Check if remove file checkbox was checked
                uploaded_file = request.files.get('data_file') # Assuming input name is 'data_file'

                # Handle file updates or removal if type is 'file' or 'image'
                current_data = content_item.get('data') # Existing data value

                if remove_file == '1' and item_type in ['file', 'image']:
                     # Remove existing file if it exists and is in uploads/content
                    if current_data and current_data.startswith('uploads/content/'):
                        old_file_path = os.path.join(app.static_folder, current_data.replace('uploads/', ''))
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                            logger.info(f"Removed old content file: {current_data}")
                    data = '' # Clear data in DB
                elif uploaded_file and uploaded_file.filename and item_type in ['file', 'image']:
                    # New file uploaded, remove old one if exists and is in uploads/content
                    if current_data and current_data.startswith('uploads/content/'):
                        old_file_path = os.path.join(app.static_folder, current_data.replace('uploads/', ''))
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                            logger.info(f"Removed old content file before uploading new: {current_data}")

                    # Sanitize new filename and save file
                    filename = secure_filename(uploaded_file.filename)
                    file_path = os.path.join(app.static_folder, 'uploads', 'content', filename)
                    uploaded_file.save(file_path)
                    data = f'uploads/content/{filename}' # Store relative path in DB
                    logger.info(f"Saved new content file: {filename} to {file_path}")
                # If no new file and not removing, data remains the old value

                # Convert course_id to ObjectId if provided
                if course_id:
                    try:
                        course_id = ObjectId(course_id)
                    except Exception:
                         flash(f'Error updating content: Invalid Course ID format.', 'danger')
                         # Re-render the form with existing data
                         return render_template('admin/edit_content.html', item=content_item)
                else:
                    course_id = None # Assign to no course if not provided

                content_data = {
                    'title': title,
                    'type': item_type,
                    'data': data,
                    'caption': caption,
                    'course_id': course_id,
                    'order': order
                }

                # Call the model function to update the content item
                success, message = update_content_item(item_id, content_data)

                if success:
                    flash('Content item updated successfully!', 'success')
                    return redirect(url_for('admin_content'))
                else:
                    flash(f'Error updating content item: {message}', 'danger')
                    logger.error(f"Error updating content item in DB {item_id}: {message}")
                    # Re-render the form with existing data and error message
                    # Fetch the item again to get the latest data if update failed
                    updated_item = get_content_item_by_id(item_id)
                    return render_template('admin/edit_content.html', item=updated_item if updated_item else content_item)

            # For GET request, render the edit form with existing data
            return render_template('admin/edit_content.html', item=content_item)

        except Exception as e:
            logger.error(f"Exception occurred while editing content item {item_id}: {str(e)}")
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            return redirect(url_for('admin_content'))

    @app.route('/admin/content/delete/<item_id>', methods=['POST'])
    @login_required
    def admin_delete_content(item_id):
        try:
            # Get the content item before deleting to check for associated files
            content_item = get_content_item_by_id(item_id)

            if not content_item:
                flash('Content item not found.', 'danger')
                return redirect(url_for('admin_content'))

            # Call the model function to delete the content item from DB
            success, message = delete_content_item(item_id)

            if success:
                # If deletion from DB is successful, attempt to delete associated file
                current_data = content_item.get('data')
                if content_item.get('type') in ['file', 'image'] and current_data and current_data.startswith('uploads/content/'):
                    file_path = os.path.join(app.static_folder, current_data.replace('uploads/', ''))
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"Removed associated content file: {current_data}")
                        except Exception as file_e:
                            logger.error(f"Error removing associated content file {file_path}: {str(file_e)}")
                            flash(f'Content item deleted, but failed to remove associated file: {str(file_e)}', 'warning')

                flash('Content item deleted successfully!', 'success')
            else:
                flash(f'Error deleting content item: {message}', 'danger')
                logger.error(f"Error deleting content item from DB {item_id}: {message}")

        except Exception as e:
            logger.error(f"Exception occurred while deleting content item {item_id}: {str(e)}")
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

        return redirect(url_for('admin_content'))

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 