import strawberry

from fastapi.encoders import jsonable_encoder
from typing import List
from datetime import datetime
import requests

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


def updateRole(uid, cookies=None, role="club"):
    try:
        query = """
                    mutation UpdateRole($roleInput: RoleInput!) {
                        updateRole(roleInput: $roleInput)
                    }
                """
        variables = {
            "roleInput": {
                "role": role,
                "uid": uid,
            }
        }
        if cookies:
            result = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables},
                cookies=cookies
            )
        else:
            result = requests.post(
                "http://gateway/graphql",
                json={"query": query, "variables": variables}
            )
    except:
        pass


@strawberry.mutation
def createClub(clubInput: NewClubInput, info: Info) -> SimpleClubType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    input = jsonable_encoder(clubInput.to_pydantic())

    if role in ["cc"]:
        exists = db.clubs.find_one({"cid": input["cid"]})
        if exists:
            raise Exception("A club with this cid already exists")

        created_id = db.clubs.insert_one(input).inserted_id
        created_sample = Club.parse_obj(db.clubs.find_one({"_id": created_id}))

        updateRole(input["cid"], info.context.cookies)

        return SimpleClubType.from_pydantic(created_sample)

    else:
        raise Exception("Not Authenticated to access this API")


@strawberry.mutation
def editClub(clubInput: EditClubInput, info: Info) -> FullClubType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]

    input = jsonable_encoder(clubInput.to_pydantic())

    if role in ["cc"]:
        exists = db.clubs.find_one({"cid": input["cid"]})
        if not exists:
            raise Exception("A club with this cid doesn't exists")

        input["state"] = exists["state"]
        input["_id"] = exists["_id"]

        db.clubs.replace_one({"cid": input["cid"]}, input)
        if "socials" in input.keys():
            db.clubs.update_one(
                {"cid": input["cid"]},
                {
                    "$set": {
                        "socials.website": input["socials"]["website"],
                        "socials.instagram": input["socials"]["instagram"],
                        "socials.facebook": input["socials"]["facebook"],
                        "socials.youtube": input["socials"]["youtube"],
                        "socials.twitter": input["socials"]["twitter"],
                        "socials.linkedin": input["socials"]["linkedin"],
                        "socials.discord": input["socials"]["discord"],
                        "socials.other_links": input["socials"]["other_links"],
                    }
                },
            )
        db.clubs.update_one(
            {"cid": input["cid"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow(),
                }
            },
        )

        result = Club.parse_obj(db.clubs.find_one({"cid": input["cid"]}))
        return FullClubType.from_pydantic(result)

    elif role in ["club"]:
        exists = db.clubs.find_one({"cid": input["cid"]})
        if uid != input["cid"]:
            raise Exception("Authentication Error! (CID CHANGED)")

        if input["name"] != exists["name"] or input["email"] != exists["email"]:
            raise Exception(
                "You don't have permission to change the name/email of the club. Please contact CC for it"
            )

        if input["category"] != exists["category"]:
            raise Exception(
                "Only CC is allowed to change the category of club.")

        input["state"] = exists["state"]
        input["_id"] = exists["_id"]

        db.clubs.replace_one({"cid": uid}, input)
        if "socials" in input.keys():
            db.clubs.update_one(
                {"cid": input["cid"]},
                {
                    "$set": {
                        "socials.website": input["socials"]["website"],
                        "socials.instagram": input["socials"]["instagram"],
                        "socials.facebook": input["socials"]["facebook"],
                        "socials.youtube": input["socials"]["youtube"],
                        "socials.twitter": input["socials"]["twitter"],
                        "socials.linkedin": input["socials"]["linkedin"],
                        "socials.discord": input["socials"]["discord"],
                        "socials.other_links": input["socials"]["other_links"],
                    }
                },
            )
        db.clubs.update_one(
            {"cid": input["cid"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow(),
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
        {"$set": {"state": "deleted", "updated_time": datetime.utcnow()}},
    )

    updateRole(input["cid"], info.context.cookies, "public")

    created_sample = Club.parse_obj(db.clubs.find_one({"cid": input["cid"]}))

    return SimpleClubType.from_pydantic(created_sample)


@strawberry.mutation
def restartClub(clubInput: SimpleClubInput, info: Info) -> SimpleClubType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    input = jsonable_encoder(clubInput)

    if role not in ["cc"]:
        raise Exception("Not Authenticated to access this API")

    db.clubs.update_one(
        {"cid": input["cid"]},
        {"$set": {"state": "active", "updated_time": datetime.utcnow()}},
    )

    updateRole(input["cid"], info.context.cookies, "club")

    created_sample = Club.parse_obj(db.clubs.find_one({"cid": input["cid"]}))

    return SimpleClubType.from_pydantic(created_sample)


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

    return MemberType.from_pydantic(created_sample)


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

    return MemberType.from_pydantic(created_sample)


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

    return MemberType.from_pydantic(updated_sample)


# register all mutations
mutations = [
    createClub,
    editClub,
    deleteClub,
    restartClub,
    createMember,
    deleteMember,
    approveMember,
    editMember,
]
