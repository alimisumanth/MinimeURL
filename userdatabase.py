import pymongo

DEFAULT_CONNECTION_URL = "mongodb://localhost:27017/"
DB_NAME = "UserDb"
# Establish a connection with mongoDB
client = pymongo.MongoClient(DEFAULT_CONNECTION_URL)

# Create a DB
dataBase = client[DB_NAME]
COLLECTION_NAME = "Users"
collection = dataBase[COLLECTION_NAME]
record = {'Username': 'admin',
         'password': 'admin',
          'email':'xyz@gmail.com',}

print(type(collection.insert_one(record)))