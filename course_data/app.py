from flask import Flask, render_template, url_for, request, jsonify, flash, redirect, session
from flask_pymongo import PyMongo
from flask_wtf import CSRFProtect
from datetime import datetime
import os
from config import config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from functools import wraps
from bson import ObjectId
from models import (
    validate_enrollment, create_enrollment, get_enrollment, get_all_enrollments,
    update_enrollment_status, create_admin, verify_admin, create_course, update_course,
    delete_course, add_gallery_item, delete_gallery_item, create_content,
    update_content, delete_content
)
import requests
import json

# Initialize Flask extensions
mongo = PyMongo()
csrf = CSRFProtect()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Auto-login with Proloy's credentials
        session['admin_id'] = 'proloy_admin'
        session['admin_username'] = 'Proloy'
        session['admin_role'] = 'super_admin'
        return f(*args, **kwargs)
    return decorated_function

def create_app(config_name='default'):
    app = Flask(__name__,
                template_folder='../frontend/templates',
                static_folder='../frontend/static')

    # Load configuration
    if config_name == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.Config')

    # Initialize MongoDB with error handling
    try:
        mongo.init_app(app)
        # Test the connection
        with app.app_context():
            mongo.db.command('ping')
            app.logger.info("Successfully connected to MongoDB")
    except Exception as e:
        app.logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise RuntimeError("Database connection failed. Please check your MongoDB configuration.")

    # Initialize other extensions
    csrf.init_app(app)
    
    # Create upload folders if they don't exist
    upload_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static', 'uploads')
    os.makedirs(upload_base, exist_ok=True)
    os.makedirs(os.path.join(upload_base, 'courses'), exist_ok=True)
    os.makedirs(os.path.join(upload_base, 'gallery'), exist_ok=True)
    os.makedirs(os.path.join(upload_base, 'content'), exist_ok=True)
    
    # Admin routes - all routes auto-login
    @app.route('/admin')
    @app.route('/admin/login')
    def admin_login():
        # Auto-login and redirect to dashboard
        session['admin_id'] = 'proloy_admin'
        session['admin_username'] = 'Proloy'
        session['admin_role'] = 'super_admin'
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/logout')
    def admin_logout():
        # Auto-login again after logout
        session.clear()
        session['admin_id'] = 'proloy_admin'
        session['admin_username'] = 'Proloy'
        session['admin_role'] = 'super_admin'
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        # Get counts for dashboard
        enrollments_count = mongo.db.enrollments.count_documents({})
        courses_count = mongo.db.courses.count_documents({})
        gallery_count = mongo.db.gallery.count_documents({})
        content_count = mongo.db.content.count_documents({})
        
        return render_template('admin/dashboard.html',
                             enrollments_count=enrollments_count,
                             courses_count=courses_count,
                             gallery_count=gallery_count,
                             content_count=content_count)
    
    # Course management routes
    @app.route('/admin/courses')
    @admin_required
    def admin_courses():
        courses = list(mongo.db.courses.find())
        return render_template('admin/courses.html', courses=courses)
    
    @app.route('/admin/courses/create', methods=['GET', 'POST'])
    @admin_required
    def admin_create_course():
        if request.method == 'POST':
            data = {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'duration': request.form.get('duration'),
                'price': request.form.get('price'),
                'syllabus': request.form.getlist('syllabus[]')
            }
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join('courses', filename)
                    file.save(os.path.join(upload_base, file_path))
                    data['image_url'] = file_path
            
            success, message = create_course(data)
            if success:
                flash('Course created successfully!', 'success')
                return redirect(url_for('admin_courses'))
            else:
                flash(f'Error: {message}', 'danger')
        
        return render_template('admin/course_form.html')
    
    @app.route('/admin/courses/<course_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_course(course_id):
        course = mongo.db.courses.find_one({'_id': ObjectId(course_id)})
        if not course:
            flash('Course not found.', 'danger')
            return redirect(url_for('admin_courses'))
        
        if request.method == 'POST':
            data = {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'duration': request.form.get('duration'),
                'price': request.form.get('price'),
                'syllabus': request.form.getlist('syllabus[]')
            }
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join('courses', filename)
                    file.save(os.path.join(upload_base, file_path))
                    data['image_url'] = file_path
            
            success, message = update_course(course_id, data)
            if success:
                flash('Course updated successfully!', 'success')
                return redirect(url_for('admin_courses'))
            else:
                flash(f'Error: {message}', 'danger')
        
        return render_template('admin/course_form.html', course=course)
    
    @app.route('/admin/courses/<course_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_course(course_id):
        success, message = delete_course(course_id)
        if success:
            flash('Course deleted successfully!', 'success')
        else:
            flash(f'Error: {message}', 'danger')
        return redirect(url_for('admin_courses'))
    
    # Gallery management routes
    @app.route('/admin/gallery')
    @admin_required
    def admin_gallery():
        gallery_items = list(mongo.db.gallery.find())
        return render_template('admin/gallery.html', gallery_items=gallery_items)
    
    @app.route('/admin/gallery/create', methods=['GET', 'POST'])
    @admin_required
    def admin_create_gallery_item():
        if request.method == 'POST':
            if 'image' not in request.files:
                flash('No image file uploaded.', 'danger')
                return redirect(request.url)
            
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join('gallery', filename)
                file.save(os.path.join(upload_base, file_path))
                
                data = {
                    'title': request.form.get('title'),
                    'description': request.form.get('description'),
                    'image_url': file_path,
                    'category': request.form.get('category', 'general')
                }
                
                success, message = add_gallery_item(data)
                if success:
                    flash('Gallery item added successfully!', 'success')
                    return redirect(url_for('admin_gallery'))
                else:
                    flash(f'Error: {message}', 'danger')
            else:
                flash('Invalid file.', 'danger')
        
        return render_template('admin/gallery_form.html')
    
    @app.route('/admin/gallery/<item_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_gallery_item(item_id):
        success, message = delete_gallery_item(item_id)
        if success:
            flash('Gallery item deleted successfully!', 'success')
        else:
            flash(f'Error: {message}', 'danger')
        return redirect(url_for('admin_gallery'))
    
    # Content management routes
    @app.route('/admin/content')
    @admin_required
    def admin_content():
        content_items = list(mongo.db.content.find())
        return render_template('admin/content.html', content_items=content_items)
    
    @app.route('/admin/content/create', methods=['GET', 'POST'])
    @admin_required
    def admin_create_content():
        if request.method == 'POST':
            data = {
                'title': request.form.get('title'),
                'content': request.form.get('content'),
                'type': request.form.get('type'),
                'author': session.get('admin_username')
            }
            
            success, message = create_content(data)
            if success:
                flash('Content created successfully!', 'success')
                return redirect(url_for('admin_content'))
            else:
                flash(f'Error: {message}', 'danger')
        
        return render_template('admin/content_form.html')
    
    @app.route('/admin/content/<content_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_content(content_id):
        content_item = mongo.db.content.find_one({'_id': ObjectId(content_id)})
        if not content_item:
            flash('Content not found.', 'danger')
            return redirect(url_for('admin_content'))
        
        if request.method == 'POST':
            data = {
                'title': request.form.get('title'),
                'content': request.form.get('content'),
                'type': request.form.get('type'),
                'status': request.form.get('status', 'published')
            }
            
            success, message = update_content(content_id, data)
            if success:
                flash('Content updated successfully!', 'success')
                return redirect(url_for('admin_content'))
            else:
                flash(f'Error: {message}', 'danger')
        
        return render_template('admin/content_form.html', content=content_item)
    
    @app.route('/admin/content/<content_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_content(content_id):
        success, message = delete_content(content_id)
        if success:
            flash('Content deleted successfully!', 'success')
        else:
            flash(f'Error: {message}', 'danger')
        return redirect(url_for('admin_content'))
    
    # Enrollment management routes
    @app.route('/admin/enrollments')
    @admin_required
    def admin_enrollments():
        enrollments = list(mongo.db.enrollments.find().sort('enrollment_date', -1))
        return render_template('admin/enrollments.html', enrollments=enrollments)
    
    @app.route('/admin/enrollments/<enrollment_id>/update-status', methods=['POST'])
    @admin_required
    def admin_update_enrollment_status(enrollment_id):
        new_status = request.form.get('status')
        if new_status in ['pending', 'approved', 'rejected']:
            success, message = update_enrollment_status(enrollment_id, new_status)
            if success:
                flash('Enrollment status updated successfully!', 'success')
            else:
                flash(f'Error: {message}', 'danger')
        else:
            flash('Invalid status.', 'danger')
        return redirect(url_for('admin_enrollments'))
    
    @app.route('/admin/enrollments/<enrollment_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_enrollment(enrollment_id):
        try:
            mongo.db.enrollments.delete_one({'_id': ObjectId(enrollment_id)})
            flash('Enrollment deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting enrollment: {str(e)}', 'danger')
        return redirect(url_for('admin_enrollments'))
    
    @app.route('/')
    def home():
        # Get all courses from database
        courses = list(mongo.db.courses.find())
        return render_template('index.html', courses=courses)
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/courses')
    def courses():
        # Get all courses from database
        courses = list(mongo.db.courses.find())
        return render_template('courses.html', courses=courses)
    
    @app.route('/courses/<course_id>')
    def course_detail(course_id):
        course = mongo.db.courses.find_one({'_id': ObjectId(course_id)})
        if not course:
            flash('Course not found.', 'danger')
            return redirect(url_for('courses'))
        return render_template('course_detail.html', course=course)
    
    def send_to_google_sheets(data):
        """Send enrollment data to Google Sheets via Apps Script"""
        try:
            # Get the Google Apps Script Web App URL from configuration
            script_url = app.config['GOOGLE_SCRIPT_URL']
            if not script_url:
                app.logger.error("Google Script URL not configured")
                return False, "Google Sheets integration not configured"

            # Prepare the data for Google Sheets
            sheet_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'student_name': data.get('student_name', ''),
                'student_email': data.get('student_email', ''),
                'date_of_birth': data.get('date_of_birth', ''),
                'education_level': data.get('education_level', ''),
                'class_grade': data.get('class_grade', ''),
                'school_name': data.get('school_name', ''),
                'student_phone': data.get('student_phone', ''),
                'hobby': data.get('hobby', ''),
                'father_name': data.get('father_name', ''),
                'mother_name': data.get('mother_name', ''),
                'parent_phone': data.get('parent_phone', ''),
                'parent_email': data.get('parent_email', ''),
                'courses': ', '.join(data.get('courses', [])),
                'additional_info': data.get('additional_info', '')
            }

            # Log the data being sent
            app.logger.info(f"Sending data to Google Sheets: {json.dumps(sheet_data)}")

            # Send data to Google Apps Script with proper headers
            response = requests.post(
                script_url,
                data=json.dumps(sheet_data),  # Send as JSON string
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=10  # Add timeout
            )

            # Log the response
            app.logger.info(f"Google Sheets response status: {response.status_code}")
            app.logger.info(f"Google Sheets response content: {response.text}")

            try:
                response_data = response.json()
                if response.status_code == 200 and response_data.get('success'):
                    app.logger.info("Data sent to Google Sheets successfully")
                    return True, "Data sent to Google Sheets successfully"
                else:
                    error_msg = response_data.get('message', 'Unknown error from Google Sheets')
                    app.logger.error(f"Google Sheets API error: {error_msg}")
                    return False, f"Failed to send data to Google Sheets: {error_msg}"
            except ValueError:
                app.logger.error(f"Invalid JSON response from Google Sheets: {response.text}")
                return False, "Invalid response from Google Sheets"

        except requests.exceptions.Timeout:
            app.logger.error("Timeout while sending data to Google Sheets")
            return False, "Request timed out while sending data to Google Sheets"
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Request error while sending data to Google Sheets: {str(e)}")
            return False, f"Network error while sending data to Google Sheets: {str(e)}"
        except Exception as e:
            app.logger.error(f"Error sending data to Google Sheets: {str(e)}")
            return False, str(e)

    @app.route('/enroll', methods=['GET', 'POST'])
    def enroll():
        if request.method == 'POST':
            try:
                # Log the raw form data for debugging
                app.logger.info("Raw form data received:")
                for key, value in request.form.items():
                    app.logger.info(f"{key}: {value}")
                
                # Get form data
                data = {
                    'student_name': request.form.get('student_name'),
                    'student_email': request.form.get('student_email'),
                    'date_of_birth': request.form.get('date_of_birth'),
                    'education_level': request.form.get('education_level'),
                    'class_grade': request.form.get('class_grade'),
                    'school_name': request.form.get('school_name'),
                    'student_phone': request.form.get('student_phone'),
                    'hobby': request.form.get('hobby'),
                    'father_name': request.form.get('father_name'),
                    'mother_name': request.form.get('mother_name'),
                    'parent_phone': request.form.get('parent_phone'),
                    'parent_email': request.form.get('parent_email'),
                    'additional_info': request.form.get('additional_info'),
                    'courses': request.form.getlist('courses'),
                    'enrollment_date': datetime.now()
                }
                
                # Validate required fields
                required_fields = ['student_name', 'student_email', 'date_of_birth', 'education_level', 
                                 'class_grade', 'school_name', 'student_phone', 'father_name', 
                                 'mother_name', 'parent_phone', 'parent_email', 'courses']
                
                missing_fields = [field for field in required_fields if not data.get(field)]
                if missing_fields:
                    error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                    app.logger.error(error_msg)
                    return jsonify({'success': False, 'message': error_msg})

                # Validate email formats
                if '@' not in data['student_email'] or '.' not in data['student_email']:
                    return jsonify({'success': False, 'message': 'Please enter a valid student email address.'})
                
                if '@' not in data['parent_email'] or '.' not in data['parent_email']:
                    return jsonify({'success': False, 'message': 'Please enter a valid parent email address.'})
                
                # Validate phone numbers
                for phone_field in ['student_phone', 'parent_phone']:
                    phone = data[phone_field].replace('-', '').replace(' ', '')
                    if not phone.isdigit() or len(phone) < 10:
                        return jsonify({'success': False, 'message': f'Please enter a valid {phone_field.replace("_", " ")} (at least 10 digits).'})

                # Send to Google Sheets first
                sheets_success, sheets_message = send_to_google_sheets(data)
                if not sheets_success:
                    app.logger.error(f"Google Sheets error: {sheets_message}")
                    # Continue with MongoDB save even if Google Sheets fails
                    app.logger.info("Continuing with MongoDB save despite Google Sheets error")

                # Save to MongoDB as backup
                try:
                    mongo.db.enrollments.insert_one(data)
                    app.logger.info("Enrollment saved to MongoDB successfully")
                except Exception as db_error:
                    app.logger.error(f"MongoDB backup error: {str(db_error)}")
                    if not sheets_success:
                        # If both Google Sheets and MongoDB failed, return error
                        return jsonify({
                            'success': False,
                            'message': 'Failed to save enrollment data. Please try again.'
                        })

                # Return success even if Google Sheets failed but MongoDB succeeded
                return jsonify({
                    'success': True,
                    'message': 'Enrollment submitted successfully! We will contact you soon.'
                })

            except Exception as e:
                app.logger.error(f"Enrollment error: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'message': 'An unexpected error occurred. Please try again later.'
                })

        # For GET request, render the enrollment form
        selected_course = request.args.get('course')
        return render_template('enroll.html', selected_course=selected_course)
    
    @app.route('/book-demo', methods=['POST'])
    def book_demo():
        try:
            # Get form data
            demo_data = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'preferred_date': request.form.get('preferred_date'),
                'additional_info': request.form.get('additional_info'),
                'created_at': datetime.now(),
                'status': 'Pending'
            }

            # Validate required fields
            required_fields = ['name', 'email', 'phone', 'preferred_date']
            for field in required_fields:
                if not demo_data[field]:
                    flash(f'Please fill in all required fields for demo class booking.', 'danger')
                    return redirect(url_for('enroll'))

            # Validate email format
            if '@' not in demo_data['email'] or '.' not in demo_data['email']:
                flash('Please enter a valid email address for demo booking.', 'danger')
                return redirect(url_for('enroll'))

            # Validate phone number
            phone = demo_data['phone'].replace('-', '').replace(' ', '')
            if not phone.isdigit() or len(phone) < 10:
                flash('Please enter a valid phone number (at least 10 digits) for demo booking.', 'danger')
                return redirect(url_for('enroll'))

            # Validate date (should be in the future)
            try:
                preferred_date = datetime.strptime(demo_data['preferred_date'], '%Y-%m-%d')
                if preferred_date.date() <= datetime.now().date():
                    flash('Please select a future date for the demo class.', 'danger')
                    return redirect(url_for('enroll'))
            except ValueError:
                flash('Please enter a valid date for the demo class.', 'danger')
                return redirect(url_for('enroll'))

            # Save demo booking
            result = mongo.db.demo_bookings.insert_one(demo_data)
            app.logger.info(f"Demo booking created with ID: {result.inserted_id}")

            # Create detailed success message
            success_message = f"""
            🎉 Demo Class Booked Successfully!

            📋 Booking Details:
            • Name: {demo_data['name']}
            • Email: {demo_data['email']}
            • Phone: {demo_data['phone']}
            • Preferred Date: {demo_data['preferred_date']}
            • Booking ID: {str(result.inserted_id)[:8]}...

            ✅ What's Next:
            • We will contact you within 24 hours to confirm the schedule
            • You will receive an email confirmation shortly
            • Please check your email and phone for updates

            Thank you for choosing DotPy Academy! 🎓
            """

            flash(success_message, 'success')
            return redirect(url_for('enroll') + '?demo_success=1')

        except Exception as e:
            app.logger.error(f"Demo booking error: {str(e)}")
            flash('An error occurred while booking the demo class. Please try again.', 'danger')
            return redirect(url_for('enroll'))
    
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        if request.method == 'POST':
            try:
                # Get form data
                name = request.form.get('name')
                email = request.form.get('email')
                phone = request.form.get('phone')
                subject = request.form.get('subject')
                message = request.form.get('message')

                # Create email message
                msg = MIMEMultipart()
                msg['From'] = os.getenv('EMAIL_USER', 'dotpyacademy1@gmail.com')
                msg['To'] = 'dotpyacademy1@gmail.com'
                msg['Subject'] = f'New Contact Form Submission: {subject}'

                # Create email body
                body = f"""
                New contact form submission from the website:

                Name: {name}
                Email: {email}
                Phone: {phone}
                Subject: {subject}

                Message:
                {message}
                """

                msg.attach(MIMEText(body, 'plain'))

                # Send email
                try:
                    # Configure your email settings here
                    # For now, we'll just print the message
                    print(f"Email would be sent with the following content:\n{body}")
                    
                    # Uncomment and configure these lines when you have email credentials
                    # server = smtplib.SMTP('smtp.gmail.com', 587)
                    # server.starttls()
                    # server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
                    # server.send_message(msg)
                    # server.quit()

                    flash('Thank you for your message! We will get back to you soon.', 'success')
                except Exception as e:
                    print(f"Error sending email: {str(e)}")
                    flash('There was an error sending your message. Please try again later.', 'error')

                return redirect(url_for('contact'))

            except Exception as e:
                print(f"Error processing form: {str(e)}")
                flash('There was an error processing your request. Please try again later.', 'error')
                return redirect(url_for('contact'))

        return render_template('contact.html')
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        mongo.db.errors.insert_one({
            'error': str(error),
            'timestamp': datetime.utcnow()
        })
        return render_template('errors/500.html'), 500
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 