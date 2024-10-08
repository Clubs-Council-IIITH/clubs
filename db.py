from os import getenv

from pymongo import MongoClient

# get mongodb URI and database name from environment variale
MONGO_URI = "mongodb://{}:{}@mongo:{}/".format(
    getenv("MONGO_USERNAME", default="username"),
    getenv("MONGO_PASSWORD", default="password"),
    getenv("MONGO_PORT", default="27017"),
)
MONGO_DATABASE = getenv("MONGO_DATABASE", default="default")

# instantiate mongo client
client = MongoClient(MONGO_URI)

# get database
db = client[MONGO_DATABASE]
clubsdb = db.clubs

try:
    # check if the clubs index exists
    if "unique_clubs" in clubsdb.index_information():
        print("The clubs index exists.")
    else:
        # create the index
        clubsdb.create_index([("cid", 1)], unique=True, name="unique_clubs")
        print("The clubs index was created.")

    print(clubsdb.index_information())
except Exception:
    pass
