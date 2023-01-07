import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List

from db import db

# import all models and types
from models import Sample
from otypes import Info, SampleQueryInput, SampleType

"""
from models import Club, Member
from otypes import SimpleClubType, FullClubType, SimpleClubInput
"""

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
@strawberry.field
def getAllClubs(info: Info) -> SimpleClubType:
    user = info.context.user
    # role = user["role"]

    result = 0  # Query mongodb based on roles

    if result:
        result = Club.parse_obj(result)
        return SimpleClubType.from_pydantic(result)
    else:
        raise Exception("No Club Result Found")


@strawberry.field
def getPendingClubs(info: Info) -> SimpleClubType:
    user = info.context.user
    # role = user["role"]

    result = 0  # Query mongodb based on cc role only

    if result:
        result = Club.parse_obj(result)
        return SimpleClubType.from_pydantic(result)
    else:
        raise Exception("No Club Result Found")


@strawberry.field
def getClub(clubInput: SimpleClubInput, info: Info) -> FullClubType:
    user = info.context.user
    # role = user["role"]

    input = jsonable_encoder(clubInput.to_pydantic())

    result = 0  # Query mongodb based on roles

    if result:
        result = Club.parse_obj(result)
        return FullClubType.from_pydantic(result)
    else:
        raise Exception("No Club Result Found")


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
    sampleQuery,
]
