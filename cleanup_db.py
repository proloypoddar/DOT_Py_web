from pymongo import MongoClient
from backend.config import Config

def cleanup_databases():
    try:
        # Connect to MongoDB
        client = MongoClient(Config.MONGO_URI)
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")

        # List all databases
        databases = client.list_database_names()
        print("\n📊 Current databases:")
        for db_name in databases:
            print(f" - {db_name}")

        # Drop sample_mflix database if it exists
        if 'sample_mflix' in databases:
            client.drop_database('sample_mflix')
            print("\n✅ Dropped 'sample_mflix' database")

        # Keep only myDatabase and admin (system database)
        print("\n📊 Remaining databases:")
        for db_name in client.list_database_names():
            print(f" - {db_name}")

        # Clean up collections in myDatabase
        db = client['myDatabase']
        collections = db.list_collection_names()
        
        # Drop all collections except essential ones
        essential_collections = {'courses', 'enrollments', 'contacts', 'gallery', 'content'}
        for coll in collections:
            if coll not in essential_collections:
                db[coll].drop()
                print(f"✅ Dropped collection: {coll}")

        print("\n📊 Collections in myDatabase:")
        for coll in db.list_collection_names():
            print(f" - {coll}")

        print("\n✨ Database cleanup completed successfully!")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    cleanup_databases() 