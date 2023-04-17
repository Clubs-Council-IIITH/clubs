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
    FullClubInput,
    SimpleClubInput,
    SimpleClubType,
    FullClubType,
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
                cookies=cookies,
            )
        else:
            result = requests.post(
                "http://gateway/graphql", json={"query": query, "variables": variables}
            )
    except:
        pass


@strawberry.mutation
def createClub(clubInput: FullClubInput, info: Info) -> SimpleClubType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    club_input = jsonable_encoder(clubInput.to_pydantic())

    if role in ["cc"]:
        exists = db.clubs.find_one({"cid": club_input["cid"]})
        if exists:
            raise Exception("A club with this cid already exists")

        created_id = db.clubs.insert_one(club_input).inserted_id
        created_sample = Club.parse_obj(db.clubs.find_one({"_id": created_id}))

        updateRole(club_input["cid"], info.context.cookies)

        return SimpleClubType.from_pydantic(created_sample)

    else:
        raise Exception("Not Authenticated to access this API")


@strawberry.mutation
def editClub(clubInput: FullClubInput, info: Info) -> FullClubType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]

    club_input = jsonable_encoder(clubInput.to_pydantic())

    if role in ["cc"]:
        exists = db.clubs.find_one({"cid": club_input["cid"]})
        if not exists:
            raise Exception("A club with this cid doesn't exists")

        club_input["state"] = exists["state"]
        club_input["_id"] = exists["_id"]

        db.clubs.replace_one({"cid": club_input["cid"]}, club_input)
        if "socials" in club_input.keys():
            db.clubs.update_one(
                {"cid": club_input["cid"]},
                {
                    "$set": {
                        "socials.website": club_input["socials"]["website"],
                        "socials.instagram": club_input["socials"]["instagram"],
                        "socials.facebook": club_input["socials"]["facebook"],
                        "socials.youtube": club_input["socials"]["youtube"],
                        "socials.twitter": club_input["socials"]["twitter"],
                        "socials.linkedin": club_input["socials"]["linkedin"],
                        "socials.discord": club_input["socials"]["discord"],
                        "socials.other_links": club_input["socials"]["other_links"],
                    }
                },
            )
        db.clubs.update_one(
            {"cid": club_input["cid"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow(),
                }
            },
        )

        result = Club.parse_obj(db.clubs.find_one({"cid": club_input["cid"]}))
        return FullClubType.from_pydantic(result)

    elif role in ["club"]:
        exists = db.clubs.find_one({"cid": club_input["cid"]})
        if uid != club_input["cid"]:
            raise Exception("Authentication Error! (CID CHANGED)")

        if (
            club_input["name"] != exists["name"]
            or club_input["email"] != exists["email"]
        ):
            raise Exception(
                "You don't have permission to change the name/email of the club. Please contact CC for it"
            )

        if club_input["category"] != exists["category"]:
            raise Exception(
                "Only CC is allowed to change the category of club.")

        club_input["state"] = exists["state"]
        club_input["_id"] = exists["_id"]

        db.clubs.replace_one({"cid": uid}, club_input)
        if "socials" in club_input.keys():
            db.clubs.update_one(
                {"cid": club_input["cid"]},
                {
                    "$set": {
                        "socials.website": club_input["socials"]["website"],
                        "socials.instagram": club_input["socials"]["instagram"],
                        "socials.facebook": club_input["socials"]["facebook"],
                        "socials.youtube": club_input["socials"]["youtube"],
                        "socials.twitter": club_input["socials"]["twitter"],
                        "socials.linkedin": club_input["socials"]["linkedin"],
                        "socials.discord": club_input["socials"]["discord"],
                        "socials.other_links": club_input["socials"]["other_links"],
                    }
                },
            )
        db.clubs.update_one(
            {"cid": club_input["cid"]},
            {
                "$set": {
                    "created_time": exists["created_time"],
                    "updated_time": datetime.utcnow(),
                }
            },
        )

        result = Club.parse_obj(db.clubs.find_one({"cid": club_input["cid"]}))
        return FullClubType.from_pydantic(result)

    else:
        raise Exception("Not Authenticated to access this API")


@strawberry.mutation
def deleteClub(clubInput: SimpleClubInput, info: Info) -> SimpleClubType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    club_input = jsonable_encoder(clubInput)

    if role not in ["cc"]:
        raise Exception("Not Authenticated to access this API")

    db.clubs.update_one(
        {"cid": club_input["cid"]},
        {"$set": {"state": "deleted", "updated_time": datetime.utcnow()}},
    )

    updateRole(club_input["cid"], info.context.cookies, "public")

    created_sample = Club.parse_obj(
        db.clubs.find_one({"cid": club_input["cid"]}))

    return SimpleClubType.from_pydantic(created_sample)


@strawberry.mutation
def restartClub(clubInput: SimpleClubInput, info: Info) -> SimpleClubType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    club_input = jsonable_encoder(clubInput)

    if role not in ["cc"]:
        raise Exception("Not Authenticated to access this API")

    db.clubs.update_one(
        {"cid": club_input["cid"]},
        {"$set": {"state": "active", "updated_time": datetime.utcnow()}},
    )

    updateRole(club_input["cid"], info.context.cookies, "club")

    created_sample = Club.parse_obj(
        db.clubs.find_one({"cid": club_input["cid"]}))

    return SimpleClubType.from_pydantic(created_sample)


def unique_roles_id(uid, cid):
    pipeline = [
        {
            "$set": {
                "roles": {
                    "$map": {
                        "input": {"$range": [0, {"$size": "$roles"}]},
                        "in": {
                            "$mergeObjects": [
                                {"$arrayElemAt": ["$roles", "$$this"]},
                                {"roleid": {"$toString":
                                            {"$add": [{"$toLong": datetime.now()}, "$$this"]}}}
                            ]
                        }
                    }
                }
            }
        }
    ]
    db.members.update_one({
        "$and": [
            {"cid": cid},
            {"uid": uid},
        ]
    }, pipeline)


