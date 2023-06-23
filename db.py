from os import getenv

from pymongo import MongoClient


# get mongodb URI and database name from environment variale
MONGO_URI = "mongodb://{}:{}@mongo:{}/".format(
    getenv("MONGO_USERNAME", default="username"),
    getenv("MONGO_PASSWORD", default="password"),
    getenv("MONGO_PORT", default="27017")
)
MONGO_DATABASE = getenv("MONGO_DATABASE", default="default")

# instantiate mongo client
client = MongoClient(MONGO_URI)

# get database
db = client[MONGO_DATABASE]

# TODO: document and properly handle error
try:
    db.clubs.create_index([("cid", 1)], unique= True, name="unique_clubs")
    db.members.create_index([("cid", 1),("uid", 1)], unique= True, name="unique_members")
    print(db.clubs.index_information())  
    print(db.members.index_information())
except:
    pass
