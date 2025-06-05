from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from config import Config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_admin_user(email, password):
    try:
        # Connect to MongoDB
        client = MongoClient(Config.MONGO_URI)
        db = client.myDatabase
        
        # Check if admin already exists
        existing_admin = db.admins.find_one({'email': email})
        if existing_admin:
            logger.warning(f"Admin user with email {email} already exists")
            return False
        
        # Create new admin user
        admin_data = {
            'email': email,
            'password': generate_password_hash(password),
            'created_at': datetime.utcnow()
        }
        
        result = db.admins.insert_one(admin_data)
        if result.inserted_id:
            logger.info(f"Successfully created admin user: {email}")
            return True
        else:
            logger.error("Failed to create admin user")
            return False
            
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        return False
    finally:
        client.close()

if __name__ == '__main__':
    import sys
    from datetime import datetime
    
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    if create_admin_user(email, password):
        print("Admin user created successfully!")
    else:
        print("Failed to create admin user. Check the logs for details.")
        sys.exit(1) 