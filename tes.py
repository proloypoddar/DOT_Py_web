from pymongo import MongoClient
from backend.config import Config

def test_mongodb_connection():
    try:
        client = MongoClient(Config.MONGO_URI)
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")

        # List all databases with their sizes
        print("\n📊 Databases in your MongoDB cluster:")
        print("-" * 50)
        for db_name in client.list_database_names():
            db = client[db_name]
            # Get database stats
            stats = db.command("dbStats")
            size_in_mb = stats['dataSize'] / (1024 * 1024)  # Convert to MB
            collections = db.list_collection_names()
            print(f"\nDatabase: {db_name}")
            print(f"Size: {size_in_mb:.2f} MB")
            print(f"Collections ({len(collections)}):")
            for coll in collections:
                # Get collection stats
                coll_stats = db.command("collstats", coll)
                coll_size_mb = coll_stats['size'] / (1024 * 1024)  # Convert to MB
                doc_count = coll_stats['count']
                print(f"  - {coll}")
                print(f"    Documents: {doc_count}")
                print(f"    Size: {coll_size_mb:.2f} MB")
            print("-" * 50)

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_mongodb_connection()
