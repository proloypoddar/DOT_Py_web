from pymongo import MongoClient
from config import Config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_admin_user(email):
    try:
        # Connect to MongoDB
        client = MongoClient(Config.MONGO_URI)
        db = client.myDatabase
        
        # Find admin user
        admin = db.admins.find_one({'email': email})
        if admin:
            logger.info(f"Found admin user: {email}")
            logger.info(f"Created at: {admin.get('created_at', 'N/A')}")
            return True
        else:
            logger.warning(f"Admin user {email} not found")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying admin user: {str(e)}")
        return False
    finally:
        client.close()

if __name__ == '__main__':
    email = 'admin'
    if verify_admin_user(email):
        print(f"Admin user '{email}' exists in the database")
    else:
        print(f"Admin user '{email}' not found in the database") 