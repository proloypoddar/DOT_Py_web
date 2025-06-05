from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from config import Config
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_admin_password(email, new_password):
    try:
        # Connect to MongoDB
        client = MongoClient(Config.MONGO_URI)
        db = client.myDatabase
        
        # Find the admin user by email
        admin = db.admins.find_one({'email': email})
        
        if not admin:
            logger.warning(f"Admin user with email {email} not found.")
            return False
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        
        # Update the password in the database
        result = db.admins.update_one(
            {'email': email},
            {'$set': {'password': hashed_password}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Successfully updated password for admin user: {email}")
            return True
        else:
            logger.warning(f"Password for admin user {email} is already the same or update failed.")
            return False
            
    except Exception as e:
        logger.error(f"Error updating password for admin user {email}: {str(e)}")
        return False
    finally:
        client.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python update_admin_password.py <email> <new_password>")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    print(f"Attempting to update password for admin user: {email}")
    
    if update_admin_password(email, new_password):
        print("Admin password updated successfully!")
    else:
        print("Failed to update admin password. Check the logs for details.")
        sys.exit(1) 