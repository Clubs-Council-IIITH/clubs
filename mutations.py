import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List

from db import db

# import all models and types
from models import Sample
from otypes import Info, SampleMutationInput, SampleType

"""
from models import Club, Member
from otypes import NewClubInput, SimpleClubInput, SimpleClubType, FullClubType
from otypes import FullMemberInput, SimpleMemberInput
"""

# sample mutation
@strawberry.mutation
def sampleMutation(sampleInput: SampleMutationInput) -> SampleType:
    sample = jsonable_encoder(sampleInput.to_pydantic())

    # add to database
    created_id = db.samples.insert_one(sample).inserted_id

    # query from database
    created_sample = Sample.parse_obj(db.samples.find_one({"_id": created_id}))

    return SampleType.from_pydantic(created_sample)


"""
@strawberry.mutation
def createClub(clubInput: NewClubInput) -> SimpleClubType:
    input = jsonable_encoder(clubInput.to_pydantic())

    # DB STUFF
    # Change upgrade & create time too
    # Add user with role too
    created_id = 0

    created_sample = Club.parse_obj(db.samples.find_one({"_id": created_id}))

    return SimpleClubType.from_pydantic(created_sample)


@strawberry.mutation
def editClub(clubInput: NewClubInput, info: Info) -> FullClubType:
    user = info.context.user
    # role = user["role"]

    input = jsonable_encoder(clubInput.to_pydantic())

    # DB STUFF
    # Change entries only as per the roles
    # Change upgrade time too
    created_id = 0

    created_sample = Club.parse_obj(db.samples.find_one({"_id": created_id}))

    return FullClubType.from_pydantic(created_sample)


@strawberry.mutation
def deleteClub(clubInput: SimpleClubInput, info: Info) -> SimpleClubType:
    user = info.context.user
    # role = user["role"]

    input = jsonable_encoder(clubInput.to_pydantic())

    # DB STUFF
    # Change upgrade time too
    created_id = 0

    created_sample = Club.parse_obj(db.samples.find_one({"_id": created_id}))

    return SimpleClubType.from_pydantic(created_sample)

# CHANGE POSTER

@strawberry.mutation
def createMember(memberInput: FullMemberInput, info: Info) -> List[Member]:
    user = info.context.user
    # role = user["role"]

    input = jsonable_encoder(memberInput.to_pydantic())

    # DB STUFF
    created_id = 0

    created_sample = Member.parse_obj(
        db.samples.find_one({"_id": created_id}))

    return Member.from_pydantic(created_sample)


@strawberry.mutation
def editMember(memberInput: FullMemberInput, info: Info) -> List[Member]:
    user = info.context.user
    # role = user["role"]

    input = jsonable_encoder(memberInput.to_pydantic())

    # DB STUFF
    created_id = 0

    created_sample = Member.parse_obj(
        db.samples.find_one({"_id": created_id}))

    return Member.from_pydantic(created_sample)


@strawberry.mutation
def deleteMember(memberInput: SimpleMemberInput, info: Info) -> List[Member]:
    user = info.context.user
    # role = user["role"]

    input = jsonable_encoder(memberInput.to_pydantic())

    # DB STUFF
    created_id = 0

    created_sample = Member.parse_obj(
        db.samples.find_one({"_id": created_id}))

    return Member.from_pydantic(created_sample)


@strawberry.mutation
def approveMember(memberInput: SimpleMemberInput, info: Info) -> List[Member]:
    user = info.context.user
    # role = user["role"]

    input = jsonable_encoder(memberInput.to_pydantic())

    # DB STUFF
    created_id = 0

    created_sample = Member.parse_obj(
        db.samples.find_one({"_id": created_id}))

    return Member.from_pydantic(created_sample)
"""


# register all mutations
mutations = [
    sampleMutation,
]
