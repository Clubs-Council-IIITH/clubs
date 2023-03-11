import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List
from datetime import datetime

from db import db

# import all models and types
from otypes import Info
from models import Club, Member
from otypes import (
    NewClubInput,
    SimpleClubInput,
    SimpleClubType,
    FullClubType,
    EditClubInput,
)
from otypes import FullMemberInput, SimpleMemberInput, MemberType


@strawberry.mutation
def createClub(clubInput: NewClubInput, info: Info) -> FullClubType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    input = jsonable_encoder(clubInput.to_pydantic())

    # Change upgrade & create time too
    # Add user with role too, if doesn't exist

    if role in ["cc"]:
        exists = db.clubs.find_one({"cid": input["cid"]})
        if exists:
            raise Exception("A club with this cid already exists")

        created_id = db.clubs.insert_one(input).inserted_id
        created_sample = Club.parse_obj(db.clubs.find_one({"_id": created_id}))

        return SimpleClubType.from_pydantic(created_sample)
    else:
        raise Exception("Not Authenticated to access this API")


@strawberry.mutation
def editClub(clubInput: EditClubInput, info: Info) -> FullClubType:
    user = info.context.user
    role = user["role"]

    role = user["role"]
    uid = user["uid"]
    input = jsonable_encoder(clubInput.to_pydantic())

    if role in ["cc"]:
        exists = db.clubs.find_one({"cid": input["cid"]})
        if uid != input["cid"] and exists:
            raise Exception("A club with this cid already exists")

        input["state"] = exists["state"]

        db.clubs.replace_one({"cid": uid}, input)
        db.clubs.update_one(
            {"cid": input["cid"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow,
                }
            },
        )

        result = Club.parse_obj(db.clubs.find_one({"cid": input["cid"]}))
        return FullClubType.from_pydantic(result)

    elif role in ["club"] and user["uid"] == input["cid"]:
        exists = db.clubs.find_one({"cid": input["cid"]})
        if uid != input["cid"]:
            raise Exception("Authentication Error! (CID CHANGED)")

        if input["name"] != exists["name"] or input["email"] != exists["email"]:
            raise Exception(
                "You don't have permission to change the name/email of the club. Please contact CC for it"
            )

        if input["category"] != exists["category"]:
            raise Exception("Only CC is allowed to change the category of club.")

        input["state"] = exists["state"]

        db.clubs.replace_one({"cid": uid}, input)
        db.clubs.update_one(
            {"cid": input["cid"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow,
                }
            },
        )

        result = Club.parse_obj(db.clubs.find_one({"cid": input["cid"]}))
        return FullClubType.from_pydantic(result)
    else:
        raise Exception("Not Authenticated to access this API")


@strawberry.mutation
def deleteClub(clubInput: SimpleClubInput, info: Info) -> SimpleClubType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    input = jsonable_encoder(clubInput)

    if role not in ["cc"]:
        raise Exception("Not Authenticated to access this API")

    db.clubs.update_one(
        {"cid": input["cid"]},
        {"$set": {"state": "deleted", "updated_time": datetime.utcnow}},
    )

    created_sample = Club.parse_obj(db.clubs.find_one({"cid": input["cid"]}))

    return SimpleClubType.from_pydantic(created_sample)


# CHANGE POSTERs API


@strawberry.mutation
def createMember(memberInput: FullMemberInput, info: Info) -> MemberType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]
    input = jsonable_encoder(memberInput.to_pydantic())

    if input["cid"] != uid and role != "club":
        raise Exception("Not Authenticated to access this API")

    input["end_year"] = 1 + input["start_year"]

    # DB STUFF
    created_id = db.members.insert_one(input).inserted_id

    created_sample = Member.parse_obj(
        db.members.find_one({"_id": created_id}, {"_id": 0})
    )

    return MemberType.from_pydantic(created_sample)


@strawberry.mutation
def deleteMember(memberInput: SimpleMemberInput, info: Info) -> MemberType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]
    input = jsonable_encoder(memberInput.to_pydantic())

    if input["cid"] != uid and role != "club":
        raise Exception("Not Authenticated to access this API")

    # DB STUFF
    created_id = db.clubs.update_one(
        {
            "$and": [
                {"cid": input["cid"]},
                {"uid": input["uid"]},
                {"start_year": input["start_year"]},
            ]
        },
        {"$set": {"deleted": True}},
    )

    created_sample = Member.parse_obj(db.members.find_one({"_id": created_id}))

    return Member.from_pydantic(created_sample)


@strawberry.mutation
def approveMember(memberInput: SimpleMemberInput, info: Info) -> MemberType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]
    input = jsonable_encoder(memberInput.to_pydantic())

    if input["cid"] != uid and role != "club":
        raise Exception("Not Authenticated to access this API")

    # DB STUFF
    created_id = db.clubs.update_one(
        {
            "$and": [
                {"cid": input["cid"]},
                {"uid": input["uid"]},
                {"start_year": input["start_year"]},
                {"deleted": False},
            ]
        },
        {"$set": {"approved": True}},
    )

    created_sample = Member.parse_obj(db.members.find_one({"_id": created_id}))

    return Member.from_pydantic(created_sample)


@strawberry.mutation
def editMember(memberInput: FullMemberInput, info: Info) -> List[MemberType]:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]
    input = jsonable_encoder(memberInput.to_pydantic())

    if input["cid"] != uid and role != "club":
        raise Exception("Not Authenticated to access this API")

    input["end_year"] = 1 + input["start_year"]

    # DB STUFF
    db.clubs.replace_one(
        {
            "$and": [
                {"cid": input["cid"]},
                {"uid": input["uid"]},
                {"start_year": input["start_year"]},
                {"deleted": False},
            ]
        },
        input,
    )

    updated_sample = Member.parse_obj(db.samples.find_one({"cid": uid}))

    return Member.from_pydantic(updated_sample)


# register all mutations
mutations = [
    createClub,
    editClub,
    deleteClub,
    createMember,
    deleteMember,
    approveMember,
    editMember,
]
