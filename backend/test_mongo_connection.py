from pymongo import MongoClient
from config import Config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_mongodb_connection():
    try:
        # Connect to MongoDB
        logger.info(f"Attempting to connect to MongoDB at: {Config.MONGO_URI}")
        client = MongoClient(Config.MONGO_URI)
        
        # Test the connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")
        
        # Get database
        db = client.myDatabase
        
        # Check if admins collection exists
        collections = db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        if 'admins' in collections:
            # Check admin users
            admin_count = db.admins.count_documents({})
            logger.info(f"Number of admin users: {admin_count}")
            
            # List admin users (without passwords)
            admins = list(db.admins.find({}, {'password': 0}))
            logger.info("Admin users:")
            for admin in admins:
                logger.info(f"- Email: {admin.get('email')}, Created at: {admin.get('created_at')}")
        else:
            logger.warning("No 'admins' collection found!")
            
        return True
        
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
        return False
    finally:
        client.close()

if __name__ == '__main__':
    print("Testing MongoDB Connection...")
    if test_mongodb_connection():
        print("\nMongoDB connection test completed successfully!")
    else:
        print("\nMongoDB connection test failed! Check the logs above for details.") 