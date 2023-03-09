import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List

from db import db

# import all models and types
from models import Sample
from otypes import Info, SampleQueryInput, SampleType

from models import Club, Member
from otypes import SimpleClubType, FullClubType, SimpleClubInput
from otypes import MemberType

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


@strawberry.field
def getAllClubs(info: Info) -> List[SimpleClubType]:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")
    
    role = user["role"]

    results = None

    if role in ["public", "club", "slc", "slo"]:
        results = db.clubs.find({"state": "active"})
    elif role in ["cc",]:
        results = db.clubs.find()

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
    if user is None:
        raise Exception("Not Authenticated")
    
    role = user["role"]

    results = None

    if role in ["cc",]:
        results = db.clubs.find({"state": "deleted"})
    else:
        raise Exception("Not Authenticated to access this API")

    if results:
        clubs = []
        for result in results:
            clubs.append(SimpleClubType.from_pydantic(Club.parse_obj(result)))
        return clubs
    else:
        raise Exception("No Club Result Found")


@strawberry.field
def getActiveClubs(info: Info) -> List[SimpleClubType]:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]

    results = None

    if role in ["public", "club", "slc", "slo", "cc"]:
        results = db.clubs.find({"state": "active"})

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
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]

    input = jsonable_encoder(clubInput)

    result = db.clubs.find_one({"cid": input["cid"]})

    if role not in ["cc",] and result["state"] == "deleted":
        result = None

    if result:
        result = Club.parse_obj(result)
        return FullClubType.from_pydantic(result)
    else:
        raise Exception("No Club Result Found")


@strawberry.field
def getMembers(clubInput: SimpleClubInput, info: Info) -> List[MemberType]:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]

    results = None
    input = jsonable_encoder(clubInput)

    if role in ["cc", ]:
        results = db.members.find(
            {"$and": [{"cid": input["cid"]}, {"deleted": False}]}, {"_id": 0})
    elif role in ["club", ] and user["uid"] == input["cid"]:
        results = db.members.find(
            {"$and": [{"cid": input["cid"]}, {"deleted": False}]}, {"_id": 0})
    else:
        results = db.members.find({"$and": [{"cid": input["cid"]}, {
            "deleted": False}, {"approved": True}]}, {"_id": 0})

    if results:
        members = []
        for result in results:
            members.append(MemberType.from_pydantic(Member.parse_obj(result)))
        return members
    else:
        raise Exception("No Member Result Found")


@strawberry.field
def getPendingMembers(info: Info) -> List[MemberType]:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]

    results = None

    if role in ["cc",]:
        results = db.members.find(
            {"$and": [{"approved": False}, {"deleted": False}]}, {"_id": 0})

    if results:
        members = []
        for result in results:
            members.append(MemberType.from_pydantic(Member.parse_obj(result)))
        return members
    else:
        raise Exception("No Member Result Found")


# register all queries
queries = [
    getAllClubs,
    getDeletedClubs,
    getActiveClubs,
    getClub,
    getMembers,
    getPendingMembers
]
