import certifi
import pymongo

ca = certifi.where()

# Connect to MongoDB (Assuming MongoDB is running locally and using the default port)
client = pymongo.MongoClient(
    "mongodb+srv://haochenluo02:CMaR2qx2cwL7GO2H@cluster0.3xts8ev.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["uploads"]

# Remove all records from the "transactions" collection
transactions_collection = db["transactions"]
transactions_collection.delete_many({})

# Remove all records from the "results" collection
results_collection = db["results"]
results_collection.delete_many({})

# Remove all records from the "users" collection
users_collection = db["users"]
users_collection.delete_many({})

# Print a message indicating the cleanup is complete
print("Cleanup complete. All records removed.")