@strawberry.mutation
def createMember(memberInput: FullMemberInput, info: Info) -> MemberType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    role = user["role"]
    uid = user["uid"]
    member_input = jsonable_encoder(memberInput.to_pydantic())

    if member_input["cid"] != uid and role != "club":
        raise Exception("Not Authenticated to access this API")

    if db.members.find_one({
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]}):
        raise Exception("A record with same uid and cid already exists")

    # DB STUFF
    created_id = db.members.insert_one(member_input).inserted_id
    unique_roles_id(member_input["uid"], member_input["cid"])

    created_sample = Member.parse_obj(
        db.members.find_one({"_id": created_id}, {"_id": 0})
    )

    return MemberType.from_pydantic(created_sample)


@strawberry.mutation
def editMember(memberInput: FullMemberInput, info: Info) -> MemberType:
    user = info.context.user
    if user is None:
        raise Exception("Not Authenticated")

    uid = user["uid"]
    member_input = jsonable_encoder(memberInput.to_pydantic())

    if member_input["cid"] != uid and user["role"] != "club":
        raise Exception("Not Authenticated to access this API")

    roles = []
    for role in member_input["roles"]:
        if role["start_year"] > datetime.now().year:
            role["start_year"] = datetime.now().year
            role["end_year"] = None
        roles.append(role)

    # DB STUFF
    db.members.update_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"$set": {
            "roles": roles,
            "poc": member_input["poc"]
        }}
    )

    updated_sample = db.members.find_one(
        {
            "$and": [
                {"cid": member_input["cid"]},
                {"uid": member_input["uid"]},
            ]
        },
        {"_id": 0}
    )
    if updated_sample == None:
        raise Exception("No such Record")

    roles = []
    for i in updated_sample['roles']:
        if i['deleted'] == True:
            continue
        roles.append(i)
    updated_sample['roles'] = roles

    return MemberType.from_pydantic(Member.parse_obj(updated_sample))


# @strawberry.mutation
# def deleteMember(memberInput: SimpleMemberInput, info: Info) -> MemberType:
#     user = info.context.user
#     if user is None:
#         raise Exception("Not Authenticated")

#     role = user["role"]
#     uid = user["uid"]
#     member_input = jsonable_encoder(memberInput.to_pydantic())

#     if member_input["cid"] != uid and role != "club":
#         raise Exception("Not Authenticated to access this API")

#     # DB STUFF
#     db.members.update_one(
#         {
#             "$and": [
#                 {"cid": member_input["cid"]},
#                 {"uid": member_input["uid"]},
#                 {"role": member_input["role"]},
#                 {"start_year": member_input["start_year"]},
#             ]
#         },
#         {"$set": {"deleted": True}},
#     )

#     updated_sample = db.members.find_one(
#         {
#             "$and": [
#                 {"cid": member_input["cid"]},
#                 {"uid": member_input["uid"]},
#                 {"role": member_input["role"]},
#                 {"start_year": member_input["start_year"]},
#             ]
#         },
#         {"_id": 0},
#     )

#     if updated_sample == None:
#         raise Exception("No such Record")

#     return MemberType.from_pydantic(Member.parse_obj(updated_sample))


# @strawberry.mutation
# def approveMember(memberInput: SimpleMemberInput, info: Info) -> MemberType:
#     user = info.context.user
#     if user is None:
#         raise Exception("Not Authenticated")

#     role = user["role"]
#     uid = user["uid"]
#     member_input = jsonable_encoder(memberInput.to_pydantic())

#     if member_input["cid"] != uid and role != "club":
#         raise Exception("Not Authenticated to access this API")

#     # DB STUFF
#     db.members.update_one(
#         {
#             "$and": [
#                 {"cid": member_input["cid"]},
#                 {"uid": member_input["uid"]},
#                 {"start_year": member_input["start_year"]},
#                 {"role": member_input["role"]},
#                 {"deleted": False},
#             ]
#         },
#         {"$set": {"approved": True}},
#     )

#     updated_sample = db.members.find_one(
#         {
#             "$and": [
#                 {"cid": member_input["cid"]},
#                 {"uid": member_input["uid"]},
#                 {"role": member_input["role"]},
#                 {"start_year": member_input["start_year"]},
#                 {"deleted": False},
#             ]
#         },
#         {"_id": 0},
#     )

#     if updated_sample == None:
#         raise Exception("No such Record")

#     return MemberType.from_pydantic(Member.parse_obj(updated_sample))


# @strawberry.mutation
# def leaveClubMember(memberInput: SimpleMemberInput, info: Info) -> MemberType:
#     user = info.context.user
#     if user is None:
#         raise Exception("Not Authenticated")

#     role = user["role"]
#     uid = user["uid"]
#     member_input = jsonable_encoder(memberInput.to_pydantic())

#     if member_input["cid"] != uid and role != "club":
#         raise Exception("Not Authenticated to access this API")

#     created_id = db.clubs.update_one(
#         {
#             "$and": [
#                 {"cid": member_input["cid"]},
#                 {"uid": member_input["uid"]},
#                 {"start_year": member_input["start_year"]},
#                 {"deleted": False},
#             ]
#         },
#         {"$set": {"end_year": datetime.now().year}},
#     )

#     created_sample = Member.parse_obj(db.members.find_one({"_id": created_id}))
#     return MemberType.from_pydantic(created_sample)

# register all mutations
mutations = [
    createClub,
    editClub,
    deleteClub,
    restartClub,
    createMember,
    editMember,
    # deleteMember,
    # approveMember,
]
