import pymongo
import certifi
import sqlite3

# Database helper function
def get_db_connection():
    conn = sqlite3.connect('./data/users.db')
    conn.row_factory = sqlite3.Row
    return conn

ca = certifi.where()

# Connect to MongoDB (Assuming MongoDB is running locally and using the default port)
client = pymongo.MongoClient("Enter your MongoDB connection here!")
db = client["uploads"]
collection = db["transactions"]
result_collection = db["results"]
user_collection = db["users"]

# Call the main function to test the connection
if __name__ == "__main__":
    # Test the connection
    try:
        # Check if the client is connected
        if client.is_mongos:
            print("Connected to MongoDB cluster as a mongos")
        else:
            print("Connected to MongoDB cluster as a standalone")

        # Check if the database exists
        if db.list_collection_names():
            print("Connected to database:", db.name)
            print("Collections in the database:", db.list_collection_names())
        else:
            print("Database does not exist or is empty")

        # Check if the collections exist
        if collection.name in db.list_collection_names():
            print("Collection", collection.name, "exists")
        else:
            print("Collection", collection.name, "does not exist")

        if result_collection.name in db.list_collection_names():
            print("Collection", result_collection.name, "exists")
        else:
            print("Collection", result_collection.name, "does not exist")

    except pymongo.errors.ConnectionFailure:
        print("Failed to connect to MongoDB cluster")

    # Close the connection
    client.close()
