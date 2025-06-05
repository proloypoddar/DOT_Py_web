"""
DotPy Academy Database Management System
This module handles all database operations including:
- Contact form submissions
- Course enrollments
- Email notifications
- Database connection management
"""

from pymongo import MongoClient, MongoClient
from datetime import datetime
from pprint import pprint
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Dict, Any, Tuple, Optional, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database Configuration
class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        self.MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://dotpyacademy1:m57HHUwKiNwggGB0@dotpy.bpeap9q.mongodb.net/dotpy_academy?retryWrites=true&w=majority&appName=dotpy')
        self.DB_NAME = 'dotpy_academy'
        self.client = None
        self.db = None

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.client = MongoClient(self.MONGODB_URI)
            self.db = self.client[self.DB_NAME]
            # Test connection
            self.db.command('ping')
            logger.info("✅ Successfully connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection error: {str(e)}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

# Email Configuration
class EmailConfig:
    """Email notification configuration and management"""
    
    def __init__(self):
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'dotpyacademy1@gmail.com')
        self.SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
        self.ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'dotpyacademy1@gmail.com')

    def send_email(self, recipient_email: str, subject: str, message: str) -> bool:
        """Send HTML email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.SENDER_EMAIL
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'html'))

            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.starttls()
                server.login(self.SENDER_EMAIL, self.SENDER_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Email sending error: {str(e)}")
            return False

# Database Operations
class DatabaseOperations:
    """Core database operations for the application"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.email_config = EmailConfig()
        self.connect()

    def connect(self) -> bool:
        """Initialize database connection"""
        return self.db_config.connect()

    def disconnect(self):
        """Close database connection"""
        self.db_config.disconnect()

    def store_form_submission(self, form_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Store contact form submission and send notifications"""
        try:
            if not self.db_config.db:
                raise Exception("Database not connected")

            # Add metadata
            form_data['submitted_at'] = datetime.utcnow()
            form_data['status'] = 'new'

            # Store in database
            result = self.db_config.db.form_submissions.insert_one(form_data)
            
            # Send notifications
            self._send_form_notifications(form_data)
            
            logger.info(f"✅ Form submission stored with ID: {result.inserted_id}")
            return True, str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Form submission error: {str(e)}")
            return False, None

    def store_enrollment(self, enrollment_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Store course enrollment and send notifications"""
        try:
            if not self.db_config.db:
                raise Exception("Database not connected")

            # Add metadata
            enrollment_data['enrolled_at'] = datetime.utcnow()
            enrollment_data['status'] = 'pending'
            enrollment_data['updated_at'] = datetime.utcnow()

            # Store in database
            result = self.db_config.db.enrollments.insert_one(enrollment_data)
            
            # Send notifications
            self._send_enrollment_notifications(enrollment_data)
            
            logger.info(f"✅ Enrollment stored with ID: {result.inserted_id}")
            return True, str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Enrollment error: {str(e)}")
            return False, None

    def update_enrollment_status(self, enrollment_id: str, new_status: str) -> bool:
        """Update enrollment status and send notification"""
        try:
            if not self.db_config.db:
                raise Exception("Database not connected")

            # Update status
            result = self.db_config.db.enrollments.update_one(
                {'_id': enrollment_id},
                {
                    '$set': {
                        'status': new_status,
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            if result.modified_count > 0:
                # Get updated enrollment
                enrollment = self.db_config.db.enrollments.find_one({'_id': enrollment_id})
                if enrollment:
                    self._send_status_update_notification(enrollment, new_status)
                logger.info(f"✅ Enrollment status updated to {new_status}")
                return True
            else:
                logger.warning("No enrollment found with the given ID")
                return False
        except Exception as e:
            logger.error(f"❌ Status update error: {str(e)}")
            return False

    def get_enrollments(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve enrollments with optional filters"""
        try:
            if not self.db_config.db:
                raise Exception("Database not connected")

            query = filters or {}
            enrollments = list(self.db_config.db.enrollments.find(query))
            logger.info(f"Retrieved {len(enrollments)} enrollments")
            return enrollments
        except Exception as e:
            logger.error(f"❌ Error retrieving enrollments: {str(e)}")
            return []

    def get_form_submissions(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve form submissions with optional filters"""
        try:
            if not self.db_config.db:
                raise Exception("Database not connected")

            query = filters or {}
            submissions = list(self.db_config.db.form_submissions.find(query))
            logger.info(f"Retrieved {len(submissions)} form submissions")
            return submissions
        except Exception as e:
            logger.error(f"❌ Error retrieving form submissions: {str(e)}")
            return []

    # Private notification methods
    def _send_form_notifications(self, form_data: Dict[str, Any]):
        """Send notifications for form submission"""
        # User notification
        user_message = f"""
        <html>
            <body>
                <h2>Thank you for contacting DotPy Academy!</h2>
                <p>Dear {form_data['name']},</p>
                <p>We have received your message and will get back to you soon.</p>
                <p>Your message details:</p>
                <ul>
                    <li>Course Interest: {form_data.get('course_interest', 'Not specified')}</li>
                    <li>Message: {form_data['message']}</li>
                </ul>
                <p>Best regards,<br>DotPy Academy Team</p>
            </body>
        </html>
        """
        self.email_config.send_email(
            form_data['email'],
            "Thank you for contacting DotPy Academy",
            user_message
        )

        # Admin notification
        admin_message = f"""
        <html>
            <body>
                <h2>New Contact Form Submission</h2>
                <p>A new message has been received:</p>
                <ul>
                    <li>Name: {form_data['name']}</li>
                    <li>Email: {form_data['email']}</li>
                    <li>Phone: {form_data.get('phone', 'Not provided')}</li>
                    <li>Course Interest: {form_data.get('course_interest', 'Not specified')}</li>
                    <li>Message: {form_data['message']}</li>
                </ul>
            </body>
        </html>
        """
        self.email_config.send_email(
            self.email_config.ADMIN_EMAIL,
            "New Contact Form Submission - DotPy Academy",
            admin_message
        )

    def _send_enrollment_notifications(self, enrollment_data: Dict[str, Any]):
        """Send notifications for new enrollment"""
        # Student notification
        student_message = f"""
        <html>
            <body>
                <h2>Welcome to DotPy Academy!</h2>
                <p>Dear {enrollment_data['student_name']},</p>
                <p>Thank you for enrolling in {enrollment_data['course_name']}.</p>
                <p>Your enrollment details:</p>
                <ul>
                    <li>Course: {enrollment_data['course_name']}</li>
                    <li>Start Date: {enrollment_data['start_date'].strftime('%B %d, %Y')}</li>
                    <li>Status: {enrollment_data['status'].title()}</li>
                    <li>Payment Status: {enrollment_data['payment_status'].title()}</li>
                </ul>
                <p>We will contact you shortly with further instructions.</p>
                <p>Best regards,<br>DotPy Academy Team</p>
            </body>
        </html>
        """
        self.email_config.send_email(
            enrollment_data['email'],
            f"Enrollment Confirmation - {enrollment_data['course_name']}",
            student_message
        )

        # Admin notification
        admin_message = f"""
        <html>
            <body>
                <h2>New Course Enrollment</h2>
                <p>A new student has enrolled:</p>
                <ul>
                    <li>Student: {enrollment_data['student_name']}</li>
                    <li>Email: {enrollment_data['email']}</li>
                    <li>Phone: {enrollment_data['phone']}</li>
                    <li>Course: {enrollment_data['course_name']}</li>
                    <li>Start Date: {enrollment_data['start_date'].strftime('%B %d, %Y')}</li>
                    <li>Payment Status: {enrollment_data['payment_status'].title()}</li>
                    <li>Additional Notes: {enrollment_data.get('additional_notes', 'None')}</li>
                </ul>
            </body>
        </html>
        """
        self.email_config.send_email(
            self.email_config.ADMIN_EMAIL,
            f"New Enrollment - {enrollment_data['course_name']}",
            admin_message
        )

    def _send_status_update_notification(self, enrollment: Dict[str, Any], new_status: str):
        """Send notification for enrollment status update"""
        message = f"""
        <html>
            <body>
                <h2>Enrollment Status Update</h2>
                <p>Dear {enrollment['student_name']},</p>
                <p>Your enrollment status for {enrollment['course_name']} has been updated to: <strong>{new_status.title()}</strong></p>
                <p>Current enrollment details:</p>
                <ul>
                    <li>Course: {enrollment['course_name']}</li>
                    <li>Status: {new_status.title()}</li>
                    <li>Payment Status: {enrollment['payment_status'].title()}</li>
                    <li>Start Date: {enrollment['start_date'].strftime('%B %d, %Y')}</li>
                </ul>
                <p>Best regards,<br>DotPy Academy Team</p>
            </body>
        </html>
        """
        self.email_config.send_email(
            enrollment['email'],
            f"Enrollment Status Update - {enrollment['course_name']}",
            message
        )

# Test the system
if __name__ == "__main__":
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    try:
        # Test form submission
        test_form = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'course_interest': 'Python Level 1',
            'message': 'I would like to learn more about the course'
        }
        print("\nTesting form submission...")
        success, form_id = db_ops.store_form_submission(test_form)
        
        # Test enrollment
        test_enrollment = {
            'student_name': 'John Smith',
            'email': 'john.smith@example.com',
            'phone': '+1234567890',
            'course_name': 'Python Level 1',
            'payment_status': 'pending',
            'start_date': datetime(2025, 6, 15),
            'additional_notes': 'Interested in morning batch'
        }
        print("\nTesting enrollment...")
        success, enrollment_id = db_ops.store_enrollment(test_enrollment)
        
        if success and enrollment_id:
            # Test status update
            print("\nTesting status update...")
            db_ops.update_enrollment_status(enrollment_id, 'confirmed')
            
            # Test retrieval
            print("\nTesting data retrieval...")
            enrollments = db_ops.get_enrollments()
            print(f"Found {len(enrollments)} enrollments")
            
            submissions = db_ops.get_form_submissions()
            print(f"Found {len(submissions)} form submissions")
    
    finally:
        # Always disconnect from database
        db_ops.disconnect() 