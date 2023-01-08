import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List

from db import db

# import all models and types
from models import Sample
from otypes import Info, SampleQueryInput, SampleType

from models import Club, Member
from otypes import SimpleClubType, FullClubType, SimpleClubInput

# sample query
@strawberry.field
def sampleQuery(sampleInput: SampleQueryInput, info: Info) -> SampleType:
    user = info.context.user
    print("user:", user)

    sample = jsonable_encoder(sampleInput.to_pydantic())

    # query from database
    found_sample = db.samples.find_one({"_id": sample["_id"]})

    # handle missing sample
    if found_sample:
        found_sample = Sample.parse_obj(found_sample)
        return SampleType.from_pydantic(found_sample)

    else:
        raise Exception("Sample not found!")


"""
async def retrieve_clubs(active:bool, pending:bool):
    clubs = []
    async for student in student_collection.find():
        clubs.append(student_helper(student))
    return clubs
"""
@strawberry.field
def getAllClubs(info: Info) -> List[SimpleClubType]:
    user = info.context.user
    # role = user["role"]

    results = db.clubs.find()
    # If not cc/club, then find with condition of only active clubs

    if results:
        clubs = []
        for result in results:
            clubs.append(SimpleClubType.from_pydantic(Club.parse_obj(result)))
        return clubs
    else:
        raise Exception("No Club Result Found")


@strawberry.field
def getDeletedClubs(info: Info) -> List[SimpleClubType]:
    user = info.context.user
    # role = user["role"]

    results = db.clubs.find({"state": "deleted"})
    # If not cc, error

    if results:
        clubs = []
        for result in results:
            clubs.append(SimpleClubType.from_pydantic(Club.parse_obj(result)))
        return clubs
    else:
        raise Exception("No Club Result Found")


@strawberry.field
def getClub(clubInput: SimpleClubInput, info: Info) -> FullClubType:
    user = info.context.user
    # role = user["role"]

    input = jsonable_encoder(clubInput)

    result = db.clubs.find_one({"cid": input["cid"]})
    # Query mongodb based on roles

    if result:
        result = Club.parse_obj(result)
        return FullClubType.from_pydantic(result)
    else:
        raise Exception("No Club Result Found")


"""
@strawberry.field
def getMembers(clubInput: SimpleClubInput, info: Info) -> List[MemberType]:
    user = info.context.user
    # role = user["role"]

    input = jsonable_encoder(clubInput.to_pydantic())

    result = 0  # Query mongodb based on roles

    if result:
        result = Member.parse_obj(result)
        return Member.from_pydantic(result)
    else:
        raise Exception("No Member Result Found")


@strawberry.field
def getPendingMembers(info: Info) -> List[MemberType]:
    user = info.context.user
    # role = user["role"]

    result = 0  # Query mongodb based on roles

    if result:
        result = Member.parse_obj(result)
        return Member.from_pydantic(result)
    else:
        raise Exception("No Member Result Found")
"""

# register all queries
queries = [
    getAllClubs,
    getDeletedClubs,
    getClub
]


# def getUserMeta(userInput: UserInput) -> UserMetaType:
#     user = jsonable_encoder(userInput)

#     # query database for user
#     found_user = db.users.find_one({"uid": user["uid"]})

#     # if user doesn't exist, add to database
#     if found_user:
#         found_user = User.parse_obj(found_user)
#     else:
#         found_user = User(uid=user["uid"])
#         db.users.insert_one(jsonable_encoder(found_user))

#     return UserMetaType.from_pydantic(found_user)
